from typing import Any
from pathlib import Path
import json

PHASES_CONFIG_FILE: Path = Path(__file__).resolve().parents[1] / "game_phases.json"


def get_phases() -> dict[str, Any]:
    with open(PHASES_CONFIG_FILE, "r") as file:
        return json.load(file)
