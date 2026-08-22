from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class SpeechBubble(QWidget):
    """Comic-style speech bubble that appears above the active creature."""

    MAX_WIDTH = 260

    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self._label = QLabel(self)
        self._label.setWordWrap(True)
        self._label.setMaximumWidth(self.MAX_WIDTH)
        self._label.setStyleSheet("color: #202020; font-size: 13px; background: transparent;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.addWidget(self._label)

        self._hide_timer = QTimer(self)
        self._hide_timer.setSingleShot(True)
        self._hide_timer.timeout.connect(self.hide)

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QColor(255, 255, 255, 235))
        painter.setPen(QPen(QColor(40, 40, 40), 2))
        painter.drawRoundedRect(self.rect().adjusted(1, 1, -1, -1), 14, 14)

    def show_message(self, text: str, anchor_x: int, anchor_y: int, duration_ms: int | None = None) -> None:
        self._label.setText(text)
        self.adjustSize()
        self.move(anchor_x - self.width() // 2, anchor_y - self.height())
        self.show()
        self.raise_()
        self._hide_timer.stop()
        if duration_ms:
            self._hide_timer.start(duration_ms)
