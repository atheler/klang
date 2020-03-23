"""Messages passed around in the system."""
import collections

from klang.music.tunings import EQUAL_TEMPERAMENT


class Note(collections.namedtuple('Note', 'pitch velocity frequency')):

    """Music note. Pitch optional. Used for voice mapping in synthesizer."""

    def __new__(cls, pitch, velocity=1.0, frequency=None,
                temperament=EQUAL_TEMPERAMENT):
        """Args:
            pitch (int): Pitch number.

        Kwargs:
            velocity (float): Note velocity.
            frequency (float): Frequency value.
            temperament (Temperament): Tuning for default frequency.
        """
        assert 0 <= pitch < 128
        assert 0 <= velocity <= 1.
        if frequency is None:
            frequency = temperament.pitch_2_frequency(pitch)

        assert frequency > 0
        return super().__new__(cls, pitch, velocity, frequency)

    @property
    def on(self):
        """If note-on."""
        return self.velocity > 0.

    @property
    def off(self):
        """If note-off."""
        return self.velocity == 0.

    def __str__(self):
        return 'Note(pitch=%d, velocity=%.1f, frequency=%.1f Hz)' % self
