"""Messages passed around in the system."""
import collections


class PitchNote(collections.namedtuple('PitchNote', 'pitch velocity')):

    """MIDI a-like pitch / velocity note."""

    pass


class FrequencyNote(collections.namedtuple('FrequencyNote', 'frequency velocity')):

    """Frequency / velocity note."""

    pass