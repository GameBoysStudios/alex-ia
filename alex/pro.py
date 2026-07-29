# -*- coding: utf-8 -*-
"""
Alex Pro 2.0 — vision y PDF sin APIs de pago.

Imagen:
  1) Caption gratuita (Hugging Face BLIP) si hay red
  2) Analisis local Pillow (colores / escena)

PDF:
  1) Texto con pypdf
  2) Si es escaneo: render pagina 1 (pypdfium2) + caption BLIP
"""

from alex.nucleo import Alex
from alex.vision import AnalizadorImagen
from alex.pdf_doc import AnalizadorPDF
from alex.vision_libre import VisionLibre


class AlexPro(Alex):
    MODELO_ID = "pro"
    MODELO_NOMBRE = "Alex Pro 2.0"

    def __init__(self, directorio_datos: str = None):
        super().__init__(directorio_datos=directorio_datos)
        self.vision = AnalizadorImagen(modo_pro=True)
        self.pdf = AnalizadorPDF()
        self.vision_libre = VisionLibre()
        # Google Vision desactivado (de pago)
        self.gvision = None

    def analizar_imagen(self, b64: str, idioma: str = None) -> str:
        idioma = idioma or self._idioma_actual or "es"
        partes = []

        # 1) Caption gratuita BLIP
        cap = self.vision_libre.caption_base64(b64, idioma=idioma)
        if cap.get("ok") and cap.get("caption"):
            if idioma == "en":
                partes.append(f"I see (free AI caption): {cap['caption']}.")
            else:
                partes.append(f"Veo (descripcion gratuita): {cap['caption']}.")
        elif cap.get("descripcion") and cap.get("error") == "modelo_cargando":
            partes.append(cap["descripcion"])

        # 2) Analisis local siempre
        local = self.vision.analizar_base64(b64, idioma=idioma)
        if local.get("descripcion"):
            partes.append(local["descripcion"])

        if not partes:
            return local.get("error") or (
                "No pude analizar la imagen."
                if idioma != "en"
                else "Could not analyze the image."
            )

        # Evitar duplicar si solo local
        return "\n\n".join(partes)

    def analizar_pdf(self, b64: str, idioma: str = None) -> dict:
        idioma = idioma or self._idioma_actual or "es"
        resultado = self.pdf.analizar_base64(b64, idioma=idioma)

        # Si hay texto util, listo
        if resultado.get("ok") and not resultado.get("texto_vacio") and (
            resultado.get("resumen") or (resultado.get("caracteres") or 0) > 80
        ):
            return resultado

        # Escaneo / sin texto: render + caption gratis
        raw_b64 = b64 or ""
        if "," in raw_b64 and raw_b64.strip().startswith("data:"):
            raw_b64 = raw_b64.split(",", 1)[1]
        import base64 as _b64

        try:
            raw = _b64.b64decode(raw_b64)
        except Exception as e:
            resultado["descripcion"] = (
                (resultado.get("descripcion") or "")
                + f"\nNo pude decodificar el PDF: {e}"
            )
            return resultado

        png = self.vision_libre.render_pdf_pagina(raw, pagina=0)
        if not png:
            # sin pypdfium2 o fallo
            if idioma == "en":
                extra = (
                    " Could not render pages (install pypdfium2) for free scan analysis."
                )
            else:
                extra = (
                    " No pude renderizar paginas para analizar el escaneo "
                    "(hace falta pypdfium2 en el servidor)."
                )
            resultado["descripcion"] = (resultado.get("descripcion") or "") + extra
            return resultado

        cap = self.vision_libre.caption_bytes(png, idioma=idioma)
        local = self.vision.analizar_bytes(png, idioma=idioma)

        lineas = []
        if idioma == "en":
            lineas.append("Scanned PDF — free analysis of page 1:")
        else:
            lineas.append("PDF tipo escaneo — analisis gratuito de la pagina 1:")

        if cap.get("ok") and cap.get("caption"):
            if idioma == "en":
                lineas.append(f"Caption: {cap['caption']}")
            else:
                lineas.append(f"Descripcion: {cap['caption']}")
        elif cap.get("descripcion"):
            lineas.append(cap["descripcion"])

        if local.get("descripcion"):
            lineas.append(local["descripcion"])

        if resultado.get("descripcion"):
            lineas.append("—")
            lineas.append(resultado["descripcion"])

        resultado["ok"] = True
        resultado["motor_escaneo"] = "blip+local"
        resultado["descripcion"] = "\n".join(lineas)
        return resultado

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
        d["google_vision"] = False
        d["vision_libre"] = self.vision_libre.disponible
        d["pdf"] = getattr(self.pdf, "disponible", False)
        return d
