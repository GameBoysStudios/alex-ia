# -*- coding: utf-8 -*-
"""Almacenamiento JSON atomico para Alex."""

import json
import os
import tempfile
from datetime import datetime


class AlmacenamientoJSON:
    def __init__(self, directorio_base: str):
        self.directorio_base = os.path.abspath(directorio_base)
        os.makedirs(self.directorio_base, exist_ok=True)
        print(f"[Alex] Datos en: {self.directorio_base}")

    def ruta(self, *partes) -> str:
        return os.path.join(self.directorio_base, *partes)

    def leer(self, ruta_relativa: str, por_defecto=None):
        ruta_completa = self.ruta(ruta_relativa)
        if not os.path.exists(ruta_completa):
            return por_defecto
        try:
            with open(ruta_completa, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            print(f"[Alex] Error leyendo {ruta_completa}: {e}")
            return por_defecto

    def escribir(self, ruta_relativa: str, datos) -> None:
        ruta_completa = self.ruta(ruta_relativa)
        carpeta = os.path.dirname(ruta_completa) or self.directorio_base
        os.makedirs(carpeta, exist_ok=True)

        fd, ruta_temporal = tempfile.mkstemp(dir=carpeta, suffix=".tmp", prefix="alex_")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(datos, f, ensure_ascii=False, indent=2)
                f.flush()
                os.fsync(f.fileno())
            os.replace(ruta_temporal, ruta_completa)
            print(f"[Alex] Guardado OK: {ruta_completa} ({os.path.getsize(ruta_completa)} bytes)")
        except Exception as e:
            print(f"[Alex] ERROR guardando {ruta_completa}: {e}")
            try:
                if os.path.exists(ruta_temporal):
                    os.remove(ruta_temporal)
            except OSError:
                pass
            raise

    @staticmethod
    def marca_tiempo() -> str:
        return datetime.now().isoformat(timespec="seconds")

    @staticmethod
    def fecha_hoy() -> str:
        return datetime.now().strftime("%Y-%m-%d")
