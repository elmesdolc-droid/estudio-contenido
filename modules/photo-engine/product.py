"""Obtiene la imagen del producto (RGBA) según la vía de recorte elegida.

Vías soportadas:
- "rembg": recorte automático local (ver background.py).
- "chatgpt" / "nanobanana": la foto ya viene recortada por una IA externa.
  Puede tener transparencia real (PNG con canal alfa) o un fondo sólido
  (negro o blanco) si la IA no respetó el prompt de fondo transparente.
"""

from pathlib import Path

from PIL import Image

from core.logging_setup import get_logger

from background import remove_background

log = get_logger(__name__)

PRECUT_SOURCES = {"chatgpt", "nanobanana"}


def _has_real_transparency(image: Image.Image, threshold: int = 250) -> bool:
    """True si el canal alfa varía de verdad (no es 255 en toda la imagen)."""
    min_alpha, _ = image.getchannel("A").getextrema()
    return min_alpha < threshold


def load_product(input_path: Path, source: str, config: dict) -> tuple:
    """Devuelve (imagen_del_producto, necesita_margen_del_perfil).

    `necesita_margen_del_perfil` indica qué función de composición usar:
    True -> compose_canvas (centra con margen sobre el fondo del perfil).
    False -> compose_canvas_fill (rellena el cuadrado 1:1 sin bordes).
    """
    image = Image.open(input_path).convert("RGBA")

    if source == "rembg":
        return remove_background(image, config), True

    if source in PRECUT_SOURCES:
        if _has_real_transparency(image):
            log.info(
                "%s: transparencia real detectada (fuente=%s), se compone sobre "
                "el fondo del perfil.",
                input_path.name, source,
            )
            return image, True

        log.info(
            "%s: sin transparencia (fuente=%s), se usa tal cual y se rellena "
            "el cuadrado 1:1 sin bordes.",
            input_path.name, source,
        )
        return image, False

    raise ValueError(f"Fuente de recorte desconocida: {source}")
