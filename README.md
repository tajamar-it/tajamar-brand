# Marca Tajamar

Site estático con el manual de marca de Tajamar para el equipo y las agencias: valores, tono de voz, logo, color, tipografía, arquitectura de marca, fotografía, look & feel y descargas oficiales.

## Estructura

- `index.html`: el site (una sola página, sin dependencias de build).
- `logos/svg/`: vectoriales oficiales.
- `logos/png/`: PNG transparentes de 2000 px generados a partir de los SVG.
- `descargas/`: kit completo (`.zip`) y paleta de color (`.csv`).

## Ver en local

Abre `index.html` en el navegador, o sirve la carpeta: `python3 -m http.server`.

## Publicación

Preparado para GitHub Pages (rama `main`, carpeta raíz). El archivo `.nojekyll` evita el procesado de Jekyll.

## Fuente

*Tajamar Identity Guidelines · Brand Book & Voice* (2016) y guía operativa del Departamento de Comunicación. Las firmas de FP, Educación Infantil y libresypunto se extrajeron del PDF del manual; si existen vectoriales originales, tienen prioridad.

Las fuentes corporativas (Avenir, Rockwell, ITC Franklin Gothic) tienen licencia y no se incluyen en este repositorio.
