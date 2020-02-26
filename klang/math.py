from klang.constants import PI, TAU


def wrap(phase):
    """Wrap `phase` to the interval [-π, π)."""
    return (phase + PI) % TAU - PI


def normalize_values(array):
    """Normalize array values to [-1., 1.]."""
    maxAmplitude = np.abs(array).max()
    if maxAmplitude == 0:
        raise ValueError('Zero amplitude! Can not normalize!')

    return array / maxAmplitude


def clip(value, lower, upper):
    """Clip value to [lower, upper]."""
    return min(max(value, lower), upper)