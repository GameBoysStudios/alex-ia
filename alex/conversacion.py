# -*- coding: utf-8 -*-
"""Historial de conversacion de Alex (no debe tumbar el chat si Firebase falla)."""

import os
from alex.storage import AlmacenamientoJSON


class Conversacion:
    def __init__(self, almacenamiento: AlmacenamientoJSON):
        self.almacenamiento = almacenamiento
        self.fecha = self.almacenamiento.fecha_hoy()
        self.id_sesion = self._generar_id_sesion()
        self.mensajes = []
        self.ruta_relativa = os.path.join(
            "conversaciones", self.fecha, f"{self.id_sesion}.json"
        )
        self._cargar_si_existe()

    def _generar_id_sesion(self) -> str:
        # Solo caracteres seguros para Firebase paths
        ts = self.almacenamiento.marca_tiempo().replace(":", "-").replace(".", "-")
        return "sesion_" + ts

    def _cargar_si_existe(self):
        try:
            datos = self.almacenamiento.leer(self.ruta_relativa)
            if isinstance(datos, dict):
                msgs = datos.get("mensajes", [])
                if isinstance(msgs, list):
                    self.mensajes = msgs
        except Exception as e:
            print(f"[Alex] No se pudo cargar conversacion: {e}")

    def agregar_mensaje(self, rol: str, texto: str, extra: dict = None):
        entrada = {
            "rol": rol,
            "texto": texto if texto is not None else "",
            "timestamp": self.almacenamiento.marca_tiempo(),
        }
        if extra and isinstance(extra, dict):
            # Solo tipos serializables basicos
            limpio = {}
            for k, v in extra.items():
                if isinstance(v, (str, int, float, bool, list, dict, type(None))):
                    limpio[str(k)] = v
            entrada["extra"] = limpio
        self.mensajes.append(entrada)
        # Limitar historial en memoria para no hinchar Firebase
        if len(self.mensajes) > 200:
            self.mensajes = self.mensajes[-150:]
        self._guardar()

    def _guardar(self):
        try:
            self.almacenamiento.escribir(self.ruta_relativa, {
                "fecha": self.fecha,
                "id_sesion": self.id_sesion,
                "mensajes": self.mensajes[-100:],
            })
        except Exception as e:
            print(f"[Alex] Aviso: no se pudo guardar conversacion ({e})")

    def contexto_reciente(self, n: int = 6) -> str:
        try:
            recientes = self.mensajes[-n:]
            partes = []
            for m in recientes:
                if not isinstance(m, dict):
                    continue
                t = m.get("texto")
                if t:
                    partes.append(str(t))
            return " ".join(partes)
        except Exception:
            return ""

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
                    datos = almacenamiento.leer(ruta_rel, {}) or {}
                    resultado.append({
                        "fecha": fecha,
                        "archivo": archivo,
                        "n_mensajes": len(datos.get("mensajes", []) or []),
                    })
        return resultado
