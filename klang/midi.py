import rtmidi

from klang.block import Block
from klang.connections import MessageInput


def open_midiout(portNumber):
    """Open rtmidi midiout instance. Close it later on!"""
    midiout = rtmidi.MidiOut()
    availablePorts = midiout.get_ports()
    print('Available ports:')

    if availablePorts:
        for i, port in enumerate(availablePorts, start=1):
            print('%d) %s' % (i, port))

        midiout.open_port(portNumber)
    else:
        print('No available ports. Going virtual!')
        midiout.open_virtual_port('My virtual output')

    return midiout


def note_to_midi_message(note, channel=0):
    """Convert klang note to midi message."""
    if note.on:
        statusByte = 0x90 + channel
    else:
        statusByte = 0x80 + channel

    velocity = int(note.velocity * 127)
    return [statusByte, note.pitch, velocity]


class MidiOut(Block):

    """Midi out interface."""

    def __init__(self, portNumber=0, channel=0):
        super().__init__()
        self.channel = channel
        self.inputs = [MessageInput(owner=self)]
        self.midiout = open_midiout(portNumber)

    def update(self):
        for note in self.input.receive():
            msg = note_to_midi_message(note)
            self.midiout.send_message(msg)

    def __del__(self):
        self.midiout.close_port()


if __name__ == '__main__':
    import time
    from klang.messages import Note

    noteOn = Note(pitch=60, velocity=1.)
    noteOff = Note(pitch=60, velocity=0.)

    midiOut = MidiOut(portNumber=0)

    midiOut.input.push(noteOn)
    midiOut.update()

    time.sleep(1.)

    midiOut.input.push(noteOff)
    midiOut.update()
