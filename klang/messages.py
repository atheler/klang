"""Messages passed around in the system."""
import collections


class Note(collections.namedtuple('Note', 'frequency velocity pitch')):

    """Music note. Pitch optional. Used for voice mapping in synthesizer."""

    def __new__(cls, frequency, velocity, pitch=None):
        return super().__new__(cls, frequency, velocity, pitch)
