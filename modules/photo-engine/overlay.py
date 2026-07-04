"""Composición del lienzo (cualquier ancho/alto) y overlay de texto/logo,
todo definido en la config del perfil — este módulo no conoce Wallapop,
Instagram ni El Mes Dolç, solo "elementos" con nombre."""

from PIL import Image, ImageDraw, ImageFont

from core.paths import PROJECT_ROOT
from core.logging_setup import get_logger

log = get_logger(__name__)


def _load_font(font_path: str, size: int) -> ImageFont.FreeTypeFont:
    try:
        return ImageFont.truetype(font_path, size)
    except OSError:
        log.warning(
            "No se encontró la fuente '%s', usando fuente por defecto.",
            font_path,
        )
        return ImageFont.load_default(size=size)


def _hex_to_rgb(hex_color: str) -> tuple:
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))


def _resolve_xy(canvas_w: int, canvas_h: int, elem_w: int, elem_h: int, position: str, margin: int) -> tuple:
    """Traduce una posición tipo 'top-right', 'bottom-left', 'center'... a (x, y)."""
    if "left" in position:
        x = margin
    elif "right" in position:
        x = canvas_w - margin - elem_w
    else:
        x = (canvas_w - elem_w) // 2

    if "top" in position:
        y = margin
    elif "bottom" in position:
        y = canvas_h - margin - elem_h
    else:
        y = (canvas_h - elem_h) // 2

    return x, y


def compose_canvas_fill(image: Image.Image, fmt_cfg: dict) -> Image.Image:
    """Recorta/escala la imagen para rellenar el formato por completo, sin
    bordes. Pensado para fotos ya recortadas externamente con fondo sólido
    (no transparente), que no deben llevar margen del perfil."""
    width = fmt_cfg["width"]
    height = fmt_cfg["height"]
    img = image.convert("RGB")

    scale = max(width / img.width, height / img.height)
    new_w = round(img.width * scale)
    new_h = round(img.height * scale)
    resized = img.resize((new_w, new_h), Image.LANCZOS)

    left = (new_w - width) // 2
    top = (new_h - height) // 2
    return resized.crop((left, top, left + width, top + height))


def compose_canvas(product: Image.Image, fmt_cfg: dict) -> Image.Image:
    """Centra el producto (RGBA, sin fondo) sobre un lienzo del formato dado."""
    width = fmt_cfg["width"]
    height = fmt_cfg["height"]
    bg_color = _hex_to_rgb(fmt_cfg["background_color"])
    margin_pct = fmt_cfg.get("product_margin_pct", 0.08)

    canvas = Image.new("RGB", (width, height), bg_color)

    usable_w = int(width * (1 - 2 * margin_pct))
    usable_h = int(height * (1 - 2 * margin_pct))
    product_copy = product.copy()
    product_copy.thumbnail((usable_w, usable_h), Image.LANCZOS)

    x = (width - product_copy.width) // 2
    y = (height - product_copy.height) // 2
    canvas.paste(product_copy, (x, y), product_copy)
    return canvas


def _draw_text_with_background(
    draw: ImageDraw.ImageDraw,
    canvas: Image.Image,
    text: str,
    position: str,
    font: ImageFont.FreeTypeFont,
    text_color: tuple,
    margin: int,
    bg_cfg: dict,
) -> None:
    bbox = draw.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]

    x, y = _resolve_xy(canvas.width, canvas.height, text_w, text_h, position, margin)

    if bg_cfg.get("enabled"):
        pad = bg_cfg.get("padding", 12)
        box_color = _hex_to_rgb(bg_cfg.get("color", "#000000"))
        opacity = int(255 * bg_cfg.get("opacity", 0.5))
        overlay = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
        overlay_draw = ImageDraw.Draw(overlay)
        box = [x - pad, y - pad, x + text_w + pad, y + text_h + pad]
        overlay_draw.rectangle(box, fill=(*box_color, opacity))

        border_width = bg_cfg.get("border_width", 0)
        if border_width:
            border_color = _hex_to_rgb(bg_cfg.get("border_color", "#000000"))
            overlay_draw.rectangle(box, outline=(*border_color, 255), width=border_width)

        canvas.paste(Image.alpha_composite(
            canvas.convert("RGBA"), overlay
        ).convert("RGB"), (0, 0))
        draw = ImageDraw.Draw(canvas)

    draw.text((x, y - bbox[1]), text, font=font, fill=text_color)


def _apply_logo(canvas: Image.Image, logo_cfg: dict) -> Image.Image:
    if not logo_cfg or not logo_cfg.get("enabled"):
        return canvas

    logo_path = PROJECT_ROOT / logo_cfg["path"]
    if not logo_path.exists():
        log.warning("Logo no encontrado en %s; se omite.", logo_path)
        return canvas

    logo = Image.open(logo_path).convert("RGBA")
    max_w = max(1, int(canvas.width * logo_cfg.get("max_width_pct", 0.2)))
    logo.thumbnail((max_w, max_w), Image.LANCZOS)

    x, y = _resolve_xy(
        canvas.width, canvas.height, logo.width, logo.height,
        logo_cfg.get("position", "top-right"), logo_cfg.get("margin", 30),
    )

    canvas_rgba = canvas.convert("RGBA")
    canvas_rgba.paste(logo, (x, y), logo)
    return canvas_rgba.convert("RGB")


def apply_overlay(canvas: Image.Image, texts: dict, config: dict) -> Image.Image:
    """Dibuja los elementos de texto definidos por `texts` (nombre -> valor)
    usando el estilo de `overlay.elements` del perfil, y el logo si está
    activado. Un nombre en `texts` que el perfil no define se ignora."""
    overlay_cfg = config.get("overlay", {})
    font_path = overlay_cfg.get("font_path")
    bg_cfg = overlay_cfg.get("text_background", {})
    elements_cfg = overlay_cfg.get("elements", {})

    draw = ImageDraw.Draw(canvas)

    for name, value in texts.items():
        if not value:
            continue
        elem_cfg = elements_cfg.get(name)
        if elem_cfg is None:
            log.warning("El perfil no define el elemento de overlay '%s'; se ignora.", name)
            continue
        font = _load_font(font_path, elem_cfg["font_size"])
        _draw_text_with_background(
            draw, canvas, value, elem_cfg["position"], font,
            _hex_to_rgb(elem_cfg["text_color"]), elem_cfg["margin"], bg_cfg,
        )

    return _apply_logo(canvas, overlay_cfg.get("logo"))
