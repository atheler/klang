"""Time clock."""


class ClockMixin:

    """Mixin class / global clock variable for blocks. Clock value has to be
    updated in main loop.

    Attributes:
        currentTime: Current clock time.
    """

    currentTime = 0.

    @classmethod
    def set_current_time(cls, time: float):
        """Set current time."""
        cls.currentTime = time

    @classmethod
    def clock(cls) -> float:
        """Get current time."""
        return cls.currentTime
