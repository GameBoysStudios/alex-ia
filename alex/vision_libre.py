# -*- coding: utf-8 -*-
"""
Vision gratuita para Alex Pro (sin Google de pago).

1) Pillow local (colores, escena) — siempre
2) Captioning opcional con Hugging Face Inference API (gratis):
   modelo BLIP: Salesforce/blip-image-captioning-base

Token opcional (cuenta HF gratuita):
  HF_TOKEN=hf_xxx

Sin token a veces funciona con rate-limit; con token es mas estable.
"""

import base64
import io
import os

try:
    import requests
    REQUESTS_OK = True
except ImportError:
    REQUESTS_OK = False

HF_MODEL = os.environ.get(
    "HF_CAPTION_MODEL",
    "Salesforce/blip-image-captioning-base",
)
HF_URL = f"https://api-inference.huggingface.co/models/{HF_MODEL}"


class VisionLibre:
    def __init__(self, timeout: int = 40):
        self.timeout = timeout
        self.token = (os.environ.get("HF_TOKEN") or os.environ.get("HUGGINGFACE_TOKEN") or "").strip()
        self.disponible = REQUESTS_OK
        self.motor = "huggingface_blip" if self.disponible else "none"

    def _headers(self) -> dict:
        h = {"Content-Type": "application/octet-stream"}
        if self.token:
            h["Authorization"] = f"Bearer {self.token}"
        return h

    def caption_bytes(self, data: bytes, idioma: str = "es") -> dict:
        if not self.disponible or not data:
            return {"ok": False, "error": "no_disponible"}
        if len(data) > 8 * 1024 * 1024:
            return {"ok": False, "error": "demasiado_grande"}

        try:
            r = requests.post(
                HF_URL,
                headers=self._headers(),
                data=data,
                timeout=self.timeout,
            )
            if r.status_code == 503:
                # modelo cargando
                return {
                    "ok": False,
                    "error": "modelo_cargando",
                    "descripcion": (
                        "El modelo de vision gratuita se esta despertando. "
                        "Espera 20-30 s y vuelve a enviar la imagen."
                        if idioma != "en"
                        else "Free vision model is loading. Wait 20-30s and retry."
                    ),
                }
            if r.status_code == 401:
                return {
                    "ok": False,
                    "error": "token",
                    "descripcion": (
                        "Hugging Face pide token. Crea uno gratis en huggingface.co "
                        "y pon HF_TOKEN en Render."
                        if idioma != "en"
                        else "HF token required. Set HF_TOKEN on Render."
                    ),
                }
            if r.status_code != 200:
                return {
                    "ok": False,
                    "error": f"http_{r.status_code}",
                    "descripcion": r.text[:240],
                }

            data_json = r.json()
            # formato tipico: [{"generated_text": "a photo of..."}]
            texto = ""
            if isinstance(data_json, list) and data_json:
                texto = data_json[0].get("generated_text") or data_json[0].get("caption") or ""
            elif isinstance(data_json, dict):
                texto = data_json.get("generated_text") or data_json.get("caption") or ""
                if data_json.get("error"):
                    return {"ok": False, "error": str(data_json["error"]), "descripcion": str(data_json["error"])}

            texto = (texto or "").strip()
            if not texto:
                return {"ok": False, "error": "sin_caption"}

            if idioma == "en":
                desc = f"Free vision caption (BLIP): {texto}"
            else:
                desc = f"Descripcion (vision gratuita BLIP): {texto}"

            return {
                "ok": True,
                "motor": "huggingface_blip",
                "caption": texto,
                "descripcion": desc,
            }
        except Exception as e:
            return {"ok": False, "error": str(e), "descripcion": str(e)}

    def caption_base64(self, b64: str, idioma: str = "es") -> dict:
        if not b64:
            return {"ok": False, "error": "vacio"}
        if "," in b64 and b64.strip().startswith("data:"):
            b64 = b64.split(",", 1)[1]
        try:
            raw = base64.b64decode(b64)
        except Exception as e:
            return {"ok": False, "error": str(e)}
        return self.caption_bytes(raw, idioma=idioma)

    def render_pdf_pagina(self, data: bytes, pagina: int = 0, escala: float = 1.5):
        """Renderiza una pagina de PDF a PNG bytes (pypdfium2, gratis)."""
        try:
            import pypdfium2 as pdfium
        except ImportError:
            return None
        try:
            doc = pdfium.PdfDocument(data)
            if pagina < 0 or pagina >= len(doc):
                pagina = 0
            page = doc[pagina]
            pil = page.render(scale=escala).to_pil()
            buf = io.BytesIO()
            pil.convert("RGB").save(buf, format="PNG")
            return buf.getvalue()
        except Exception as e:
            print(f"[Alex] render PDF fallo: {e}")
            return None
