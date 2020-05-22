"""MIDI stuff. Work in progress."""
import rtmidi

from klang.block import Block
from klang.connections import MessageInput


MIDI_NOTE_OFF = 0b10000000
"""int: MIDI note off message status byte for MIDI channel 0."""

MIDI_NOTE_ON = 0b10010000
"""int: MIDI note on message status byte for MIDI channel 0."""


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
        statusByte = MIDI_NOTE_ON + channel
    else:
        statusByte = MIDI_NOTE_OFF + channel

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
