"""Carga de perfiles de configuración desde configs/<perfil>.json."""

import json

from core.paths import CONFIGS_DIR


def load_profile(name: str) -> dict:
    """Carga el perfil `name` (sin extensión) desde la carpeta configs/."""
    path = CONFIGS_DIR / f"{name}.json"
    if not path.exists():
        raise FileNotFoundError(
            f"No existe el perfil de configuración: {path}"
        )
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
