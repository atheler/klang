"""Web scraping from Wikipedia for scale and chord names."""
import re

import numpy as np
import requests

import bs4

from klang.constants import SEMITONES_PER_OCTAVE
from klang.music.scales import pitches_2_scale


LIST_OF_CHORDS_URL = 'https://en.wikipedia.org/wiki/List_of_chords'
LIST_OF_SCALES_URL = 'https://en.wikipedia.org/wiki/List_of_musical_scales_and_modes'
REFERENCES_RE = re.compile(r'\[.+\]')
COMMENTS_RE = re.compile(r'\(.+\)')
DEGREES = {
    '1': 0,
    '2': 2,
    '3': 4,
    '4': 5,
    '5': 7,
    '6': 9,
    '7': 11,
    '8': 12,

    '♯': 1,
    '♭': -1,
    '♯': 1,
    '♮': 0,
}


def load_soup(url):
    """Load webpage and parse via Beautiful Soup."""
    page = requests.get(url)
    return bs4.BeautifulSoup(page.content, 'html.parser')


def find_table(tables, caption):
    """Find table with caption text."""
    for table in tables:
        if table.caption is None:
            continue

        if table.caption.text.strip() == caption:
            return table

    raise ValueError('Could not find table with %r' % caption)


def iter_table_rows(table):
    """Iterate over rows of Beautiful Soup HTML table."""
    body = table.find('tbody')
    rows = body.find_all('tr')
    for row in rows:
        cells = row.find_all('td')
        yield [e.text.strip() for e in cells]


def is_valid_chord(_, pitchClasses):
    """Check input validity / support."""
    if 'x' in pitchClasses:
        return False

    return True


def prettify_name(name):
    """Prettify chord / scale name."""
    for ptr in [REFERENCES_RE, COMMENTS_RE]:
        name = ptr.sub('', name).strip()

    name = name.replace('"', '')
    return name.lower()


def multi_seperator_pack(text, separators):
    """Split string with multiple separators. Always return list even when no
    split occurred.
    """
    for sep in separators:
        if sep in text:
            return text.split(sep)

    return [text]


def spawn_jobs(name, data, nameSeps=[' / ', ' or '], dataSeps=[' / ', ' or ', 'or']):
    """Detect synonym jobs. E.g. if there is a "a or b" in the name / data entry."""
    for nam in multi_seperator_pack(name, nameSeps):
        for i, dat in enumerate(multi_seperator_pack(data, dataSeps)):
            if i > 0:
                nam += ' %d' % i

            yield nam.strip(), dat


def pitch_classes_2_chord(pitchClasses):
    """Parse pitch classes. Chords listed on Wikipedia sometimes have this format.

    Usage:
        >>> pitch_classes_2_chord('0 4 7 t')
        np.array([0, 4, 7, 10])
    """
    pitchClasses = pitchClasses.replace('t', '10')
    pitchClasses = pitchClasses.replace('A', '10')
    pitchClasses = pitchClasses.replace('e', '11')
    pitchClasses = pitchClasses.replace('B', '11')

    base = 0
    prev = -float('inf')
    chord = []
    for pc in pitchClasses.split(' '):
        pitch = base + int(pc)
        if pitch < prev:
            base += SEMITONES_PER_OCTAVE

        chord.append(base + pitch)
        prev = pitch

    return np.array(chord)


def extract_chords(table):
    """Extract chords from Beautiful Soup HTML table.

    Returns:
        dict: Chord name (str) -> Chord (array).
    """
    jobs = []
    for row in iter_table_rows(table):
        if not row:
            continue

        name, _, _, _, pitchClasses, _ = row
        if not is_valid_chord(name, pitchClasses):
            #print('Skipping %r, %r' % (name, pitchClasses))
            continue

        name = prettify_name(name)
        if name == 'power chordp5':
            name = 'power chord or p5'

        jobs.extend(spawn_jobs(name, pitchClasses))

    chords = {}
    for name, pitchClasses in jobs:
        chords[name] = pitch_classes_2_chord(pitchClasses)

    return chords


def is_valid_scale(name, degrees):
    """Validate scale name and degrees."""
    if 'quarter tone scale' in name.lower():
        return False

    if degrees == '—':
        return False

    if 'etc.' in degrees:
        return False

    if '(' in degrees:
        return False

    return True


def parse_degrees(degrees):
    """Parse degrees into scale."""
    pitches = []
    for part in degrees.split():
        pitches.append(
            sum(map(DEGREES.__getitem__, part))
        )

    return pitches_2_scale(pitches)


def extract_scales(table):
    """Extract scales from Beautiful Soup HTML table."""
    jobs = []
    for row in iter_table_rows(table):
        if not row:
            continue

        name, _, _, degrees, intervals, nPc, _, _, _ = row
        if not is_valid_scale(name, degrees):
            #print('Skipping %r, %r' % (name, degrees))
            continue

        name = prettify_name(name)
        jobs.extend(spawn_jobs(name, degrees, dataSeps=['\n']))

    scales = {}
    for name, degrees in jobs:
        # Overwrite
        if name == 'chromatic scale':
            scale = 12 * (1, )
        else:
            scale = parse_degrees(degrees)

        scales[name] = scale

    return scales


def get_them(url, caption, extractor_func):
    """Extractor helper."""
    soup = load_soup(url)
    tables = soup.findAll('table')
    table = find_table(tables, caption)
    return extractor_func(table)


def print_dict_2_csv(dct, sep=','):
    """Print chords / scale dict as CSV string to stdout."""
    for key, data in sorted(dct.items()):
        print(key, end=sep)
        print(sep.join(map(str, data)))


if __name__ == '__main__':
    print('Chords in %r:' % LIST_OF_CHORDS_URL)
    chords = get_them(
        LIST_OF_CHORDS_URL,
        caption='List of musical chords',
        extractor_func=extract_chords,
    )
    print_dict_2_csv(chords)

    print('\nScales and modes in %r:' % LIST_OF_SCALES_URL)
    scales = get_them(
        LIST_OF_SCALES_URL,
        caption='List of musical scales and modes',
        extractor_func=extract_scales,
    )
    print_dict_2_csv(scales)
