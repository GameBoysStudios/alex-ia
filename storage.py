# -*- coding: utf-8 -*-
"""
Módulo de almacenamiento JSON para Alex.

Se encarga de leer/escribir de forma segura los archivos JSON usados por
el resto del sistema (memoria permanente y conversaciones por fecha).
"""

import json
import os
import shutil
import tempfile
from datetime import datetime


class AlmacenamientoJSON:
    """Gestiona lectura/escritura atómica de archivos JSON en disco."""

    def __init__(self, directorio_base: str):
        self.directorio_base = directorio_base
        os.makedirs(self.directorio_base, exist_ok=True)

    def ruta(self, *partes) -> str:
        return os.path.join(self.directorio_base, *partes)

    def leer(self, ruta_relativa: str, por_defecto=None):
        """Lee un archivo JSON. Si no existe o está corrupto, devuelve por_defecto."""
        ruta_completa = self.ruta(ruta_relativa)
        if not os.path.exists(ruta_completa):
            return por_defecto
        try:
            with open(ruta_completa, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            # Archivo corrupto: se hace copia de seguridad y se devuelve el valor por defecto.
            try:
                shutil.copy(ruta_completa, ruta_completa + ".corrupto.bak")
            except OSError:
                pass
            return por_defecto

    def escribir(self, ruta_relativa: str, datos) -> None:
        """Escribe datos en JSON de forma atómica (evita corrupción si se interrumpe)."""
        ruta_completa = self.ruta(ruta_relativa)
        os.makedirs(os.path.dirname(ruta_completa) or ".", exist_ok=True)

        fd, ruta_temporal = tempfile.mkstemp(
            dir=os.path.dirname(ruta_completa) or ".", suffix=".tmp"
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(datos, f, ensure_ascii=False, indent=2, sort_keys=False)
            shutil.move(ruta_temporal, ruta_completa)
        except Exception:
            if os.path.exists(ruta_temporal):
                os.remove(ruta_temporal)
            raise

    @staticmethod
    def marca_tiempo() -> str:
        return datetime.now().isoformat(timespec="seconds")

    @staticmethod
    def fecha_hoy() -> str:
        return datetime.now().strftime("%Y-%m-%d")
