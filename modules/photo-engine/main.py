"""CLI del photo-engine: quita fondo, añade overlay y exporta según el
perfil elegido (Wallapop, Instagram, El Mes Dolç...). El motor es el mismo
para todos los perfiles; solo cambia la configuración que se carga."""

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from core.config import load_profile
from core.paths import DATA_OUTPUTS_DIR
from core.logging_setup import get_logger

from product import load_product
from overlay import compose_canvas, compose_canvas_fill, apply_overlay

log = get_logger(__name__)

SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
SOURCES = ("rembg", "chatgpt", "nanobanana")


def process_image(
    input_path: Path,
    output_dir: Path,
    texts: dict,
    config: dict,
    source: str,
    format_name: str,
) -> list:
    log.info("Procesando %s (fuente=%s)", input_path.name, source)

    # El recorte de fondo se hace una sola vez, aunque el perfil tenga
    # varios formatos de salida (ej. Instagram: feed + stories).
    product, needs_margin = load_product(input_path, source, config)

    formats = config["formats"]
    if format_name:
        if format_name not in formats:
            raise ValueError(
                f"El perfil no define el formato '{format_name}'. "
                f"Formatos disponibles: {', '.join(formats)}"
            )
        selected = {format_name: formats[format_name]}
    else:
        selected = formats

    profile_name = config.get("profile", "output")
    single_format = len(formats) == 1

    output_dir.mkdir(parents=True, exist_ok=True)
    saved_paths = []

    for fmt_name, fmt_cfg in selected.items():
        canvas = (
            compose_canvas(product, fmt_cfg)
            if needs_margin
            else compose_canvas_fill(product, fmt_cfg)
        )
        canvas = apply_overlay(canvas, texts, config)

        fmt = fmt_cfg.get("format", "JPEG").upper()
        ext = ".jpg" if fmt == "JPEG" else f".{fmt.lower()}"
        suffix = f"_{profile_name}" if single_format else f"_{profile_name}_{fmt_name}"
        output_path = output_dir / f"{input_path.stem}{suffix}{ext}"
        canvas.save(output_path, fmt, quality=fmt_cfg.get("quality", 90))
        log.info("Guardado en %s", output_path)
        saved_paths.append(output_path)

    return saved_paths


def gather_inputs(input_path: Path) -> list:
    if input_path.is_file():
        return [input_path]
    if input_path.is_dir():
        return sorted(
            p for p in input_path.iterdir()
            if p.suffix.lower() in SUPPORTED_EXTENSIONS
        )
    raise FileNotFoundError(f"No existe la ruta de entrada: {input_path}")


def parse_texts(args: argparse.Namespace) -> dict:
    texts = {}
    if args.title is not None:
        texts["title"] = args.title
    if args.price is not None:
        texts["price"] = args.price
    for item in args.text:
        if "=" not in item:
            raise ValueError(f"--text debe tener forma clave=valor: '{item}'")
        key, value = item.split("=", 1)
        texts[key.strip()] = value
    return texts


def main():
    parser = argparse.ArgumentParser(
        description="Quita el fondo y añade overlay a fotos, según el perfil elegido."
    )
    parser.add_argument("--input", required=True, help="Foto suelta o carpeta con fotos")
    parser.add_argument("--profile", default="wallapop", help="Perfil de configs/ a usar")
    parser.add_argument("--title", default=None, help="Atajo para --text title=... (perfil Wallapop)")
    parser.add_argument("--price", default=None, help="Atajo para --text price=... (perfil Wallapop)")
    parser.add_argument(
        "--text",
        action="append",
        default=[],
        metavar="CLAVE=VALOR",
        help=(
            "Texto para un elemento de overlay del perfil, ej. "
            "--text product_name=\"Tarta de manzana\". Repetible."
        ),
    )
    parser.add_argument(
        "--format",
        dest="format_name",
        default=None,
        help=(
            "Nombre del formato de salida a generar (ver 'formats' del perfil). "
            "Por defecto genera todos los formatos del perfil."
        ),
    )
    parser.add_argument(
        "--source",
        choices=SOURCES,
        default="rembg",
        help=(
            "Vía de recorte de fondo: 'rembg' (automático local, por defecto), "
            "'chatgpt' o 'nanobanana' (foto ya recortada por ti con esa IA)."
        ),
    )
    parser.add_argument(
        "--output", default=None, help="Carpeta de salida (por defecto data/outputs)"
    )
    args = parser.parse_args()

    config = load_profile(args.profile)
    texts = parse_texts(args)
    output_dir = Path(args.output) if args.output else DATA_OUTPUTS_DIR

    inputs = gather_inputs(Path(args.input))
    if not inputs:
        log.warning("No se encontraron fotos en %s", args.input)
        return

    total_outputs = 0
    for image_path in inputs:
        saved = process_image(
            image_path, output_dir, texts, config, args.source, args.format_name
        )
        total_outputs += len(saved)

    log.info("Listo: %d foto(s) procesada(s), %d fichero(s) generado(s).", len(inputs), total_outputs)


if __name__ == "__main__":
    main()
