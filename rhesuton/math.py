from rhesuton.constants import PI, TAU


def wrap(phase):
    """Wrap `phase` to the interval [-π, π)."""
    return (phase + PI) % TAU - PI


def normalize_values(array):
    """Normalize array values to [-1., 1.]."""
    maxAmplitude = max(
        abs(array.max()),
        abs(array.min()),
    )

    if maxAmplitude == 0:
        raise ValueError('Zero amplitude! Can not normalize!')

    return array / maxAmplitude
