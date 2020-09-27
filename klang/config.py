"""Klang config module. Some global Klang parameters."""
from fractions import Fraction


BUFFER_SIZE: int = 256
"""Internal buffer size."""

KAMMERTON: float = 440.
"""Concert pitch frequency."""

SAMPLING_RATE: int = 44100
"""Audio sampling rate."""

TEMPO: float = 120.
"""Tempo in beats per minute."""

METRE: Fraction = Fraction(4, 4, _normalize=False)
"""Time signature."""
