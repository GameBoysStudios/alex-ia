# -*- coding: utf-8 -*-
"""Analisis de PDF: texto pypdf + resumen extractivo."""

import base64
import io
import re
from collections import Counter

try:
    from pypdf import PdfReader
    PYPDF_OK = True
except ImportError:
    try:
        from PyPDF2 import PdfReader  # type: ignore
        PYPDF_OK = True
    except ImportError:
        PYPDF_OK = False

try:
    import pdfplumber
    PLUMBER_OK = True
except ImportError:
    PLUMBER_OK = False

STOP = {
    "de", "la", "que", "el", "en", "y", "a", "los", "del", "se", "las", "por",
    "un", "para", "con", "no", "una", "su", "al", "lo", "como", "mas", "pero",
    "sus", "le", "ya", "o", "este", "si", "porque", "esta", "entre", "cuando",
    "muy", "sin", "sobre", "tambien", "me", "hasta", "hay", "donde", "quien",
    "desde", "todo", "nos", "durante", "todos", "uno", "les", "ni", "contra",
    "the", "of", "and", "to", "in", "is", "for", "on", "with", "as", "at",
    "by", "an", "be", "this", "that", "from", "or", "are", "was", "were",
    "not", "have", "has", "had", "it", "its", "you", "your", "we", "our",
}


def _tokens(texto: str) -> list:
    return re.findall(r"[a-záéíóúñüA-ZÁÉÍÓÚÑÜ]{3,}", (texto or "").lower())


def _frases(texto: str) -> list:
    partes = re.split(r"(?<=[\.\!\?\n])\s+", texto.strip())
    out = []
    for p in partes:
        p = re.sub(r"\s+", " ", p).strip()
        if len(p) < 40 or len(p) > 400:
            continue
        if p.count(" ") < 5:
            continue
        out.append(p)
    return out


def _resumen_extractivo(texto: str, max_frases: int = 5) -> list:
    frases = _frases(texto)
    if not frases:
        bloques = [b.strip() for b in re.split(r"\n{2,}", texto) if len(b.strip()) > 60]
        return bloques[:max_frases]

    freq = Counter(t for t in _tokens(texto) if t not in STOP)
    if not freq:
        return frases[:max_frases]

    puntuadas = []
    for i, f in enumerate(frases):
        toks = [t for t in _tokens(f) if t not in STOP]
        if not toks:
            continue
        score = sum(freq.get(t, 0) for t in toks) / len(toks)
        score += max(0, 0.15 - i * 0.01)
        puntuadas.append((score, i, f))

    puntuadas.sort(key=lambda x: (-x[0], x[1]))
    elegidas = sorted(puntuadas[:max_frases], key=lambda x: x[1])
    return [f for _, _, f in elegidas]


def _palabras_clave(texto: str, n: int = 12) -> list:
    freq = Counter(t for t in _tokens(texto) if t not in STOP and len(t) > 3)
    return [w for w, _ in freq.most_common(n)]


def _meta_seguro(info) -> dict:
    if not info:
        return {}
    titulo = autor = ""
    try:
        titulo = str(getattr(info, "title", None) or "") or ""
    except Exception:
        pass
    try:
        autor = str(getattr(info, "author", None) or "") or ""
    except Exception:
        pass
    if not titulo and isinstance(info, dict):
        titulo = str(info.get("/Title") or info.get("title") or "")
    if not autor and isinstance(info, dict):
        autor = str(info.get("/Author") or info.get("author") or "")
    return {"titulo": titulo.strip(), "autor": autor.strip()}


class AnalizadorPDF:
    def __init__(self):
        self.disponible = PYPDF_OK or PLUMBER_OK

    def analizar_bytes(self, data: bytes, idioma: str = "es", max_paginas: int = 30) -> dict:
        if not self.disponible:
            return {
                "ok": False,
                "error": "pypdf no instalado",
                "descripcion": (
                    "No puedo leer PDFs: falta pypdf en el servidor. "
                    "Redeploy en Render tras añadir pypdf a requirements.txt."
                ),
            }
        if not data:
            return {"ok": False, "descripcion": "PDF vacio."}
        if len(data) > 8 * 1024 * 1024:
            return {"ok": False, "descripcion": "PDF demasiado grande (max 8 MB)."}
        # Magic number check
        if not data[:5].startswith(b"%PDF"):
            return {
                "ok": False,
                "descripcion": (
                    "El archivo no parece un PDF valido (no empieza por %PDF). "
                    "Prueba otro archivo o exporta de nuevo a PDF."
                ),
            }

        meta = {}
        paginas_txt = []
        n_pag = 0
        errores = []

        if PLUMBER_OK:
            try:
                with pdfplumber.open(io.BytesIO(data)) as doc:
                    n_pag = len(doc.pages)
                    for pg in doc.pages[:max_paginas]:
                        try:
                            t = pg.extract_text() or ""
                        except Exception:
                            t = ""
                        if t.strip():
                            paginas_txt.append(t.strip())
            except Exception as e:
                errores.append(f"pdfplumber: {e}")
                print(f"[Alex] pdfplumber fallo: {e}")

        if not paginas_txt and PYPDF_OK:
            try:
                reader = PdfReader(io.BytesIO(data))
                n_pag = len(reader.pages)
                meta = _meta_seguro(getattr(reader, "metadata", None))
                if getattr(reader, "is_encrypted", False):
                    try:
                        reader.decrypt("")
                    except Exception:
                        return {
                            "ok": False,
                            "descripcion": "El PDF esta protegido con contraseña; no puedo leerlo.",
                        }
                for page in reader.pages[:max_paginas]:
                    try:
                        t = page.extract_text() or ""
                    except Exception:
                        t = ""
                    if t.strip():
                        paginas_txt.append(t.strip())
            except Exception as e:
                errores.append(str(e))
                return {
                    "ok": False,
                    "error": str(e),
                    "descripcion": f"No pude abrir el PDF: {e}",
                }

        texto = "\n\n".join(paginas_txt).strip()
        if not texto:
            nota_err = ("; ".join(errores) if errores else "")
            if idioma == "en":
                desc = (
                    f"PDF opened ({n_pag} pages) but no extractable text. "
                    f"It may be a scan (images only). "
                    + (f"({nota_err})" if nota_err else "")
                )
            else:
                desc = (
                    f"He abierto el PDF ({n_pag} paginas) pero no hay texto extraible. "
                    f"Puede ser un escaneo (solo imagenes). "
                    f"Con Google Vision API puedo intentar OCR. "
                    + (f"Detalle: {nota_err}" if nota_err else "")
                )
            return {
                "ok": True,
                "paginas": n_pag,
                "caracteres": 0,
                "texto_vacio": True,
                "meta": meta,
                "descripcion": desc,
                "resumen": "",
                "puntos": [],
                "palabras_clave": [],
            }

        resumen_frases = _resumen_extractivo(texto, max_frases=5)
        claves = _palabras_clave(texto, n=12)
        puntos = resumen_frases[:5]
        resumen = " ".join(resumen_frases[:3])
        if len(resumen) > 900:
            resumen = resumen[:897] + "..."

        chars = len(texto)
        palabras = len(texto.split())

        if idioma == "en":
            lineas = [f"PDF analysis ({n_pag} pages, ~{palabras} words):"]
            if meta.get("titulo"):
                lineas.append(f"Title: {meta['titulo']}")
            if meta.get("autor"):
                lineas.append(f"Author: {meta['autor']}")
            lineas.append(f"Summary: {resumen}" if resumen else "Summary: (insufficient text)")
            if puntos:
                lineas.append("Key points:")
                for i, p in enumerate(puntos, 1):
                    lineas.append(f"{i}. {p}")
            if claves:
                lineas.append("Keywords: " + ", ".join(claves[:10]))
        else:
            lineas = [f"Analisis del PDF ({n_pag} paginas, ~{palabras} palabras):"]
            if meta.get("titulo"):
                lineas.append(f"Titulo: {meta['titulo']}")
            if meta.get("autor"):
                lineas.append(f"Autor: {meta['autor']}")
            lineas.append(f"Resumen: {resumen}" if resumen else "Resumen: (texto insuficiente)")
            if puntos:
                lineas.append("Puntos clave:")
                for i, p in enumerate(puntos, 1):
                    lineas.append(f"{i}. {p}")
            if claves:
                lineas.append("Palabras clave: " + ", ".join(claves[:10]))

        return {
            "ok": True,
            "paginas": n_pag,
            "paginas_leidas": min(n_pag, max_paginas) if n_pag else 0,
            "caracteres": chars,
            "palabras": palabras,
            "meta": meta,
            "resumen": resumen,
            "puntos": puntos,
            "palabras_clave": claves,
            "texto_preview": texto[:1500],
            "descripcion": "\n".join(lineas),
        }

    def analizar_base64(self, b64: str, idioma: str = "es") -> dict:
        if not b64:
            return {
                "ok": False,
                "descripcion": "No recibí datos de PDF (base64 vacio). Recarga y vuelve a elegir el archivo.",
            }
        if "," in b64 and b64.strip().startswith("data:"):
            b64 = b64.split(",", 1)[1]
        b64 = b64.strip().replace("\n", "").replace(" ", "")
        try:
            raw = base64.b64decode(b64, validate=False)
        except Exception as e:
            return {"ok": False, "descripcion": f"Base64 invalido: {e}"}
        if not raw:
            return {"ok": False, "descripcion": "PDF decodificado vacio."}
        return self.analizar_bytes(raw, idioma=idioma)
