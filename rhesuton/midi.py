import numpy as np

from config import KAMMERTON


def frequency_2_pitch(frequency):
    """Frequency to MIDI note number (equal temperament)."""
    return 69 + 12 * np.log2(frequency / KAMMERTON)


assert frequency_2_pitch(KAMMERTON) == 69


def pitch_2_frequency(noteNumber):
    """MIDI note number to frequency (equal temperament)."""
    return (2 ** ((noteNumber - 69) / 12)) * KAMMERTON


assert pitch_2_frequency(69) == KAMMERTON