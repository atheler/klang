# Klang

Block based synthesis and music library for Python. *Klang* is German for sound.

## Getting Started

### Prerequisites

We use Python bindings for PortAudio and RtMidi. On Mac they can be installed via [Homebrew](https://brew.sh).

### Installing

Klang can be installed via PyPi / pip or directly via setup.py. Note that there is a C extension which needs to be compiled (`klang/audio/_envelope.c`).

## Running the tests

Tests can be run via with
```
python3 setup.py test
```

## Klang Primer

Klang provides various audio related blocks, which can be connected to each other to form a network. Every block can have multiple in- or output connections. Be connecting the various connections together we can define our network and then execute it with `run_klang(*blocks)`.

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

### Connections

There are two different connection types in Klang:
- *Value* (`Input` and `Output` classes)
- *Message* (`MessageInput` and `MessageOutput` classes)

Value based connections can hold any kind of Python object as value. Message connections have an internal queue.
The former is mostly used to propgate audio samples and modulation signals through the network (Numpy arrays as values). The latter is used for discrete messages like note messages.
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

## Coding Style

PEP8 / Google flavored. With the one exception for variable and argument names (`lowerCamelCase`). Function and methods are `written_like_this()`.

## Authors

* **Alexander Theler** - [GitHub](https://github.com/atheler)

## Acknowledgments

Thanks for the support and inputs!
- Nico Neureiter
- Andreas Steiner
