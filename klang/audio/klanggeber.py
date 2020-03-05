"""Klang sound engine object."""
import collections
import time

import numpy as np
import pyaudio

from config import BUFFER_SIZE, SAMPLING_RATE
from klang.blocks import Block, output_neighbors, input_neighbors
from klang.constants import MONO, STEREO
from klang.errors import KlangError
from klang.graph import graph_matrix, topological_sorting


class ChannelMismatchError(KlangError):

    """Can not match received audio signals to output channels."""

    pass


def pack_signals(signals, bufferSize):
    """Interleave samples from multiple mono signals. C contiguous for audio card.

    Format:
        [[L0, R0]
         [L1, R1]
         [L2, R3]
            ...
         [LN, RN]]
    """
    ret = np.empty((bufferSize, len(signals)))
    for i, samples in enumerate(signals):
        ret[:, i] = samples

    return ret


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
        """Get signal for each active channel."""
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

    def __init__(self, nInputs=0, nOutputs=STEREO):
        self.nInputs = nInputs
        self.nOutputs = nOutputs

        self.adc = Adc(nOutputs=nInputs)
        self.dac = Dac(nInputs=nOutputs)

        self.block2idx = {}
        self.idx2block = {}
        self.executionOrder = []

    def register_block(self, block):
        """Register block to executor."""
        if block in self.block2idx:
            raise ValueError('Block %r already registered!' % block)

        newIdx = len(self.block2idx)
        self.block2idx[block] = newIdx
        self.idx2block[newIdx] = block

    def get_block_index(self, block):
        """Get block index. If block not present in mapping it will be added."""
        if block not in self.block2idx:
            self.register_block(block)

        return self.block2idx[block]

    def update_execution_order(self):
        """Update executor order."""
        queue = collections.deque(self.block2idx)
        visited = set()
        edges = set()
        while queue:
            block = queue.popleft()
            if block in visited:
                continue

            visited.add(block)

            here = self.block2idx[block]

            for child in output_neighbors(block):
                there = self.get_block_index(child)
                edges.add((here, there))
                queue.append(child)

            for parent in input_neighbors(block):
                back = self.get_block_index(parent)
                edges.add((back, here))
                queue.append(parent)

        graph = graph_matrix(list(edges))
        order = topological_sorting(graph)
        self.executionOrder = [
            self.idx2block[idx] for idx in order
        ]

    def add_block(self, *blocks):
        """Add block(s) to executor."""
        size = len(self.block2idx)
        for block in blocks:
            self.register_block(block)

        sizeChanged = (len(self.block2idx) != size)
        if sizeChanged:
            self.update_execution_order()

    def start(self):
        silence = np.zeros((BUFFER_SIZE, self.nOutputs), dtype=np.float32)

        def audio_callback(inData, frameCount, timeInfo, status):
            """Audio stream callback for pyaudio."""
            if inData is not None:
                # TODO(atheler): How to stereo signals?
                for samples, channel in zip(inData.T, self.adc.outputs):
                    channel.set_value(samples)

            for block in self.executionOrder:
                block.update()

            channels = list(self.dac.get_channels(self.nOutputs))
            if len(channels) < self.nOutputs:
                msg = 'Not engough channels %d' % len(channels)
                error = ChannelMismatchError(msg)
                print(error)
                return silence, pyaudio.paAbort

            outData = pack_signals(channels, BUFFER_SIZE)
            assert outData.shape == (BUFFER_SIZE, self.nOutputs)
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

    def __enter__(self):
        if self.nInputs == 0:
            return self.dac

        if self.nOutputs == 0:
            return self.adc

        return self.adc, self.dac

    def __exit__(self, exception_type, exception_value, traceback):
        self.add_block(self.adc, self.dac)
        self.start()

    def __str__(self):
        return '%s(%d blocks)' % (
            self.__class__.__name__,
            len(self.block2idx),
        )
