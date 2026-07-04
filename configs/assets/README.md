# Assets de marca

Aquí van los logos que cada perfil puede superponer como marca de agua
(ver `overlay.logo` en `configs/<perfil>.json`).

- `instagram_logo.png` — logo para el perfil Instagram (aún no añadido).
- `elmesdolc_logo.png` — sello circular de El Mes Dolç (añadido, activado en
  `configs/elmesdolc.json`).

Usa PNG con fondo transparente. Mientras el fichero no exista, el motor
simplemente omite el logo (sin dar error) aunque `logo.enabled` esté en
`true`.
