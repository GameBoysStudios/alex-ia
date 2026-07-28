# -*- coding: utf-8 -*-
"""
Almacenamiento para Alex.

- Local JSON (por defecto)
- Firebase Realtime Database (si hay variables de entorno configuradas)

Variables Firebase:
  FIREBASE_DATABASE_URL  -> https://TU-PROYECTO-default-rtdb.europe-west1.firebasedatabase.app
  FIREBASE_CREDENTIALS   -> JSON completo de la cuenta de servicio (una sola linea o normal)
  FIREBASE_ROOT          -> ruta raiz opcional (por defecto: alex)
"""

import json
import os
import tempfile
from datetime import datetime

_firebase_app = None


def _firebase_disponible() -> bool:
    url = os.environ.get("FIREBASE_DATABASE_URL", "").strip()
    cred = os.environ.get("FIREBASE_CREDENTIALS", "").strip()
    return bool(url and cred)


def _init_firebase():
    global _firebase_app
    if _firebase_app is not None:
        return _firebase_app
    import firebase_admin
    from firebase_admin import credentials

    raw = os.environ["FIREBASE_CREDENTIALS"].strip()
    info = json.loads(raw)
    cred = credentials.Certificate(info)
    url = os.environ["FIREBASE_DATABASE_URL"].strip()
    try:
        _firebase_app = firebase_admin.get_app()
    except ValueError:
        _firebase_app = firebase_admin.initialize_app(cred, {"databaseURL": url})
    return _firebase_app


class AlmacenamientoJSON:
    """Backend local en disco (JSON atomico)."""

    backend = "local"

    def __init__(self, directorio_base: str):
        self.directorio_base = os.path.abspath(directorio_base)
        os.makedirs(self.directorio_base, exist_ok=True)
        print(f"[Alex] Backend LOCAL -> {self.directorio_base}")

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
            print(f"[Alex] Guardado LOCAL OK: {ruta_relativa}")
        except Exception as e:
            print(f"[Alex] ERROR guardando LOCAL {ruta_completa}: {e}")
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


class AlmacenamientoFirebase:
    """Backend Firebase Realtime Database (persistente entre reinicios)."""

    backend = "firebase"

    def __init__(self, directorio_base: str = None):
        _init_firebase()
        from firebase_admin import db

        root = os.environ.get("FIREBASE_ROOT", "alex").strip() or "alex"
        self._root = root.strip("/")
        self._db = db
        self.directorio_base = f"firebase://{self._root}"
        print(f"[Alex] Backend FIREBASE -> {self.directorio_base}")

    def _ref(self, ruta_relativa: str):
        # memoria_permanente.json -> memoria_permanente
        # conversaciones/2026-01-01/sesion_x.json -> conversaciones/2026-01-01/sesion_x
        clave = ruta_relativa.replace("\\", "/")
        if clave.endswith(".json"):
            clave = clave[:-5]
        clave = clave.strip("/")
        path = f"{self._root}/{clave}" if clave else self._root
        return self._db.reference(path)

    def ruta(self, *partes) -> str:
        return "/".join(str(p) for p in partes)

    def leer(self, ruta_relativa: str, por_defecto=None):
        try:
            datos = self._ref(ruta_relativa).get()
            if datos is None:
                return por_defecto
            return datos
        except Exception as e:
            print(f"[Alex] Error leyendo Firebase {ruta_relativa}: {e}")
            return por_defecto

    def escribir(self, ruta_relativa: str, datos) -> None:
        try:
            self._ref(ruta_relativa).set(datos)
            print(f"[Alex] Guardado FIREBASE OK: {ruta_relativa}")
        except Exception as e:
            print(f"[Alex] ERROR guardando Firebase {ruta_relativa}: {e}")
            raise

    @staticmethod
    def marca_tiempo() -> str:
        return datetime.now().isoformat(timespec="seconds")

    @staticmethod
    def fecha_hoy() -> str:
        return datetime.now().strftime("%Y-%m-%d")


def crear_almacenamiento(directorio_base: str = None):
    """Elige Firebase si hay credenciales; si no, JSON local."""
    if _firebase_disponible():
        try:
            return AlmacenamientoFirebase(directorio_base)
        except Exception as e:
            print(f"[Alex] Firebase no disponible ({e}); usando disco local.")
    if not directorio_base:
        directorio_base = os.environ.get("ALEX_DATA_DIR") or os.environ.get("DATA_DIR")
        if not directorio_base:
            # raiz del proyecto / data
            aqui = os.path.dirname(os.path.abspath(__file__))
            directorio_base = os.path.join(os.path.dirname(aqui), "data")
    return AlmacenamientoJSON(directorio_base)
