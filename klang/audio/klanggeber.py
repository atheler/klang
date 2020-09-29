"""Klang sound engine object."""
from typing import Callable, List
import logging
import time

import numpy as np
import pyaudio

from klang.audio.helpers import INTERVAL, get_silence, get_time
from klang.audio.wavfile import write_wave
from klang.block import Block
from klang.clock import ClockMixin
from klang.config import BUFFER_SIZE, SAMPLING_RATE
from klang.constants import INF
from klang.constants import MONO
from klang.errors import KlangError
from klang.progress_bar import ProgressBar


__all__ = ['ChannelMismatch', 'Adc', 'Dac', 'run_audio_engine']


D_TYPE = np.float32
"""type: Numpy audio sample datatype (has to be compatible with
pyaudio.paFloat32 otherwise bad things will happen!).
"""


PY_AUDIO_CODE_NAMES = {
    value: key
    for key, value in vars(pyaudio).items()
    if isinstance(value, int)
}
"""dict[int, str]: PyAudio error codes to name mapping."""


def look_for_audio_blocks(blocks):
    """Get the first best Adc and Dac blocks.

    Args:
        blocks (list): List of blocks.

    Returns:
        tuple: Adc and dac instances.
    """
    for block in blocks:
        if isinstance(block, Adc):
            adc = block
            break
    else:
        adc = Adc(nChannels=0)

    for block in blocks:
        if isinstance(block, Dac):
            dac = block
            break
    else:
        dac = Dac(nChannels=0)

    return adc, dac


def validate_sound_card_channels(pa, adc, dac):
    """Given the audio input and output blocks determine if we have enough audio
    channels on the default devices.

    Args:
        pa (pyaudio): PyAudio instance.
        adc (Adc): Audio input block.
        dac (dac): Audio output block.
    """
    inputDeviceInfo = pa.get_default_input_device_info()
    if adc.nChannels > inputDeviceInfo['maxInputChannels']:
        raise ValueError('Not enough sound card inputs!')

    outputDeviceInfo = pa.get_default_output_device_info()
    if dac.nChannels > outputDeviceInfo['maxOutputChannels']:
        raise ValueError('Not enough sound card outputs!')


def pack_signals(signals):
    """Interleave samples from multiple mono signals. C contiguous for audio
    card (transposing signals does not work).

    Packed format:
        [[L0, R0]
         [L1, R1]
         [L2, R3]
            ...
         [LN, RN]]
    """
    shape = (BUFFER_SIZE, len(signals))
    ret = np.empty(shape, dtype=D_TYPE)
    for col, samples in enumerate(signals):
        ret[:, col] = samples

    return ret


class ChannelMismatch(KlangError):

    """Can not match received audio signals to output channels."""


class Adc(Block):

    """Sound card audio input."""

    def __init__(self, nChannels):
        super().__init__(nOutputs=nChannels)
        self.nChannels = nChannels
        self.mute_outputs()

    def mute_outputs(self):
        """Mute all output connections."""
        silence = get_silence(BUFFER_SIZE)
        for output in self.outputs:
            output.set_value(silence)

    def inject_samples(self, samples):
        """Inject audio samples into network."""
        for signal, output in zip(samples.T, self.outputs):
            output.set_value(signal)


class Dac(Block):

    """Sound card audio output."""

    def __init__(self, nChannels=MONO):
        super().__init__(nInputs=nChannels)
        self.nChannels = nChannels
        self.mute_inputs()

    def mute_inputs(self):
        """Mute all input connections."""
        silence = get_silence(BUFFER_SIZE)
        for input_ in self.inputs:
            input_.set_value(silence)

    def iterate_channels(self):
        """Iterate over all incoming audio channels (no matter if value
        connections provides a MONO, STEREO or multichannel signal).
        """
        # ndim check implementation is a little faster than iterating over
        # np.atleast_2d(...)
        channelCount = 0
        for input_ in self.inputs:
            val = input_.get_value()
            ndim = np.ndim(val)
            if ndim == MONO:
                yield val
                channelCount += 1
                if channelCount == self.nChannels:
                    return

            elif ndim > MONO:
                for channel in val:
                    yield channel
                    channelCount += 1
                    if channelCount == self.nChannels:
                        return

    def collect_samples(self):
        """Collect audio samples from all incoming connections. Pack them
        together for audio card.

        Returns:
            array: Audio samples (BUFFER_SIZE, nChannels) shaped.
        """
        signals = list(self.iterate_channels())
        if len(signals) != self.nChannels:
            msg = 'Got %d channels. Need %d!' % (len(signals), self.nChannels)
            raise ChannelMismatch(msg)

        return pack_signals(signals)


def run_audio_engine(adc: Adc, dac: Dac, execute_all_blocks: Callable, duration:
                     float = INF, fadeout: float = 0., filepath: str = '',
                     offline: bool = False):
    """Run klang audio engine from adc / dac blocks. Ex-KlangGeber. Can work
    offline and dump the generated audio to a WAV file by the end.

    Args:
        adc: Sound card input block.
        dac: Sound card output block.
        execute_all_blocks: Callback for execOrder execution.

    Kwargs:
        duration: Maximum running duration.
        fadeout: Fadeout time for WAV export.
        filepath: WAV file path. Dumpy audio output to WAV file.
        offline: Render audio offline.
    """
    logger = logging.getLogger('KlangGeber')

    # Setup stream callback
    playTime = 0.
    """Current play time."""

    capturedFrames: List[np.ndarray] = []
    """Captured audio chunks for WAV dump."""

    fadeOutStart = duration - fadeout
    """Start time of fade out."""

    T = get_time(BUFFER_SIZE)

    def fade_out_envelope(t):
        """Create fade-out envelope for a given timestamp."""
        env = np.interp(t + T, [fadeOutStart, duration], [1., 0.], left=1., right=0.)
        return env.reshape(-1, 1)

    def stream_callback(in_data, frame_count, time_info, status):
        """Audio stream callback for PyAudio."""
        nonlocal playTime, capturedFrames
        if status:
            name = PY_AUDIO_CODE_NAMES.get(status, status)
            logger.warning('PyAudio status changed to %s', name)

        # Process input audio samples
        if in_data:
            # TODO: Make me, test me
            raw = np.frombuffer(in_data, dtype=D_TYPE)
            samples = raw.reshape((frame_count, adc.nChannels))
            adc.inject_samples(samples)

        # Trigger global block execution / propagate audio stream callback
        # upwards
        # TODO: Use time_info['current_time'] for clock?
        ClockMixin.set_current_time(playTime)
        execute_all_blocks()

        # Fetch output audio samples from block network
        try:
            outData = dac.collect_samples()
        except ChannelMismatch as err:
            logger.error(err, exc_info=True)
            silence = get_silence((frame_count, dac.nChannels), D_TYPE)
            return silence, pyaudio.paAbort

        if playTime >= fadeOutStart:
            outData *= fade_out_envelope(playTime)

        if filepath:
            capturedFrames.append(outData)

        playTime += INTERVAL
        if playTime >= duration:
            return outData, pyaudio.paComplete

        return outData, pyaudio.paContinue

    if offline:
        logger.info('Offline bouncing.')
        if duration == INF:
            msg = 'Offline mode and duration set to INF. You will never get anything.'
            logger.warning(msg)

        nCycles = int(duration * SAMPLING_RATE // BUFFER_SIZE)
        for _ in ProgressBar.range(nCycles, prefix='Bouncing'):
            stream_callback(None, BUFFER_SIZE, None, 0)

    else:
        # Example: Callback Mode Audio I/O from
        # https://people.csail.mit.edu/hubert/pyaudio/docs/
        pa = pyaudio.PyAudio()
        validate_sound_card_channels(pa, adc, dac)
        assert D_TYPE is np.float32
        capturedFrames = []
        stream = pa.open(
            rate=SAMPLING_RATE,
            frames_per_buffer=BUFFER_SIZE,
            channels=dac.nChannels,  # TODO: How to 1x input, 2x outputs?
            format=pyaudio.paFloat32,
            input=(adc.nChannels > 0),
            output=(dac.nChannels > 0),
            stream_callback=stream_callback,
        )

        try:
            logger.info('Starting up audio engine with default devices')
            stream.start_stream()
            while stream.is_active():
                time.sleep(0.1)

        except KeyboardInterrupt:
            pass

        finally:
            logger.info('Shutting down audio engine')
            stream.stop_stream()
            stream.close()
            pa.terminate()

    if filepath:
        logger.info('Writing audio dump to WAV file %r', filepath)
        samples = np.concatenate(capturedFrames)
        write_wave(samples, filepath)
