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


def network_graph(blocks):
    """Get network graph and mapping."""
    block2idx = {}
    idx2block = {}
    queue = collections.deque(blocks)
    visited = set()
    edges = set()

    def get_block_index(block):
        """Get index for block."""
        if block not in block2idx:
            newId = len(block2idx)
            block2idx[block] = newId
            idx2block[newId] = block

        return block2idx[block]

    while queue:
        block = queue.popleft()
        if block in visited:
            continue

        visited.add(block)
        here = get_block_index(block)
        for child in output_neighbors(block):
            there = get_block_index(child)
            edges.add((here, there))
            queue.append(child)

        for parent in input_neighbors(block):
            back = get_block_index(parent)
            edges.add((back, here))
            queue.append(parent)

    return idx2block, graph_matrix(list(edges))


def determine_execution_order(blocks):
    """Get appropriate execution order for block network."""
    idx2block, graph = network_graph(blocks)
    order = topological_sorting(graph)
    return [idx2block[idx] for idx in order]


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

    def __init__(self, nInputs=0, nOutputs=STEREO):
        self.nInputs = nInputs
        self.nOutputs = nOutputs
        self.adc = Adc(nOutputs=nInputs)
        self.dac = Dac(nInputs=nOutputs)

    def start(self):
        silence = np.zeros((BUFFER_SIZE, self.nOutputs), dtype=np.float32)
        executionOrder = determine_execution_order(blocks=[self.dac, self.adc])

        def audio_callback(inData, frameCount, timeInfo, status):
            """Audio stream callback for pyaudio."""
            if inData is not None:
                # TODO(atheler): How to stereo signals?
                for samples, channel in zip(inData.T, self.adc.outputs):
                    channel.set_value(samples)

            for block in executionOrder:
                block.update()

            channels = list(self.dac.get_channels(self.nOutputs))
            if len(channels) < self.nOutputs:
                msg = 'Not enough channels %d' % len(channels)
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
        self.start()
