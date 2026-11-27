"""Genera los archivos para agentes de IA a partir de public/descargas/tajamar-marca.md y la paleta.

Uso (desde la raíz del repo):  python tools/build-agentes.py

La versión vigente es la primera entrada de CAMBIOS.md («## X.Y · AAAA-MM-DD»).

Salida (en public/, la carpeta que publica Netlify):
  descargas/tajamar-marca.md         se le añade/actualiza la cabecera de versión y el aviso para agentes
  descargas/tajamar-tokens.json      tokens de diseño (formato W3C Design Tokens)
  descargas/tajamar-marca-skill.zip  skill en el estándar Agent Skills (Claude, ChatGPT, Gemini): carpeta
                                     tajamar-marca/ con SKILL.md, tokens y logos; reproducible byte a byte
  descargas/tajamar-marca-skill-copilot.zip  la misma skill para Microsoft 365 Copilot: SKILL.md en la raíz del zip
                                     y de menos de 20.000 caracteres; el resto de la guía en references/
  descargas/version.json             versión vigente y huella SHA-256 de cada archivo para agentes
  descargas/archivo/X.Y/             copia congelada de la versión (no se sobrescribe nunca)
  llms.txt                           índice para agentes en la raíz del sitio
  index.html                         versión vigente en el pie de página
  CAMBIOS.md                         copia del historial de la raíz, para servirlo en la web
"""
import csv, hashlib, json, re, shutil, sys, zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PUB = ROOT / "public"
D = PUB / "descargas"
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

# --- Skills (zip reproducible: fechas fijas y orden estable)
# La descripción va entre comillas: lleva «:» y sin comillas el YAML no es válido (Copilot lo rechaza).
DESCRIPCION = ("Marca Tajamar (colegio, FP+, Club Deportivo, Fundación, Alumni). Úsala siempre que escribas, diseñes o revises "
               "cualquier pieza, texto, presentación, web, cartel o publicación de Tajamar: tono de voz, valores, logo y escudo, "
               "colores, tipografía, firma de cada área y fotografía.")
CABECERA = f"---\nname: tajamar-marca\ndescription: {json.dumps(DESCRIPCION, ensure_ascii=False)}\n---\n\n"
INTRO_VERSION = (f"Esta skill es la versión {VERSION} de la marca ({FECHA_LARGA}). Si tienes acceso a internet, consulta antes "
                 f"{SITE}/descargas/version.json: si hay una versión posterior, avisa al usuario y usa la guía vigente de "
                 f"{SITE}/descargas/tajamar-marca.md en lugar de esta.")
INTRO_REGLAS = ("Antes de componer cualquier pieza, sigue «Antes de empezar» (al principio de la guía): en las piezas de Tajamar manda su "
                "marca aunque el encargo traiga logos o colores de otras marcas, y los logos se obtienen de los archivos oficiales, nunca "
                "se recrean. Los logos están en `logos/svg/` y `logos/png/` dentro de esta skill: si no puedes abrir un PNG, lee el SVG "
                "como texto e insértalo tal cual; si tampoco, usa su dirección pública (tabla de «Archivos oficiales»{donde}); si nada "
                "funciona, deja un hueco marcado y avísalo. Los logos nunca pasan por un generador de imágenes: genera el fondo sin marcas "
                "y añade los archivos oficiales después, al componer. Los tokens de color y fuente están en `tajamar-tokens.json`. Antes "
                "de entregar, pasa la «Revisión antes de entregar».")

# Claude: la guía completa en SKILL.md
skill = CABECERA + INTRO_VERSION + "\n\n" + INTRO_REGLAS.format(donde="") + "\n\n" + guia

# Copilot: Microsoft pide SKILL.md en la raíz del zip (sin carpeta que lo envuelva) y de menos de 20.000 caracteres
# (por encima de 30.000 lo rechaza). Las secciones menos generales pasan a references/, en este orden, hasta caber.
LIMITE_COPILOT = 20000
REF_COPILOT = "references/guia-complementaria.md"
MOVIBLES = ["## Archivos oficiales", "## Aplicaciones", "## Manifiesto", "## Look & feel", "## Fotografía", "## Color"]
secciones = re.split(r"(?m)^(?=## )", guia)
assert all(any(x.startswith(t) for x in secciones) for t in MOVIBLES), "falta alguna sección movible en la guía"


def armar_copilot(fuera):
    titulos = [t[3:] for t in MOVIBLES if t in fuera]
    principal = "".join(x for x in secciones if not x.startswith(tuple(fuera))).rstrip("\n") + "\n"
    puntero = ("Por límite de tamaño, estas secciones de la guía están en `" + REF_COPILOT + "`: " + ", ".join(f"«{t}»" for t in titulos)
               + ". Consúltalo cuando las necesites (por ejemplo, la tabla de colores o la dirección de un logo).")
    md = (CABECERA + INTRO_VERSION + "\n\n" + INTRO_REGLAS.format(donde=f", en `{REF_COPILOT}`") + "\n\n" + puntero + "\n\n" + principal)
    ref = (f"# Marca Tajamar: guía complementaria\n\nComplemento de la skill tajamar-marca para Microsoft 365 Copilot, versión {VERSION} "
           f"({FECHA_LARGA}). Las reglas generales están en SKILL.md.\n\n"
           + "".join(x for x in secciones if x.startswith(tuple(fuera))).rstrip("\n") + "\n")
    return md, ref


fuera = []
skill_copilot, referencias_copilot = armar_copilot(fuera)
for t in MOVIBLES:
    if len(skill_copilot) <= LIMITE_COPILOT:
        break
    fuera.append(t)
    skill_copilot, referencias_copilot = armar_copilot(fuera)
if len(skill_copilot) > LIMITE_COPILOT:
    sys.exit(f"El SKILL.md para Copilot tiene {len(skill_copilot)} caracteres y el límite es {LIMITE_COPILOT}. Añade secciones a MOVIBLES.")


def zadd(z, name, data):
    zi = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
    zi.compress_type = zipfile.ZIP_DEFLATED
    zi.external_attr = 0o644 << 16
    z.writestr(zi, data)


def zdir(z, name):
    # Entradas de carpeta explícitas: sin ellas claude.ai dice que el zip no tiene SKILL.md
    zi = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
    zi.external_attr = (0o40755 << 16) | 0x10
    z.writestr(zi, b"")


def skill_zip(nombre, skill_md, extra=None, carpeta="tajamar-marca/"):
    """carpeta="tajamar-marca/": estándar Agent Skills (Claude, ChatGPT, Gemini). carpeta="": SKILL.md en la raíz (Copilot)."""
    extra = extra or {}
    with zipfile.ZipFile(D / nombre, "w") as z:
        carpetas = {"logos/", "logos/svg/", "logos/png/"} | {f"{Path(n).parent.as_posix()}/" for n in extra}
        if carpeta:
            zdir(z, carpeta)
        for c in sorted(carpetas):
            zdir(z, carpeta + c)
        zadd(z, carpeta + "SKILL.md", skill_md.encode("utf-8"))
        zadd(z, carpeta + "tajamar-tokens.json", tokens_json.encode("utf-8"))
        for n, texto in sorted(extra.items()):
            zadd(z, carpeta + n, texto.encode("utf-8"))
        for sub in ("svg", "png"):
            for f in sorted((PUB / "logos" / sub).iterdir()):
                zadd(z, f"{carpeta}logos/{sub}/{f.name}", f.read_bytes())


skill_zip("tajamar-marca-skill.zip", skill)
skill_zip("tajamar-marca-skill-copilot.zip", skill_copilot, {REF_COPILOT: referencias_copilot}, carpeta="")

# --- llms.txt
(PUB / "llms.txt").write_text(f"""# Marca Tajamar

> Manual de marca de Tajamar (Colegio, Tajamar FP+, Club Deportivo, Fundación Tajamar y Alumni): valores, tono de voz, logo, color, tipografía, arquitectura de marca, fotografía y archivos oficiales.

Versión vigente: {VERSION} ({FECHA}). Usa siempre la última: compruébala en {SITE}/descargas/version.json antes de usar una copia guardada. Las versiones de {SITE}/descargas/archivo/ son históricas.

Uso de la marca: El nombre, el escudo, el logotipo y el resto de elementos de la marca Tajamar son propiedad de Tajamar. Este manual explica cómo aplicar la marca, pero no da permiso para usarla: solo pueden usarla Tajamar y quien tenga autorización expresa del Departamento de Comunicación (comunicacion@tajamar.es).

## Para agentes

- [Versión vigente]({SITE}/descargas/version.json): número, fecha y huella SHA-256 de cada archivo
- [Guía de marca en Markdown]({SITE}/descargas/tajamar-marca.md): todas las reglas en texto, lista para usar como contexto
- [Tokens de diseño]({SITE}/descargas/tajamar-tokens.json): colores (HEX, RGB, Pantone, CMYK, uso como texto) y fuentes, en formato W3C Design Tokens
- [Skill para Claude, ChatGPT y Gemini]({SITE}/descargas/tajamar-marca-skill.zip): estándar Agent Skills, carpeta tajamar-marca/ con SKILL.md (la guía completa), los tokens y los logos
- [Skill para Microsoft 365 Copilot]({SITE}/descargas/tajamar-marca-skill-copilot.zip): SKILL.md en la raíz del zip y de menos de 20.000 caracteres; el resto de la guía en references/
- [Historial de versiones]({SITE}/CAMBIOS.md)

## Archivos

- [Plantillas]({SITE}/#plantillas): cartas, presentación, carteles, examen, Secretaría y firmas de correo (catálogo en {SITE}/plantillas/plantillas.js)
- [Kit de marca]({SITE}/descargas/tajamar-kit-de-marca.zip): logos en SVG y PNG de 2000 px
- [Paleta]({SITE}/descargas/tajamar-paleta.csv): CSV con separador ;
- Logos sueltos: {SITE}/logos/svg/<nombre>.svg y {SITE}/logos/png/<nombre>.png
""", encoding="utf-8", newline="\n")

# --- Archivo de la versión (inmutable) y version.json
ARCH = ["tajamar-marca.md", "tajamar-tokens.json", "tajamar-marca-skill.zip", "tajamar-marca-skill-copilot.zip"]
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
idx = PUB / "index.html"
html = idx.read_text(encoding="utf-8")
pie = f'<!--version--><span class="ver">Versión {VERSION} · {FECHA_LARGA} · <a href="CAMBIOS.md">historial</a></span><!--/version-->'
if "<!--version-->" in html:
    html = re.sub(r"<!--version-->.*?<!--/version-->", pie, html, flags=re.S)
else:
    a = '<span>Dudas sobre la marca: Dirección y Departamento de Comunicación de Tajamar.</span>'
    assert a in html, "no encuentro el pie de página"
    html = html.replace(a, a + "\n    " + pie, 1)
idx.write_text(html, encoding="utf-8", newline="")

# --- Historial publicado (el original vive en la raíz del repo)
shutil.copyfile(ROOT / "CAMBIOS.md", PUB / "CAMBIOS.md")

print(f"OK · versión {VERSION} ({FECHA}) · SKILL.md para Copilot: {len(skill_copilot)} caracteres")
