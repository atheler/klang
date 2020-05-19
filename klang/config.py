import fractions


ATTACK_RELEASE = 0.002
"""float: Attack / release time for primitive linear fade in/out envelope."""

BIT_DEPTH = 16
"""int: WAV bit depth."""

BUFFER_SIZE = 256
"""int: Internal buffer size."""

KAMMERTON = 440.
"""float: Concert pitch frequency."""

SAMPLING_RATE = 44100
"""int: WAV sampling rate."""

TEMPERAMENT_NAME = 'Young'
"""str: Temperament name for synthesizer."""

CHORDS_FILEPATH = 'resources/chords.csv'
"""str: Filepath to chords CSV file."""

SCALES_FILEPATH = 'resources/scales.csv'
"""str: Filepath to scales CSV file."""

INTERVALS_FILEPATH = 'resources/intervals.csv'
"""str: Filepath to intervals CSV file."""

TUNINGS_FILEPATH = 'resources/tunings.csv'
"""str: Filepath to tunings CSV file."""

TEMPO = 120.
"""float: Tempo in beats per minute."""

METRE = fractions.Fraction(4, 4, _normalize=False)
"""Fraction: Time signature."""
