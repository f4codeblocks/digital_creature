import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

from ui.desktop import CognimonWindow

ASSET_PATH = Path(__file__).parent / "assets" / "cognimon" / "idle" / "idle_01.png"


def main() -> None:
    app = QApplication(sys.argv)
    window = CognimonWindow(ASSET_PATH)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
