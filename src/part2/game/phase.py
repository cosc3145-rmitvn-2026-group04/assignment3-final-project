from typing import Any
from pathlib import Path
import json

PHASES_CONFIG_FILE: Path = Path(__file__).resolve().parents[1] / "game_phases.json"


def get_phases(phases_config_file: Path | None = None) -> list[dict[str, Any]]:
    file_path: Path = phases_config_file if phases_config_file else PHASES_CONFIG_FILE
    with open(file_path, "r") as file:
        return json.load(file)
