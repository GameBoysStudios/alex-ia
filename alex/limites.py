# -*- coding: utf-8 -*-
"""
Limites de mensajes por cuenta (ventana de 12 horas).

  guest   (sin cuenta): 10 mensajes / 12h
  normal  (cuenta):     50 mensajes / 12h
  premium:              ilimitado

Persistencia: Firebase si esta activo; si no, archivo JSON local.
"""

import hashlib
import time
from datetime import datetime, timezone

VENTANA_SEG = 12 * 60 * 60  # 12 horas

LIMITES = {
    "guest": 10,
    "normal": 50,
    "premium": None,  # ilimitado
}


def _ahora() -> float:
    return time.time()


def _clave_cuenta(cuenta_id: str) -> str:
    return f"cuotas/{cuenta_id}"


class GestorLimites:
    def __init__(self, almacenamiento):
        self.almacenamiento = almacenamiento

    def _leer_cuenta(self, cuenta_id: str) -> dict:
        datos = self.almacenamiento.leer(_clave_cuenta(cuenta_id) + ".json", None)
        if not datos:
            # Firebase path without .json handled by storage; try plain key
            datos = self.almacenamiento.leer(_clave_cuenta(cuenta_id), None)
        if not isinstance(datos, dict):
            datos = {
                "cuenta_id": cuenta_id,
                "tier": "guest",
                "email": "",
                "password_hash": "",
                "ventanas": {},  # ventana_id -> contador
            }
        datos.setdefault("tier", "guest")
        datos.setdefault("ventanas", {})
        return datos

    def _guardar_cuenta(self, datos: dict) -> None:
        cid = datos["cuenta_id"]
        try:
            self.almacenamiento.escribir(_clave_cuenta(cid) + ".json", datos)
        except Exception:
            self.almacenamiento.escribir(_clave_cuenta(cid), datos)

    def _ventana_id(self, ts: float = None) -> str:
        ts = ts or _ahora()
        # Ventanas de 12h alineadas a epoch
        return str(int(ts // VENTANA_SEG))

    def estado(self, cuenta_id: str) -> dict:
        datos = self._leer_cuenta(cuenta_id)
        tier = datos.get("tier") or "guest"
        if tier not in LIMITES:
            tier = "guest"
        limite = LIMITES[tier]
        vid = self._ventana_id()
        usados = int(datos.get("ventanas", {}).get(vid, 0))
        if limite is None:
            restantes = None
            permitido = True
        else:
            restantes = max(0, limite - usados)
            permitido = usados < limite
        return {
            "cuenta_id": cuenta_id,
            "tier": tier,
            "email": datos.get("email") or "",
            "limite": limite,
            "usados": usados,
            "restantes": restantes,
            "permitido": permitido,
            "ventana_horas": 12,
            "version": "2.0",
        }

    def consumir(self, cuenta_id: str) -> dict:
        """Intenta consumir 1 mensaje. Devuelve estado; si no permitido, permitido=False."""
        datos = self._leer_cuenta(cuenta_id)
        tier = datos.get("tier") or "guest"
        if tier not in LIMITES:
            tier = "guest"
        limite = LIMITES[tier]
        vid = self._ventana_id()
        ventanas = datos.setdefault("ventanas", {})
        # Limpiar ventanas viejas (mantener solo la actual)
        datos["ventanas"] = {vid: int(ventanas.get(vid, 0))}
        usados = int(datos["ventanas"].get(vid, 0))

        if limite is not None and usados >= limite:
            return self.estado(cuenta_id)

        datos["ventanas"][vid] = usados + 1
        self._guardar_cuenta(datos)
        return self.estado(cuenta_id)

    def registrar(self, cuenta_id: str, email: str, password: str, tier: str = "normal") -> dict:
        datos = self._leer_cuenta(cuenta_id)
        email = (email or "").strip().lower()
        if not email or not password:
            return {"ok": False, "error": "Email y contraseña requeridos"}
        datos["email"] = email
        datos["password_hash"] = hashlib.sha256(password.encode("utf-8")).hexdigest()
        # No subir a premium desde cliente sin control; solo guest->normal
        if tier == "premium" and datos.get("tier") != "premium":
            tier = "normal"
        if datos.get("tier") != "premium":
            datos["tier"] = tier if tier in LIMITES else "normal"
        datos["cuenta_id"] = cuenta_id
        self._guardar_cuenta(datos)
        st = self.estado(cuenta_id)
        st["ok"] = True
        return st

    def login(self, cuenta_id: str, email: str, password: str) -> dict:
        datos = self._leer_cuenta(cuenta_id)
        # Busqueda simple: si este cuenta_id no coincide email, aun asi validamos hash local
        email = (email or "").strip().lower()
        ph = hashlib.sha256(password.encode("utf-8")).hexdigest()
        if datos.get("email") == email and datos.get("password_hash") == ph:
            st = self.estado(cuenta_id)
            st["ok"] = True
            return st
        # Permitir "login" creando vinculo si no habia cuenta con ese id
        if not datos.get("password_hash"):
            return self.registrar(cuenta_id, email, password, tier="normal")
        return {"ok": False, "error": "Credenciales incorrectas"}

    def set_tier(self, cuenta_id: str, tier: str) -> dict:
        """Solo para admin / variable de entorno interna."""
        if tier not in LIMITES:
            return {"ok": False, "error": "tier invalido"}
        datos = self._leer_cuenta(cuenta_id)
        datos["tier"] = tier
        self._guardar_cuenta(datos)
        st = self.estado(cuenta_id)
        st["ok"] = True
        return st
