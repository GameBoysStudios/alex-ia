# -*- coding: utf-8 -*-
"""Servidor web Alex 2.0 / Pro 2.0 (roles admin, cuotas, Firebase)."""

import json
import os
import sys
import traceback
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from alex import Alex
from alex.pro import AlexPro
from alex.limites import GestorLimites
from alex.roles import GestorRoles, MODELOS
from alex.nucleo import texto_suscripcion

ALEX = Alex()
ALEX_PRO = AlexPro()  # clon por ahora; solo accesible a admin
LIMITES = GestorLimites(ALEX.almacenamiento)
ROLES = GestorRoles(ALEX.almacenamiento)
PORT = 8765
STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
VERSION = "2.0"
ADMIN_KEY = (os.environ.get("ALEX_ADMIN_KEY") or "").strip()


def _motor(modelo: str):
    m = ROLES.normalizar_modelo(modelo)
    if m == "pro":
        return ALEX_PRO, "pro", "Alex Pro 2.0"
    return ALEX, "2.0", "Alex 2.0"


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
        qs = parse_qs(parsed.query or "")

        if parsed.path in ("/api/stats", "/api/memoria"):
            try:
                data = ALEX.resumen_memoria()
            except Exception as e:
                data = {"error": str(e)}
            data["version"] = VERSION
            self._send_json(data)
            return

        if parsed.path == "/api/version":
            cuenta = self.headers.get("X-Alex-Account") or (qs.get("uid") or [""])[0] or "guest"
            admin = ROLES.es_admin(cuenta)
            modelos = ROLES.modelos_disponibles(cuenta)
            self._send_json({
                "version": VERSION,
                "nombre": "Alex 2.0",
                "rol": ROLES.rol_de(cuenta),
                "admin": admin,
                "traductor": getattr(ALEX.traductor, "motor", "?"),
                "vision": getattr(ALEX.vision, "disponible", False),
                "mapas": getattr(ALEX.buscador_mapas, "motor", "?"),
                "versiones": [
                    {
                        "id": m["id"],
                        "nombre": m["nombre"],
                        "activa": m["disponible"],
                        "requiere_admin": m["requiere_admin"],
                        "nota": m.get("descripcion", ""),
                    }
                    for m in modelos
                ],
            })
            return

        if parsed.path == "/api/rol":
            cuenta = self.headers.get("X-Alex-Account") or (qs.get("uid") or [""])[0] or "guest"
            self._send_json({
                "uid": cuenta,
                "rol": ROLES.rol_de(cuenta),
                "admin": ROLES.es_admin(cuenta),
                "modelos": ROLES.modelos_disponibles(cuenta),
            })
            return

        if parsed.path == "/api/cuota":
            cuenta = self.headers.get("X-Alex-Account") or "guest"
            try:
                st = LIMITES.estado(cuenta)
            except Exception as e:
                st = {
                    "tier": "guest", "limite": 10, "usados": 0,
                    "restantes": 10, "permitido": True, "error": str(e),
                }
            st["suscripcion"] = texto_suscripcion(st, "es")
            st["rol"] = ROLES.rol_de(cuenta)
            st["admin"] = ROLES.es_admin(cuenta)
            st["modelos"] = ROLES.modelos_disponibles(cuenta)
            self._send_json(st)
            return

        if parsed.path == "/api/admin/premium":
            if not self._admin_ok({}):
                self._send_json({"ok": False, "error": "admin no autorizado"}, status=401)
                return
            self._send_json(LIMITES.listar_premium())
            return

        if parsed.path == "/api/admin/admins":
            if not self._admin_ok({}):
                self._send_json({"ok": False, "error": "admin no autorizado"}, status=401)
                return
            self._send_json(ROLES.listar_admins())
            return

        if parsed.path in ("/", ""):
            self.path = "/index.html"
        return super().do_GET()

    def _check_cuota(self, data, cuenta):
        try:
            if data.get("firebase_uid") or (cuenta and not str(cuenta).startswith("guest-")):
                uid = data.get("firebase_uid") or cuenta
                LIMITES.vincular_firebase(uid, data.get("email", ""), tier="normal")
                cuenta = uid
            cuota = LIMITES.consumir(cuenta)
            return cuenta, cuota
        except Exception as e:
            print(f"[Alex] Error cuota (se permite el mensaje): {e}")
            return cuenta, {
                "cuenta_id": cuenta,
                "tier": "normal" if cuenta and not str(cuenta).startswith("guest-") else "guest",
                "limite": None,
                "usados": 0,
                "restantes": None,
                "permitido": True,
                "ventana_horas": 12,
                "version": VERSION,
            }

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

            modelo_req = ROLES.normalizar_modelo(
                data.get("modelo") or data.get("version") or "2.0"
            )
            if not ROLES.puede_usar_modelo(cuenta, modelo_req):
                self._send_json({
                    "error": "modelo_restringido",
                    "respuesta": (
                        "Alex Pro 2.0 solo esta disponible para el rol administrador. "
                        "Sigue con Alex 2.0 o pide acceso admin."
                    ),
                    "modelo": "2.0",
                    "rol": ROLES.rol_de(cuenta),
                    "version": VERSION,
                }, status=403)
                return

            motor, modelo_id, modelo_nombre = _motor(modelo_req)

            cuenta, cuota = self._check_cuota(data, cuenta)
            if not cuota.get("permitido", True):
                self._send_json({
                    "error": "limite",
                    "respuesta": (
                        f"Has alcanzado el limite de mensajes "
                        f"({cuota.get('limite')} cada 12h) para el plan "
                        f"'{cuota.get('tier')}'. Inicia sesion en Game Boys "
                        f"(Normal: 50/12h) o activa Premium (ilimitado)."
                    ),
                    "cuota": cuota,
                    "suscripcion": texto_suscripcion(cuota, "es"),
                    "version": VERSION,
                    "modelo": modelo_id,
                }, status=429)
                return

            try:
                respuesta = motor.responder(mensaje, cuota=cuota)
                try:
                    stats = motor.resumen_memoria()
                except Exception:
                    stats = {}
                self._send_json({
                    "respuesta": respuesta,
                    "stats": stats,
                    "cuota": cuota,
                    "suscripcion": texto_suscripcion(cuota, "es"),
                    "version": VERSION,
                    "modelo": modelo_id,
                    "modelo_nombre": modelo_nombre,
                    "rol": ROLES.rol_de(cuenta),
                    "admin": ROLES.es_admin(cuenta),
                })
            except Exception as e:
                print("[Alex] Error en /api/chat:")
                traceback.print_exc()
                self._send_json({
                    "respuesta": (
                        "Se me ha cruzado un cable con ese mensaje. "
                        "Prueba a reformularlo o empezar una nueva conversacion. "
                        f"(detalle tecnico: {type(e).__name__})"
                    ),
                    "cuota": cuota,
                    "suscripcion": texto_suscripcion(cuota, "es"),
                    "version": VERSION,
                    "modelo": modelo_id,
                    "error_tipo": type(e).__name__,
                })
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
                    "descripcion": "Limite de mensajes alcanzado. " + texto_suscripcion(cuota, "es"),
                    "cuota": cuota,
                    "suscripcion": texto_suscripcion(cuota, "es"),
                }, status=429)
                return
            b64 = data.get("imagen") or data.get("image") or ""
            idioma = data.get("idioma") or "es"
            modelo_req = ROLES.normalizar_modelo(data.get("modelo") or "2.0")
            if not ROLES.puede_usar_modelo(cuenta, modelo_req):
                modelo_req = "2.0"
            motor, modelo_id, modelo_nombre = _motor(modelo_req)
            try:
                resultado = motor.vision.analizar_base64(b64, idioma=idioma)
            except Exception as e:
                traceback.print_exc()
                resultado = {"descripcion": f"No pude analizar la imagen ({type(e).__name__})."}
            try:
                desc = resultado.get("descripcion") or ""
                motor.conversacion.agregar_mensaje("usuario", "[imagen]")
                motor.conversacion.agregar_mensaje("alex", desc, {"origen": "vision", "modelo": modelo_id})
                motor.memoria.guardar()
            except Exception:
                pass
            resultado["cuota"] = cuota
            resultado["suscripcion"] = texto_suscripcion(cuota, "es")
            resultado["version"] = VERSION
            resultado["modelo"] = modelo_id
            resultado["modelo_nombre"] = modelo_nombre
            self._send_json(resultado)
            return

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
            st["suscripcion"] = texto_suscripcion(st, "es")
            self._send_json(st)
            return

        if parsed.path in ("/api/admin/set_admin", "/api/admin/admin"):
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
            admin = data.get("admin", True)
            if isinstance(admin, str):
                admin = admin.strip().lower() in ("1", "true", "yes", "si", "sí", "admin")
            st = ROLES.set_admin(
                uid,
                admin=bool(admin),
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
                st["suscripcion"] = texto_suscripcion(st, "es")
                st["rol"] = ROLES.rol_de(uid)
                st["admin"] = ROLES.es_admin(uid)
                st["modelos"] = ROLES.modelos_disponibles(uid)
                self._send_json(st)
                return
            if parsed.path == "/api/registro":
                st = LIMITES.registrar(
                    cuenta, email, data.get("password", ""), tier=data.get("tier", "normal")
                )
            else:
                st = LIMITES.login(cuenta, email, data.get("password", ""))
            st["suscripcion"] = texto_suscripcion(st, "es")
            st["rol"] = ROLES.rol_de(cuenta)
            st["admin"] = ROLES.es_admin(cuenta)
            self._send_json(st)
            return

        if parsed.path == "/api/cuota":
            st = LIMITES.estado(cuenta)
            st["suscripcion"] = texto_suscripcion(st, "es")
            st["rol"] = ROLES.rol_de(cuenta)
            st["admin"] = ROLES.es_admin(cuenta)
            st["modelos"] = ROLES.modelos_disponibles(cuenta)
            self._send_json(st)
            return

        if parsed.path == "/api/feedback":
            positiva = bool(data.get("positiva", True))
            ALEX.retroalimentacion(positiva)
            self._send_json({"ok": True, "stats": ALEX.resumen_memoria()})
            return

        if parsed.path == "/api/borrar_memoria":
            ALEX.borrar_memoria()
            try:
                ALEX_PRO.borrar_memoria()
            except Exception:
                pass
            self._send_json({"ok": True, "stats": ALEX.resumen_memoria()})
            return

        if parsed.path == "/api/resembrar":
            n = ALEX.resembrar_conocimiento()
            try:
                ALEX_PRO.resembrar_conocimiento()
            except Exception:
                pass
            self._send_json({"ok": True, "temas_base": n, "stats": ALEX.resumen_memoria()})
            return

        self._send_json({"error": "ruta no encontrada"}, status=404)


def main():
    port = int(os.environ.get("PORT", PORT))
    server = HTTPServer(("0.0.0.0", port), AlexHandler)
    print("=" * 55)
    print(f"  Alex {VERSION} + Pro 2.0  ->  http://0.0.0.0:{port}")
    print(f"  Backend        ->  {ALEX.backend}")
    print(f"  Traductor      ->  {ALEX.traductor.motor}")
    print(f"  Vision         ->  {ALEX.vision.disponible}")
    print(f"  Admin key      ->  {'ON' if ADMIN_KEY else 'OFF'}")
    print(f"  Admin UIDs env ->  {os.environ.get('ALEX_ADMIN_UIDS') or '(ninguno)'}")
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
