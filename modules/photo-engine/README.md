# Photo Engine

Flujo: foto → se obtiene el producto sin fondo (tres vías posibles) → se
añade overlay de título y precio (según `configs/wallapop.json`) → imagen
1:1 lista para Wallapop, guardada en `data/outputs/`.

## Uso

Desde la raíz del repo, con el entorno virtual activado:

```
python modules/photo-engine/main.py --input data/inputs/silla.jpg --title "Silla de madera" --price "25 EUR"
```

También acepta una carpeta entera (procesa todas las fotos dentro, con el
mismo título y precio para todas):

```
python modules/photo-engine/main.py --input data/inputs --title "Silla de madera" --price "25 EUR"
```

El resultado se guarda en `data/outputs/<nombre>_wallapop.jpg`.

## Vías de recorte de fondo (`--source`)

No hay detección automática: tú eliges la vía según el objeto.

- `--source rembg` (por defecto): recorte automático local, sin límite de
  uso. Configurable en `configs/wallapop.json` → `background_removal`
  (modelo, alpha matting, limpieza de restos desconectados).
- `--source chatgpt`: la foto ya viene recortada por ti con ChatGPT.
- `--source nanobanana`: la foto ya viene recortada por ti con Nano
  Banana / Google AI Studio.

Para `chatgpt` y `nanobanana`, el programa detecta solo si la imagen tiene
transparencia real (canal alfa con variación) o no:

- **Con transparencia real** (PNG con fondo transparente, tal como se pidió
  en el prompt): se compone centrada sobre el fondo del perfil (color de
  `configs/<perfil>.json` → `output.background_color`).
- **Sin transparencia** (la IA devolvió fondo sólido negro o blanco en vez
  de transparente, algo que ocurre a veces): se usa la imagen tal cual, sin
  intentar quitar ese fondo, rellenando el cuadrado 1:1 completo sin
  bordes.

```
python modules/photo-engine/main.py --input data/inputs/silla_recortada.png --title "Silla de madera" --price "25 EUR" --source chatgpt
```

## Ajustar el recorte automático (`rembg`)

En `configs/wallapop.json` → `background_removal`:

- `model`: modelo de segmentación de rembg (por defecto `birefnet-massive`,
  el más preciso disponible; más lento en CPU que `u2net`/`isnet`).
- `alpha_matting`: suaviza bordes. Con modelos BiRefNet suele dar peor
  resultado (bordes ya son muy nítidos) — se deja en `false` por defecto.
- `keep_largest_component`: elimina del recorte cualquier resto totalmente
  desconectado del objeto principal (útil si hay otro objeto de fondo o
  manchas de suelo). Si el objeto de fondo *toca* visualmente al principal
  en la foto, no se puede separar con esto — hace falta dejar espacio entre
  ambos al fotografiar.

## Ajustar el estilo del overlay

Todo el estilo (posición del texto, colores, tamaño de letra, fondo detrás
del texto, tamaño final de la imagen) se controla desde
`configs/wallapop.json`, sin tocar el código.
