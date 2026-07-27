# -*- coding: utf-8 -*-
"""
Módulo de Conversación para Alex.

Gestiona el historial de la sesión actual en memoria (para tener contexto
inmediato) y su persistencia en archivos JSON organizados por fecha, dentro
de una carpeta "conversaciones/AAAA-MM-DD/".
"""

import os
from alex.storage import AlmacenamientoJSON


class Conversacion:
    def __init__(self, almacenamiento: AlmacenamientoJSON):
        self.almacenamiento = almacenamiento
        self.fecha = self.almacenamiento.fecha_hoy()
        self.id_sesion = self._generar_id_sesion()
        self.mensajes = []  # lista de {rol, texto, timestamp}
        self.ruta_relativa = os.path.join(
            "conversaciones", self.fecha, f"{self.id_sesion}.json"
        )
        self._cargar_si_existe()

    def _generar_id_sesion(self) -> str:
        return "sesion_" + self.almacenamiento.marca_tiempo().replace(":", "-")

    def _cargar_si_existe(self):
        datos = self.almacenamiento.leer(self.ruta_relativa)
        if datos:
            self.mensajes = datos.get("mensajes", [])

    def agregar_mensaje(self, rol: str, texto: str, extra: dict = None):
        entrada = {
            "rol": rol,
            "texto": texto,
            "timestamp": self.almacenamiento.marca_tiempo(),
        }
        if extra:
            entrada["extra"] = extra
        self.mensajes.append(entrada)
        self._guardar()

    def _guardar(self):
        self.almacenamiento.escribir(self.ruta_relativa, {
            "fecha": self.fecha,
            "id_sesion": self.id_sesion,
            "mensajes": self.mensajes,
        })

    def contexto_reciente(self, n: int = 6) -> str:
        recientes = self.mensajes[-n:]
        return " ".join(m["texto"] for m in recientes)

    def exportar(self, ruta_destino: str):
        import json
        with open(ruta_destino, "w", encoding="utf-8") as f:
            json.dump({
                "fecha": self.fecha,
                "id_sesion": self.id_sesion,
                "mensajes": self.mensajes,
            }, f, ensure_ascii=False, indent=2)

    @staticmethod
    def listar_conversaciones(almacenamiento: AlmacenamientoJSON) -> list:
        base = almacenamiento.ruta("conversaciones")
        resultado = []
        if not os.path.isdir(base):
            return resultado
        for fecha in sorted(os.listdir(base)):
            carpeta_fecha = os.path.join(base, fecha)
            if not os.path.isdir(carpeta_fecha):
                continue
            for archivo in sorted(os.listdir(carpeta_fecha)):
                if archivo.endswith(".json"):
                    ruta_rel = os.path.join("conversaciones", fecha, archivo)
                    datos = almacenamiento.leer(ruta_rel, {})
                    resultado.append({
                        "fecha": fecha,
                        "archivo": archivo,
                        "n_mensajes": len(datos.get("mensajes", [])),
                    })
        return resultado
