"""Pure Python / NumPy envelopes.

Envelope curves are built with the curve_samples() and constant_samples()
generators. These generators yield the next envelope samples and the current
envelope state / current value (so that we can switch to another generator
whenever we want). The constant_samples() generator will run forever but the
curve_samples() generators signals that it is depletetd by outputing a samples
array which is less than BUFFER_SIZE long.

We use exponential envelope curves with overshoot for curve shaping. overshoot
values close to 0. result in an exponential shape, >1 is more linear.

    y = f(t) = min(1, (1 + overshoot) * (1 - exp(-coeff * t)))

This curve can be produced online, without calling exp(), with a simple first
order low pass filter (via scipy.signal.lfilter).

Resources:
  - http://www.earlevel.com/main/2013/06/01/envelope-generators/
  - https://dsp.stackexchange.com/questions/54086/single-pole-iir-low-pass-filter-which-is-the-correct-formula-for-the-decay-coe
  - https://dsp.stackexchange.com/questions/28308/exponential-weighted-moving-average-time-constant/28314#28314
  - https://www.earlevel.com/main/2012/12/15/a-one-pole-filter/
"""
import enum
import functools
import math

import numpy as np
from scipy.signal import lfilter

from klang.config import BUFFER_SIZE, SAMPLING_RATE
from klang.constants import INF
from klang.math import sign


DEFAULT_OVERSHOOT = 1e-3
"""float: Default overshoot parameter. Approx. exponential envelope."""

UPPER = 1.
"""float: Upper limit of envelope."""

LOWER = 0.
"""float: Lower limit of envelope."""

SENTINEL_ARRAY = np.zeros(0)
"""array: Empty array signaling the end of sample generators."""

UNUSED = 'Unused'


@functools.lru_cache()
def full(shape, fill_value):
    """Get array of given `shape` filled with `fill_value`. Cached np.full."""
    arr = np.full(shape, fill_value)
    arr.setflags(write=False)
    return arr


def calculate_coefficient(duration, overshoot=DEFAULT_OVERSHOOT):
    """Calculate coefficient of exponential envelope function.

    Args:
        duration (float): Duration parameter.

    Kwargs:
        overshoot (float): Overshoot parameter.

    Returns:
        float: Exponential coefficient.
    """
    if duration <= 0:
        return INF

    if overshoot <= 0:
        return 1. / duration

    return 1. / duration * math.log((UPPER + overshoot) / overshoot)


def time_needed_until_upper(startValue, duration, overshoot=DEFAULT_OVERSHOOT):
    """Time needed for reaching upper limit of exponential envelope function.
    Given y_1 = f(t_1) < 1.: How long does it take until we reach the upper
    limit 1.0? (Note: Reaching 1., not (1. + overshoot)!)

    Args:
        startValue (float): Starting value.
        duration (float): Duration parameter.

    Kwargs:
        overshoot (float): Overshoot parameter.

    Returns:
        float: Time needed until exp envelope filter reaches UPPER value.
    """
    if duration <= 0:
        return 0.

    if overshoot <= 0:
        return INF

    coeff = calculate_coefficient(duration, overshoot)
    tStart = math.log(1. - startValue / (1. + overshoot)) / -coeff  # 1. != UPPER!
    return max(0, duration - tStart)


def time_needed(start, target, duration, overshoot=DEFAULT_OVERSHOOT):
    """Time needed for reaching `target` from a `start` value.

    Args:
        start (float): Start value.
        target (float): Target value.
        duration (float): Duration parameter.

    Kwargs:
        overshoot (float): Overshoot parameter.

    Returns:
        float: Time needed to get from start -> target (given `duration` and
            `overshoot`).
    """
    err = abs(target - start)
    return time_needed_until_upper(1. - err, duration, overshoot)


def calculate_transfer_function(duration, overshoot=DEFAULT_OVERSHOOT):
    """Get transfer function for scipy.signal.lfilter in ba format.

    Args:
        duration (float): Duration parameter.

    Kwargs:
        overshoot (float): Overshoot parameter.

    Returns:
        tuple: Transfer function coefficients.
    """
    coeff = calculate_coefficient(duration, overshoot)
    numerator = (coeff, )
    denominator = (1., coeff - 1.)
    return numerator, denominator


def generator_finished(samples):
    """Check if sample generator finished by inspecting its sample output. If
    length < BUFFER_SIZE there are no more new samples and we reached the end of
    associated the generator (next next() call would raise StopIteration).

    Args:
        samples (array): Sample buffer.

    Returns:
        bool: Generator has finished.
    """
    return samples.size < BUFFER_SIZE


def curve_samples(start, target, duration, overshoot=DEFAULT_OVERSHOOT, prepend=None):
    """Curve sample generator. Get exponential envelope samples leading from
    `start` -> `target`. Previously generated samples can be incorporated via
    prepend. These values will be prepended to the first yield samples.
    Generator is depleted when it yields an array which is less than BUFFER_SIZE
    long (can be checked via generator_finished(samples)). After this last array
    curve_samples() will raise a StopIteration error.

    Args:
        start (float): Start value.
        target (float): Target value.

    Kwargs:
        overshoot (float): Overshoot parameter (bigger than zero) for curve
            shape (exponential <-> linear).
        prepend (array): Samples to prepend in first call. Last, incomplete
            sample buffer from another sample generator.

    Yields:
        tuple: Samples array and last filter state (or target value if there was
        no crossover).
    """
    rate = SAMPLING_RATE * duration
    nSamples = int(time_needed(start, target, rate, overshoot))  # rate -> samples

    # Arguments for lfilter
    tf = calculate_transfer_function(rate, overshoot)
    targetArr = full(BUFFER_SIZE, target + sign(target - start) * overshoot)
    zi = [start]

    # Prepend samples to first output
    if prepend is not None:
        missing = BUFFER_SIZE - prepend.size
        available = min(nSamples, missing)
        tail, zi = lfilter(*tf, targetArr[:available], zi=zi)
        samples = np.concatenate([prepend, tail])
        if generator_finished(samples):
            yield samples, target
            return

        yield samples, zi[0]
        nSamples -= available

    assert nSamples >= 0

    fullCycles, remainder = divmod(nSamples, BUFFER_SIZE)
    for _ in range(fullCycles):
        samples, zi = lfilter(*tf, targetArr, zi=zi)
        yield samples, zi[0]

    if remainder > 0:
        samples, zi = lfilter(*tf, targetArr[:remainder], zi=zi)
        yield samples, zi[0]
    else:
        yield SENTINEL_ARRAY, target


def constant_samples(value, prepend=None):
    """Constant value sample generator. Yields a full buffer with `value`
    (besides prepend values). Forever.

    Args:
        value (float): Target value to hold.

    Kwargs:
        prepend (array): Samples to prepend. Previously generated, incomplete
            sample buffer (from another terminated generator).
    """
    if prepend is not None:
        missing = BUFFER_SIZE - prepend.size
        tail = full(missing, value)
        samples = np.concatenate([prepend, tail])
        yield samples, value

    samples = full(BUFFER_SIZE, value)
    while True:
        yield samples, value


class Stage(enum.Enum):

    """ADSR envelope stage. States of the envelope state machine: OFF ->
    ATTACKING -> DECAYING -> SUSTAINING -> RELEASING -> OFF.
    """

    OFF = 0
    ATTACKING = 1
    DECAYING = 2
    SUSTAINING = 3
    RELEASING = 4


class Envelope:

    """Pure Python / NumPy ADSR envelope generator.

    Attributes:
        value (float): Filter state.
        stage (Stage): tage.
        sampleGenerator (generator): Current sample source.
        enabled (bool): Additional flag for being able to differentiate envelope
            on / off while looping.

    TODO:
      - attack, decay, sustain, release getters and setters (with
        update_sample_generator() call?)
    """

    def __init__(self, attack, decay, sustain, release, dt=UNUSED,
                 overshoot=DEFAULT_OVERSHOOT, retrigger=False, loop=False):
        """Args:
            attack (float): Attack time duration.
            decay (float): Decay time duration.
            sustain (float): Sustain value.
            release (float): Release time duration.

        Kwargs:
            dt (float): UNUSED sampling interval. For same API as C Envelope.
            overshoot (float): Overshoot amount.
            retrigger (bool): Allow envelope retrigger on repeated note-ons.
            loop (bool): Loop envelope (skip SUSTAINING and OFF stages if
                envelope is enabled).
        """
        self.attack = attack
        self.decay = decay
        self.sustain = sustain
        self.release = release

        self.overshoot = overshoot
        self.retrigger = retrigger
        self.loop = loop

        self.stage = Stage.OFF
        self.value = 0.
        self.sampleGenerator = None
        self.enabled = False

        self.update_sample_generator()

    @property
    def active(self):
        """Is envelope active."""
        return self.stage is not Stage.OFF

    def update_sample_generator(self, prepend=None):
        """Initialize sample generator according to current stage.

        Kwargs:
            prepend (array): Samples to prepend on first generator call.
        """
        if self.stage is Stage.OFF:
            self.sampleGenerator = constant_samples(
                value=LOWER, prepend=prepend
            )
        elif self.stage is Stage.ATTACKING:
            self.sampleGenerator = curve_samples(
                start=self.value, target=UPPER, duration=self.attack,
                overshoot=self.overshoot, prepend=prepend
            )
        elif self.stage is Stage.DECAYING:
            self.sampleGenerator = curve_samples(
                start=self.value, target=self.sustain, duration=self.decay,
                overshoot=self.overshoot, prepend=prepend
            )
        elif self.stage is Stage.SUSTAINING:
            self.sampleGenerator = constant_samples(
                value=self.sustain, prepend=prepend
            )
        elif self.stage is Stage.RELEASING:
            self.sampleGenerator = curve_samples(
                start=self.value, target=LOWER, duration=self.release,
                overshoot=self.overshoot, prepend=prepend
            )

    def switch_stage(self, stage, prepend=None):
        """Switch to another envelope stage and update sample generator."""
        self.stage = stage
        self.update_sample_generator(prepend)

    def gate(self, triggered):
        """Process incoming note messages and turn envelope on / off."""
        if triggered:
            self.enabled = True
            if self.retrigger or self.stage in {Stage.OFF, Stage.RELEASING}:
                self.switch_stage(Stage.ATTACKING)
        else:
            self.enabled = False
            if self.stage in {Stage.ATTACKING, Stage.DECAYING, Stage.SUSTAINING}:
                self.switch_stage(Stage.RELEASING)

    def determine_next_stage(self):
        """Determine which envelope stage comes next. Stage transition logic.
        Also depends on the `loop` and `enabled` attributes.

        Returns:
            Stage: Next envelope stage.
        """
        # Keeping it pure is easier to read here
        # pylint: disable=no-else-return
        if self.stage is Stage.ATTACKING:
            return Stage.DECAYING

        elif self.stage is Stage.DECAYING:
            if self.loop:
                return Stage.RELEASING
            else:
                return Stage.SUSTAINING

        elif self.stage == Stage.RELEASING:
            if self.loop and self.enabled:
                return Stage.ATTACKING
            else:
                return Stage.OFF

        else:
            return self.stage

    def go_to_next_stage(self):
        """Advance to next envelope stage."""
        nextStage = self.determine_next_stage()
        self.switch_stage(nextStage)

    def sample(self, bufferSize=UNUSED):
        """Get next BUFFER_SIZE envelope samples.

        Kwargs:
            bufferSize (float): UNUSED buffer length. For same API as C Envelope.

        Returns:
            array: Envelope samples.
        """
        samples, self.value = next(self.sampleGenerator)
        while generator_finished(samples):
            self.go_to_next_stage()
            samples, self.value = next(self.sampleGenerator)

        return samples
