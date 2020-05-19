import fractions


BUFFER_SIZE = 256
"""int: Internal buffer size."""

KAMMERTON = 440.
"""float: Concert pitch frequency."""

SAMPLING_RATE = 44100
"""int: WAV sampling rate."""

TEMPO = 120.
"""float: Tempo in beats per minute."""

METRE = fractions.Fraction(4, 4, _normalize=False)
"""Fraction: Time signature."""
