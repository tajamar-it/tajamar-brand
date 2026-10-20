"""Genera los archivos para agentes de IA a partir de descargas/tajamar-marca.md y la paleta.

Uso (desde la raíz del repo):  python tools/build-agentes.py

Salida:
  descargas/tajamar-tokens.json      tokens de diseño (formato W3C Design Tokens)
  descargas/tajamar-marca-skill.zip  skill para Claude (SKILL.md + tokens + logos)
  llms.txt                           índice para agentes en la raíz del sitio
"""
import csv, json, zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
D = ROOT / "descargas"
SITE = "https://brand.tajamar.es"


def lum(h):
    c = [int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    c = [v / 12.92 if v <= .03928 else ((v + .055) / 1.055) ** 2.4 for v in c]
    return .2126 * c[0] + .7152 * c[1] + .0722 * c[2]


def ratio(a, b):
    x, y = lum(a), lum(b)
    return (max(x, y) + .05) / (min(x, y) + .05)


# Tokens
color = {}
for r in csv.DictReader(open(D / "tajamar-paleta.csv", encoding="utf-8-sig"), delimiter=";"):
    h = r["hex"].upper()
    gama = r["gama"].lower().replace(" ", "-")
    color.setdefault(gama, {})[r["nombre"]] = {
        "$type": "color", "$value": h,
        "$extensions": {"tajamar": {
            "rgb": r["rgb"], "pantone": r["pantone"] or None, "cmyk": r["cmyk"],
            "textoSobreBlanco": ratio(h, "#FFFFFF") >= 4.5,
            "textoEncima": "#000000" if ratio(h, "#000000") >= ratio(h, "#FFFFFF") else "#FFFFFF",
        }},
    }
tokens = {
    "$description": f"Tokens de marca Tajamar. Reglas completas: {SITE}/descargas/tajamar-marca.md",
    "color": color,
    "font": {
        "display": {"$type": "fontFamily", "$value": ["Rockwell", "Rokkitt", "Courier", "serif"],
                    "$description": "Titulares de gran formato y frases aspiracionales. Nunca cursiva."},
        "text": {"$type": "fontFamily", "$value": ["Avenir", "Montserrat", "Verdana", "sans-serif"],
                 "$description": "Principal: titulares informativos y texto corrido."},
        "architecture": {"$type": "fontFamily", "$value": ["ITC Franklin Gothic", "Libre Franklin", "Arial", "sans-serif"],
                         "$description": "Descriptores de área (Medium); Fundación en Demi."},
    },
}
tokens_json = json.dumps(tokens, ensure_ascii=False, indent=2) + "\n"
(D / "tajamar-tokens.json").write_text(tokens_json, encoding="utf-8")

# Skill para Claude
guide = (D / "tajamar-marca.md").read_text(encoding="utf-8")
skill = f"""---
name: tajamar-marca
description: Marca Tajamar (colegio, FP, Club Deportivo, Fundación, Alumni). Úsala siempre que escribas, diseñes o revises cualquier pieza, texto, presentación, web, cartel o publicación de Tajamar: tono de voz, valores, logo y escudo, colores, tipografía, firma de cada área y fotografía.
---

Los logos oficiales están en `logos/svg/` y `logos/png/` dentro de esta skill, y los tokens de color y fuente en `tajamar-tokens.json`. Usa siempre esos archivos, nunca recrees el logo. Antes de entregar un texto, pásale la prueba «libres y punto».

{guide}"""
with zipfile.ZipFile(D / "tajamar-marca-skill.zip", "w", zipfile.ZIP_DEFLATED) as z:
    z.writestr("tajamar-marca/SKILL.md", skill)
    z.writestr("tajamar-marca/tajamar-tokens.json", tokens_json)
    for sub in ("svg", "png"):
        for f in sorted((ROOT / "logos" / sub).iterdir()):
            z.write(f, f"tajamar-marca/logos/{sub}/{f.name}")

# llms.txt
(ROOT / "llms.txt").write_text(f"""# Marca Tajamar

> Manual de marca de Tajamar (Colegio, FP + Professional Education, Club Deportivo, Fundación Tajamar y Alumni): valores, tono de voz, logo, color, tipografía, arquitectura de marca, fotografía y archivos oficiales.

## Para agentes

- [Guía de marca en Markdown]({SITE}/descargas/tajamar-marca.md): todas las reglas en texto, lista para usar como contexto
- [Tokens de diseño]({SITE}/descargas/tajamar-tokens.json): colores (HEX, RGB, Pantone, CMYK, uso como texto) y fuentes, en formato W3C Design Tokens
- [Skill para Claude]({SITE}/descargas/tajamar-marca-skill.zip): SKILL.md con la guía, los tokens y los logos

## Archivos

- [Plantillas]({SITE}/#plantillas): cartas, presentación, carteles, examen, Secretaría y firmas de correo (catálogo en {SITE}/plantillas/plantillas.js)

- [Kit de marca]({SITE}/descargas/tajamar-kit-de-marca.zip): logos en SVG y PNG de 2000 px
- [Paleta]({SITE}/descargas/tajamar-paleta.csv): CSV con separador ;
- Logos sueltos: {SITE}/logos/svg/<nombre>.svg y {SITE}/logos/png/<nombre>.png
""", encoding="utf-8")

print("OK")
