# -*- coding: utf-8 -*-
"""
Limites de mensajes por cuenta (ventana de 12 horas).

  guest   (sin cuenta Firebase): 10 mensajes / 12h
  normal  (cuenta Firebase):     50 mensajes / 12h
  premium:                       ilimitado

Las cuentas de la web GameBoys (Firebase Auth) se vinculan por UID.
"""

import hashlib
import time

VENTANA_SEG = 12 * 60 * 60

LIMITES = {
    "guest": 10,
    "normal": 50,
    "premium": None,
}


def _ahora() -> float:
    return time.time()


def _clave_cuenta(cuenta_id: str) -> str:
    return f"cuotas/{cuenta_id}"


def _parece_firebase_uid(cuenta_id: str) -> bool:
    """UID de Firebase Auth suelen ser 28 chars alfanumericos (no empiezan por guest-)."""
    if not cuenta_id or cuenta_id.startswith("guest-"):
        return False
    return len(cuenta_id) >= 20 and cuenta_id.replace("-", "").isalnum()


class GestorLimites:
    def __init__(self, almacenamiento):
        self.almacenamiento = almacenamiento

    def _leer_cuenta(self, cuenta_id: str) -> dict:
        datos = self.almacenamiento.leer(_clave_cuenta(cuenta_id) + ".json", None)
        if not datos:
            datos = self.almacenamiento.leer(_clave_cuenta(cuenta_id), None)
        if not isinstance(datos, dict):
            tier_default = "normal" if _parece_firebase_uid(cuenta_id) else "guest"
            datos = {
                "cuenta_id": cuenta_id,
                "tier": tier_default,
                "email": "",
                "password_hash": "",
                "provider": "firebase" if tier_default == "normal" else "guest",
                "ventanas": {},
            }
        datos.setdefault("tier", "guest")
        datos.setdefault("ventanas", {})
        # Si llega un UID de Firebase y seguia en guest, subir a normal
        if _parece_firebase_uid(cuenta_id) and datos.get("tier") == "guest":
            datos["tier"] = "normal"
            datos["provider"] = "firebase"
        return datos

    def _guardar_cuenta(self, datos: dict) -> None:
        cid = datos["cuenta_id"]
        try:
            self.almacenamiento.escribir(_clave_cuenta(cid) + ".json", datos)
        except Exception:
            self.almacenamiento.escribir(_clave_cuenta(cid), datos)

    def _ventana_id(self, ts: float = None) -> str:
        ts = ts or _ahora()
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
            "provider": datos.get("provider") or "",
            "limite": limite,
            "usados": usados,
            "restantes": restantes,
            "permitido": permitido,
            "ventana_horas": 12,
            "version": "2.0",
        }

    def consumir(self, cuenta_id: str) -> dict:
        datos = self._leer_cuenta(cuenta_id)
        # Persistir auto-upgrade Firebase si aplicaba
        if _parece_firebase_uid(cuenta_id) and datos.get("tier") == "normal":
            self._guardar_cuenta(datos)

        tier = datos.get("tier") or "guest"
        if tier not in LIMITES:
            tier = "guest"
        limite = LIMITES[tier]
        vid = self._ventana_id()
        ventanas = datos.setdefault("ventanas", {})
        datos["ventanas"] = {vid: int(ventanas.get(vid, 0))}
        usados = int(datos["ventanas"].get(vid, 0))

        if limite is not None and usados >= limite:
            return self.estado(cuenta_id)

        datos["ventanas"][vid] = usados + 1
        self._guardar_cuenta(datos)
        return self.estado(cuenta_id)

    def vincular_firebase(self, uid: str, email: str = "", tier: str = "normal") -> dict:
        """Vincula UID de Firebase Auth (misma cuenta que la web GameBoys)."""
        uid = (uid or "").strip()
        if not uid or uid.startswith("guest-"):
            return {"ok": False, "error": "UID de Firebase invalido"}
        datos = self._leer_cuenta(uid)
        datos["cuenta_id"] = uid
        datos["email"] = (email or "").strip().lower()
        datos["provider"] = "firebase"
        if datos.get("tier") != "premium":
            if tier == "premium":
                tier = "normal"  # premium solo por admin
            datos["tier"] = tier if tier in ("normal", "guest") else "normal"
        self._guardar_cuenta(datos)
        st = self.estado(uid)
        st["ok"] = True
        return st

    def registrar(self, cuenta_id: str, email: str, password: str, tier: str = "normal") -> dict:
        # Si parece Firebase UID, no hace falta password local
        if _parece_firebase_uid(cuenta_id):
            return self.vincular_firebase(cuenta_id, email, tier=tier or "normal")
        datos = self._leer_cuenta(cuenta_id)
        email = (email or "").strip().lower()
        if not email or not password:
            return {"ok": False, "error": "Email y contraseña requeridos"}
        datos["email"] = email
        datos["password_hash"] = hashlib.sha256(password.encode("utf-8")).hexdigest()
        datos["provider"] = "local"
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
        if _parece_firebase_uid(cuenta_id):
            return self.vincular_firebase(cuenta_id, email, tier="normal")
        datos = self._leer_cuenta(cuenta_id)
        email = (email or "").strip().lower()
        ph = hashlib.sha256(password.encode("utf-8")).hexdigest()
        if datos.get("email") == email and datos.get("password_hash") == ph:
            st = self.estado(cuenta_id)
            st["ok"] = True
            return st
        if not datos.get("password_hash"):
            return self.registrar(cuenta_id, email, password, tier="normal")
        return {"ok": False, "error": "Credenciales incorrectas"}

    def set_tier(self, cuenta_id: str, tier: str) -> dict:
        if tier not in LIMITES:
            return {"ok": False, "error": "tier invalido"}
        datos = self._leer_cuenta(cuenta_id)
        datos["tier"] = tier
        self._guardar_cuenta(datos)
        st = self.estado(cuenta_id)
        st["ok"] = True
        return st
