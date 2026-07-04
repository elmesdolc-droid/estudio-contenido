# Photo Engine

Flujo: foto de móvil → se quita el fondo (rembg) → se añade overlay de
título y precio (según `configs/wallapop.json`) → imagen 1:1 lista para
Wallapop, guardada en `data/outputs/`.

## Uso

Desde la raíz del repo, con el entorno virtual activado:

```
python modules/photo-engine/main.py --input data/inputs/silla.jpg --title "Silla de madera" --price "25 EUR"
```

También acepta una carpeta entera (procesa todas las fotos dentro):

```
python modules/photo-engine/main.py --input data/inputs --title "Silla de madera" --price "25 EUR"
```

El resultado se guarda en `data/outputs/<nombre>_wallapop.jpg`.

## Ajustar el estilo del overlay

Todo el estilo (posición del texto, colores, tamaño de letra, fondo detrás
del texto, tamaño final de la imagen) se controla desde
`configs/wallapop.json`, sin tocar el código.
