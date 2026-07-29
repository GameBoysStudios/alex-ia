# -*- coding: utf-8 -*-
"""
Roles de cuenta para Alex.

Firebase Realtime Database:
  alex/admins/{UID} = true
  o
  alex/admins/{UID} = { "admin": true, "email": "...", "nota": "..." }

Tambien se puede fijar por variable de entorno (coma-separado):
  ALEX_ADMIN_UIDS=uid1,uid2

El rol admin puede seleccionar el modelo Pro 2.0.
"""

import os
import time

MODELOS = {
    "2.0": {
        "id": "2.0",
        "nombre": "Alex 2.0",
        "descripcion": "Modelo estandar (todos)",
        "requiere_admin": False,
    },
    "pro": {
        "id": "pro",
        "nombre": "Alex Pro 2.0",
        "descripcion": "Modelo Pro (solo administradores por ahora)",
        "requiere_admin": True,
    },
}


def _es_admin_val(val) -> bool:
    if val is True or val == 1 or val == "1":
        return True
    if isinstance(val, str) and val.strip().lower() in ("true", "admin", "yes", "si", "sí"):
        return True
    if isinstance(val, dict):
        if val.get("admin") is True or val.get("role") == "admin" or val.get("rol") == "admin":
            return True
        if str(val.get("admin", "")).lower() in ("true", "1", "yes", "si", "sí"):
            return True
    return False


def _uids_env() -> set:
    raw = (os.environ.get("ALEX_ADMIN_UIDS") or "").strip()
    if not raw:
        return set()
    return {u.strip() for u in raw.split(",") if u.strip()}


class GestorRoles:
    def __init__(self, almacenamiento):
        self.almacenamiento = almacenamiento

    def es_admin(self, uid: str) -> bool:
        uid = (uid or "").strip()
        if not uid or uid.startswith("guest-"):
            return False
        if uid in _uids_env():
            return True
        try:
            val = self.almacenamiento.leer(f"admins/{uid}", None)
            if val is None:
                val = self.almacenamiento.leer(f"admins/{uid}.json", None)
            if _es_admin_val(val):
                return True
            # Alternativa: roles/{uid}
            val2 = self.almacenamiento.leer(f"roles/{uid}", None)
            if val2 is None:
                val2 = self.almacenamiento.leer(f"roles/{uid}.json", None)
            if isinstance(val2, str) and val2.strip().lower() == "admin":
                return True
            if _es_admin_val(val2):
                return True
        except Exception as e:
            print(f"[Alex] Error leyendo rol admin {uid}: {e}")
        return False

    def set_admin(self, uid: str, admin: bool = True, email: str = "", nota: str = "") -> dict:
        uid = (uid or "").strip()
        if not uid or uid.startswith("guest-"):
            return {"ok": False, "error": "UID invalido"}
        payload = {
            "admin": bool(admin),
            "rol": "admin" if admin else "user",
            "email": (email or "").strip().lower(),
            "nota": nota or ("" if admin else "revocado"),
            "updated": time.strftime("%Y-%m-%dT%H:%M:%S"),
        }
        try:
            self.almacenamiento.escribir(f"admins/{uid}", payload)
        except Exception:
            self.almacenamiento.escribir(f"admins/{uid}.json", payload)
        return {
            "ok": True,
            "uid": uid,
            "admin": bool(admin),
            "rol": payload["rol"],
        }

    def listar_admins(self) -> dict:
        try:
            raw = self.almacenamiento.leer("admins", None)
            if raw is None:
                raw = self.almacenamiento.leer("admins.json", None)
            limpio = {}
            if isinstance(raw, dict):
                for u, v in raw.items():
                    if _es_admin_val(v):
                        limpio[u] = v if isinstance(v, dict) else {"admin": True}
            for u in _uids_env():
                limpio.setdefault(u, {"admin": True, "fuente": "env"})
            return {"ok": True, "admins": limpio}
        except Exception as e:
            return {"ok": False, "error": str(e), "admins": {}}

    def rol_de(self, uid: str) -> str:
        if self.es_admin(uid):
            return "admin"
        if uid and not str(uid).startswith("guest-"):
            return "user"
        return "guest"

    def modelos_disponibles(self, uid: str) -> list:
        admin = self.es_admin(uid)
        out = []
        for mid, meta in MODELOS.items():
            item = dict(meta)
            item["disponible"] = (not meta["requiere_admin"]) or admin
            out.append(item)
        return out

    def puede_usar_modelo(self, uid: str, modelo: str) -> bool:
        modelo = (modelo or "2.0").strip().lower()
        if modelo in ("2", "2.0", "normal", "standard"):
            return True
        if modelo in ("pro", "pro2", "pro 2.0", "pro2.0"):
            return self.es_admin(uid)
        return False

    def normalizar_modelo(self, modelo: str) -> str:
        m = (modelo or "2.0").strip().lower()
        if m in ("pro", "pro2", "pro 2.0", "pro2.0"):
            return "pro"
        return "2.0"
