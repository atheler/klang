"""Audio blocks."""
import collections
import itertools
import time

import numpy as np
import matplotlib.pyplot as plt
import pyaudio

from config import SAMPLING_RATE, BUFFER_SIZE
from klang.connections import Input, Output
from klang.graph import graph_matrix, topological_sorting
from klang.util import write_wave


def output_neighbors(block):
    """Get output neighbors of block."""
    for output in block.outputs:
        for input_ in output.connections:
            if input_.owner:
                yield input_.owner


def input_neighbors(block):
    """Get input neighbors of block."""
    for input_ in block.inputs:
        for output in input_.connections:
            if output.owner:
                yield output.owner


def block_network(*blocks):
    """Convert block network to graph."""
    queue = collections.deque(blocks)
    visited = set()
    edges = set()
    mapping = collections.defaultdict(itertools.count().__next__)
    """defaultdict: Block (Block) -> Graph node index (int)."""

    while queue:
        block = queue.popleft()
        if block in visited:
            continue

        visited.add(block)
        i = mapping[block]

        for child in output_neighbors(block):
            j = mapping[child]
            edges.add((i, j))
            queue.append(child)

        for parent in input_neighbors(block):
            h = mapping[child]
            edges.add((h, i))
            queue.append(parent)

    graph = graph_matrix(list(edges))
    return graph, mapping


def block_execution_order(*blocks):
    """Find block execution order."""
    graph, mapping = block_network(*blocks)
    execOrder = topological_sorting(graph)
    rev = {v: k for k, v in mapping.items()}
    return [rev[node] for node in execOrder]


class Block:

    """Block base class.

    Attributes:
        name (str): Custom name of the owner (if any).
        inputs (list of klang.connections.Input): Input connection.
        outputs (list of klang.connections.Output): Output connection.
    """

    def __init__(self, name='', nInputs=0, nOutputs=0):
        """
        Kwargs:
            nInputs (int): Number of inputs.
            nOutputs (int): Number of outputs.
            name (str): Custom name of the owner.
        """
        self.name = name
        self.inputs = [Input(owner=self) for _ in range(nInputs)]
        self.outputs = [Output(owner=self) for _ in range(nOutputs)]

    @property
    def nInputs(self):
        """Number of inputs."""
        return len(self.inputs)

    @property
    def nOutputs(self):
        """Number of outputs."""
        return len(self.outputs)

    @property
    def input(self):
        """First input."""
        return self.inputs[0]

    @property
    def output(self):
        """First output."""
        return self.outputs[0]

    def update(self):
        """Block's run method.

        Trivia:
            We use 'update' instead of 'run' because of name collision with
            Python thread's run method.
        """
        raise NotImplementedError('Abstract base class')

    def __str__(self):
        if self.name:
            return '%s(%r)' % (self.__class__.__name__, self.name)

        return self.__class__.__name__


class Plotter(Block):
    def __init__(self):
        super().__init__()
        self.buffers = collections.defaultdict(list)

    def register(self, output):
        self.inputs.append(Input(self))
        output.connect(self.inputs[-1])

    def update(self):
        for input in self.inputs:
            self.buffers[input].append(input.get_value())

    def plot(self):
        for input, chunks in self.buffers.items():
            plt.plot(np.concatenate(chunks))


class WavWriter(Block):

    """Write WAV file from input."""

    def __init__(self, filepath, samplingRate=SAMPLING_RATE):
        super().__init__(nInputs=1)
        self.filepath = filepath
        self.samplingRate = samplingRate
        self.buffer = []

    def update(self):
        samples = self.input.get_value()
        self.buffer.append(samples)

    def finalize(self):
        write_wave(np.concatenate(self.buffer), self.filepath, self.samplingRate)


class Dac(Block):

    """Send audio to sound card. Register callback_func which gets called every
    audio callback cycle.
    """

    def __init__(self):
        super().__init__(nInputs=1)
        self.callback_func = None
        self.running = False

    def update(self):
        pass  # Dummy overwrite so that Dac.update() can also be called

    def register_callback(self, func):
        self.callback_func = func

    def run(self):
        def audio_callback(inData, frameCount, timeInfo, status):
            """Audio stream callback for pyaudio."""
            if self.callback_func:
                self.callback_func()

            data = np.asarray(self.input.get_value(), dtype=np.float32)
            return data, pyaudio.paContinue

        """Synthesizer main loop."""
        # Example: Callback Mode Audio I/O from
        # https://people.csail.mit.edu/hubert/pyaudio/docs/
        pa = pyaudio.PyAudio()
        stream = pa.open(
            rate=SAMPLING_RATE,
            channels=1,
            format=pyaudio.paFloat32,
            input=False,
            output=True,
            frames_per_buffer=BUFFER_SIZE,
            stream_callback=audio_callback,
        )
        stream.start_stream()

        try:
            while self.running and stream.is_active():
                time.sleep(0.1)

        finally:
            stream.stop_stream()
            stream.close()
            pa.terminate()

    def start(self):
        self.running = True
        self.run()
