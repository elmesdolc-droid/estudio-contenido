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
core/                  utilidades compartidas (config, logging, rutas)
modules/
  photo-engine/        motor de fotos (fondo + overlay) — fase 1
  video-engine/         motor de vídeo — futuro
  agents/
    ideas/              agente de ideas de contenido — futuro
    sound/              agente de sonido/música — futuro
    qc/                 agente de control de calidad — futuro
  dashboard/            panel de control — futuro
  distribution/          publicación en redes — futuro
configs/               perfiles por proyecto (wallapop.json, ...)
data/                  entradas/salidas locales (no se sube a git)
```

## Fase actual: Photo Engine — perfil Wallapop

Flujo: foto de móvil → se quita el fondo → se añade overlay de título y
precio → imagen 1:1 lista para publicar en Wallapop.

Ver `modules/photo-engine/README.md` para instrucciones de uso.
