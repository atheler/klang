# Klang

Block based synthesis and music library for Python. *Klang* is German for sound.

## Getting Started

### Prerequisites

We use Python bindings for [PortAudio](http://www.portaudio.com) and [RtMidi](https://www.music.mcgill.ca/~gary/rtmidi/). On Mac they can be installed via [Homebrew](https://brew.sh).

### Installing

Klang can be installed via PyPi / pip or directly via setup.py. Note that there is a C extension which needs to be compiled (`klang/audio/_envelope.c`). C extensions can be compiled in place with:

```bash
python3 setup.py build_ext --inplace
```

For developing you can link your working copy with

```python
python3 setup.py develop
```

## Running the tests

Tests can be run via with
```
python3 setup.py test
```

## Safety First
As always when programming with sound: Unplug your headphones or be very sure of what you are doing! Also with low headphone volume bugs in the code can result in very unpleasant loud noises which could probably impair your hearing. Be careful!

## Klang Primer
Klang provides various audio related blocks. Every block can have multiple in- and outputs and by connecting them with each other we can define our network. Once we are finished with patching we can run our network with by calling `run_klang(*blocks)`. This function only needs some blocks which belong to the network. It will then automatically discovers the other blocks of the network and deduce an appropriate block execution order.

In the following script we create a 440 Hz sine oscillator which output gets send to the sound card.

```python
from klang.audio import Oscillator, Dac
from klang.klang import run_klang

# Init blocks
osc = Oscillator(frequency=440.)
dac = Dac(nChannels=1)

# Define network
osc.output.connect(dac.input)

# Run it
run_klang(dac)
```

Audio can be written to disk as a WAV file with the `filepath` argument.

```python
run_klang(*blocks, filepath='some/filepath.wav')`
```

### Connections

There are two different connection types in Klang:
- *Value* (`Input` and `Output` classes)
- *Message* (`MessageInput` and `MessageOutput` classes)

Value based connections can hold any kind of Python object as value. Message connections have an internal queue.
The former is mostly used to propagate audio samples and modulation signals through the network (Numpy arrays as values). The latter is used for discrete messages like note messages.
There are also corresponding *Relay* connections (`Relay` and `MessageRelay` classes). These are used to build composite blocks (blocks which contain there own network of child blocks). Relays can be used to interface between the inside and outside of an composite block.

### Defining The Network

The `connect` method can be used to connect inputs and outputs with each other. Note that it is always possible to connect one output to multiple inputs but not the other way round. As a shorthand there are two overloaded operators:
- Pipe operator `|`: Connect multiple blocks in series.
- Mix operator `+`: Mix multiple value outputs together.

```python
# Pipe operator
a | b | c

# Is equivalanet to:
# >>> a.output.connect(b.input)
# ... b.output.connect(c.input)
```

```python
# Mix operator
mixer = a + b + c

# Is equivalanet to:
# >>> mixer = Mixer(nInputs=0)
# ... mixer.add_new_channel()
# ... a.output.connect(mixer.inputs[-1])
# ... mixer.add_new_channel()
# ... b.output.connect(mixer.inputs[-1])
# ... mixer.add_new_channel()
# ... c.output.connect(mixer.inputs[-1])
```

## Examples

See the `examples/` directory with a couple example script which illustrate the core functionality of Klang. Currently there are:
- `hello_world.py`: 440 Hz sine wave generator
- `arpeggiator_demo.py`: Two synthesizer patch with an arpeggiator and some sound effects
- `audio_file_demo.py`: Looped audio file playback (`gong.wav` sample) with audio effects
- `micro_rhythm_demo.py`: Kick and Hi-Hat pattern where the latter is phrased with a micro rhythm
- `sequencer_demo.py`: Techno patch with sequencer
- `synthesizer_demo.py`: This has to be started as root. Computer keyboard playable monophonic synthesizer
- `tempo_aware_effects.py`: Modulated noise with time synced effects

## Coding Style

PEP8 / Google flavored. With the one exception for variable and argument names (`camelCase`). Function and in methods are `snake_case()`.

## Author

* **Alexander Theler** - [GitHub](https://github.com/atheler)

## Acknowledgments

Thanks for the support and inputs!
- Nico Neureiter [GitHub](https://github.com/NicoNeureiter)
- Andreas Steiner [Smoke And Mirrors](http://smokeandmirrors.ch)
- Lawrence Markwalder [GitHub](https://github.com/lmarkwalder)
