import random

from PySide6.QtCore import QTimer

from character.animation import BobAnimation, FrameAnimation
from character.movement import Movement
from character.states import State

IDLE_BOB = dict(amplitude=6, period_ms=2200)
THINKING_BOB = dict(amplitude=3, period_ms=900)
TALKING_BOB = dict(amplitude=5, period_ms=350)

IDLE_FRAME_MS = 450
THINKING_FRAME_MS = 420
TALKING_FRAME_MS = 190
WALK_FRAME_MS = 160


class Cognimon:
    """Owns Cognimon's state machine: IDLE, WALK, THINKING and TALKING."""

    def __init__(self, window):
        self._window = window
        self.state = State.IDLE

        self._idle_bob = BobAnimation(window, **IDLE_BOB)
        self._idle_frames = FrameAnimation(window.sprite_label, window.idle_frames, IDLE_FRAME_MS)

        self._thinking_bob = BobAnimation(window, **THINKING_BOB)
        self._thinking_frames = FrameAnimation(window.sprite_label, window.thinking_frames, THINKING_FRAME_MS)

        self._talking_bob = BobAnimation(window, **TALKING_BOB)
        self._talking_frames = FrameAnimation(window.sprite_label, window.talking_frames, TALKING_FRAME_MS)

        self._walk_frames = FrameAnimation(window.sprite_label, window.walk_frames, WALK_FRAME_MS, ping_pong=False)

        self._movement = Movement(window, on_direction_change=self._on_direction_change)

        self._all_animations = (
            self._idle_bob,
            self._idle_frames,
            self._thinking_bob,
            self._thinking_frames,
            self._talking_bob,
            self._talking_frames,
            self._walk_frames,
        )

        self._state_timer = QTimer()
        self._state_timer.setSingleShot(True)
        self._state_timer.timeout.connect(self._toggle_walk_idle)

    def start(self) -> None:
        self._enter_idle()

    def is_busy(self) -> bool:
        return self.state in (State.THINKING, State.TALKING)

    def pause(self) -> None:
        self._state_timer.stop()
        self._movement.stop()
        for animation in self._all_animations:
            animation.stop()

    def resume(self) -> None:
        self._enter_idle()

    def resume_after_drag(self) -> None:
        """Restart whatever was playing before a drag paused it, without
        resetting THINKING/TALKING (that would cut off a pending reply)."""
        if self.state == State.THINKING:
            self._thinking_bob.start()
            self._thinking_frames.start()
        elif self.state == State.TALKING:
            self._talking_bob.start()
            self._talking_frames.start()
        else:
            self._enter_idle()

    def enter_thinking(self) -> None:
        self.pause()
        self.state = State.THINKING
        self._thinking_bob.start()
        self._thinking_frames.start()

    def enter_talking(self) -> None:
        self.pause()
        self.state = State.TALKING
        self._talking_bob.start()
        self._talking_frames.start()

    def _on_direction_change(self, direction: int) -> None:
        frames = self._window.walk_frames if direction == 1 else self._window.walk_frames_flipped
        self._walk_frames.set_frames(frames)

    def _enter_idle(self) -> None:
        self.pause()
        self.state = State.IDLE
        self._idle_bob.start()
        self._idle_frames.start()
        self._state_timer.start(random.randint(3000, 6000))

    def _enter_walk(self) -> None:
        self.pause()
        self.state = State.WALK
        self._on_direction_change(self._movement.direction)
        self._walk_frames.start()
        self._movement.start()
        self._state_timer.start(random.randint(2000, 5000))

    def _toggle_walk_idle(self) -> None:
        if self.state == State.IDLE:
            self._enter_walk()
        else:
            self._enter_idle()
