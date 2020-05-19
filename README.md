# Klang

Block based synthesis and music library for Python. *Klang* is German for sound.

## Getting Started

### Prerequisites

We use Python bindings for PortAudio and RtMidi. On Mac they can be installed via Homebrew.

### Installing

Klang can be installed via pip or the setup.py. Note that there is a C extension which needs to be compiled (`klang/audio/_envelope.c`).

## Running the tests

Tests can be run via with
```
python3 setup.py test
```

### And coding style tests

PEP8 / Google flavored. With the one exception for variable and argument names (`lowerCamelCase`). Function and methods are `written_like_this()`.

## Primer

Klang provides various audio related blocks, which can be connected to each other. In the following script we create a 440 Hz sine oscillator which output gets send to the sound card.

```python
from klang.audio import Oscillator, Dac
from klang.klang import run_klang

osc = Oscillator(frequency=440.)
dac = Dac(nChannels=1)
osc.output.connect(dac.input)
run_klang(dac)
```

Each block can have multiple in- and outputs (`inputs` and `outputs` list attributes). `input` and `output`are a shorthand property to the first (or primary) in- or output.

### Connections

There are two different kind of connections inside Klang: *Values* and *Messages*. Values can be any kind of Python object which get polled in each cycle. Messages are a sent to a message queue. The former is mostly used to propgate audio samples and modulation signals through the network (Numpy arrays as values). The latter is used for discrete messages like note messages.

There are also corresponding *Relay* connections. These are used to build composite blocks (blocks which contain there own network of child blocks). Relays can be used to interface between the inside and outside of an composite block.

### Defining The Network

Use the connections `connect` method for connecting with other in- or outputs. As a shorthand there are two overloaded operators:
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

## Authors

* **Alexander Theler** - *Initial work* - [GitHub](https://github.com/atheler)

## Acknowledgments

Thanks to:
* Nico Neureiter
* Andreas Steiner
