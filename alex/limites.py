# -*- coding: utf-8 -*-
"""
Limites de mensajes por cuenta (ventana de 12 horas).

  guest   (sin cuenta Firebase): 10 mensajes / 12h
  normal  (cuenta Firebase):     50 mensajes / 12h
  premium:                       ilimitado

Premium se controla desde Firebase Realtime Database:

  alex/premium/{UID} = true
  o
  alex/premium/{UID} = { "premium": true, "email": "...", "nota": "..." }

Tambien se puede fijar en la cuota:
  alex/cuotas/{UID}/tier = "premium"

La lista alex/premium tiene prioridad (lo que marques ahi manda).
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


def _clave_premium(cuenta_id: str) -> str:
    return f"premium/{cuenta_id}"


def _parece_firebase_uid(cuenta_id: str) -> bool:
    if not cuenta_id or cuenta_id.startswith("guest-"):
        return False
    return len(cuenta_id) >= 20 and cuenta_id.replace("-", "").isalnum()


def _es_valor_premium(val) -> bool:
    if val is True or val == 1 or val == "1":
        return True
    if isinstance(val, str) and val.strip().lower() in ("true", "premium", "yes", "si", "sí"):
        return True
    if isinstance(val, dict):
        if val.get("premium") is True or val.get("tier") == "premium":
            return True
        if str(val.get("premium", "")).lower() in ("true", "1", "yes", "si", "sí"):
            return True
    return False


class GestorLimites:
    def __init__(self, almacenamiento):
        self.almacenamiento = almacenamiento

    def _premium_en_firebase(self, cuenta_id: str) -> bool:
        """Lee alex/premium/{uid} — lo que marques ahi manda."""
        if not cuenta_id or cuenta_id.startswith("guest-"):
            return False
        try:
            val = self.almacenamiento.leer(_clave_premium(cuenta_id), None)
            if val is None:
                val = self.almacenamiento.leer(_clave_premium(cuenta_id) + ".json", None)
            return _es_valor_premium(val)
        except Exception as e:
            print(f"[Alex] Error leyendo premium {cuenta_id}: {e}")
            return False

    def _aplicar_premium_overlay(self, datos: dict) -> dict:
        cid = datos.get("cuenta_id") or ""
        if self._premium_en_firebase(cid):
            datos["tier"] = "premium"
            datos["provider"] = datos.get("provider") or "firebase"
            datos["premium_fuente"] = "firebase/premium"
        return datos

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
        datos["cuenta_id"] = cuenta_id
        if _parece_firebase_uid(cuenta_id) and datos.get("tier") == "guest":
            datos["tier"] = "normal"
            datos["provider"] = "firebase"
        # Overlay premium desde lista central en Firebase
        datos = self._aplicar_premium_overlay(datos)
        return datos

    def _guardar_cuenta(self, datos: dict) -> None:
        cid = datos["cuenta_id"]
        # No pisar premium de la lista central al guardar cuota
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
            "premium_fuente": datos.get("premium_fuente") or "",
            "limite": limite,
            "usados": usados,
            "restantes": restantes,
            "permitido": permitido,
            "ventana_horas": 12,
            "version": "2.0",
        }

    def consumir(self, cuenta_id: str) -> dict:
        datos = self._leer_cuenta(cuenta_id)
        if _parece_firebase_uid(cuenta_id) and datos.get("tier") in ("normal", "premium"):
            # Persistir vinculo sin bajar de premium
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

    def set_premium(self, uid: str, premium: bool = True, email: str = "", nota: str = "") -> dict:
        """
        Escribe en Firebase: alex/premium/{uid}
        Asi tu puedes gestionar premium desde consola o API admin.
        """
        uid = (uid or "").strip()
        if not uid or uid.startswith("guest-"):
            return {"ok": False, "error": "UID invalido"}

        if premium:
            payload = {
                "premium": True,
                "tier": "premium",
                "email": (email or "").strip().lower(),
                "nota": nota or "",
                "updated": time.strftime("%Y-%m-%dT%H:%M:%S"),
            }
            try:
                self.almacenamiento.escribir(_clave_premium(uid), payload)
            except Exception:
                self.almacenamiento.escribir(_clave_premium(uid) + ".json", payload)
            # Reflejar tambien en cuota
            datos = self._leer_cuenta(uid)
            datos["tier"] = "premium"
            if email:
                datos["email"] = email.strip().lower()
            self._guardar_cuenta(datos)
        else:
            # Quitar premium: escribir false (o borrar valor)
            payload = {
                "premium": False,
                "tier": "normal",
                "email": (email or "").strip().lower(),
                "nota": nota or "revocado",
                "updated": time.strftime("%Y-%m-%dT%H:%M:%S"),
            }
            try:
                self.almacenamiento.escribir(_clave_premium(uid), payload)
            except Exception:
                self.almacenamiento.escribir(_clave_premium(uid) + ".json", payload)
            datos = self._leer_cuenta(uid)
            # Si la lista ya no marca premium, bajar a normal
            if not self._premium_en_firebase(uid):
                datos["tier"] = "normal" if _parece_firebase_uid(uid) else "guest"
                datos.pop("premium_fuente", None)
                self._guardar_cuenta(datos)

        st = self.estado(uid)
        st["ok"] = True
        return st

    def listar_premium(self) -> dict:
        """Lee alex/premium completo."""
        try:
            raw = self.almacenamiento.leer("premium", None)
            if raw is None:
                raw = self.almacenamiento.leer("premium.json", None)
            if not isinstance(raw, dict):
                return {"ok": True, "premium": {}}
            limpio = {}
            for uid, val in raw.items():
                if _es_valor_premium(val):
                    limpio[uid] = val if isinstance(val, dict) else {"premium": True}
            return {"ok": True, "premium": limpio}
        except Exception as e:
            return {"ok": False, "error": str(e), "premium": {}}

    def vincular_firebase(self, uid: str, email: str = "", tier: str = "normal") -> dict:
        uid = (uid or "").strip()
        if not uid or uid.startswith("guest-"):
            return {"ok": False, "error": "UID de Firebase invalido"}
        datos = self._leer_cuenta(uid)
        datos["cuenta_id"] = uid
        datos["email"] = (email or "").strip().lower()
        datos["provider"] = "firebase"
        # No bajar de premium si esta en la lista Firebase
        if self._premium_en_firebase(uid):
            datos["tier"] = "premium"
        elif datos.get("tier") != "premium":
            if tier == "premium":
                tier = "normal"  # premium solo por lista/admin
            datos["tier"] = tier if tier in ("normal", "guest") else "normal"
        self._guardar_cuenta(datos)
        st = self.estado(uid)
        st["ok"] = True
        return st

    def registrar(self, cuenta_id: str, email: str, password: str, tier: str = "normal") -> dict:
        if _parece_firebase_uid(cuenta_id):
            return self.vincular_firebase(cuenta_id, email, tier=tier or "normal")
        datos = self._leer_cuenta(cuenta_id)
        email = (email or "").strip().lower()
        if not email or not password:
            return {"ok": False, "error": "Email y contraseña requeridos"}
        datos["email"] = email
        datos["password_hash"] = hashlib.sha256(password.encode("utf-8")).hexdigest()
        datos["provider"] = "local"
        if self._premium_en_firebase(cuenta_id):
            datos["tier"] = "premium"
        else:
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
        if tier == "premium":
            return self.set_premium(cuenta_id, premium=True)
        if tier in ("normal", "guest"):
            # Si estaba en lista premium, revocar
            if self._premium_en_firebase(cuenta_id):
                return self.set_premium(cuenta_id, premium=False)
        datos = self._leer_cuenta(cuenta_id)
        datos["tier"] = tier
        self._guardar_cuenta(datos)
        st = self.estado(cuenta_id)
        st["ok"] = True
        return st
