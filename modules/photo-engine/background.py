"""Quitar el fondo de una foto usando rembg (modelo local)."""

from PIL import Image
from rembg import remove

from core.logging_setup import get_logger

log = get_logger(__name__)


def remove_background(image: Image.Image) -> Image.Image:
    """Devuelve la imagen sin fondo, con transparencia (RGBA)."""
    log.info("Quitando fondo...")
    result = remove(image)
    return result.convert("RGBA")
