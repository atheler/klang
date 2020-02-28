"""Rhyhtm related stuff."""


def _compute_bitmap(num_slots, num_pulses):
    """Bjorklund algorithm for Euclidian rhythm.

    Resources:
      - The Theory of Rep-Rate Pattern Generation in the SNS Timing System from
        https://pdfs.semanticscholar.org/c652/d0a32895afc5d50b6527447824c31a553659.pdf
    """
    print('_compute_bitmap(%d, %d)' % (num_slots, num_pulses))
    # First, compute the count and remainder arrays
    divisor = num_slots - num_pulses
    remainder = [num_pulses]
    count = []
    level = 0
    cycleLength = 1
    remLength = 1

    while remainder[level] > 1:
        count.append(divisor // remainder[level])
        remainder.append(divisor % remainder[level])
        divisor = remainder[level]
        newLength = (cycleLength * count[level]) + remLength
        remLength = cycleLength
        cycleLength = newLength
        level += 1

    count.append(divisor)

    if remainder[level] > 0:
        cycleLength = (cycleLength * count[level]) + remLength

    print('remainder:', remainder)
    print('count    :', count)
    print('level    :', level)


    def build_string(level, bitmap=None):
        if bitmap is None:
            bitmap = []

        if level == -1:
            bitmap.append(0)
        elif level == -2:
            bitmap.append(1)
        else:
            for i in range(count[level]):
                build_string(level - 1, bitmap)

            if remainder[level]:
                build_string(level - 2, bitmap)

        return bitmap

    return build_string(level)


def euclidian_rhythm(nPulses, nSlots):
    """Euclidian rhyhtm pattern generator."""
    bitmap = _compute_bitmap(nSlots, nPulses)
    return list(reversed(bitmap))