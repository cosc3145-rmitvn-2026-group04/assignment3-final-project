from typing import Any
from pathlib import Path
import json

PHASES_DB: Path = Path(__file__).resolve().parents[1] / "game_phases.json"


def get_phases() -> dict[str, Any]:
    with open(PHASES_DB, "r") as file:
        return json.load(file)
