"""Rutas comunes del proyecto, resueltas desde la raíz del repo."""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIGS_DIR = PROJECT_ROOT / "configs"
DATA_DIR = PROJECT_ROOT / "data"
DATA_INPUTS_DIR = DATA_DIR / "inputs"
DATA_OUTPUTS_DIR = DATA_DIR / "outputs"
