# Configs

Cada fichero de esta carpeta es el "perfil" de un proyecto: qué estilo de
overlay usar, tamaños de salida, etc. El código de `modules/` no cambia
entre proyectos — solo cambia el perfil que se le pasa.

- `wallapop.json` — anuncios de segunda mano: formato único 1:1, overlay
  título + precio.
- `instagram.json` — publicaciones de producto/marca: dos formatos (feed
  4:5 y Stories 9:16) generados en una sola pasada, overlay de nombre de
  producto (sin precio), calidad de exportación alta para compensar la
  recompresión de Instagram.
- `elmesdolc.json` — catálogo de pastelería: formato 1:1, overlay de marca
  propia (sin precio tipo "artículo usado").

Los tres perfiles usan el mismo motor (`modules/photo-engine/`) y las
mismas tres vías de recorte de fondo (`rembg` / `chatgpt` / `nanobanana`).
Los logos de marca (opcionales) van en `configs/assets/`; El Mes Dolç ya
tiene el suyo activado, Instagram todavía no.

Nota: el overlay "editorial" de Instagram/El Mes Dolç (tipografía,
franja/desenfoque, recorte agresivo) se dejó de iterar — ver "Alcance del
proyecto" en `modules/photo-engine/README.md`. Los tres perfiles siguen
siendo válidos para recorte + redimensionado en lote.
