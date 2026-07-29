# -*- coding: utf-8 -*-
"""
Google Cloud Vision API — alternativa oficial a "Google Lens".

Lens no tiene API publica gratuita. Vision ofrece:
  - LABEL_DETECTION (que hay en la foto)
  - OBJECT_LOCALIZATION
  - TEXT_DETECTION / DOCUMENT_TEXT_DETECTION (OCR)
  - LANDMARK / LOGO
  - WEB_DETECTION (paginas similares)
  - PDF via files:annotate

Clave (Render env):
  GOOGLE_VISION_API_KEY=...
  o reutiliza GOOGLE_MAPS_API_KEY si el proyecto tiene Vision habilitado.
"""

import base64
import os

try:
    import requests
    REQUESTS_OK = True
except ImportError:
    REQUESTS_OK = False


def _api_key() -> str:
    return (
        os.environ.get("GOOGLE_VISION_API_KEY")
        or os.environ.get("GOOGLE_MAPS_API_KEY")
        or os.environ.get("GOOGLE_PLACES_API_KEY")
        or ""
    ).strip()


class GoogleVision:
    def __init__(self, timeout: int = 25):
        self.timeout = timeout
        self.key = _api_key()
        self.disponible = bool(self.key) and REQUESTS_OK

    def analizar_imagen_bytes(self, data: bytes, idioma: str = "es") -> dict:
        if not self.disponible:
            return {"ok": False, "error": "sin_clave", "descripcion": ""}
        if not data:
            return {"ok": False, "error": "vacio", "descripcion": ""}
        if len(data) > 15 * 1024 * 1024:
            return {"ok": False, "error": "demasiado_grande", "descripcion": "Imagen > 15 MB."}

        b64 = base64.b64encode(data).decode("ascii")
        body = {
            "requests": [{
                "image": {"content": b64},
                "features": [
                    {"type": "LABEL_DETECTION", "maxResults": 12},
                    {"type": "OBJECT_LOCALIZATION", "maxResults": 10},
                    {"type": "TEXT_DETECTION", "maxResults": 5},
                    {"type": "LANDMARK_DETECTION", "maxResults": 5},
                    {"type": "LOGO_DETECTION", "maxResults": 5},
                    {"type": "WEB_DETECTION", "maxResults": 5},
                ],
                "imageContext": {
                    "languageHints": ["es", "en"] if idioma == "es" else ["en", "es"],
                },
            }]
        }
        try:
            url = f"https://vision.googleapis.com/v1/images:annotate?key={self.key}"
            r = requests.post(url, json=body, timeout=self.timeout)
            data_json = r.json() if r.content else {}
            if r.status_code != 200:
                err = data_json.get("error", {})
                msg = err.get("message") or r.text[:200]
                return {
                    "ok": False,
                    "error": f"http_{r.status_code}",
                    "descripcion": f"Google Vision error: {msg}",
                }
            responses = data_json.get("responses") or [{}]
            resp = responses[0] if responses else {}
            if resp.get("error"):
                return {
                    "ok": False,
                    "error": "api",
                    "descripcion": f"Google Vision: {resp['error'].get('message', resp['error'])}",
                }
            return self._formatear_imagen(resp, idioma=idioma)
        except Exception as e:
            return {"ok": False, "error": str(e), "descripcion": f"Vision fallo: {e}"}

    def analizar_imagen_base64(self, b64: str, idioma: str = "es") -> dict:
        if not b64:
            return {"ok": False, "descripcion": "Sin imagen."}
        if "," in b64 and b64.strip().startswith("data:"):
            b64 = b64.split(",", 1)[1]
        try:
            raw = base64.b64decode(b64)
        except Exception as e:
            return {"ok": False, "descripcion": f"Base64 invalido: {e}"}
        return self.analizar_imagen_bytes(raw, idioma=idioma)

    def ocr_pdf_bytes(self, data: bytes, idioma: str = "es", max_paginas: int = 5) -> dict:
        """OCR de PDF con files:annotate (DOCUMENT_TEXT_DETECTION)."""
        if not self.disponible:
            return {"ok": False, "error": "sin_clave"}
        if not data or len(data) > 20 * 1024 * 1024:
            return {"ok": False, "error": "tamano"}

        b64 = base64.b64encode(data).decode("ascii")
        pages = list(range(1, max_paginas + 1))
        body = {
            "requests": [{
                "inputConfig": {
                    "content": b64,
                    "mimeType": "application/pdf",
                },
                "features": [{"type": "DOCUMENT_TEXT_DETECTION"}],
                "pages": pages,
            }]
        }
        try:
            url = f"https://vision.googleapis.com/v1/files:annotate?key={self.key}"
            r = requests.post(url, json=body, timeout=max(self.timeout, 45))
            data_json = r.json() if r.content else {}
            if r.status_code != 200:
                err = data_json.get("error", {})
                msg = err.get("message") or r.text[:300]
                return {"ok": False, "error": f"http_{r.status_code}", "descripcion": msg}

            # Estructura: responses[0].responses[] con fullTextAnnotation
            outer = (data_json.get("responses") or [{}])[0]
            if outer.get("error"):
                return {
                    "ok": False,
                    "error": "api",
                    "descripcion": str(outer["error"].get("message", outer["error"])),
                }
            textos = []
            for page_resp in outer.get("responses") or []:
                full = page_resp.get("fullTextAnnotation") or {}
                t = (full.get("text") or "").strip()
                if t:
                    textos.append(t)
                else:
                    anns = page_resp.get("textAnnotations") or []
                    if anns:
                        t0 = (anns[0].get("description") or "").strip()
                        if t0:
                            textos.append(t0)
            texto = "\n\n".join(textos).strip()
            return {
                "ok": True,
                "texto": texto,
                "paginas_ocr": len(textos),
                "motor": "google_vision",
            }
        except Exception as e:
            return {"ok": False, "error": str(e), "descripcion": str(e)}

    def _formatear_imagen(self, resp: dict, idioma: str = "es") -> dict:
        labels = []
        for lab in resp.get("labelAnnotations") or []:
            desc = lab.get("description") or ""
            score = lab.get("score") or 0
            if desc:
                labels.append({"nombre": desc, "score": round(float(score), 3)})

        objetos = []
        for obj in resp.get("localizedObjectAnnotations") or []:
            name = obj.get("name") or ""
            score = obj.get("score") or 0
            if name:
                objetos.append({"nombre": name, "score": round(float(score), 3)})

        landmarks = []
        for lm in resp.get("landmarkAnnotations") or []:
            if lm.get("description"):
                landmarks.append(lm["description"])

        logos = []
        for lg in resp.get("logoAnnotations") or []:
            if lg.get("description"):
                logos.append(lg["description"])

        texto = ""
        anns = resp.get("textAnnotations") or []
        if anns:
            texto = (anns[0].get("description") or "").strip()
        full = resp.get("fullTextAnnotation") or {}
        if full.get("text"):
            texto = full["text"].strip()

        web = resp.get("webDetection") or {}
        web_ents = [e.get("description") for e in (web.get("webEntities") or []) if e.get("description")]
        best_guess = [g.get("label") for g in (web.get("bestGuessLabels") or []) if g.get("label")]

        # Descripcion en lenguaje natural
        if idioma == "en":
            partes = ["Google Vision analysis (Lens-like):"]
            if best_guess:
                partes.append("Best guess: " + ", ".join(best_guess[:3]) + ".")
            if labels:
                top = ", ".join(f"{x['nombre']} ({int(x['score']*100)}%)" for x in labels[:8])
                partes.append("Labels: " + top + ".")
            if objetos:
                partes.append("Objects: " + ", ".join(x["nombre"] for x in objetos[:8]) + ".")
            if landmarks:
                partes.append("Landmarks: " + ", ".join(landmarks[:5]) + ".")
            if logos:
                partes.append("Logos: " + ", ".join(logos[:5]) + ".")
            if texto:
                tshort = texto if len(texto) < 400 else texto[:397] + "..."
                partes.append("Text found (OCR):\n" + tshort)
            if web_ents:
                partes.append("Related: " + ", ".join(web_ents[:6]) + ".")
            if len(partes) == 1:
                partes.append("No strong signals detected.")
        else:
            partes = ["Analisis con Google Vision (estilo Lens):"]
            if best_guess:
                partes.append("Parece: " + ", ".join(best_guess[:3]) + ".")
            if labels:
                top = ", ".join(f"{x['nombre']} ({int(x['score']*100)}%)" for x in labels[:8])
                partes.append("Etiquetas: " + top + ".")
            if objetos:
                partes.append("Objetos: " + ", ".join(x["nombre"] for x in objetos[:8]) + ".")
            if landmarks:
                partes.append("Lugares / monumentos: " + ", ".join(landmarks[:5]) + ".")
            if logos:
                partes.append("Logos: " + ", ".join(logos[:5]) + ".")
            if texto:
                tshort = texto if len(texto) < 400 else texto[:397] + "..."
                partes.append("Texto detectado (OCR):\n" + tshort)
            if web_ents:
                partes.append("Relacionado en la web: " + ", ".join(web_ents[:6]) + ".")
            if len(partes) == 1:
                partes.append("No detecte senales claras.")

        return {
            "ok": True,
            "motor": "google_vision",
            "labels": labels,
            "objetos": objetos,
            "landmarks": landmarks,
            "logos": logos,
            "texto_ocr": texto[:2000] if texto else "",
            "best_guess": best_guess,
            "web_entities": web_ents[:10],
            "descripcion": "\n".join(partes),
        }
