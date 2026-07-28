# -*- coding: utf-8 -*-
"""Servidor web Alex 2.0 (Render + cuotas por cuenta)."""

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
        raw = self.rfile.read(length)
        try:
            return json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError:
            return {}

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, X-Alex-Account")
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
        if parsed.path in ("/", ""):
            self.path = "/index.html"
        return super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        data = self._read_json()
        cuenta = (
            data.get("cuenta_id")
            or self.headers.get("X-Alex-Account")
            or "guest"
        )

        if parsed.path == "/api/chat":
            mensaje = (data.get("mensaje") or "").strip()
            if not mensaje:
                self._send_json({"respuesta": "Puedes escribir algo?", "version": VERSION})
                return

            cuota = LIMITES.consumir(cuenta)
            if not cuota.get("permitido", True):
                self._send_json({
                    "error": "limite",
                    "respuesta": (
                        f"Has alcanzado el limite de mensajes "
                        f"({cuota.get('limite')} cada 12h) para la cuenta "
                        f"'{cuota.get('tier')}'. Crea cuenta (50/12h) o Premium (ilimitado)."
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

        if parsed.path == "/api/registro":
            st = LIMITES.registrar(
                cuenta,
                data.get("email", ""),
                data.get("password", ""),
                tier=data.get("tier", "normal"),
            )
            self._send_json(st)
            return

        if parsed.path == "/api/login":
            st = LIMITES.login(cuenta, data.get("email", ""), data.get("password", ""))
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
