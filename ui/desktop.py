from pathlib import Path

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPixmap, QTransform
from PySide6.QtWidgets import QApplication, QLabel, QMenu, QWidget

from ai.ollama_client import OllamaClient, OllamaWorker
from ui.chat_input import ChatInput
from ui.speech_bubble import SpeechBubble

SPRITE_SCALE = 0.36
MIN_BUBBLE_DURATION_MS = 3000
MAX_BUBBLE_DURATION_MS = 9000
READING_MS_PER_CHAR = 70
ASSETS_ROOT = Path(__file__).parent.parent / "assets"


class CreatureWindow(QWidget):
    """Borderless, transparent, always-on-top window that shows one digital creature.

    Which creature is generic here: `character_name` picks its asset folder
    (assets/<character_name>/<state>/*.png) and `creature_cls` is the state
    machine class (e.g. character.cognimon.Cognimon) that drives it -- see
    main.py for how a name is resolved to both."""

    def __init__(self, character_name: str, creature_cls):
        super().__init__()

        self._assets_root = ASSETS_ROOT / character_name

        self.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)

        idle_path = self._assets_root / "idle" / "idle_01.png"
        loaded_pixmap = QPixmap(str(idle_path))
        self._box_size = loaded_pixmap.size() * SPRITE_SCALE

        self.sprite_label = QLabel(self)
        self.sprite_label.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.sprite_label.setAlignment(Qt.AlignCenter)

        self._original_pixmap = self._fit(loaded_pixmap)
        self.sprite_label.setPixmap(self._original_pixmap)

        self.idle_frames = self.load_frames("idle")
        self.thinking_frames = self.load_frames("thinking")
        self.talking_frames = self.load_frames("talking")
        self.walk_frames = self.load_frames("walk")
        self.walk_frames_flipped = [p.transformed(QTransform().scale(-1, 1)) for p in self.walk_frames]

        self.resize(self._box_size)
        self.sprite_label.resize(self._box_size)

        self._place_on_screen()

        self.bubble = SpeechBubble()
        self.chat_input = ChatInput()
        self.chat_input.submitted.connect(self._on_message_submitted)

        self._ollama_client = OllamaClient(character_name)
        self._worker = None

        self.creature = creature_cls(self)
        self.creature.start()

        self._drag_offset = None
        self._press_pos = None
        self._dragging = False

    def _fit(self, pixmap: QPixmap) -> QPixmap:
        return pixmap.scaled(self._box_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)

    def load_frames(self, state: str) -> list:
        """Loads assets/<character>/<state>/*.png, fitted to the sprite box.
        Returns an empty list if the creature has no frames for this state --
        FrameAnimation treats that as a no-op, so a missing state degrades to
        a bob-only pulse instead of erroring."""
        folder = self._assets_root / state
        return [self._fit(QPixmap(str(p))) for p in sorted(folder.glob("*.png"))]

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.LeftButton:
            self._press_pos = event.globalPosition().toPoint()
            self._drag_offset = self._press_pos - self.pos()
            self._dragging = False
            self.creature.pause()
        elif event.button() == Qt.RightButton:
            self._open_context_menu(event.globalPosition().toPoint())

    def mouseMoveEvent(self, event) -> None:
        if self._drag_offset is None:
            return
        current = event.globalPosition().toPoint()
        if not self._dragging and (current - self._press_pos).manhattanLength() > 4:
            self._dragging = True
        if self._dragging:
            self.move(current - self._drag_offset)

    def mouseReleaseEvent(self, event) -> None:
        if event.button() != Qt.LeftButton or self._drag_offset is None:
            return
        was_dragging = self._dragging
        self._drag_offset = None
        self._dragging = False
        self.creature.resume_after_drag()
        if not was_dragging:
            self._open_chat()

    def _open_chat(self) -> None:
        if self.creature.is_busy():
            return
        self.creature.pause()
        self.bubble.hide()
        anchor_x, anchor_y = self._bubble_anchor()
        self.chat_input.open_at(anchor_x, anchor_y)

    def _open_context_menu(self, global_pos) -> None:
        menu = QMenu(self)
        menu.addAction("Hablar", self._open_chat)
        if hasattr(self.creature, "trigger_dab"):
            menu.addAction("Dab", self.creature.trigger_dab)
        if hasattr(self.creature, "trigger_shooting"):
            menu.addAction("Shooting", self.creature.trigger_shooting)
        menu.addAction("Dormir", self._sleep)
        menu.addAction("Salir", self._quit)
        menu.exec(global_pos)

    def _sleep(self) -> None:
        self.chat_input.hide()
        self.bubble.hide()
        self.creature.pause()

    def _quit(self) -> None:
        if hasattr(self.creature, "trigger_exit"):
            self.chat_input.hide()
            self.bubble.hide()
            self.creature.trigger_exit(QApplication.instance().quit)
        else:
            QApplication.instance().quit()

    def _on_message_submitted(self, text: str) -> None:
        self.creature.enter_thinking()
        anchor_x, anchor_y = self._bubble_anchor()
        self.bubble.show_message("...", anchor_x, anchor_y)

        self._worker = OllamaWorker(self._ollama_client, text)
        self._worker.reply_ready.connect(self._on_reply_ready)
        self._worker.start()

    def _on_reply_ready(self, reply: str) -> None:
        self.creature.enter_talking()
        anchor_x, anchor_y = self._bubble_anchor()
        duration_ms = min(
            MAX_BUBBLE_DURATION_MS,
            max(MIN_BUBBLE_DURATION_MS, len(reply) * READING_MS_PER_CHAR),
        )
        self.bubble.show_message(reply, anchor_x, anchor_y, duration_ms=duration_ms)
        QTimer.singleShot(duration_ms, self.creature.resume)

    def _bubble_anchor(self) -> tuple[int, int]:
        return self.x() + self.width() // 2, self.y()

    def _place_on_screen(self) -> None:
        screen = self.screen().availableGeometry()
        x = screen.width() - self.width() - 80
        y = screen.height() - self.height() - 80
        self.move(x, y)
