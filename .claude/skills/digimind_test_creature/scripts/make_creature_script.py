"""Generate creature_test/show_<name>.py from the project's standard
floating-creature test template (same pattern as show_creature.py /
show_amicimon.py): a borderless, transparent, always-on-top PySide6 window
showing one hardcoded image with the shared BobAnimation floating effect.

Usage: python make_creature_script.py <project_root> <name> <image_path_relative_to_project_root> [scale]
"""
import sys
from pathlib import Path

TEMPLATE = '''"""Standalone test: opens a borderless, transparent, always-on-top window
showing a hardcoded creature image on the desktop, gently floating in place.
Click and drag the creature to reposition it."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QApplication, QLabel, QWidget

from character.animation import BobAnimation

IMAGE_PATH = Path(__file__).parent.parent / "{image_rel_path}"
SCALE = {scale}


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
'''


def main() -> None:
    project_root = Path(sys.argv[1])
    name = sys.argv[2]
    image_rel_path = sys.argv[3]
    scale = sys.argv[4] if len(sys.argv) > 4 else "0.216"

    out_path = project_root / "creature_test" / f"show_{name}.py"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        TEMPLATE.format(image_rel_path=image_rel_path.replace("\\", "/"), scale=scale),
        encoding="utf-8",
    )
    print(f"Saved {out_path}")


if __name__ == "__main__":
    main()
