import json
from pathlib import Path

import requests
from PySide6.QtCore import QThread, Signal

from ai.prompt import system_prompt

CONFIG_PATH = Path(__file__).parent.parent / "config" / "config.json"


def _load_config() -> dict:
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)["ollama"]


class OllamaClient:
    """Sends a message to Ollama and returns the creature's reply as plain text."""

    def __init__(self, character_name: str = "cognimon"):
        config = _load_config()
        self._host = config["host"]
        self._model = config["model"]
        self._timeout = config["timeout_seconds"]
        self._system_prompt = system_prompt(character_name.capitalize())

    def ask(self, message: str) -> str:
        try:
            response = requests.post(
                f"{self._host}/api/chat",
                json={
                    "model": self._model,
                    "messages": [
                        {"role": "system", "content": self._system_prompt},
                        {"role": "user", "content": message},
                    ],
                    "stream": False,
                },
                timeout=self._timeout,
            )
            response.raise_for_status()
            return response.json()["message"]["content"].strip()
        except requests.RequestException:
            return "Hmm... no puedo conectar con mi cerebro ahora mismo."


class OllamaWorker(QThread):
    """Runs an Ollama request off the UI thread so the app never freezes."""

    reply_ready = Signal(str)

    def __init__(self, client: OllamaClient, message: str):
        super().__init__()
        self._client = client
        self._message = message

    def run(self) -> None:
        reply = self._client.ask(self._message)
        self.reply_ready.emit(reply)
