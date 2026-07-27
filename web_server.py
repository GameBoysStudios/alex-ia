# -*- coding: utf-8 -*-
"""
Servidor web local para Alex (solo biblioteca estándar).

Uso:
    python web_server.py

Luego abre http://127.0.0.1:8765 en el navegador.
"""

import json
import os
import sys
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse

# Asegura que el paquete alex sea importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from alex import Alex

# Instancia global de Alex (persiste entre peticiones)
ALEX = Alex()
PORT = 8765
STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")


class AlexHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=STATIC_DIR, **kwargs)

    def log_message(self, format, *args):
        # Log más limpio
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
        if parsed.path == "/api/stats":
            stats = ALEX.estadisticas()
            n_palabras = len(ALEX.memoria.datos.get("diccionario", {}))
            n_temas = len(ALEX.memoria.datos.get("conocimiento", {}))
            n_sin = sum(len(v) for v in ALEX.memoria.datos.get("sinonimos", {}).values()) // 2
            self._send_json({
                "mensajes_totales": stats.get("mensajes_totales", 0),
                "conversaciones_totales": stats.get("conversaciones_totales", 0),
                "palabras": n_palabras,
                "temas": n_temas,
                "sinonimos": n_sin,
            })
            return
        # Servir archivos estáticos (index.html, etc.)
        if parsed.path in ("/", ""):
            self.path = "/index.html"
        return super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        data = self._read_json()

        if parsed.path == "/api/chat":
            mensaje = (data.get("mensaje") or "").strip()
            if not mensaje:
                self._send_json({"respuesta": "¿Puedes escribir algo?"})
                return
            try:
                respuesta = ALEX.responder(mensaje)
            except Exception as e:
                respuesta = f"Error interno: {e}"
            self._send_json({"respuesta": respuesta})
            return

        if parsed.path == "/api/feedback":
            positiva = bool(data.get("positiva", True))
            ALEX.retroalimentacion(positiva)
            self._send_json({"ok": True})
            return

        if parsed.path == "/api/borrar_memoria":
            ALEX.borrar_memoria()
            self._send_json({"ok": True})
            return

        self._send_json({"error": "ruta no encontrada"}, status=404)


def main():
    # Render (y otros PaaS) asignan el puerto con la variable de entorno PORT.
    port = int(os.environ.get("PORT", PORT))
    # 0.0.0.0 permite conexiones externas (necesario en Render).
    server = HTTPServer(("0.0.0.0", port), AlexHandler)
    print("=" * 55)
    print(f"  Alex Web UI  →  http://0.0.0.0:{port}")
    print("  Ctrl+C para detener")
    print("=" * 55)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor detenido.")
        server.server_close()


if __name__ == "__main__":
    main()
