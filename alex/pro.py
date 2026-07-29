# -*- coding: utf-8 -*-
"""
Alex Pro 2.0:
  - Vision casera + Google Cloud Vision (estilo Lens) si hay API key
  - PDF: texto con pypdf + OCR Vision si el PDF es escaneado
"""

from alex.nucleo import Alex
from alex.vision import AnalizadorImagen
from alex.pdf_doc import AnalizadorPDF
from alex.google_vision import GoogleVision


class AlexPro(Alex):
    MODELO_ID = "pro"
    MODELO_NOMBRE = "Alex Pro 2.0"

    def __init__(self, directorio_datos: str = None):
        super().__init__(directorio_datos=directorio_datos)
        self.vision = AnalizadorImagen(modo_pro=True)
        self.pdf = AnalizadorPDF()
        self.gvision = GoogleVision()

    def analizar_imagen(self, b64: str, idioma: str = None) -> str:
        idioma = idioma or self._idioma_actual or "es"
        # 1) Google Vision si hay clave
        if self.gvision.disponible:
            r = self.gvision.analizar_imagen_base64(b64, idioma=idioma)
            if r.get("ok") and r.get("descripcion"):
                return r["descripcion"]
            # si falla la API, cae a casero
            extra = r.get("descripcion") or r.get("error") or ""
            casero = self.vision.analizar_base64(b64, idioma=idioma)
            base = casero.get("descripcion") or ""
            if extra:
                return base + f"\n(Nota: Google Vision no respondio bien: {extra})"
            return base
        r = self.vision.analizar_base64(b64, idioma=idioma)
        return r.get("descripcion") or r.get("error") or "No pude analizar la imagen."

    def analizar_pdf(self, b64: str, idioma: str = None) -> dict:
        idioma = idioma or self._idioma_actual or "es"
        resultado = self.pdf.analizar_base64(b64, idioma=idioma)

        # Si no hay texto y tenemos Vision, intentar OCR de las primeras paginas
        if resultado.get("texto_vacio") or not (resultado.get("resumen") or resultado.get("caracteres")):
            if self.gvision.disponible:
                raw_b64 = b64
                if "," in raw_b64 and raw_b64.strip().startswith("data:"):
                    raw_b64 = raw_b64.split(",", 1)[1]
                import base64 as _b64
                try:
                    raw = _b64.b64decode(raw_b64)
                except Exception as e:
                    resultado["descripcion"] = (
                        resultado.get("descripcion") or ""
                    ) + f"\nNo pude decodificar el PDF para OCR: {e}"
                    return resultado

                ocr = self.gvision.ocr_pdf_bytes(raw, idioma=idioma, max_paginas=5)
                if ocr.get("ok") and ocr.get("texto"):
                    texto = ocr["texto"]
                    # Re-resumir con el analizador local sobre el texto OCR
                    from alex import pdf_doc as mod_pdf
                    resumen_frases = mod_pdf._resumen_extractivo(texto, max_frases=5)
                    claves = mod_pdf._palabras_clave(texto, n=12)
                    resumen = " ".join(resumen_frases[:3])
                    if len(resumen) > 900:
                        resumen = resumen[:897] + "..."
                    lineas = [
                        f"PDF escaneado: OCR con Google Vision ({ocr.get('paginas_ocr', '?')} paginas leidas).",
                        f"Resumen: {resumen}" if resumen else "Resumen: (poco texto tras OCR)",
                    ]
                    if resumen_frases:
                        lineas.append("Puntos clave:")
                        for i, p in enumerate(resumen_frases[:5], 1):
                            lineas.append(f"{i}. {p}")
                    if claves:
                        lineas.append("Palabras clave: " + ", ".join(claves[:10]))
                    resultado.update({
                        "ok": True,
                        "texto_vacio": False,
                        "caracteres": len(texto),
                        "palabras": len(texto.split()),
                        "resumen": resumen,
                        "puntos": resumen_frases[:5],
                        "palabras_clave": claves,
                        "texto_preview": texto[:1500],
                        "motor_ocr": "google_vision",
                        "descripcion": "\n".join(lineas),
                    })
                elif ocr.get("descripcion") or ocr.get("error"):
                    resultado["descripcion"] = (
                        (resultado.get("descripcion") or "")
                        + "\nOCR Vision: "
                        + str(ocr.get("descripcion") or ocr.get("error"))
                    )
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
        d["google_vision"] = self.gvision.disponible
        d["pdf"] = getattr(self.pdf, "disponible", False)
        return d
