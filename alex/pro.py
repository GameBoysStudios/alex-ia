# -*- coding: utf-8 -*-
"""
Alex Pro 2.0 — capacidades extra sobre Alex 2.0:
  - Vision mas rica (heurísticas de escena)
  - Analisis y resumen de PDF
"""

from alex.nucleo import Alex
from alex.vision import AnalizadorImagen
from alex.pdf_doc import AnalizadorPDF


class AlexPro(Alex):
    MODELO_ID = "pro"
    MODELO_NOMBRE = "Alex Pro 2.0"

    def __init__(self, directorio_datos: str = None):
        super().__init__(directorio_datos=directorio_datos)
        # Vision Pro: mismas herramientas, mas descripcion / escena
        self.vision = AnalizadorImagen(modo_pro=True)
        self.pdf = AnalizadorPDF()

    def analizar_imagen(self, b64: str, idioma: str = None) -> str:
        idioma = idioma or self._idioma_actual or "es"
        r = self.vision.analizar_base64(b64, idioma=idioma)
        return r.get("descripcion") or r.get("error") or "No pude analizar la imagen."

    def analizar_pdf(self, b64: str, idioma: str = None) -> dict:
        idioma = idioma or self._idioma_actual or "es"
        return self.pdf.analizar_base64(b64, idioma=idioma)

    def responder(self, texto_usuario: str, cuota: dict = None) -> str:
        respuesta = super().responder(texto_usuario, cuota=cuota)
        try:
            if self.conversacion.mensajes:
                ultimo = self.conversacion.mensajes[-1]
                if ultimo.get("rol") == "alex":
                    extra = ultimo.setdefault("extra", {}) or {}
                    extra["modelo"] = self.MODELO_ID
                    extra["modelo_nombre"] = self.MODELO_NOMBRE
                    ultimo["extra"] = extra
        except Exception:
            pass
        return respuesta

    def resumen_memoria(self) -> dict:
        d = super().resumen_memoria()
        d["modelo"] = self.MODELO_ID
        d["modelo_nombre"] = self.MODELO_NOMBRE
        d["vision_pro"] = True
        d["pdf"] = getattr(self.pdf, "disponible", False)
        return d
