# -*- coding: utf-8 -*-
"""
Traductor para Alex 2.0.

1) Google Cloud Translation API v2 si existe GOOGLE_TRANSLATE_API_KEY
2) Fallback gratuito: MyMemory Translation API (sin clave, con limites)
"""

import os
import re
from urllib.parse import quote

try:
    import requests
    REQUESTS_OK = True
except ImportError:
    REQUESTS_OK = False

# Codigos ISO que usamos
IDIOMAS_OK = {"es", "en", "fr", "pt", "de", "it", "ca"}


class Traductor:
    def __init__(self):
        self.api_key = (
            os.environ.get("GOOGLE_TRANSLATE_API_KEY")
            or os.environ.get("GOOGLE_API_KEY")
            or ""
        ).strip()
        self.disponible = REQUESTS_OK
        self.motor = "google" if self.api_key else "mymemory"

    def traducir(self, texto: str, destino: str = "es", origen: str = "auto") -> dict:
        """
        Devuelve {texto, origen, destino, motor, ok}.
        """
        texto = (texto or "").strip()
        destino = (destino or "es").lower()[:5]
        origen = (origen or "auto").lower()[:5]
        if not texto:
            return {"texto": "", "origen": origen, "destino": destino, "motor": self.motor, "ok": False}
        if not self.disponible:
            return {
                "texto": texto,
                "origen": origen,
                "destino": destino,
                "motor": "none",
                "ok": False,
                "error": "requests no disponible",
            }

        if self.api_key:
            r = self._google(texto, destino, origen)
            if r.get("ok"):
                return r

        return self._mymemory(texto, destino, origen)

    def _google(self, texto: str, destino: str, origen: str) -> dict:
        try:
            url = "https://translation.googleapis.com/language/translate/v2"
            params = {"key": self.api_key, "q": texto, "target": destino, "format": "text"}
            if origen and origen != "auto":
                params["source"] = origen
            resp = requests.post(url, data=params, timeout=10)
            if resp.status_code != 200:
                return {"ok": False, "error": f"google {resp.status_code}", "texto": texto}
            data = resp.json()
            traducciones = (data.get("data") or {}).get("translations") or []
            if not traducciones:
                return {"ok": False, "error": "sin traducciones", "texto": texto}
            t = traducciones[0]
            return {
                "texto": t.get("translatedText") or texto,
                "origen": t.get("detectedSourceLanguage") or origen,
                "destino": destino,
                "motor": "google",
                "ok": True,
            }
        except Exception as e:
            return {"ok": False, "error": str(e), "texto": texto}

    def _mymemory(self, texto: str, destino: str, origen: str) -> dict:
        """Fallback gratuito (limite diario por IP)."""
        try:
            src = origen if origen and origen != "auto" else "autodetect"
            # MyMemory usa pares tipo es|en
            if src == "autodetect":
                # Heuristica simple: si hay caracteres tipicos ES, origen es
                if re.search(r"[ñáéíóúü¿¡]", texto.lower()):
                    src = "es"
                else:
                    src = "en"
            langpair = f"{src}|{destino}"
            url = (
                "https://api.mymemory.translated.net/get"
                f"?q={quote(texto[:450])}&langpair={quote(langpair)}"
            )
            resp = requests.get(url, timeout=10, headers={"User-Agent": "AlexLocalAI/2.0"})
            if resp.status_code != 200:
                return {"ok": False, "error": f"mymemory {resp.status_code}", "texto": texto}
            data = resp.json()
            translated = ((data.get("responseData") or {}).get("translatedText") or "").strip()
            if not translated or translated.lower() == texto.lower():
                return {"ok": False, "error": "sin cambio", "texto": texto, "motor": "mymemory"}
            return {
                "texto": translated,
                "origen": src,
                "destino": destino,
                "motor": "mymemory",
                "ok": True,
            }
        except Exception as e:
            return {"ok": False, "error": str(e), "texto": texto, "motor": "mymemory"}

    def alinear_idioma(self, respuesta: str, idioma_usuario: str) -> str:
        """
        Si la respuesta parece de otro idioma, intenta traducirla al del usuario.
        Conservadora: solo si hay senales claras.
        """
        if not respuesta or not idioma_usuario:
            return respuesta
        idioma_usuario = idioma_usuario.lower()[:2]
        low = respuesta.lower()

        # Si el usuario habla espanol y la respuesta parece ingles densa
        if idioma_usuario == "es":
            en_hits = len(re.findall(r"\b(the|and|is|are|with|from|this|that|have)\b", low))
            es_hits = len(re.findall(r"\b(el|la|de|que|en|los|las|una|por|para)\b", low))
            if en_hits >= 4 and en_hits > es_hits * 2:
                r = self.traducir(respuesta, destino="es", origen="en")
                if r.get("ok"):
                    return r["texto"]
        elif idioma_usuario == "en":
            es_hits = len(re.findall(r"\b(el|la|de|que|en|los|las|una|por|para|está|está)\b", low))
            en_hits = len(re.findall(r"\b(the|and|is|are|with|from|this|that)\b", low))
            if es_hits >= 4 and es_hits > en_hits * 2:
                r = self.traducir(respuesta, destino="en", origen="es")
                if r.get("ok"):
                    return r["texto"]
        return respuesta
