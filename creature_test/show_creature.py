"""Standalone test: opens a borderless, transparent, always-on-top window
showing a hardcoded creature image on the desktop, gently floating in place.
Click and drag the creature to reposition it."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QApplication, QLabel, QWidget

from character.animation import BobAnimation

IMAGE_PATH = Path(__file__).parent.parent / "images" / "curimon_transparent.png"
SCALE = 0.216


class CreatureWindow(QWidget):
    def __init__(self, image_path: Path):
        super().__init__()

        self.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.label = QLabel(self)
        self.label.setAttribute(Qt.WA_TransparentForMouseEvents)
        pixmap = QPixmap(str(image_path))
        pixmap = pixmap.scaled(pixmap.size() * SCALE, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.label.setPixmap(pixmap)
        self.label.resize(pixmap.size())

        self.resize(pixmap.size())

        screen = self.screen().availableGeometry()
        x = screen.width() - self.width() - 80
        y = screen.height() - self.height() - 80
        self.move(x, y)

        self.float_animation = BobAnimation(self, amplitude=6, period_ms=2200)
        self.float_animation.start()

        self._drag_offset = None

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.LeftButton:
            self.float_animation.stop()
            self._drag_offset = event.globalPosition().toPoint() - self.pos()

    def mouseMoveEvent(self, event) -> None:
        if self._drag_offset is not None:
            self.move(event.globalPosition().toPoint() - self._drag_offset)

    def mouseReleaseEvent(self, event) -> None:
        if event.button() == Qt.LeftButton:
            self._drag_offset = None
            self.float_animation.start()


def main() -> None:
    app = QApplication(sys.argv)
    window = CreatureWindow(IMAGE_PATH)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
