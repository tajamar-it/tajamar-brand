# Marca Tajamar

El manual de marca de Tajamar, online, para el equipo y las agencias: manifiesto, valores, tono de voz, logo, color, tipografía, arquitectura de marca, fotografía, look & feel, aplicaciones y descargas oficiales. Publicado en https://brand.tajamar.es.

## Estructura

- `index.html`: el site (una sola página, sin dependencias de build).
- `logos/svg/`: vectoriales oficiales.
- `logos/png/`: PNG transparentes de 2000 px generados a partir de los SVG.
- `img/construccion/`: retículas de construcción y áreas de protección.
- `descargas/`: kit completo (`.zip`), paleta (`.csv`) y archivos para agentes de IA (guía `.md`, tokens `.json`, skill `.zip`).
- `llms.txt`: índice para agentes.
- `tools/build-agentes.py`: regenera tokens, skill y `llms.txt` a partir de `descargas/tajamar-marca.md` y la paleta.

## Ver en local

Abre `index.html` en el navegador, o sirve la carpeta: `python3 -m http.server`.

## Publicación

Netlify, desde la rama `main` (configuración en `netlify.toml`). Cada push a `main` se publica.

## Mantenimiento

### Versiones

La versión vigente es la primera entrada de `CAMBIOS.md` (`## X.Y · AAAA-MM-DD`). Para publicar una nueva:

1. Añade la entrada arriba en `CAMBIOS.md` con lo que cambia.
2. Ejecuta `python tools/build-agentes.py`. Pone la versión en la guía, la skill, los tokens, `llms.txt` y el pie de la web; genera `descargas/version.json` con la huella SHA-256 de cada archivo, y archiva la versión en `descargas/archivo/X.Y/`.
3. Haz commit y crea la etiqueta: `git tag -a marca-vX.Y -m "Marca Tajamar X.Y"` y `git push --tags`.

Una versión archivada no se toca: si cambias la guía sin subir de versión, el script se detiene y avisa.


Este site es la referencia de la marca. Si cambia una regla, cámbiala en `index.html` y en `descargas/tajamar-marca.md`, y ejecuta `python tools/build-agentes.py`.

Las fuentes corporativas (Avenir, Rockwell, ITC Franklin Gothic) tienen licencia y no se incluyen en este repositorio.
