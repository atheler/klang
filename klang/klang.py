"""Main entry point function."""
import collections
import logging
import math
import time

from klang.audio.helpers import INTERVAL
# pylint: disable=unused-import
from klang.audio.klanggeber import Dac, Adc
from klang.audio.klanggeber import look_for_audio_blocks, run_audio_engine
from klang.clock import ClockMixin
from klang.composite import Composite
from klang.execution import determine_execution_order


def unravel(execOrder):
    """Flatten global execution order. Turn internal execution order of
    composites inside out.
    """
    for block in execOrder:
        if isinstance(block, Composite):
            yield from unravel(block.execOrder)
        else:
            yield block


def validate_global_execution_order(execOrder, logger):
    """Check for duplicates in flattened global execOrder. Issue a warning.

    Args:
        execOrder (list): Execution order.
        logger (Logger): Logger instance to output the warning to.
    """
    flattenedExecOrder = unravel(execOrder)
    counter = collections.Counter(flattenedExecOrder)
    hasDuplicates = max(counter.values()) > 1
    if hasDuplicates:
        fmt = (
            'Found duplicates in flattened execOrder! Following blocks will '
            'get executed multiple times per buffer cycle!\n%s'
        )

        duplicates = '\n'.join(
            '  - %s: %dx' % (block, occurences)
            for block, occurences in counter.items()
            if occurences > 1
        )
        logger.warning(fmt, duplicates)


def sleep_until_next_cycle():
    """Sleep until next cycle and return timestamp."""
    now = time.perf_counter()
    then = math.ceil(now / INTERVAL) * INTERVAL
    time.sleep(max(0, then - now))
    return then


def run_klang(*blocks, **kwargs):
    """Run klang block network.

    Args:
        blocks: Klang blocks to run.

    Kwargs:
        See help(klang.audio.run_audio_engine) for options.
    """
    if not blocks:
        raise ValueError('No blocks to run specified!')

    logger = logging.getLogger('Klang')
    logger.info('Determining execution order from %s', ', '.join(map(str, blocks)))
    execOrder = determine_execution_order(blocks)
    validate_global_execution_order(execOrder, logger)

    def execute_all_blocks():
        for block in execOrder:
            block.update()

    # Do we have audio?
    adc, dac = look_for_audio_blocks(execOrder)
    if adc.nChannels > 0 or dac.nChannels > 0:
        return run_audio_engine(adc, dac, execute_all_blocks, **kwargs)

    logger.warning('Did not find any audio activity')
    logger.info('Starting non-audio main loop')
    while True:
        now = sleep_until_next_cycle()
        ClockMixin.set_current_time(now)
        execute_all_blocks()
