"""Composición del lienzo (cualquier ancho/alto) y overlay de texto/logo,
todo definido en la config del perfil — este módulo no conoce Wallapop,
Instagram ni El Mes Dolç, solo "elementos" con nombre."""

import re
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

from core.paths import PROJECT_ROOT
from core.logging_setup import get_logger

log = get_logger(__name__)

# La fuente de overlay no tiene por qué traer glifos de emoji: se eliminan
# antes de medir/dibujar para no dejar cuadros vacíos.
_EMOJI_PATTERN = re.compile(
    "["
    "\U0001F300-\U0001FAFF"
    "\U00002600-\U000027BF"
    "\U0001F1E6-\U0001F1FF"
    "\U00002B00-\U00002BFF"
    "\U0000FE0F"
    "\U0000200D"
    "]+",
    flags=re.UNICODE,
)


def _strip_unsupported_chars(text: str) -> str:
    cleaned = _EMOJI_PATTERN.sub("", text)
    cleaned = re.sub(r"\s{2,}", " ", cleaned).strip()
    if cleaned != text:
        log.warning(
            "El texto de overlay contenía caracteres no soportados por la "
            "fuente (ej. emoji); se han quitado: '%s' -> '%s'", text, cleaned,
        )
    return cleaned


def _resolve_font_path(font_path: str) -> Path:
    path = Path(font_path)
    return path if path.is_absolute() else PROJECT_ROOT / path


def _load_font(font_path: str, size: int, weight_name: str = None) -> ImageFont.FreeTypeFont:
    resolved = _resolve_font_path(font_path)
    try:
        font = ImageFont.truetype(str(resolved), size)
    except OSError:
        log.error(
            "ERROR: no se pudo cargar la fuente '%s' (ruta resuelta: '%s'); "
            "se usa el fallback interno de PIL (bitmap básico).",
            font_path, resolved,
        )
        return ImageFont.load_default(size=size)

    if weight_name:
        try:
            font.set_variation_by_name(weight_name)
        except Exception as exc:
            log.warning(
                "Fuente '%s' cargada, pero no admite el peso '%s' (%s); "
                "se usa su peso por defecto.", resolved, weight_name, exc,
            )

    return font


def _fit_font(
    draw: ImageDraw.ImageDraw, text: str, font_path: str, base_size: int,
    max_width: int, min_size: int = 16, stroke_width: int = 0,
    weight_name: str = None,
) -> ImageFont.FreeTypeFont:
    """Reduce el tamaño de letra hasta que el texto quepa en `max_width`."""
    size = base_size
    font = _load_font(font_path, size, weight_name)
    while size > min_size:
        bbox = draw.textbbox((0, 0), text, font=font, stroke_width=stroke_width)
        if bbox[2] - bbox[0] <= max_width:
            break
        size -= 2
        font = _load_font(font_path, size, weight_name)

    resolved = _resolve_font_path(font_path)
    if resolved.exists():
        log.info(
            "CONFIRMADO: fuente cargada desde '%s' (peso solicitado='%s', "
            "tamaño final=%dpx) para el texto '%s'.",
            resolved, weight_name, size, text,
        )
    else:
        log.error(
            "ERROR: la ruta de fuente '%s' NO EXISTE en disco; el texto "
            "'%s' se está dibujando con el fallback de PIL.", resolved, text,
        )
    return font


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


def _crop_to_content(image: Image.Image) -> Image.Image:
    """Recorta el margen transparente sobrante alrededor del producto, para
    que el margen del perfil se aplique sobre el contenido real y no sobre
    el encuadre original de la foto."""
    bbox = image.getchannel("A").getbbox()
    return image.crop(bbox) if bbox else image


def _build_blur_backdrop(
    product_content: Image.Image, width: int, height: int,
    bg_color: tuple, blur_cfg: dict,
) -> Image.Image:
    """Fondo a pantalla completa hecho con el propio producto, ampliado y
    desenfocado, para que el espacio que el producto no llena (típico en
    Stories con fotos panorámicas) se sienta parte del diseño en vez de
    vacío."""
    pad_pct = 0.06
    base_w = max(1, int(product_content.width * (1 + 2 * pad_pct)))
    base_h = max(1, int(product_content.height * (1 + 2 * pad_pct)))
    base = Image.new("RGB", (base_w, base_h), bg_color)
    ox = (base_w - product_content.width) // 2
    oy = (base_h - product_content.height) // 2
    base.paste(product_content, (ox, oy), product_content)

    scale = max(width / base_w, height / base_h)
    new_w = max(1, round(base_w * scale))
    new_h = max(1, round(base_h * scale))
    resized = base.resize((new_w, new_h), Image.LANCZOS)

    left = (new_w - width) // 2
    top = (new_h - height) // 2
    cropped = resized.crop((left, top, left + width, top + height))

    radius = max(1, int(min(width, height) * blur_cfg.get("radius_pct", 0.05)))
    blurred = cropped.filter(ImageFilter.GaussianBlur(radius))

    tint_opacity = blur_cfg.get("tint_opacity", 0.0)
    if tint_opacity > 0:
        tint_color = _hex_to_rgb(blur_cfg.get("tint_color", "#000000"))
        tint = Image.new("RGB", (width, height), tint_color)
        blurred = Image.blend(blurred, tint, tint_opacity)

    return blurred


def compose_canvas(product: Image.Image, fmt_cfg: dict) -> Image.Image:
    """Centra el producto (RGBA, sin fondo) sobre un lienzo del formato dado.

    - `max_crop_pct`: si la forma de la foto no encaja con el formato (ej.
      producto panorámico en un lienzo cuadrado/vertical), permite recortar
      un poco los bordes del producto para que ocupe más lienzo, en vez de
      dejarlo pequeño con aire de sobra. 0 = nunca recorta.
    - `fill_style: "blur"`: si tras el recorte controlado sigue sobrando
      espacio, se rellena con una versión ampliada y desenfocada del propio
      producto en vez de dejar el color de fondo liso.
    """
    width = fmt_cfg["width"]
    height = fmt_cfg["height"]
    bg_color = _hex_to_rgb(fmt_cfg["background_color"])
    margin_pct = fmt_cfg.get("product_margin_pct", 0.08)
    max_crop_pct = fmt_cfg.get("max_crop_pct", 0.0)

    product_copy = _crop_to_content(product)

    if fmt_cfg.get("fill_style") == "blur":
        canvas = _build_blur_backdrop(
            product_copy, width, height, bg_color, fmt_cfg.get("blur_fill", {})
        )
    else:
        canvas = Image.new("RGB", (width, height), bg_color)

    usable_w = int(width * (1 - 2 * margin_pct))
    usable_h = int(height * (1 - 2 * margin_pct))

    scale_contain = min(usable_w / product_copy.width, usable_h / product_copy.height)
    scale_cover = max(usable_w / product_copy.width, usable_h / product_copy.height)
    scale = min(scale_cover, scale_contain * (1 + max_crop_pct))
    effective_crop_pct = (scale / scale_contain) - 1

    new_w = max(1, round(product_copy.width * scale))
    new_h = max(1, round(product_copy.height * scale))
    resized = product_copy.resize((new_w, new_h), Image.LANCZOS)

    crop_w = min(new_w, usable_w)
    crop_h = min(new_h, usable_h)
    left = (new_w - crop_w) // 2
    top = (new_h - crop_h) // 2
    resized = resized.crop((left, top, left + crop_w, top + crop_h))

    log.info(
        "CONFIRMADO: compose_canvas %dx%d | product_margin_pct=%.3f | "
        "max_crop_pct=%.3f (permitido) -> %.3f (aplicado realmente) | "
        "fill_style=%s | producto recortado a contenido=%dx%d -> final=%dx%d",
        width, height, margin_pct, max_crop_pct, effective_crop_pct,
        fmt_cfg.get("fill_style", "solid"),
        product_copy.width, product_copy.height,
        resized.width, resized.height,
    )

    x = (width - resized.width) // 2
    y = (height - resized.height) // 2
    canvas.paste(resized, (x, y), resized)
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


def _draw_text_with_stroke(
    draw: ImageDraw.ImageDraw,
    canvas: Image.Image,
    text: str,
    position: str,
    font: ImageFont.FreeTypeFont,
    text_color: tuple,
    margin: int,
    stroke_color: tuple,
    stroke_width: int,
    shadow_cfg: dict = None,
) -> None:
    """Dibuja el texto directamente sobre la imagen: sombra suave (opcional)
    + contorno grueso, sin caja de color de por medio. Pensado para tener
    presencia real sobre fotos variadas sin tapar el producto."""
    bbox = draw.textbbox((0, 0), text, font=font, stroke_width=stroke_width)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]

    x, y = _resolve_xy(canvas.width, canvas.height, text_w, text_h, position, margin)

    if shadow_cfg and shadow_cfg.get("enabled"):
        offset = shadow_cfg.get("offset", 4)
        shadow_color = _hex_to_rgb(shadow_cfg.get("color", "#000000"))
        shadow_opacity = int(255 * shadow_cfg.get("opacity", 0.55))
        shadow_layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
        ImageDraw.Draw(shadow_layer).text(
            (x - bbox[0] + offset, y - bbox[1] + offset), text, font=font,
            fill=(*shadow_color, shadow_opacity),
        )
        canvas.paste(Image.alpha_composite(
            canvas.convert("RGBA"), shadow_layer
        ).convert("RGB"), (0, 0))
        draw = ImageDraw.Draw(canvas)

    draw.text(
        (x - bbox[0], y - bbox[1]), text, font=font, fill=text_color,
        stroke_width=stroke_width, stroke_fill=stroke_color,
    )


def _apply_scrim(canvas: Image.Image, scrim_cfg: dict) -> Image.Image:
    """Franja degradada (transparente -> color) para dar legibilidad al
    texto sin tapar el producto con un bloque sólido."""
    if not scrim_cfg or not scrim_cfg.get("enabled"):
        return canvas

    position = scrim_cfg.get("position", "bottom")
    height_pct = scrim_cfg.get("height_pct", 0.32)
    color = _hex_to_rgb(scrim_cfg.get("color", "#000000"))
    max_opacity = scrim_cfg.get("max_opacity", 0.7)

    w, h = canvas.size
    band_h = max(1, int(h * height_pct))

    gradient = Image.new("L", (1, band_h), 0)
    for i in range(band_h):
        ratio = i / band_h if position == "bottom" else 1 - i / band_h
        gradient.putpixel((0, i), int(max_opacity * 255 * ratio))
    gradient = gradient.resize((w, band_h))

    alpha_layer = Image.new("L", (w, h), 0)
    y_offset = h - band_h if position == "bottom" else 0
    alpha_layer.paste(gradient, (0, y_offset))

    overlay = Image.new("RGBA", (w, h), (*color, 0))
    overlay.putalpha(alpha_layer)

    return Image.alpha_composite(canvas.convert("RGBA"), overlay).convert("RGB")


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
    activado. Un nombre en `texts` que el perfil no define se ignora.

    `overlay.text_style` decide cómo se asegura la legibilidad del texto:
    - "box" (por defecto): caja de color sólido detrás del texto.
    - "stroke": el texto va directamente sobre la foto, con sombra suave y
      contorno grueso y, opcionalmente, una franja degradada (`overlay.scrim`)
      detrás.
    """
    overlay_cfg = config.get("overlay", {})
    font_path = overlay_cfg.get("font_path")
    font_weight = overlay_cfg.get("font_weight")
    elements_cfg = overlay_cfg.get("elements", {})
    text_style = overlay_cfg.get("text_style", "box")

    if text_style == "stroke":
        canvas = _apply_scrim(canvas, overlay_cfg.get("scrim"))

    draw = ImageDraw.Draw(canvas)
    bg_cfg = overlay_cfg.get("text_background", {})
    stroke_cfg = overlay_cfg.get("text_stroke", {})
    shadow_cfg = overlay_cfg.get("text_shadow", {})
    stroke_width = stroke_cfg.get("width", 0)
    stroke_color = _hex_to_rgb(stroke_cfg.get("color", "#000000"))

    for name, value in texts.items():
        if not value:
            continue
        elem_cfg = elements_cfg.get(name)
        if elem_cfg is None:
            log.warning("El perfil no define el elemento de overlay '%s'; se ignora.", name)
            continue

        text = _strip_unsupported_chars(str(value))
        if not text:
            continue

        margin = elem_cfg["margin"]
        max_width = max(1, canvas.width - 2 * margin)

        if text_style == "stroke":
            font = _fit_font(
                draw, text, font_path, elem_cfg["font_size"], max_width,
                stroke_width=stroke_width, weight_name=font_weight,
            )
            _draw_text_with_stroke(
                draw, canvas, text, elem_cfg["position"], font,
                _hex_to_rgb(elem_cfg["text_color"]), margin,
                stroke_color, stroke_width, shadow_cfg,
            )
        else:
            font = _fit_font(
                draw, text, font_path, elem_cfg["font_size"], max_width,
                weight_name=font_weight,
            )
            _draw_text_with_background(
                draw, canvas, text, elem_cfg["position"], font,
                _hex_to_rgb(elem_cfg["text_color"]), margin, bg_cfg,
            )

    return _apply_logo(canvas, overlay_cfg.get("logo"))
