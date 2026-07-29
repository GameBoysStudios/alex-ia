# -*- coding: utf-8 -*-
"""
Alex Pro 2.0 — por ahora es un clon de Alex 2.0 con identidad propia.
Aqui se iran diferenciando capacidades (mas contexto, mejor ranking, etc.).
"""

from alex.nucleo import Alex


class AlexPro(Alex):
    """Misma base que Alex 2.0; marca de modelo Pro."""

    MODELO_ID = "pro"
    MODELO_NOMBRE = "Alex Pro 2.0"

    def responder(self, texto_usuario: str, cuota: dict = None) -> str:
        respuesta = super().responder(texto_usuario, cuota=cuota)
        # Por ahora no altera la logica; solo deja traza en extra del ultimo mensaje
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
