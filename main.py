import argparse
import sys

from PySide6.QtWidgets import QApplication

from character.cognimon import Cognimon
from character.curimon import Curimon
from ui.desktop import CreatureWindow

CREATURES = {
    "cognimon": Cognimon,
    "curimon": Curimon,
}


def parse_character() -> str:
    parser = argparse.ArgumentParser(description="Run one digital creature on the desktop.")
    group = parser.add_mutually_exclusive_group()
    for name in CREATURES:
        group.add_argument(f"--{name}", action="store_const", const=name, dest="character")
    parser.set_defaults(character="cognimon")
    return parser.parse_args().character


def main() -> None:
    character_name = parse_character()
    app = QApplication(sys.argv)
    window = CreatureWindow(character_name, CREATURES[character_name])
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
