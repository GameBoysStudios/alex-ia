# -*- coding: utf-8 -*-
"""
Analisis casero de imagenes para Alex / Alex Pro.

Sin redes neuronales: colores, brillo, complejidad, orientacion y heurísticas
de escena (documento, paisaje, foto nocturna, etc.).
"""

import base64
import io
from collections import Counter

try:
    from PIL import Image, ImageFilter, ImageStat
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
    ((210, 180, 140), "beige"),
    ((135, 206, 235), "celeste"),
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
    ((210, 180, 140), "beige"),
    ((135, 206, 235), "sky blue"),
]


def _dist(a, b):
    return sum((x - y) ** 2 for x, y in zip(a, b))


def _nombre_color(rgb, idioma="es"):
    tabla = NOMBRES_COLOR_EN if idioma == "en" else NOMBRES_COLOR_ES
    mejor = min(tabla, key=lambda t: _dist(rgb, t[0]))
    return mejor[1]


def _brillo(rgb):
    return 0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2]


def _saturacion(rgb):
    r, g, b = [x / 255.0 for x in rgb]
    mx, mn = max(r, g, b), min(r, g, b)
    if mx < 1e-6:
        return 0.0
    return (mx - mn) / mx


def _parece_piel(rgb):
    r, g, b = rgb
    if r < 60 or g < 40 or b < 20:
        return False
    if r < g or r < b:
        return False
    if abs(r - g) < 15:
        return False
    return 95 < r < 255 and 40 < g < 200 and 20 < b < 170


class AnalizadorImagen:
    def __init__(self, modo_pro: bool = False):
        self.disponible = PIL_OK
        self.modo_pro = modo_pro

    def analizar_bytes(self, data: bytes, idioma: str = "es") -> dict:
        if not PIL_OK:
            return {
                "ok": False,
                "error": "Pillow no instalado",
                "descripcion": "No puedo analizar imagenes aun (falta Pillow).",
            }
        try:
            img = Image.open(io.BytesIO(data))
            formato = (img.format or "?").upper()
            img_rgb = img.convert("RGB")
            w, h = img_rgb.size

            muestra = img_rgb.copy()
            muestra.thumbnail((120, 120))
            pixels = list(muestra.getdata())
            n = max(len(pixels), 1)

            buckets = Counter()
            for r, g, b in pixels:
                key = (r // 32 * 32 + 16, g // 32 * 32 + 16, b // 32 * 32 + 16)
                buckets[key] += 1
            top = [c for c, _ in buckets.most_common(6)]
            nombres = []
            for c in top:
                nomb = _nombre_color(c, idioma)
                if nomb not in nombres:
                    nombres.append(nomb)

            brillos = [_brillo(p) for p in pixels]
            brillo_medio = sum(brillos) / n
            sat_media = sum(_saturacion(p) for p in pixels) / n
            piel = sum(1 for p in pixels if _parece_piel(p)) / n

            # Complejidad: varianza de brillo + bordes aproximados
            media_b = brillo_medio
            var_b = sum((b - media_b) ** 2 for b in brillos) / n
            try:
                gris = muestra.convert("L")
                edges = gris.filter(ImageFilter.FIND_EDGES)
                edge_stat = ImageStat.Stat(edges)
                edge_mean = edge_stat.mean[0] if edge_stat.mean else 0
            except Exception:
                edge_mean = 0

            if brillo_medio < 55:
                ambiente = "muy oscura" if idioma != "en" else "very dark"
            elif brillo_medio < 100:
                ambiente = "oscura" if idioma != "en" else "dark"
            elif brillo_medio < 160:
                ambiente = "media" if idioma != "en" else "medium brightness"
            elif brillo_medio < 210:
                ambiente = "clara" if idioma != "en" else "bright"
            else:
                ambiente = "muy clara / sobreexpuesta" if idioma != "en" else "very bright"

            if w > h * 1.25:
                orient = "horizontal / apaisada" if idioma != "en" else "landscape"
            elif h > w * 1.25:
                orient = "vertical / retrato" if idioma != "en" else "portrait"
            else:
                orient = "cuadrada" if idioma != "en" else "square"

            ratio = round(w / max(h, 1), 2)
            colores_txt = ", ".join(nombres[:5]) or ("indefinidos" if idioma != "en" else "unknown")

            escena, confianza = self._inferir_escena(
                brillo_medio=brillo_medio,
                sat_media=sat_media,
                var_b=var_b,
                edge_mean=edge_mean,
                piel=piel,
                nombres=nombres,
                orient=orient,
                idioma=idioma,
            )

            if idioma == "en":
                desc = self._desc_en(
                    w, h, orient, ratio, ambiente, brillo_medio, colores_txt,
                    escena, confianza, formato, sat_media, edge_mean, piel,
                )
            else:
                desc = self._desc_es(
                    w, h, orient, ratio, ambiente, brillo_medio, colores_txt,
                    escena, confianza, formato, sat_media, edge_mean, piel,
                )

            return {
                "ok": True,
                "ancho": w,
                "alto": h,
                "formato": formato,
                "orientacion": orient,
                "ratio": ratio,
                "brillo": round(brillo_medio, 1),
                "saturacion": round(sat_media, 3),
                "complejidad": round(edge_mean, 1),
                "ambiente": ambiente,
                "colores": nombres[:6],
                "escena": escena,
                "confianza_escena": confianza,
                "posible_persona": piel > 0.12,
                "descripcion": desc,
                "modo": "pro" if self.modo_pro else "standard",
            }
        except Exception as e:
            return {
                "ok": False,
                "error": str(e),
                "descripcion": f"No pude leer la imagen: {e}",
            }

    def _inferir_escena(self, brillo_medio, sat_media, var_b, edge_mean, piel, nombres, orient, idioma):
        """Heuristica de que podria ser la imagen (no es IA de objetos)."""
        nombres_l = [n.lower() for n in nombres]
        tiene = lambda *xs: any(x in " ".join(nombres_l) for x in xs)

        candidatos = []

        # Documento / captura de texto: mucha claridad, bajo color, muchos bordes
        if brillo_medio > 170 and sat_media < 0.18 and edge_mean > 18:
            candidatos.append((("documento o captura de texto" if idioma != "en" else "document or text capture"), 0.72))
        if brillo_medio > 200 and sat_media < 0.12:
            candidatos.append((("fondo blanco / papel" if idioma != "en" else "white background / paper"), 0.55))

        # Paisaje cielo / naturaleza
        if tiene("azul", "celeste", "sky") and tiene("verde", "green"):
            candidatos.append((("paisaje o exterior" if idioma != "en" else "landscape / outdoors"), 0.65))
        if tiene("verde", "green") and sat_media > 0.25 and brillo_medio > 90:
            candidatos.append((("vegetacion / naturaleza" if idioma != "en" else "vegetation / nature"), 0.55))

        # Atardecer / tonos calidos
        if tiene("naranja", "orange", "rojo", "red", "amarillo", "yellow", "dorado", "gold") and brillo_medio > 80:
            if sat_media > 0.3:
                candidatos.append((("escena calida (atardecer o luces)" if idioma != "en" else "warm scene (sunset or lights)"), 0.5))

        # Nocturna
        if brillo_medio < 70 and edge_mean < 25:
            candidatos.append((("foto nocturna o interior oscuro" if idioma != "en" else "night photo or dark interior"), 0.6))

        # Persona / selfie
        if piel > 0.18:
            candidatos.append((("posible persona o selfie" if idioma != "en" else "possible person or selfie"), min(0.55 + piel, 0.8)))
        elif piel > 0.08:
            candidatos.append((("puede haber tono de piel" if idioma != "en" else "possible skin tone"), 0.4))

        # UI / interfaz: grises + azules + bordes
        if tiene("gris", "gray", "azul", "blue") and edge_mean > 22 and sat_media < 0.35:
            candidatos.append((("posible interfaz o captura de pantalla" if idioma != "en" else "possible UI / screenshot"), 0.48))

        # Producto / objeto centrado: orientacion vertical o cuadrada, saturacion media
        if orient.startswith("vertical") or orient.startswith("portrait") or orient.startswith("cuadrada") or orient.startswith("square"):
            if 0.15 < sat_media < 0.55 and 70 < brillo_medio < 200 and edge_mean > 12:
                candidatos.append((("objeto o producto en primer plano" if idioma != "en" else "object or product close-up"), 0.42))

        # Abstracto / simple
        if var_b < 400 and edge_mean < 10:
            candidatos.append((("imagen simple o fondo uniforme" if idioma != "en" else "simple image or flat background"), 0.5))

        if not candidatos:
            return (
                "imagen general (sin patron claro)" if idioma != "en" else "general image (no clear pattern)",
                0.25,
            )

        candidatos.sort(key=lambda x: x[1], reverse=True)
        return candidatos[0]

    def _desc_es(self, w, h, orient, ratio, ambiente, brillo, colores, escena, conf, formato, sat, edges, piel):
        pct = int(round(conf * 100))
        partes = [
            f"Analisis de imagen{' (Pro)' if self.modo_pro else ''}:",
            f"Parece {escena} (confianza ~{pct}%).",
            f"Formato {formato}, {w}×{h} px ({orient}, ratio {ratio}).",
            f"Brillo {ambiente} (~{int(brillo)}/255), saturacion media {sat:.2f}.",
            f"Colores dominantes: {colores}.",
        ]
        if piel > 0.12:
            partes.append("Detecto zonas con tono similar a piel (posible persona).")
        if edges > 25:
            partes.append("Hay bastante detalle / bordes (imagen compleja).")
        elif edges < 8:
            partes.append("Pocos bordes: imagen lisa o desenfocada.")
        if self.modo_pro:
            partes.append(
                "Nota Pro: es vision casera (colores + estadisticas), no una red neuronal. "
                "Sirve para orientarte sobre el tipo de foto, no para leer texto ni nombrar marcas exactas."
            )
        else:
            partes.append("Analisis estructural basico (sin red neuronal).")
        return " ".join(partes)

    def _desc_en(self, w, h, orient, ratio, ambiente, brillo, colores, escena, conf, formato, sat, edges, piel):
        pct = int(round(conf * 100))
        parts = [
            f"Image analysis{' (Pro)' if self.modo_pro else ''}:",
            f"Looks like {escena} (~{pct}% confidence).",
            f"Format {formato}, {w}×{h}px ({orient}, ratio {ratio}).",
            f"Brightness {ambiente} (~{int(brillo)}/255), avg saturation {sat:.2f}.",
            f"Dominant colors: {colores}.",
        ]
        if piel > 0.12:
            parts.append("Skin-like tones detected (possible person).")
        if edges > 25:
            parts.append("High edge detail (complex image).")
        if self.modo_pro:
            parts.append("Pro note: homemade vision (colors + stats), not a neural net.")
        return " ".join(parts)

    def analizar_base64(self, b64: str, idioma: str = "es") -> dict:
        if not b64:
            return {"ok": False, "descripcion": "No recibí datos de imagen."}
        if "," in b64 and b64.strip().startswith("data:"):
            b64 = b64.split(",", 1)[1]
        try:
            raw = base64.b64decode(b64)
        except Exception as e:
            return {"ok": False, "descripcion": f"Base64 invalido: {e}"}
        if len(raw) > 5 * 1024 * 1024:
            return {"ok": False, "descripcion": "Imagen demasiado grande (max 5 MB)."}
        return self.analizar_bytes(raw, idioma=idioma)
