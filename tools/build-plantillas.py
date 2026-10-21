"""Monta el repositorio de plantillas (public/plantillas/) a partir de la carpeta origen/.

Uso (desde la raíz del repo, en Windows con Office):  python tools/build-plantillas.py

- Copia cada archivo de la lista CATALOGO a public/plantillas/<categoría>/<slug>.<ext>.
- Genera una miniatura .jpg de la primera página (Word/PowerPoint exportan a PDF y PyMuPDF la rasteriza).
  Si la miniatura ya existe y el original no ha cambiado, no la regenera.
- Escribe public/plantillas/plantillas.js con el catálogo que pinta la web.

origen/ no se versiona (tipografías con licencia y documentos internos): pídelo a Comunicación.
"""
import json, os, shutil, subprocess, sys, tempfile
import pymupdf
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "origen")
OUT = os.path.join(ROOT, "public", "plantillas")
PS = os.path.join(ROOT, "tools", "office-a-pdf.ps1")
THUMB_W = 640

CATEGORIAS = [
    ("firmas", "Firma de correo", "Rellena tus datos, elige la imagen de tu área y copia la firma. Debajo tienes cómo añadirla en Gmail y en Outlook."),
    ("cartas", "Cartas", "Papel de carta en Word, una versión por etapa y área. Escribe sobre la plantilla: márgenes, escudo y pie ya están en su sitio."),
    ("presentaciones", "Presentaciones", "Plantilla de PowerPoint con portada, portadillas, índice e interiores."),
    ("carteles", "Carteles", "Carteles en Word sobre fondos de la gama oficial. Antes de imprimir, en Word: Archivo › Opciones › Mostrar › activa «Imprimir colores e imágenes de fondo»; si no, sale en blanco."),
    ("examenes", "Exámenes", "Modelo de examen en Word."),
    ("secretaria", "Secretaría", "Documentos de Secretaría en Word."),
    ("ejemplos", "Ejemplos aplicados", "Folletos reales hechos con la marca, como referencia. No son plantillas."),
]

# (origen relativo a origen/, categoría, slug, título, nota). El archivo de origen se llama como su slug.
CATALOGO = [
    *[(f"plantillas/cartas/{s}.docx", "cartas", s, t, n) for s, t, n in [
        ("carta-estandar", "Carta estándar", "Colegio Tajamar"),
        ("carta-infantil", "Carta Infantil", ""),
        ("carta-primaria", "Carta Primaria", ""),
        ("carta-secundaria", "Carta Secundaria", ""),
        ("carta-fp", "Carta FP + Professional Education", ""),
        ("carta-club-deportivo", "Carta Club Deportivo", ""),
        ("carta-ampa", "Carta AMPA", ""),
    ]],
    ("plantillas/presentaciones/presentacion-corporativa.pptx", "presentaciones", "presentacion-corporativa", "Presentación corporativa", ""),
    *[(f"plantillas/carteles/cartel-{i:02d}.docx", "carteles", f"cartel-{i:02d}", f"Cartel {i:02d}", "") for i in range(1, 18)],
    ("plantillas/carteles/cartel-aforo-banos.docx", "carteles", "cartel-aforo-banos", "Aforo máximo en los baños", "Ejemplo terminado"),
    ("plantillas/examenes/examen.docx", "examenes", "examen", "Modelo de examen", ""),
    ("plantillas/secretaria/secretaria.docx", "secretaria", "secretaria", "Hoja de Secretaría", "Con pie de contacto"),
    ("plantillas/secretaria/secretaria-2.docx", "secretaria", "secretaria-2", "Hoja de Secretaría, sin pie", ""),
    *[(f"firmas-correo/{s}.jpg", "firmas", s, t, "Imagen de firma") for s, t in [
        ("firma-alumni", "Alumni"),
        ("firma-bachillerato", "Bachillerato"),
        ("firma-club-deportivo", "Club Deportivo"),
        ("firma-fp", "FP + Professional Education"),
        ("firma-fundacion", "Fundación Tajamar"),
        ("firma-fundacion-sin-dibujo", "Fundación Tajamar, sin dibujo"),
        ("firma-infantil", "Infantil"),
        ("firma-primaria", "Primaria"),
        ("firma-secundaria", "Secundaria"),
        ("firma-secretaria", "Secretaría"),
    ]],
    *[(f"folletos/{s}.pdf", "ejemplos", s, t, "Folleto") for s, t in [
        ("folleto-programa-tajamar", "Programa Tajamar"),
        ("folleto-bachillerato", "Mucho más que un Bachillerato"),
        ("folleto-guia-normativa", "La guía normativa de Tajamar"),
        ("folleto-buenos-modales", "Buenos modales en el comedor"),
    ]],
]

# Datos personales que no se publican: se sustituyen al copiar (el original no se toca).
# Los folletos del COF no están en el catálogo porque llevan correos personales.
ANONIMIZAR = {}

FMT = {".docx": "Word", ".pptx": "PowerPoint", ".pdf": "PDF", ".jpg": "JPG", ".png": "PNG", ".psd": "Photoshop"}


def thumb_from_pdf(pdf, dest):
    d = pymupdf.open(pdf)
    p = d[0]
    z = THUMB_W / p.rect.width
    pix = p.get_pixmap(matrix=pymupdf.Matrix(z, z), alpha=False)
    Image.frombytes("RGB", (pix.width, pix.height), pix.samples).save(dest, quality=82, optimize=True)


def copiar_anonimizado(src, dst, reglas):
    import zipfile
    hechas = set()
    with zipfile.ZipFile(src) as zi, zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as zo:
        for it in zi.infolist():
            data = zi.read(it.filename)
            if it.filename.endswith((".xml", ".rels")):
                t = data.decode("utf-8")
                for a, b in reglas:
                    if a in t:
                        t = t.replace(a, b)
                        hechas.add(a)
                data = t.encode("utf-8")
            zo.writestr(it, data)
    falta = [a for a, _ in reglas if a not in hechas]
    if falta:
        raise SystemExit(f"No se pudo anonimizar {src}: {falta}")


def recortar_blanco(src, dst, margen=2):
    """Quita el margen blanco sobrante de las imágenes de firma (no toca el dibujo)."""
    from PIL import ImageOps
    im = Image.open(src).convert("RGB")
    bb = ImageOps.invert(im.convert("L")).point(lambda v: 255 if v > 12 else 0).getbbox()
    if bb:
        im = im.crop((max(bb[0] - margen, 0), max(bb[1] - margen, 0), min(bb[2] + margen, im.width), min(bb[3] + margen, im.height)))
    im.save(dst, quality=92)


def office_to_pdf(src, tmpdir):
    ext = os.path.splitext(src)[1].lower()
    tmp_in = os.path.join(tmpdir, "in" + ext)
    tmp_out = os.path.join(tmpdir, "out.pdf")
    shutil.copyfile(src, tmp_in)
    if os.path.exists(tmp_out):
        os.remove(tmp_out)
    try:
        subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", PS, "-In", tmp_in, "-Out", tmp_out],
                       capture_output=True, timeout=180)
    except subprocess.TimeoutExpired:
        for exe in ("WINWORD.EXE", "POWERPNT.EXE"):
            subprocess.run(["taskkill", "/F", "/IM", exe], capture_output=True)
    return tmp_out if os.path.exists(tmp_out) else None


def main():
    items = []
    with tempfile.TemporaryDirectory() as tmpdir:
        for rel, cat, slug, title, note in CATALOGO:
            src = os.path.join(SRC, rel)
            if not os.path.exists(src):
                print("FALTA", rel)
                continue
            ext = os.path.splitext(src)[1].lower()
            os.makedirs(os.path.join(OUT, cat), exist_ok=True)
            dst = os.path.join(OUT, cat, slug + ext)
            if slug in ANONIMIZAR:
                copiar_anonimizado(src, dst, ANONIMIZAR[slug])
            elif cat == "firmas" and ext == ".jpg":
                recortar_blanco(src, dst)
            else:
                shutil.copyfile(src, dst)
            thumb = os.path.join(OUT, cat, slug + ".thumb.jpg")
            if not os.path.exists(thumb) or os.path.getmtime(thumb) < os.path.getmtime(src):
                if ext in (".jpg", ".png"):
                    im = Image.open(src).convert("RGB")
                    im.thumbnail((THUMB_W, THUMB_W * 2))
                    im.save(thumb, quality=85, optimize=True)
                elif ext == ".pdf":
                    thumb_from_pdf(src, thumb)
                elif ext in (".docx", ".pptx"):
                    pdf = office_to_pdf(dst, tmpdir)
                    if pdf:
                        thumb_from_pdf(pdf, thumb)
                    else:
                        print("SIN MINIATURA", rel)
                print("ok", cat, slug)
            items.append({
                "cat": cat, "title": title, "note": note,
                "file": f"plantillas/{cat}/{slug}{ext}",
                "thumb": f"plantillas/{cat}/{slug}.thumb.jpg" if os.path.exists(thumb) else None,
                "fmt": FMT.get(ext, ext[1:].upper()),
                "kb": round(os.path.getsize(dst) / 1024),
                # Las imágenes de firma no se listan: las usa el generador de firmas.
                "asset": cat == "firmas",
            })
    data = {"categorias": [{"id": i, "h": h, "p": p} for i, h, p in CATEGORIAS], "items": items}
    with open(os.path.join(OUT, "plantillas.js"), "w", encoding="utf-8") as f:
        f.write("// Generado por tools/build-plantillas.py. No editar a mano.\nwindow.PLANTILLAS = ")
        json.dump(data, f, ensure_ascii=False, indent=1)
        f.write(";\n")
    print(len(items), "elementos")


if __name__ == "__main__":
    main()
