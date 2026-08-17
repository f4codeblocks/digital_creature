import math

from PySide6.QtCore import QTimer


class BobAnimation:
    """Vertical bob whose amplitude/period conveys a different tempo per state
    (slow breathing for idle, quick pulse for thinking, small jitter for talking)."""

    def __init__(self, window, amplitude: int = 6, period_ms: int = 2200, interval_ms: int = 33):
        self._window = window
        self._amplitude = amplitude
        self._period_ms = period_ms
        self._interval_ms = interval_ms
        self._base_y = window.y()
        self._elapsed = 0

        self._timer = QTimer()
        self._timer.timeout.connect(self._tick)

    def start(self) -> None:
        self._base_y = self._window.y()
        self._elapsed = 0
        self._timer.start(self._interval_ms)

    def stop(self) -> None:
        self._timer.stop()

    def _tick(self) -> None:
        self._elapsed = (self._elapsed + self._interval_ms) % self._period_ms
        phase = (self._elapsed / self._period_ms) * 2 * math.pi
        offset = int(self._amplitude * math.sin(phase))
        self._window.move(self._window.x(), self._base_y + offset)


class FrameAnimation:
    """Cycles a QLabel through a list of sprite frames (optionally ping-ponging
    back and forth instead of looping straight through)."""

    def __init__(self, label, frames: list, interval_ms: int = 200, ping_pong: bool = True):
        self._label = label
        self._frames = frames
        self._interval_ms = interval_ms
        self._ping_pong = ping_pong
        self._index = 0
        self._step = 1

        self._timer = QTimer()
        self._timer.timeout.connect(self._tick)

    def start(self) -> None:
        if not self._frames:
            return
        self._index = 0
        self._step = 1
        self._label.setPixmap(self._frames[0])
        self._timer.start(self._interval_ms)

    def stop(self) -> None:
        self._timer.stop()

    def set_frames(self, frames: list) -> None:
        self._frames = frames
        if self._timer.isActive() and frames:
            self._label.setPixmap(frames[min(self._index, len(frames) - 1)])

    def _tick(self) -> None:
        if len(self._frames) < 2:
            return

        self._index += self._step
        if self._ping_pong:
            if self._index >= len(self._frames):
                self._index = len(self._frames) - 2
                self._step = -1
            elif self._index < 0:
                self._index = 1
                self._step = 1
        else:
            self._index %= len(self._frames)

        self._label.setPixmap(self._frames[self._index])
