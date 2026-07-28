# -*- coding: utf-8 -*-
"""Servidor web para Alex (compatible con Render)."""

import json
import os
import sys
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from alex import Alex

ALEX = Alex()
PORT = 8765
STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")


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
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path in ("/api/stats", "/api/memoria"):
            self._send_json(ALEX.resumen_memoria())
            return
        if parsed.path in ("/", ""):
            self.path = "/index.html"
        return super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        data = self._read_json()

        if parsed.path == "/api/chat":
            mensaje = (data.get("mensaje") or "").strip()
            if not mensaje:
                self._send_json({"respuesta": "Puedes escribir algo?"})
                return
            try:
                respuesta = ALEX.responder(mensaje)
                self._send_json({
                    "respuesta": respuesta,
                    "stats": ALEX.resumen_memoria(),
                })
            except Exception as e:
                self._send_json({"respuesta": f"Error interno: {e}"})
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
    print(f"  Alex Web UI  ->  http://0.0.0.0:{port}")
    print(f"  Backend     ->  {ALEX.backend}")
    print(f"  Datos       ->  {ALEX.directorio_datos}")
    print("  Ctrl+C para detener")
    print("=" * 55)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor detenido.")
        server.server_close()


if __name__ == "__main__":
    main()
