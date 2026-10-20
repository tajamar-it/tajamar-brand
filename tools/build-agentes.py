"""Genera los archivos para agentes de IA a partir de descargas/tajamar-marca.md y la paleta.

Uso (desde la raíz del repo):  python tools/build-agentes.py

La versión vigente es la primera entrada de CAMBIOS.md («## X.Y · AAAA-MM-DD»).

Salida:
  descargas/tajamar-marca.md         se le añade/actualiza la cabecera de versión y el aviso para agentes
  descargas/tajamar-tokens.json      tokens de diseño (formato W3C Design Tokens)
  descargas/tajamar-marca-skill.zip  skill para Claude (SKILL.md + tokens + logos), reproducible byte a byte
  descargas/version.json             versión vigente y huella SHA-256 de cada archivo para agentes
  descargas/archivo/X.Y/             copia congelada de la versión (no se sobrescribe nunca)
  llms.txt                           índice para agentes en la raíz del sitio
  index.html                         versión vigente en el pie de página
"""
import csv, hashlib, json, re, shutil, sys, zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
D = ROOT / "descargas"
SITE = "https://brand.tajamar.es"
MESES = "enero febrero marzo abril mayo junio julio agosto septiembre octubre noviembre diciembre".split()

# --- Versión vigente
m = re.search(r"^## (\d+\.\d+) · (\d{4})-(\d{2})-(\d{2})", (ROOT / "CAMBIOS.md").read_text(encoding="utf-8"), re.M)
if not m:
    sys.exit("CAMBIOS.md no tiene ninguna entrada «## X.Y · AAAA-MM-DD».")
VERSION, Y, MO, DA = m.group(1), m.group(2), m.group(3), m.group(4)
FECHA = f"{Y}-{MO}-{DA}"
FECHA_LARGA = f"{int(DA)} de {MESES[int(MO) - 1]} de {Y}"

AVISO = (f"> **Versión {VERSION} · {FECHA_LARGA}.** Usa siempre la última versión de esta guía. "
         f"Antes de trabajar, comprueba la vigente en {SITE}/descargas/version.json: si es posterior a la {VERSION}, "
         f"descarga {SITE}/descargas/tajamar-marca.md y usa esa. Si no puedes comprobarlo, díselo a quien te lo pide: "
         f"esta copia podría estar desactualizada. Las versiones archivadas en {SITE}/descargas/archivo/ son históricas y no deben usarse.")


def lum(h):
    c = [int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    c = [v / 12.92 if v <= .03928 else ((v + .055) / 1.055) ** 2.4 for v in c]
    return .2126 * c[0] + .7152 * c[1] + .0722 * c[2]


def ratio(a, b):
    x, y = lum(a), lum(b)
    return (max(x, y) + .05) / (min(x, y) + .05)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


# --- Guía: cabecera de versión entre marcadores (se reescribe en cada ejecución)
guia_p = D / "tajamar-marca.md"
guia = guia_p.read_text(encoding="utf-8")
guia = re.sub(r"\n?<!-- version -->.*?<!-- /version -->\n", "\n", guia, flags=re.S)
titulo, resto = guia.split("\n", 1)
guia = f"{titulo}\n\n<!-- version -->\n{AVISO}\n<!-- /version -->\n{resto.lstrip(chr(10)) and chr(10) + resto.lstrip(chr(10))}"
guia_p.write_text(guia, encoding="utf-8", newline="\n")

# --- Tokens
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
    "$description": (f"Tokens de marca Tajamar · versión {VERSION} ({FECHA}). Usa siempre la última: {SITE}/descargas/version.json. "
                     f"Reglas completas: {SITE}/descargas/tajamar-marca.md"),
    "$extensions": {"tajamar": {"version": VERSION, "fecha": FECHA}},
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
(D / "tajamar-tokens.json").write_text(tokens_json, encoding="utf-8", newline="\n")

# --- Skill para Claude (zip reproducible: fechas fijas y orden estable)
skill = f"""---
name: tajamar-marca
description: Marca Tajamar (colegio, FP+, Club Deportivo, Fundación, Alumni). Úsala siempre que escribas, diseñes o revises cualquier pieza, texto, presentación, web, cartel o publicación de Tajamar: tono de voz, valores, logo y escudo, colores, tipografía, firma de cada área y fotografía.
---

Esta skill es la versión {VERSION} de la marca ({FECHA_LARGA}). Si tienes acceso a internet, consulta antes {SITE}/descargas/version.json: si hay una versión posterior, avisa al usuario y usa la guía vigente de {SITE}/descargas/tajamar-marca.md en lugar de esta.

Los logos oficiales están en `logos/svg/` y `logos/png/` dentro de esta skill, y los tokens de color y fuente en `tajamar-tokens.json`. Usa siempre esos archivos, nunca recrees el logo. Antes de entregar un texto, pásale la prueba «libres y punto».

{guia}"""


def zadd(z, name, data):
    zi = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
    zi.compress_type = zipfile.ZIP_DEFLATED
    zi.external_attr = 0o644 << 16
    z.writestr(zi, data)


with zipfile.ZipFile(D / "tajamar-marca-skill.zip", "w") as z:
    zadd(z, "tajamar-marca/SKILL.md", skill.encode("utf-8"))
    zadd(z, "tajamar-marca/tajamar-tokens.json", tokens_json.encode("utf-8"))
    for sub in ("svg", "png"):
        for f in sorted((ROOT / "logos" / sub).iterdir()):
            zadd(z, f"tajamar-marca/logos/{sub}/{f.name}", f.read_bytes())

# --- llms.txt
(ROOT / "llms.txt").write_text(f"""# Marca Tajamar

> Manual de marca de Tajamar (Colegio, Tajamar FP+, Club Deportivo, Fundación Tajamar y Alumni): valores, tono de voz, logo, color, tipografía, arquitectura de marca, fotografía y archivos oficiales.

Versión vigente: {VERSION} ({FECHA}). Usa siempre la última: compruébala en {SITE}/descargas/version.json antes de usar una copia guardada. Las versiones de {SITE}/descargas/archivo/ son históricas.

## Para agentes

- [Versión vigente]({SITE}/descargas/version.json): número, fecha y huella SHA-256 de cada archivo
- [Guía de marca en Markdown]({SITE}/descargas/tajamar-marca.md): todas las reglas en texto, lista para usar como contexto
- [Tokens de diseño]({SITE}/descargas/tajamar-tokens.json): colores (HEX, RGB, Pantone, CMYK, uso como texto) y fuentes, en formato W3C Design Tokens
- [Skill para Claude]({SITE}/descargas/tajamar-marca-skill.zip): SKILL.md con la guía, los tokens y los logos
- [Historial de versiones]({SITE}/CAMBIOS.md)

## Archivos

- [Plantillas]({SITE}/#plantillas): cartas, presentación, carteles, examen, Secretaría y firmas de correo (catálogo en {SITE}/plantillas/plantillas.js)
- [Kit de marca]({SITE}/descargas/tajamar-kit-de-marca.zip): logos en SVG y PNG de 2000 px
- [Paleta]({SITE}/descargas/tajamar-paleta.csv): CSV con separador ;
- Logos sueltos: {SITE}/logos/svg/<nombre>.svg y {SITE}/logos/png/<nombre>.png
""", encoding="utf-8", newline="\n")

# --- Archivo de la versión (inmutable) y version.json
ARCH = ["tajamar-marca.md", "tajamar-tokens.json", "tajamar-marca-skill.zip"]
dest = D / "archivo" / VERSION
if dest.exists():
    cambiados = [n for n in ARCH if not (dest / n).exists() or sha(dest / n) != sha(D / n)]
    if cambiados:
        sys.exit(f"La versión {VERSION} ya está archivada y estos archivos han cambiado: {', '.join(cambiados)}.\n"
                 f"Añade una versión nueva arriba en CAMBIOS.md y vuelve a ejecutar.")
else:
    dest.mkdir(parents=True)
    for n in ARCH:
        shutil.copy2(D / n, dest / n)

info = {
    "version": VERSION,
    "fecha": FECHA,
    "aviso": "Usa siempre esta versión. Si tu copia es anterior, descarga la vigente.",
    "guia": f"{SITE}/descargas/tajamar-marca.md",
    "historial": f"{SITE}/CAMBIOS.md",
    "archivo": f"{SITE}/descargas/archivo/{VERSION}/",
    "archivos": {n: {"url": f"{SITE}/descargas/{n}", "sha256": sha(D / n), "bytes": (D / n).stat().st_size} for n in ARCH},
}
(D / "version.json").write_text(json.dumps(info, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")

# --- Pie de página de la web
idx = ROOT / "index.html"
html = idx.read_text(encoding="utf-8")
pie = f'<!--version--><span class="ver">Versión {VERSION} · {FECHA_LARGA} · <a href="CAMBIOS.md">historial</a></span><!--/version-->'
if "<!--version-->" in html:
    html = re.sub(r"<!--version-->.*?<!--/version-->", pie, html, flags=re.S)
else:
    a = '<span>Dudas sobre la marca: Dirección y Departamento de Comunicación de Tajamar.</span>'
    assert a in html, "no encuentro el pie de página"
    html = html.replace(a, a + "\n    " + pie, 1)
idx.write_text(html, encoding="utf-8", newline="")

print(f"OK · versión {VERSION} ({FECHA})")
