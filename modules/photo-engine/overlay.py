"""Composición del lienzo 1:1 y overlay de título/precio, según perfil."""

from PIL import Image, ImageDraw, ImageFont

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


def compose_canvas_fill(image: Image.Image, config: dict) -> Image.Image:
    """Recorta/escala la imagen para rellenar el cuadrado 1:1 por completo,
    sin bordes. Pensado para fotos ya recortadas externamente con fondo
    sólido (no transparente), que no deben llevar margen del perfil."""
    size = config["output"]["size"]
    img = image.convert("RGB")

    scale = max(size / img.width, size / img.height)
    new_w = round(img.width * scale)
    new_h = round(img.height * scale)
    resized = img.resize((new_w, new_h), Image.LANCZOS)

    left = (new_w - size) // 2
    top = (new_h - size) // 2
    return resized.crop((left, top, left + size, top + size))


def compose_canvas(product: Image.Image, config: dict) -> Image.Image:
    """Centra el producto (RGBA, sin fondo) sobre un lienzo cuadrado."""
    out_cfg = config["output"]
    size = out_cfg["size"]
    bg_color = _hex_to_rgb(out_cfg["background_color"])
    margin_pct = out_cfg.get("product_margin_pct", 0.08)

    canvas = Image.new("RGB", (size, size), bg_color)

    usable = int(size * (1 - 2 * margin_pct))
    product_copy = product.copy()
    product_copy.thumbnail((usable, usable), Image.LANCZOS)

    x = (size - product_copy.width) // 2
    y = (size - product_copy.height) // 2
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

    size = canvas.width
    if position == "bottom-left":
        x = margin
    elif position == "bottom-right":
        x = size - margin - text_w
    else:
        x = (size - text_w) // 2
    y = size - margin - text_h

    if bg_cfg.get("enabled"):
        pad = bg_cfg.get("padding", 12)
        box_color = _hex_to_rgb(bg_cfg.get("color", "#000000"))
        opacity = int(255 * bg_cfg.get("opacity", 0.5))
        overlay = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
        overlay_draw = ImageDraw.Draw(overlay)
        overlay_draw.rectangle(
            [x - pad, y - pad, x + text_w + pad, y + text_h + pad],
            fill=(*box_color, opacity),
        )
        canvas.paste(Image.alpha_composite(
            canvas.convert("RGBA"), overlay
        ).convert("RGB"), (0, 0))
        draw = ImageDraw.Draw(canvas)

    draw.text((x, y - bbox[1]), text, font=font, fill=text_color)


def apply_overlay(canvas: Image.Image, title: str, price: str, config: dict) -> Image.Image:
    """Dibuja título y precio sobre el lienzo, según el perfil."""
    overlay_cfg = config["overlay"]
    font_path = overlay_cfg["font_path"]
    bg_cfg = overlay_cfg.get("text_background", {})

    draw = ImageDraw.Draw(canvas)

    title_cfg = overlay_cfg["title"]
    title_font = _load_font(font_path, title_cfg["font_size"])
    _draw_text_with_background(
        draw, canvas, title, title_cfg["position"], title_font,
        _hex_to_rgb(title_cfg["text_color"]), title_cfg["margin"], bg_cfg,
    )

    price_cfg = overlay_cfg["price"]
    price_font = _load_font(font_path, price_cfg["font_size"])
    _draw_text_with_background(
        draw, canvas, price, price_cfg["position"], price_font,
        _hex_to_rgb(price_cfg["text_color"]), price_cfg["margin"], bg_cfg,
    )

    return canvas
