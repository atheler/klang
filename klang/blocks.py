import collections
import time

import numpy as np
import matplotlib.pyplot as plt
import pyaudio

from config import SAMPLING_RATE, BUFFER_SIZE
from klang.errors import KlangError
from klang.util import write_wave


class NotConnectedError(KlangError):

    """Connectable is not connected."""

    pass


class InputAlreadyConnectedError(KlangError):

    """Connectable already connected."""

    pass


def output_neighbors(block):
    """Get output neighbors of block."""
    for output in block.outputs:
        for input_ in output.connections:
            yield input_.owner


def input_neighbors(block):
    """Get input neighbors of block."""
    for input_ in block.inputs:
        for output in input_.connections:
            yield output.owner


class Connectable:

    """Base class."""

    def __init__(self, owner, value=0.):
        self.owner = owner
        self.value = value  # Also paceholder value for unconnected Input
        self.connections = set()

    def connect(self, other):
        """Make a connection to another connectable."""
        self.connections.add(other)
        other.connections.add(self)

    def disconnect(self, other):
        """Disconnect from another connectable."""
        self.connections.remove(other)
        other.connections.remove(self)

    def unplug(self):
        """Kill all connections."""
        for con in set(self.connections):
            self.disconnect(con)

    def get_value(self):
        return self.value

    def set_value(self, value):
        self.value = value

    @property
    def connected(self):
        """Is connected?"""
        return bool(self.connections)

    def __str__(self):
        return '%s(connected: %s)' % (self.__class__.__name__, self.connected)


class Input(Connectable):

    """Input slot.

    Can be connected to only one output.
    """

    def connect(self, output):
        assert isinstance(output, Output)
        if self.connected:
            msg = 'Only one connection possible for Input owner!'
            raise InputAlreadyConnectedError(msg)

        super().connect(output)

    def get_value(self):
        if not self.connected:
            return self.value

        output, = self.connections
        return output.value


class Output(Connectable):

    """Output slot.

    Holds the value. Can be connected to multiple inputs.
    """

    def connect(self, input):
        assert isinstance(input, Input)
        super().connect(input)


class Block:

    """Block base class.

    Attributes:
        name (str): Custom name of the owner (if any).
        inputs (list of Input): Input connection.
        outputs (list of Output): Output connection.
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
