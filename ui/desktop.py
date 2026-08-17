from pathlib import Path

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPixmap, QTransform
from PySide6.QtWidgets import QApplication, QLabel, QMenu, QWidget

from ai.ollama_client import OllamaClient, OllamaWorker
from character.cognimon import Cognimon
from ui.chat_input import ChatInput
from ui.speech_bubble import SpeechBubble

SPRITE_SCALE = 0.36
MIN_BUBBLE_DURATION_MS = 3000
MAX_BUBBLE_DURATION_MS = 9000
READING_MS_PER_CHAR = 70
ASSETS_ROOT = Path(__file__).parent.parent / "assets" / "cognimon"


class CognimonWindow(QWidget):
    """Borderless, transparent, always-on-top window that shows Cognimon."""

    def __init__(self, sprite_path: Path):
        super().__init__()

        self.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)

        loaded_pixmap = QPixmap(str(sprite_path))
        self._box_size = loaded_pixmap.size() * SPRITE_SCALE

        self.sprite_label = QLabel(self)
        self.sprite_label.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.sprite_label.setAlignment(Qt.AlignCenter)

        self._original_pixmap = self._fit(loaded_pixmap)
        self.sprite_label.setPixmap(self._original_pixmap)

        self.idle_frames = self._load_frames("idle")
        self.thinking_frames = self._load_frames("thinking")
        self.talking_frames = self._load_frames("talking")
        self.walk_frames = self._load_frames("walk")
        self.walk_frames_flipped = [p.transformed(QTransform().scale(-1, 1)) for p in self.walk_frames]

        self.resize(self._box_size)
        self.sprite_label.resize(self._box_size)

        self._place_on_screen()

        self.bubble = SpeechBubble()
        self.chat_input = ChatInput()
        self.chat_input.submitted.connect(self._on_message_submitted)

        self._ollama_client = OllamaClient()
        self._worker = None

        self.cognimon = Cognimon(self)
        self.cognimon.start()

    def _fit(self, pixmap: QPixmap) -> QPixmap:
        return pixmap.scaled(self._box_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)

    def _load_frames(self, state: str) -> list:
        folder = ASSETS_ROOT / state
        return [self._fit(QPixmap(str(p))) for p in sorted(folder.glob("*.png"))]

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.LeftButton:
            self._open_chat()
        elif event.button() == Qt.RightButton:
            self._open_context_menu(event.globalPosition().toPoint())

    def _open_chat(self) -> None:
        if self.cognimon.is_busy():
            return
        self.cognimon.pause()
        self.bubble.hide()
        anchor_x, anchor_y = self._bubble_anchor()
        self.chat_input.open_at(anchor_x, anchor_y)

    def _open_context_menu(self, global_pos) -> None:
        menu = QMenu(self)
        menu.addAction("Hablar", self._open_chat)
        menu.addAction("Dormir", self._sleep)
        menu.addAction("Salir", QApplication.instance().quit)
        menu.exec(global_pos)

    def _sleep(self) -> None:
        self.chat_input.hide()
        self.bubble.hide()
        self.cognimon.pause()

    def _on_message_submitted(self, text: str) -> None:
        self.cognimon.enter_thinking()
        anchor_x, anchor_y = self._bubble_anchor()
        self.bubble.show_message("...", anchor_x, anchor_y)

        self._worker = OllamaWorker(self._ollama_client, text)
        self._worker.reply_ready.connect(self._on_reply_ready)
        self._worker.start()

    def _on_reply_ready(self, reply: str) -> None:
        self.cognimon.enter_talking()
        anchor_x, anchor_y = self._bubble_anchor()
        duration_ms = min(
            MAX_BUBBLE_DURATION_MS,
            max(MIN_BUBBLE_DURATION_MS, len(reply) * READING_MS_PER_CHAR),
        )
        self.bubble.show_message(reply, anchor_x, anchor_y, duration_ms=duration_ms)
        QTimer.singleShot(duration_ms, self.cognimon.resume)

    def _bubble_anchor(self) -> tuple[int, int]:
        return self.x() + self.width() // 2, self.y()

    def _place_on_screen(self) -> None:
        screen = self.screen().availableGeometry()
        x = screen.width() - self.width() - 80
        y = screen.height() - self.height() - 80
        self.move(x, y)
