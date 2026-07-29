# -*- coding: utf-8 -*-
"""Servidor web Alex 2.0 (Render + cuotas + premium Firebase + translate + vision)."""

import json
import os
import sys
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from alex import Alex
from alex.limites import GestorLimites

ALEX = Alex()
LIMITES = GestorLimites(ALEX.almacenamiento)
PORT = 8765
STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
VERSION = "2.0"
ADMIN_KEY = (os.environ.get("ALEX_ADMIN_KEY") or "").strip()


class AlexHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=STATIC_DIR, **kwargs)

    def log_message(self, format, *args):
        print(f"[{self.log_date_time_string()}] {args[0]}")

    def _send_json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("X-Alex-Version", VERSION)
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self):
        length = int(self.headers.get("Content-Length", 0))
        if length == 0:
            return {}
        if length > 6 * 1024 * 1024:
            return {"_error": "payload_too_large"}
        raw = self.rfile.read(length)
        try:
            return json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError:
            return {}

    def _admin_ok(self, data) -> bool:
        if not ADMIN_KEY:
            return False
        key = (
            (data or {}).get("admin_key")
            or self.headers.get("X-Alex-Admin-Key")
            or ""
        ).strip()
        return key == ADMIN_KEY

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header(
            "Access-Control-Allow-Headers",
            "Content-Type, X-Alex-Account, X-Alex-Admin-Key",
        )
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path in ("/api/stats", "/api/memoria"):
            data = ALEX.resumen_memoria()
            data["version"] = VERSION
            self._send_json(data)
            return
        if parsed.path == "/api/version":
            self._send_json({
                "version": VERSION,
                "nombre": "Alex 2.0",
                "traductor": ALEX.traductor.motor,
                "vision": ALEX.vision.disponible,
                "versiones": [
                    {"id": "2.0", "nombre": "Alex 2.0", "activa": True},
                    {"id": "pro", "nombre": "Alex Pro", "activa": False, "nota": "Proximamente"},
                ],
            })
            return
        if parsed.path == "/api/cuota":
            cuenta = self.headers.get("X-Alex-Account") or "guest"
            self._send_json(LIMITES.estado(cuenta))
            return
        if parsed.path == "/api/admin/premium":
            # Listar requiere admin key en header
            if not self._admin_ok({}):
                self._send_json({"ok": False, "error": "admin no autorizado"}, status=401)
                return
            self._send_json(LIMITES.listar_premium())
            return
        if parsed.path in ("/", ""):
            self.path = "/index.html"
        return super().do_GET()

    def _check_cuota(self, data, cuenta):
        if data.get("firebase_uid") or (cuenta and not str(cuenta).startswith("guest-")):
            uid = data.get("firebase_uid") or cuenta
            LIMITES.vincular_firebase(uid, data.get("email", ""), tier="normal")
            cuenta = uid
        cuota = LIMITES.consumir(cuenta)
        return cuenta, cuota

    def do_POST(self):
        parsed = urlparse(self.path)
        data = self._read_json()
        if data.get("_error") == "payload_too_large":
            self._send_json({"error": "payload demasiado grande (max ~4MB imagen)"}, status=413)
            return

        cuenta = (
            data.get("cuenta_id")
            or data.get("uid")
            or self.headers.get("X-Alex-Account")
            or "guest"
        )

        if parsed.path == "/api/chat":
            mensaje = (data.get("mensaje") or "").strip()
            if not mensaje:
                self._send_json({"respuesta": "Puedes escribir algo?", "version": VERSION})
                return

            cuenta, cuota = self._check_cuota(data, cuenta)
            if not cuota.get("permitido", True):
                self._send_json({
                    "error": "limite",
                    "respuesta": (
                        f"Has alcanzado el limite de mensajes "
                        f"({cuota.get('limite')} cada 12h) para la cuenta "
                        f"'{cuota.get('tier')}'. Inicia sesion en Game Boys "
                        f"(50/12h) o usa Premium (ilimitado)."
                    ),
                    "cuota": cuota,
                    "version": VERSION,
                }, status=429)
                return

            try:
                respuesta = ALEX.responder(mensaje)
                self._send_json({
                    "respuesta": respuesta,
                    "stats": ALEX.resumen_memoria(),
                    "cuota": cuota,
                    "version": VERSION,
                })
            except Exception as e:
                self._send_json({"respuesta": f"Error interno: {e}", "version": VERSION})
            return

        if parsed.path == "/api/traducir":
            texto = (data.get("texto") or data.get("mensaje") or "").strip()
            destino = (data.get("destino") or "es").lower()[:5]
            origen = (data.get("origen") or "auto").lower()[:5]
            if not texto:
                self._send_json({"ok": False, "error": "texto vacio"})
                return
            r = ALEX.traductor.traducir(texto, destino=destino, origen=origen)
            r["version"] = VERSION
            self._send_json(r)
            return

        if parsed.path == "/api/analizar_imagen":
            cuenta, cuota = self._check_cuota(data, cuenta)
            if not cuota.get("permitido", True):
                self._send_json({
                    "error": "limite",
                    "descripcion": "Limite de mensajes alcanzado.",
                    "cuota": cuota,
                }, status=429)
                return
            b64 = data.get("imagen") or data.get("image") or ""
            idioma = data.get("idioma") or "es"
            resultado = ALEX.vision.analizar_base64(b64, idioma=idioma)
            try:
                desc = resultado.get("descripcion") or ""
                ALEX.conversacion.agregar_mensaje("usuario", "[imagen]")
                ALEX.conversacion.agregar_mensaje("alex", desc, {"origen": "vision"})
                ALEX.memoria.guardar()
            except Exception:
                pass
            resultado["cuota"] = cuota
            resultado["version"] = VERSION
            self._send_json(resultado)
            return

        # ---- Admin premium ----
        if parsed.path in ("/api/admin/set_premium", "/api/admin/premium"):
            if not ADMIN_KEY:
                self._send_json({
                    "ok": False,
                    "error": "ALEX_ADMIN_KEY no configurada en Render",
                }, status=503)
                return
            if not self._admin_ok(data):
                self._send_json({"ok": False, "error": "admin no autorizado"}, status=401)
                return
            uid = (data.get("uid") or data.get("cuenta_id") or "").strip()
            premium = data.get("premium", True)
            if isinstance(premium, str):
                premium = premium.strip().lower() in ("1", "true", "yes", "si", "sí", "premium")
            st = LIMITES.set_premium(
                uid,
                premium=bool(premium),
                email=data.get("email", ""),
                nota=data.get("nota", ""),
            )
            self._send_json(st)
            return

        if parsed.path in ("/api/vincular_firebase", "/api/registro", "/api/login"):
            uid = data.get("uid") or data.get("firebase_uid") or cuenta
            email = data.get("email", "")
            if uid and not str(uid).startswith("guest-"):
                st = LIMITES.vincular_firebase(uid, email, tier=data.get("tier", "normal"))
                self._send_json(st)
                return
            if parsed.path == "/api/registro":
                st = LIMITES.registrar(
                    cuenta, email, data.get("password", ""), tier=data.get("tier", "normal")
                )
            else:
                st = LIMITES.login(cuenta, email, data.get("password", ""))
            self._send_json(st)
            return

        if parsed.path == "/api/cuota":
            self._send_json(LIMITES.estado(cuenta))
            return

        if parsed.path == "/api/feedback":
            positiva = bool(data.get("positiva", True))
            ALEX.retroalimentacion(positiva)
            self._send_json({"ok": True, "stats": ALEX.resumen_memoria()})
            return

        if parsed.path == "/api/borrar_memoria":
            ALEX.borrar_memoria()
            self._send_json({"ok": True, "stats": ALEX.resumen_memoria()})
            return

        if parsed.path == "/api/resembrar":
            n = ALEX.resembrar_conocimiento()
            self._send_json({"ok": True, "temas_base": n, "stats": ALEX.resumen_memoria()})
            return

        self._send_json({"error": "ruta no encontrada"}, status=404)


def main():
    port = int(os.environ.get("PORT", PORT))
    server = HTTPServer(("0.0.0.0", port), AlexHandler)
    print("=" * 55)
    print(f"  Alex {VERSION}  ->  http://0.0.0.0:{port}")
    print(f"  Backend        ->  {ALEX.backend}")
    print(f"  Traductor      ->  {ALEX.traductor.motor}")
    print(f"  Vision         ->  {ALEX.vision.disponible}")
    print(f"  Admin premium  ->  {'ON' if ADMIN_KEY else 'OFF (pon ALEX_ADMIN_KEY)'}")
    print(f"  Datos          ->  {ALEX.directorio_datos}")
    print("  Ctrl+C para detener")
    print("=" * 55)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor detenido.")
        server.server_close()


if __name__ == "__main__":
    main()
