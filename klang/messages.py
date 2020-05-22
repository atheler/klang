"""Messages passed around in the system."""
import collections
import json

from klang.music.tunings import EQUAL_TEMPERAMENT


class Note(collections.namedtuple('Note', 'pitch velocity frequency')):

    """Music note. Pitch is optional. Used for voice mapping in synthesizer.

    Note:
      - pitch before velocity for lexicographical order.
    """

    def __new__(cls, pitch, velocity=1.0, frequency=None,
                temperament=EQUAL_TEMPERAMENT):
        """Args:
            pitch (int): Pitch number.

        Kwargs:
            velocity (float): Note velocity.
            frequency (float): Frequency value.
            temperament (Temperament): Tuning for default frequency.
        """
        if not 0 <= pitch < 128:
            raise ValueError('Invalid pitch %s!' % pitch)
        if not 0 <= velocity <= 1.:
            raise ValueError('Invalid velocity %s!' % velocity)
        if frequency is None:
            frequency = temperament.pitch_2_frequency(pitch)
        if frequency < 0:
            raise ValueError('Invalid frequency %s!' % frequency)

        return super().__new__(cls, pitch, velocity, frequency)

    @classmethod
    def from_dict(cls, dct):
        """Construct Note from dct."""
        if dct.pop('type') != cls.__name__:
            fmt = 'Can not construct Note from dict %s'
            raise ValueError(fmt % dct)

        return cls(**dct)

    @classmethod
    def from_json(cls, string):
        """Construct Note from JSON string."""
        dct = json.loads(string)
        return cls.from_dict(dct)

    @property
    def on(self):
        """If note-on."""
        # Note-on is kind of a known expression. pylint: disable=invalid-name
        return self.velocity > 0.

    @property
    def off(self):
        """If note-off."""
        return self.velocity == 0.

    def silence(self):
        """Silence note. Get a copy with velocity set to zero."""
        return self._replace(velocity=0.)

    def to_dict(self):
        """Convert note to dict."""
        dct = dict(zip(self._fields, self))
        dct['type'] = type(self).__name__
        return dct

    def to_json(self):
        """Serialize as JSON string."""
        return json.dumps(self.to_dict())

    def __str__(self):
        return 'Note(pitch=%d, velocity=%.1f, frequency=%.1f Hz)' % self
