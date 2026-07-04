"""Quitar el fondo de una foto usando rembg, con alpha matting y limpieza
de restos desconectados del objeto principal (segundo objeto de fondo,
manchas de suelo, carteles...)."""

import numpy as np
from PIL import Image
from rembg import new_session, remove
from scipy.ndimage import label

from core.logging_setup import get_logger

log = get_logger(__name__)

_SESSIONS = {}


def _get_session(model_name: str):
    if model_name not in _SESSIONS:
        log.info("Cargando modelo de segmentación '%s'...", model_name)
        _SESSIONS[model_name] = new_session(model_name)
    return _SESSIONS[model_name]


def _keep_largest_component(image: Image.Image) -> Image.Image:
    """Se queda solo con la región conectada más grande del canal alfa;
    descarta cualquier isla desconectada del objeto principal."""
    alpha = np.array(image.getchannel("A"))
    mask = alpha > 10
    if not mask.any():
        return image

    # Conectividad de 4 vecinos (sin diagonales): más estricta, separa mejor
    # dos objetos que solo se tocan por una esquina/cruce fino.
    labeled, num_features = label(mask)
    if num_features <= 1:
        return image

    sizes = np.bincount(labeled.ravel())
    sizes[0] = 0  # la etiqueta 0 es el fondo, no cuenta
    largest_label = sizes.argmax()

    cleaned_alpha = np.where(labeled == largest_label, alpha, 0).astype(np.uint8)
    result = image.copy()
    result.putalpha(Image.fromarray(cleaned_alpha))
    return result


def remove_background(image: Image.Image, config: dict) -> Image.Image:
    """Devuelve la imagen sin fondo (RGBA), según `background_removal` del perfil."""
    bg_cfg = config.get("background_removal", {})
    model_name = bg_cfg.get("model", "u2net")
    alpha_matting = bg_cfg.get("alpha_matting", False)

    log.info(
        "Quitando fondo (modelo=%s, alpha_matting=%s)...", model_name, alpha_matting
    )
    result = remove(
        image,
        session=_get_session(model_name),
        alpha_matting=alpha_matting,
        alpha_matting_foreground_threshold=bg_cfg.get(
            "alpha_matting_foreground_threshold", 240
        ),
        alpha_matting_background_threshold=bg_cfg.get(
            "alpha_matting_background_threshold", 10
        ),
        alpha_matting_erode_size=bg_cfg.get("alpha_matting_erode_size", 10),
    ).convert("RGBA")

    if bg_cfg.get("keep_largest_component", False):
        result = _keep_largest_component(result)

    return result
