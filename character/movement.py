import random

from PySide6.QtCore import QTimer


class Movement:
    """Drives horizontal walking, bouncing off the screen edges."""

    def __init__(self, window, speed: int = 2, interval_ms: int = 16, on_direction_change=None):
        self._window = window
        self._speed = speed
        self._interval_ms = interval_ms
        self._on_direction_change = on_direction_change
        self._direction = random.choice([-1, 1])

        self._timer = QTimer()
        self._timer.timeout.connect(self._tick)

    @property
    def direction(self) -> int:
        return self._direction

    def start(self) -> None:
        self._timer.start(self._interval_ms)

    def stop(self) -> None:
        self._timer.stop()

    def _set_direction(self, direction: int) -> None:
        if direction != self._direction:
            self._direction = direction
            if self._on_direction_change:
                self._on_direction_change(direction)

    def _tick(self) -> None:
        screen = self._window.screen().availableGeometry()
        min_x = 0
        max_x = screen.width() - self._window.width()

        new_x = self._window.x() + self._speed * self._direction
        if new_x <= min_x:
            new_x = min_x
            self._set_direction(1)
        elif new_x >= max_x:
            new_x = max_x
            self._set_direction(-1)

        self._window.move(new_x, self._window.y())
