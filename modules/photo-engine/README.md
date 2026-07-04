# Photo Engine

## Alcance del proyecto (decisión, 2026-07-04)

El photo-engine se congela como **herramienta de apoyo simple**:

- **Recorte de fondo** (rembg/BiRefNet, o foto ya recortada con ChatGPT/Nano
  Banana) — esto sí se mantiene y sigue siendo útil para los tres perfiles.
- **Redimensionado en lote a formatos** (1:1, 4:5, 9:16 según el perfil).
- **Overlay de texto básico** (título + precio) — pensado y mantenido
  para **Wallapop**, uso simple.

Se exploró un overlay "editorial" más avanzado (tipografía Playfair
Display, logo de marca, franja/desenfoque, recorte agresivo) para los
perfiles Instagram y El Mes Dolç. Se descarta continuar iterándolo: el
resultado programático no llega al nivel de una imagen gancho premium, y
ese tipo de imagen se va a producir **manualmente con IA generativa**
(Nano Banana / ChatGPT), que da mejor resultado con menos esfuerzo que
seguir afinando composición/tipografía por código.

El código de ese overlay avanzado (`text_style: "stroke"`, `scrim`,
`fill_style: "blur"`, fuente Playfair en `assets/fonts/`) se queda tal
cual en el repo — no se borra, pero tampoco se sigue desarrollando. Los
perfiles Instagram/El Mes Dolç siguen siendo útiles para la parte de
recorte + redimensionado por lotes, sin depender de su overlay para la
imagen final.

## Cómo funciona

Flujo: foto → se obtiene el producto sin fondo (tres vías posibles) → se
compone sobre uno o varios formatos de salida → se añade el overlay de
texto/logo del perfil → imagen(es) lista(s), guardadas en `data/outputs/`.

El motor es el mismo para todos los perfiles (`wallapop`, `instagram`,
`elmesdolc`...); solo cambia la configuración que se carga con `--profile`.

## Uso básico

Desde la raíz del repo, con el entorno virtual activado:

```
python modules/photo-engine/main.py --input data/inputs/silla.jpg --profile wallapop --title "Silla de madera" --price "25 EUR"
```

También acepta una carpeta entera (procesa todas las fotos dentro, con el
mismo texto para todas):

```
python modules/photo-engine/main.py --input data/inputs --profile wallapop --title "Silla de madera" --price "25 EUR"
```

## Perfiles y formatos (`--profile`, `--format`)

Cada perfil (`configs/<perfil>.json`) define uno o varios `formats` con su
propio ancho/alto/calidad. Si no se indica `--format`, se generan **todos**
los formatos del perfil en una sola pasada (el recorte de fondo solo se
hace una vez, aunque haya varios formatos):

```
# Genera feed (4:5) y stories (9:16) a la vez
python modules/photo-engine/main.py --input data/inputs/bolso.jpg --profile instagram --text product_name="Bolso de cuero"

# Solo un formato concreto
python modules/photo-engine/main.py --input data/inputs/bolso.jpg --profile instagram --text product_name="Bolso de cuero" --format feed
```

El resultado se guarda como `data/outputs/<nombre>_<perfil>.jpg` (perfiles
de un solo formato, ej. Wallapop) o `data/outputs/<nombre>_<perfil>_<formato>.jpg`
(perfiles con varios formatos, ej. Instagram).

**Dos comportamientos automáticos del overlay, válidos para cualquier perfil:**

- Si el texto no cabe en el ancho disponible (frecuente en formatos
  estrechos como Stories), el tamaño de letra se reduce automáticamente
  hasta que quepa, sin cortarse.
- Los emoji u otros caracteres que la fuente no sabe dibujar (Arial no
  trae glifos de emoji) se eliminan automáticamente del texto antes de
  dibujarlo, para no dejar un cuadro vacío. Si quieres emoji en la
  publicación, ponlos en el pie de la publicación al subirla, no en el
  texto que se graba dentro de la imagen.

## Texto del overlay (`--title`/`--price`, `--text`)

Cada perfil define sus propios "elementos" de texto en
`overlay.elements` (ver `configs/<perfil>.json`). Wallapop usa `title` y
`price`, para los que hay atajos dedicados:

```
--title "Silla de madera" --price "25 EUR"
```

Instagram y El Mes Dolç usan otros nombres (ej. `product_name`, sin
precio), que se pasan con `--text clave=valor` (repetible):

```
--text product_name="Tarta de manzana"
```

## Vías de recorte de fondo (`--source`)

No hay detección automática: tú eliges la vía según el objeto.

- `--source rembg` (por defecto): recorte automático local, sin límite de
  uso. Configurable en `configs/<perfil>.json` → `background_removal`
  (modelo, alpha matting, limpieza de restos desconectados).
- `--source chatgpt`: la foto ya viene recortada por ti con ChatGPT.
- `--source nanobanana`: la foto ya viene recortada por ti con Nano
  Banana / Google AI Studio.

Para `chatgpt` y `nanobanana`, el programa detecta solo si la imagen tiene
transparencia real (canal alfa con variación) o no:

- **Con transparencia real** (PNG con fondo transparente, tal como se pidió
  en el prompt): se compone centrada sobre el fondo de cada formato del
  perfil (`background_color`).
- **Sin transparencia** (la IA devolvió fondo sólido negro o blanco en vez
  de transparente, algo que ocurre a veces): se usa la imagen tal cual, sin
  intentar quitar ese fondo, rellenando el formato completo sin bordes.

```
python modules/photo-engine/main.py --input data/inputs/silla_recortada.png --profile wallapop --title "Silla de madera" --price "25 EUR" --source chatgpt
```

## Ajustar el recorte automático (`rembg`)

En `configs/<perfil>.json` → `background_removal`:

- `model`: modelo de segmentación de rembg (por defecto `birefnet-massive`,
  el más preciso disponible; más lento en CPU que `u2net`/`isnet`).
- `alpha_matting`: suaviza bordes. Con modelos BiRefNet suele dar peor
  resultado (bordes ya son muy nítidos) — se deja en `false` por defecto.
- `keep_largest_component`: elimina del recorte cualquier resto totalmente
  desconectado del objeto principal (útil si hay otro objeto de fondo o
  manchas de suelo). Si el objeto de fondo *toca* visualmente al principal
  en la foto, no se puede separar con esto — hace falta dejar espacio entre
  ambos al fotografiar.

## Ajustar el estilo del overlay y el logo

Todo el estilo (posición del texto, colores, tamaño de letra, fondo detrás
del texto, tamaño de cada formato) se controla desde
`configs/<perfil>.json`, sin tocar el código.

Cada perfil puede además superponer un logo de marca (`overlay.logo`),
desactivado por defecto hasta que exista el fichero en `configs/assets/`
(ver `configs/assets/README.md`). Si `enabled: true` pero el fichero no
existe, se omite el logo sin dar error (se avisa en el log).
