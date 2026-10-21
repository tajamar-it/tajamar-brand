# Marca Tajamar

El manual de marca de Tajamar, online, para el equipo y las agencias: manifiesto, valores, tono de voz, logo, color, tipografía, arquitectura de marca, fotografía, look & feel, aplicaciones y descargas oficiales. Publicado en https://brand.tajamar.es.

## Estructura

```
public/                 lo que publica Netlify (brand.tajamar.es)
  index.html            el site: una sola página, sin dependencias de build
  logos/svg/, logos/png/  logos oficiales (SVG y PNG transparente de 2000 px)
  img/                  retículas de construcción y otros recursos de la página
  plantillas/           plantillas descargables y su catálogo (plantillas.js, generado)
  descargas/            kit, paleta y archivos para agentes de IA (guía, tokens, skill, version.json, archivo/)
  llms.txt, CAMBIOS.md  generados por tools/build-agentes.py
tools/                  scripts de mantenimiento
CAMBIOS.md              historial de versiones de la marca (el original)
origen/                 material de origen, fuera de git (ver abajo)
```

### origen/ (no se versiona)

Plantillas de Office, imágenes de firma, folletos, recursos gráficos y tipografías con licencia. Está en `.gitignore` porque el repositorio es público: **pídelo a Comunicación** (comunicacion@tajamar.es). Estructura esperada, con nombres en minúsculas y guiones (cada archivo se llama como el slug con que se publica):

```
origen/
  plantillas/{cartas,carteles,examenes,presentaciones,secretaria}/
  firmas-correo/        firma-<área>.jpg y firmas-correo.psd
  folletos/             folleto-<nombre>.pdf
  recursos-graficos/
  tipografias/          con-licencia/ y libres/ (ver su LEEME.md)
```

## Ver en local

Sirve la carpeta publicada: `python -m http.server -d public`.

## Publicación

Netlify, desde la rama `main`, publicando solo `public/` (configuración en `netlify.toml`). Cada push a `main` se publica.

## Mantenimiento

### Versiones

La versión vigente es la primera entrada de `CAMBIOS.md` (`## X.Y · AAAA-MM-DD`). Para publicar una nueva:

1. Añade la entrada arriba en `CAMBIOS.md` con lo que cambia.
2. Ejecuta `python tools/build-agentes.py`. Pone la versión en la guía, la skill, los tokens, `llms.txt` y el pie de la web; genera `public/descargas/version.json` con la huella SHA-256 de cada archivo, y archiva la versión en `public/descargas/archivo/X.Y/`.
3. Haz commit y crea la etiqueta: `git tag -a marca-vX.Y -m "Marca Tajamar X.Y"` y `git push --tags`.

Una versión archivada no se toca: si cambias la guía sin subir de versión, el script se detiene y avisa.


Este site es la referencia de la marca. Si cambia una regla, cámbiala en `public/index.html` y en `public/descargas/tajamar-marca.md`, sube de versión en `CAMBIOS.md` y ejecuta `python tools/build-agentes.py`.

Para actualizar las plantillas, cambia el archivo en `origen/` y ejecuta `python tools/build-plantillas.py` (Windows con Office).

Las fuentes corporativas (Avenir, Rockwell, ITC Franklin Gothic) tienen licencia y no se incluyen en este repositorio: están en `origen/tipografias/`.
