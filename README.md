# Estudio de Contenido Digital

Repositorio único para el estudio de contenido digital: fotografía, vídeo,
agentes de IA y distribución (Instagram, YouTube, WhatsApp), construido por
fases.

## Principios del proyecto

- **Orquestación propia**: el código de este repo es 100% propio.
- **Commodity resuelto = herramienta de terceros**: no reinventamos lo que
  ya está resuelto (ej. quitar fondos de fotos con `rembg`).
- **Servicios externos**: una cuenta individual por servicio, usando solo
  créditos gratuitos.
- **Proyectos = perfiles de configuración**: cada "proyecto" (Wallapop,
  Instagram, El Mes Dolç...) es un fichero en `configs/`, no una copia del
  código.

## Estructura

```
assets/fonts/          tipografías compartidas del motor de overlay
core/                  utilidades compartidas (config, logging, rutas)
modules/
  photo-engine/        motor de fotos (fondo + redimensionado + overlay básico) — fase 1, cerrada
  video-engine/         motor de vídeo — fase actual
  agents/
    ideas/              agente de ideas de contenido — futuro
    sound/              agente de sonido/música — futuro
    qc/                 agente de control de calidad — futuro
  dashboard/            panel de control — futuro
  distribution/          publicación en redes — futuro
configs/               perfiles por proyecto (wallapop.json, ...)
data/                  entradas/salidas locales (no se sube a git)
```

## Fase 1 (cerrada): Photo Engine

Recorte de fondo (rembg/BiRefNet o recortado manual con ChatGPT/Nano
Banana) + redimensionado en lote a formatos (1:1, 4:5, 9:16) + overlay
básico de texto (título/precio, pensado para Wallapop). Las imágenes
gancho premium para Instagram/El Mes Dolç se producen manualmente con IA
generativa, no con este motor — ver "Alcance del proyecto" en
`modules/photo-engine/README.md`.

## Fase actual: Video Engine

Por definir.
