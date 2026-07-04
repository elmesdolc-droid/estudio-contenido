"""CLI del photo-engine: quita fondo, añade overlay y exporta 1:1."""

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from PIL import Image

from core.config import load_profile
from core.paths import DATA_OUTPUTS_DIR
from core.logging_setup import get_logger

from background import remove_background
from overlay import compose_canvas, apply_overlay

log = get_logger(__name__)

SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


def process_image(
    input_path: Path, output_dir: Path, title: str, price: str, config: dict
) -> Path:
    log.info("Procesando %s", input_path.name)
    image = Image.open(input_path).convert("RGBA")

    product = remove_background(image)
    canvas = compose_canvas(product, config)
    canvas = apply_overlay(canvas, title, price, config)

    output_dir.mkdir(parents=True, exist_ok=True)
    out_cfg = config["output"]
    fmt = out_cfg["format"].upper()
    ext = ".jpg" if fmt == "JPEG" else f".{fmt.lower()}"
    output_path = output_dir / f"{input_path.stem}_wallapop{ext}"
    canvas.save(output_path, fmt, quality=out_cfg.get("quality", 90))
    log.info("Guardado en %s", output_path)
    return output_path


def gather_inputs(input_path: Path) -> list:
    if input_path.is_file():
        return [input_path]
    if input_path.is_dir():
        return sorted(
            p for p in input_path.iterdir()
            if p.suffix.lower() in SUPPORTED_EXTENSIONS
        )
    raise FileNotFoundError(f"No existe la ruta de entrada: {input_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Quita el fondo y añade título/precio a fotos para Wallapop."
    )
    parser.add_argument("--input", required=True, help="Foto suelta o carpeta con fotos")
    parser.add_argument("--title", required=True, help="Título del anuncio")
    parser.add_argument("--price", required=True, help="Precio del anuncio (ej. '25 EUR')")
    parser.add_argument("--profile", default="wallapop", help="Perfil de configs/ a usar")
    parser.add_argument(
        "--output", default=None, help="Carpeta de salida (por defecto data/outputs)"
    )
    args = parser.parse_args()

    config = load_profile(args.profile)
    output_dir = Path(args.output) if args.output else DATA_OUTPUTS_DIR

    inputs = gather_inputs(Path(args.input))
    if not inputs:
        log.warning("No se encontraron fotos en %s", args.input)
        return

    for image_path in inputs:
        process_image(image_path, output_dir, args.title, args.price, config)

    log.info("Listo: %d foto(s) procesada(s).", len(inputs))


if __name__ == "__main__":
    main()
