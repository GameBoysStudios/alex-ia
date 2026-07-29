# -*- coding: utf-8 -*-
"""
Analisis casero de imagenes para Alex (sin redes neuronales pesadas).

Usa Pillow si esta instalado:
  - tamano, formato, modo
  - brillo medio
  - colores dominantes (muestreo)
  - orientacion / aspect ratio
  - descripcion textual en el idioma pedido
"""

import base64
import io
from collections import Counter

try:
    from PIL import Image
    PIL_OK = True
except ImportError:
    PIL_OK = False

NOMBRES_COLOR_ES = [
    ((0, 0, 0), "negro"),
    ((255, 255, 255), "blanco"),
    ((128, 128, 128), "gris"),
    ((255, 0, 0), "rojo"),
    ((0, 128, 0), "verde"),
    ((0, 0, 255), "azul"),
    ((255, 255, 0), "amarillo"),
    ((255, 165, 0), "naranja"),
    ((128, 0, 128), "morado"),
    ((255, 192, 203), "rosa"),
    ((165, 42, 42), "marron"),
    ((0, 255, 255), "cian"),
    ((0, 0, 128), "azul oscuro"),
    ((144, 238, 144), "verde claro"),
    ((255, 215, 0), "dorado"),
]

NOMBRES_COLOR_EN = [
    ((0, 0, 0), "black"),
    ((255, 255, 255), "white"),
    ((128, 128, 128), "gray"),
    ((255, 0, 0), "red"),
    ((0, 128, 0), "green"),
    ((0, 0, 255), "blue"),
    ((255, 255, 0), "yellow"),
    ((255, 165, 0), "orange"),
    ((128, 0, 128), "purple"),
    ((255, 192, 203), "pink"),
    ((165, 42, 42), "brown"),
    ((0, 255, 255), "cyan"),
    ((0, 0, 128), "dark blue"),
    ((144, 238, 144), "light green"),
    ((255, 215, 0), "gold"),
]


def _dist(a, b):
    return sum((x - y) ** 2 for x, y in zip(a, b))


def _nombre_color(rgb, idioma="es"):
    tabla = NOMBRES_COLOR_EN if idioma == "en" else NOMBRES_COLOR_ES
    mejor = min(tabla, key=lambda t: _dist(rgb, t[0]))
    return mejor[1]


def _brillo(rgb):
    return 0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2]


class AnalizadorImagen:
    def __init__(self):
        self.disponible = PIL_OK

    def analizar_bytes(self, data: bytes, idioma: str = "es") -> dict:
        if not PIL_OK:
            return {
                "ok": False,
                "error": "Pillow no instalado. Anade pillow a requirements.txt",
                "descripcion": "No puedo analizar imagenes aun (falta Pillow).",
            }
        try:
            img = Image.open(io.BytesIO(data))
            img = img.convert("RGB")
            w, h = img.size
            # Reducir para muestrear rapido
            muestra = img.copy()
            muestra.thumbnail((80, 80))
            pixels = list(muestra.getdata())

            # Cuantizar colores a buckets de 32
            buckets = Counter()
            for r, g, b in pixels:
                key = (r // 32 * 32 + 16, g // 32 * 32 + 16, b // 32 * 32 + 16)
                buckets[key] += 1
            top = [c for c, _ in buckets.most_common(5)]
            nombres = [_nombre_color(c, idioma) for c in top]
            # unicos manteniendo orden
            nombres_u = []
            for n in nombres:
                if n not in nombres_u:
                    nombres_u.append(n)

            brillos = [_brillo(p) for p in pixels]
            brillo_medio = sum(brillos) / max(len(brillos), 1)
            if brillo_medio < 60:
                ambiente = "oscura" if idioma != "en" else "dark"
            elif brillo_medio < 140:
                ambiente = "media" if idioma != "en" else "medium brightness"
            else:
                ambiente = "clara" if idioma != "en" else "bright"

            if w > h * 1.2:
                orient = "horizontal / apaisada" if idioma != "en" else "landscape"
            elif h > w * 1.2:
                orient = "vertical / retrato" if idioma != "en" else "portrait"
            else:
                orient = "cuadrada" if idioma != "en" else "square"

            ratio = round(w / max(h, 1), 2)
            colores_txt = ", ".join(nombres_u[:4]) or ("indefinidos" if idioma != "en" else "unknown")

            if idioma == "en":
                desc = (
                    f"I analyzed the image (homemade vision, no neural net). "
                    f"Size: {w}x{h}px ({orient}, ratio {ratio}). "
                    f"Overall brightness: {ambiente} (~{int(brillo_medio)}/255). "
                    f"Dominant colors: {colores_txt}. "
                    f"This is a basic structural analysis, not object recognition."
                )
            else:
                desc = (
                    f"He analizado la imagen de forma casera (sin red neuronal). "
                    f"Tamano: {w}x{h} px ({orient}, ratio {ratio}). "
                    f"Brillo general: {ambiente} (~{int(brillo_medio)}/255). "
                    f"Colores dominantes: {colores_txt}. "
                    f"Es un analisis estructural basico, no reconoce objetos concretos."
                )

            return {
                "ok": True,
                "ancho": w,
                "alto": h,
                "orientacion": orient,
                "ratio": ratio,
                "brillo": round(brillo_medio, 1),
                "ambiente": ambiente,
                "colores": nombres_u[:5],
                "descripcion": desc,
            }
        except Exception as e:
            return {
                "ok": False,
                "error": str(e),
                "descripcion": f"No pude leer la imagen: {e}",
            }

    def analizar_base64(self, b64: str, idioma: str = "es") -> dict:
        if not b64:
            return {"ok": False, "descripcion": "No recibí datos de imagen."}
        # quitar prefijo data:image/...;base64,
        if "," in b64 and b64.strip().startswith("data:"):
            b64 = b64.split(",", 1)[1]
        try:
            raw = base64.b64decode(b64)
        except Exception as e:
            return {"ok": False, "descripcion": f"Base64 invalido: {e}"}
        # Limite ~4 MB
        if len(raw) > 4 * 1024 * 1024:
            return {"ok": False, "descripcion": "Imagen demasiado grande (max 4 MB)."}
        return self.analizar_bytes(raw, idioma=idioma)
