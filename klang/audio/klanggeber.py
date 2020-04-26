"""Klang sound engine object."""
import time

import numpy as np
import pyaudio

from config import BUFFER_SIZE, SAMPLING_RATE
from klang.block import Block
from klang.constants import MONO, STEREO
from klang.errors import KlangError
from klang.execution import determine_execution_order, execute
from klang.util import WavWriter


def pack_signals(signals, bufferSize):
    """Interleave samples from multiple mono signals. C contiguous for audio
    card.

    Format:
        [[L0, R0]
         [L1, R1]
         [L2, R3]
            ...
         [LN, RN]]
    """
    shape = (bufferSize, len(signals))
    ret = np.empty(shape)
    for i, samples in enumerate(signals):
        ret[:, i] = samples

    return ret


class ChannelMismatchError(KlangError):

    """Can not match received audio signals to output channels."""

    pass


class Adc(Block):

    """Dummy block to inject audio into the block network."""

    def __init__(self, nOutputs):
        super().__init__(nOutputs=nOutputs)

    def update(self):
        pass


class Dac(Block):

    """Dummy block to skim off audio from block network."""

    def __init__(self, nInputs):
        super().__init__(nInputs=nInputs)

    def update(self):
        pass

    def get_channels(self, nChannels):
        """Get signal from each active channel."""
        counter = 0
        for input in self.inputs:
            signal = input.get_value()
            ndim = np.ndim(signal)
            if ndim == 0:
                return

            if ndim == MONO:
                yield signal
                counter += 1
                if counter >= nChannels:
                    return

            else:
                for channel in signal:
                    yield channel
                    counter += 1
                    if counter >= nChannels:
                        return


class KlangGeber:

    """Sound engine block executor."""

    def __init__(self, nInputs=0, nOutputs=STEREO, filepath=None):
        """Kwargs:
            nInputs (int): Number of audio inputs.
            nOutputs (int): Number of audio outputs.
            filepath (str): WAV file output filepath.
        """
        self.nInputs = nInputs
        self.nOutputs = nOutputs
        self.adc = Adc(nOutputs=nInputs)
        self.dac = Dac(nInputs=nOutputs)
        if filepath:
            self.wavWriter = WavWriter(filepath, nChannels=nOutputs)
        else:
            self.wavWriter = None

    def start(self):
        silence = np.zeros((BUFFER_SIZE, self.nOutputs), dtype=np.float32)
        execOrder = determine_execution_order(blocks=[self.dac, self.adc])

        def audio_callback(inData, frameCount, timeInfo, status):
            """Audio stream callback for pyaudio."""
            if inData is not None:
                # TODO(atheler): How to stereo signals?
                for samples, channel in zip(inData.T, self.adc.outputs):
                    channel.set_value(samples)

            execute(execOrder)
            channels = list(self.dac.get_channels(self.nOutputs))
            if len(channels) < self.nOutputs:
                msg = 'Not enough channels %d' % len(channels)
                error = ChannelMismatchError(msg)
                print(error)
                return silence, pyaudio.paAbort

            outData = pack_signals(channels, BUFFER_SIZE)
            assert outData.shape == (BUFFER_SIZE, self.nOutputs)

            if self.wavWriter:
                self.wavWriter.write(outData)

            return outData.astype(np.float32), pyaudio.paContinue

        # Example: Callback Mode Audio I/O from
        # https://people.csail.mit.edu/hubert/pyaudio/docs/
        pa = pyaudio.PyAudio()
        stream = pa.open(
            rate=SAMPLING_RATE,
            channels=self.nOutputs,
            format=pyaudio.paFloat32,
            input=(self.nInputs > 0),
            output=(self.nOutputs > 0),
            frames_per_buffer=BUFFER_SIZE,
            stream_callback=audio_callback,
        )
        stream.start_stream()

        try:
            while stream.is_active():
                time.sleep(0.1)

        finally:
            stream.stop_stream()
            stream.close()
            pa.terminate()
            if self.wavWriter:
                self.wavWriter.close()

    def __enter__(self):
        if self.nInputs == 0:
            return self.dac

        if self.nOutputs == 0:
            return self.adc

        return self.adc, self.dac

    def __exit__(self, exception_type, exception_value, traceback):
        """Start klang execution."""
        anErrorOccured = exception_type or exception_value or traceback
        if anErrorOccured:
            return

        self.start()
