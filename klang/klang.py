"""Main entry point function."""
import time
import logging

from klang.audio.helpers import INTERVAL
from klang.audio.klanggeber import look_for_audio_blocks, run_audio_engine, Dac, Adc
from klang.execution import determine_execution_order


class Clock:

    """Pocket watch. Clock giver."""

    def __init__(self, startTime=0.):
        self.currentTime = startTime

    def __call__(self):
        return self.currentTime

    def step(self, dt):
        """Move clock forward in time."""
        self.currentTime += dt


def run_klang(*blocks, filepath=''):
    """Run klang block network."""
    if not blocks:
        raise ValueError('No blocks to run specified!')

    execOrder = determine_execution_order(blocks)

    def callback():
        for block in execOrder:
            block.update()

    adc, dac = look_for_audio_blocks(execOrder)
    if adc.nChannels > 0 or dac.nChannels > 0:
        return run_audio_engine(adc, dac, callback, filepath)

    logger = logging.getLogger('Klang')
    logger.warning('Did not find any audio activity')
    logger.info('Starting non-audio main loop')
    while True:
        start = time.time()
        callback()
        end = time.time()
        time.sleep(max(0, INTERVAL - (end - start)))
