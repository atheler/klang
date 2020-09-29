import sys
import time


class ProgressBar:

    """Simple progress bar with remaining time."""

    stream = sys.stdout
    clock = time.perf_counter

    def __init__(self, length: int, width: int = 20, prefix: str = ''):
        self.length = length
        self.width = width
        self.prefix = prefix

        self.startTime = 0.

    @classmethod
    def range(cls, length, *args, **kwargs):
        """Wraps a range with a progress bar. Currently only with length (no
        start, stop, step).
        """
        progressBar = cls(length, *args, **kwargs)
        for i in range(length):
            progressBar.print(i)
            yield i

    def render(self, i) -> str:
        """Render progress bar."""
        progress = max(0, min(1, i / (self.length - 1)))

        # ETA
        now = self.clock()
        if progress == 0:
            self.startTime = now
            eta = float('inf')
        else:
            passed = now - self.startTime
            eta = self.startTime + passed / progress

        remaining = eta - now

        # Render bar
        ticks = int(progress * self.width)
        bar = '[%s%s]' % (
            ticks * '*',
            (self.width - ticks) * ' '
        )

        infos = []
        if self.prefix:
            infos.append(self.prefix)

        infos.extend([
            bar,
            '%.3f sec' % remaining,
        ])
        return ' '.join(infos)

    def is_at_end(self, i):
        """Is it the end?"""
        return i >= self.length - 1

    def print(self, i):
        """Print progress bar."""
        eraseLine = '\33[2K'
        self.stream.write(eraseLine)
        self.stream.write('\r')
        self.stream.write(self.render(i))
        if self.is_at_end(i):
            self.stream.write('\n')

        self.stream.flush()
