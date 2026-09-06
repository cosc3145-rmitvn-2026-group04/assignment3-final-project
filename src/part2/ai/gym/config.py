from typing import Any
from pathlib import Path
import json

HYPERPARAMETER_CONFIG_FILE: Path = Path(__file__).resolve().parents[2] / "rl_env_hparams.json"


def get_hyperparameters() -> dict[str, Any]:
    with open(HYPERPARAMETER_CONFIG_FILE, "r") as file:
        return json.load(file)
