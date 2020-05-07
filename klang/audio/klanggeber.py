"""Klang sound engine object."""
import logging
import time

import numpy as np
import pyaudio

from config import BUFFER_SIZE, SAMPLING_RATE
from klang.audio import get_silence
from klang.block import Block
from klang.constants import MONO, STEREO
from klang.errors import KlangError
from klang.util import WavWriter


D_TYPE = np.float32
"""type: Numpy audio sample datatype (compatible with pyaudio.paFloat32)."""


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


class ChannelMismatchError(KlangError):

    """Can not match received audio signals to output channels."""

    pass


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

    def __init__(self, nChannels):
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
        counter = 0
        for input_ in self.inputs:
            val = input_.get_value()
            ndim = np.ndim(val)
            if ndim == MONO:
                yield val
                counter += 1
                if counter == self.nChannels:
                    return

            elif ndim > MONO:
                for channel in val:
                    yield channel
                    counter += 1
                    if counter == self.nChannels:
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
            raise ChannelMismatchError(msg)

        return pack_signals(signals)


class KlangGeber:

    """Audio card interface.

    PyAudio / Portaudio sound engine. Callback argument in order to propagate
    audio stream callback upwards.
    """

    def __init__(self, nInputs=0, nOutputs=STEREO, callback=None, filepath=''):
        """Kwargs:
            nInputs (int): Number of audio input channels.
            nOutputs (int): Number of audio output channels.
            callback (function): Block execution callback function.
        """
        self.adc = Adc(nChannels=nInputs)
        self.dac = Dac(nChannels=nOutputs)
        self.logger = logging.getLogger(type(self).__name__)
        if callback is None:
            self.logger.warning('No callback defined!')
            callback = lambda: None  # Callback placeholder

        self.callback = callback
        self.capturedFrames = []
        self.filepath = filepath

    @property
    def nInputs(self):
        """Number of audio input channels."""
        return self.adc.nChannels

    @property
    def nOutputs(self):
        """Number of audio output channels."""
        return self.dac.nChannels

    def stream_callback(self, in_data, frame_count, time_info, status):
        """Audio stream callback for PyAudio."""
        if status is not pyaudio.paContinue:
            self.logger.warning('Status changed to %s', status)

        # Process input audio samples
        if in_data:
            # TODO: Make me, test me
            raw = np.frombuffer(in_data, dtype=D_TYPE)
            samples = raw.reshape((frame_count, self.adc.nChannels))
            self.adc.inject_samples(raw)

        # Trigger global block execution / propgate audio stream callback upwards
        self.callback()

        # Fetch output audio samples from block network
        try:
            outData = self.dac.collect_samples()
        except ChannelMismatchError as err:
            self.logger.error(err, exc_info=True)
            silence = get_silence((frame_count, self.dac.nChannels), D_TYPE)
            return silence, pyaudio.paAbort

        if self.filepath:
            self.capturedFrames.append(outData)

        return (outData, pyaudio.paContinue)

    def validate_sound_card_channels(self, pa):
        """Validate number of audio inputs / outputs with default audio
        devices.

        Args:
            pa (PyAudio): PyAudio instance.

        Raises:
            AssertionError: If we do not have enough audio channels on the sound
                card.
        """
        inputDeviceInfo = pa.get_default_input_device_info()
        assert self.nInputs <= inputDeviceInfo['maxInputChannels'], 'Not enough sound card inputs!'
        outputDeviceInfo = pa.get_default_output_device_info()
        assert self.nOutputs <= outputDeviceInfo['maxOutputChannels'], 'Not enough sound card outputs!'

    def dump_audio_to_wav(self):
        """Dumpy captured audio frames to WAV file."""
        self.logger.info('Writing audio dump to WAV file %r', self.filepath)
        wavWriter = WavWriter(self.filepath, self.nOutputs, SAMPLING_RATE)
        for frame in self.capturedFrames:
            wavWriter.write(frame)

        wavWriter.close()

    def start(self):
        """Start audio engine main loop."""
        pa = pyaudio.PyAudio()
        self.validate_sound_card_channels(pa)
        assert D_TYPE is np.float32

        # Example: Callback Mode Audio I/O from
        # https://people.csail.mit.edu/hubert/pyaudio/docs/
        stream = pa.open(
            rate=SAMPLING_RATE,
            frames_per_buffer=BUFFER_SIZE,
            channels=self.nOutputs,  # TODO: How to 1x input, 2x outputs?
            format=pyaudio.paFloat32,
            input=(self.nInputs > 0),
            output=(self.nOutputs > 0),
            stream_callback=self.stream_callback,
        )

        self.logger.info('Starting up audio engine with default devices')
        stream.start_stream()

        try:
            while stream.is_active():
                time.sleep(0.1)

        finally:
            self.logger.info('Shutting down audio engine')
            stream.stop_stream()
            stream.close()
            pa.terminate()
            if self.filepath:
                self.dump_audio_to_wav()
