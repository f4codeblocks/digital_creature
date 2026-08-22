from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QHBoxLayout, QLineEdit, QWidget


class ChatInput(QWidget):
    """Small floating text field for talking to the active creature."""

    submitted = Signal(str)

    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self._field = QLineEdit(self)
        self._field.setPlaceholderText("Escribe algo...")
        self._field.setFixedWidth(240)
        self._field.setStyleSheet(
            "QLineEdit {"
            "  border-radius: 14px;"
            "  padding: 8px 14px;"
            "  background: rgba(255, 255, 255, 235);"
            "  border: 2px solid #282828;"
            "  font-size: 13px;"
            "  color: #202020;"
            "}"
        )
        self._field.returnPressed.connect(self._on_submit)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._field)

    def _on_submit(self) -> None:
        text = self._field.text().strip()
        if text:
            self._field.clear()
            self.hide()
            self.submitted.emit(text)

    def open_at(self, anchor_x: int, anchor_y: int) -> None:
        self.adjustSize()
        self.move(anchor_x - self.width() // 2, anchor_y - self.height())
        self.show()
        self.raise_()
        self._field.setFocus()
