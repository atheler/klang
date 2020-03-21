"""Messages passed around in the system."""
import collections

from klang.music.tunings import EQUAL_TEMPERAMENT


class Note(collections.namedtuple('Note', 'frequency velocity pitch')):

    """Music note. Pitch optional. Used for voice mapping in synthesizer."""

    def __new__(cls, frequency, velocity, pitch=None):
        return super().__new__(cls, frequency, velocity, pitch)

    @classmethod
    def from_pitch(cls, pitch, velocity=1., temperament=EQUAL_TEMPERAMENT):
        """Create Note from pitch."""
        freq = temperament.pitch_2_frequency(pitch)
        return cls(freq, velocity, pitch)

    def __str__(self):
        return 'Note(frequency=%.1f, velocity=%.1f, pitch=%d)' % self
        #return 'Note(pitch=%d, velocity=%.1f)' % (self.pitch, self.velocity)
