# -*- coding: utf-8 -*-
"""
Busqueda de lugares para Alex con ranking por probabilidad.

1) OpenStreetMap Nominatim (gratis)
2) Google Places (si hay GOOGLE_MAPS_API_KEY)

Mejora consultas (ej. 'puente de Brooklyn' -> tambien 'Brooklyn Bridge')
y ordena resultados por similitud con lo pedido.
"""

import os
import re
from urllib.parse import quote_plus

try:
    import requests
    REQUESTS_OK = True
except ImportError:
    REQUESTS_OK = False

STOP = {
    "el", "la", "los", "las", "de", "del", "un", "una", "y", "en", "al", "a",
    "the", "of", "and", "near", "in", "at", "para", "por", "con",
}

# Traducciones utiles ES -> EN para hitos conocidos / genericos
TRADUCCIONES = [
    (re.compile(r"\bpuente\s+de\s+brooklyn\b", re.I), "Brooklyn Bridge"),
    (re.compile(r"\bpuente\s+brooklyn\b", re.I), "Brooklyn Bridge"),
    (re.compile(r"\bestatua\s+de\s+la\s+libertad\b", re.I), "Statue of Liberty"),
    (re.compile(r"\btorre\s+eiffel\b", re.I), "Eiffel Tower"),
    (re.compile(r"\bgran\s+muralla\b", re.I), "Great Wall of China"),
    (re.compile(r"\bcasas\s+de\s+parlamento\b", re.I), "Houses of Parliament"),
    (re.compile(r"\btorre\s+de\s+londres\b", re.I), "Tower of London"),
    (re.compile(r"\bmuseo\s+del\s+prado\b", re.I), "Museo del Prado Madrid"),
    (re.compile(r"\bsagrada\s+familia\b", re.I), "Sagrada Familia Barcelona"),
]

TIPO_PREFERENCIA = {
    "puente": {"bridge", "yes", "way", "route", "monument", "attraction"},
    "bridge": {"bridge", "yes", "way", "route"},
    "museo": {"museum", "gallery", "attraction"},
    "museum": {"museum", "gallery"},
    "torre": {"tower", "attraction", "monument"},
    "tower": {"tower", "attraction"},
    "parque": {"park", "garden"},
    "park": {"park", "garden"},
    "restaurante": {"restaurant", "cafe", "fast_food"},
    "hotel": {"hotel", "motel", "hostel"},
    "estacion": {"station", "railway", "subway_entrance"},
    "aeropuerto": {"aerodrome", "airport", "terminal"},
    "playa": {"beach"},
    "iglesia": {"church", "cathedral", "chapel"},
    "hospital": {"hospital", "clinic"},
    "farmacia": {"pharmacy"},
}


def _maps_url(nombre: str = "", lat=None, lon=None, query: str = "") -> str:
    if lat is not None and lon is not None:
        return f"https://www.google.com/maps/search/?api=1&query={lat},{lon}"
    q = query or nombre or ""
    return f"https://www.google.com/maps/search/?api=1&query={quote_plus(q)}"


def _tokens(texto: str) -> set:
    toks = re.findall(r"[a-záéíóúñüA-ZÁÉÍÓÚÑÜ0-9]{2,}", (texto or "").lower())
    return {t for t in toks if t not in STOP}


def _variantes_consulta(consulta: str) -> list:
    """Genera varias queries para mejorar el hit de Nominatim."""
    c = (consulta or "").strip()
    if not c:
        return []
    variantes = [c]

    for pat, reemplazo in TRADUCCIONES:
        if pat.search(c):
            variantes.append(reemplazo)

    # puente de X -> X Bridge
    m = re.search(r"\bpuente\s+(?:de\s+)?(.+)$", c, re.I)
    if m:
        resto = m.group(1).strip()
        variantes.append(f"{resto} Bridge")
        variantes.append(f"Bridge {resto}")

    # torre de X -> X Tower
    m = re.search(r"\btorre\s+(?:de\s+)?(.+)$", c, re.I)
    if m:
        resto = m.group(1).strip()
        variantes.append(f"{resto} Tower")

    # museo de/del X
    m = re.search(r"\bmuseo\s+(?:de\s+|del\s+)?(.+)$", c, re.I)
    if m:
        variantes.append(f"{m.group(1).strip()} Museum")

    # quitar articulos para query limpia
    limpia = re.sub(r"\b(el|la|los|las|un|una|the)\b", " ", c, flags=re.I)
    limpia = re.sub(r"\s+", " ", limpia).strip()
    if limpia and limpia.lower() != c.lower():
        variantes.append(limpia)

    # deduplicar preservando orden
    vistos = set()
    out = []
    for v in variantes:
        k = v.lower().strip()
        if k and k not in vistos:
            vistos.add(k)
            out.append(v.strip())
    return out


def _score_lugar(consulta: str, item: dict) -> float:
    """0..1 probabilidad heuristica de que el resultado sea el pedido."""
    q_toks = _tokens(consulta)
    nombre = str(item.get("nombre") or "")
    direccion = str(item.get("direccion") or "")
    tipo = str(item.get("tipo") or "").lower()
    clase = str(item.get("clase") or "").lower()
    blob = f"{nombre} {direccion} {tipo} {clase}".lower()
    r_toks = _tokens(blob)

    if not q_toks:
        return 0.2

    inter = q_toks & r_toks
    solape = len(inter) / max(len(q_toks), 1)

    # Bonus si el nombre corto contiene casi toda la query
    nombre_low = nombre.lower()
    hits_nombre = sum(1 for t in q_toks if t in nombre_low)
    bonus_nombre = hits_nombre / max(len(q_toks), 1) * 0.35

    # Preferir tipo coherente (puente -> bridge)
    bonus_tipo = 0.0
    for clave, tipos_ok in TIPO_PREFERENCIA.items():
        if clave in q_toks:
            if tipo in tipos_ok or clase in tipos_ok or any(t in blob for t in tipos_ok):
                bonus_tipo = 0.25
            else:
                # penalizar si pides puente y sale cafe/escuela
                if tipo in {"cafe", "school", "restaurant", "yes"} and clave in ("puente", "bridge"):
                    # 'yes' en OSM a veces es generico; no penalizar fuerte si nombre encaja
                    if "bridge" not in blob and "puente" not in blob:
                        bonus_tipo = -0.35
            break

    # Penalizar ruido tipo "El Puente Academy" cuando buscas el puente famoso
    if "puente" in q_toks or "bridge" in q_toks:
        if re.search(r"\b(academy|school|cafe|community|garden|leaders|justice)\b", blob):
            if "bridge" not in blob:
                bonus_tipo -= 0.4

    # Importancia OSM (si viene)
    imp = item.get("importancia")
    try:
        bonus_imp = min(float(imp or 0), 1.0) * 0.15
    except (TypeError, ValueError):
        bonus_imp = 0.0

    score = solape * 0.45 + bonus_nombre + bonus_tipo + bonus_imp + 0.05
    return round(min(max(score, 0.0), 1.0), 3)


class BuscadorMapas:
    def __init__(self, timeout: int = 10):
        self.timeout = timeout
        self.disponible = REQUESTS_OK
        self.google_key = (
            os.environ.get("GOOGLE_MAPS_API_KEY")
            or os.environ.get("GOOGLE_PLACES_API_KEY")
            or ""
        ).strip()
        self.motor = "google_places" if self.google_key else "nominatim"
        self._headers = {
            "User-Agent": "AlexLocalAI/2.0 (GameBoysStudios; contact: gameboystudio25@gmail.com)",
            "Accept-Language": "es,en",
        }

    def buscar(self, consulta: str, max_resultados: int = 5, cerca_de: str = "") -> list:
        consulta = (consulta or "").strip()
        if not self.disponible or not consulta:
            return []

        base = f"{consulta} {cerca_de}".strip() if cerca_de else consulta
        variantes = _variantes_consulta(base)

        brutos = []
        if self.google_key:
            for v in variantes[:3]:
                brutos.extend(self._google_places(v, max_resultados=max_resultados))
                if len(brutos) >= max_resultados * 2:
                    break

        if len(brutos) < 2:
            for v in variantes[:4]:
                brutos.extend(self._nominatim(v, max_resultados=max_resultados + 2))
                if len(brutos) >= max_resultados * 3:
                    break

        # Deduplicar por nombre+coords aprox
        vistos = set()
        unicos = []
        for r in brutos:
            key = (
                (r.get("nombre") or "").lower()[:40],
                round(float(r["lat"]), 4) if r.get("lat") is not None else 0,
                round(float(r["lon"]), 4) if r.get("lon") is not None else 0,
            )
            if key in vistos:
                continue
            vistos.add(key)
            r["probabilidad"] = _score_lugar(base, r)
            unicos.append(r)

        unicos.sort(key=lambda x: x.get("probabilidad", 0), reverse=True)
        return unicos[:max_resultados]

    def _nominatim(self, consulta: str, max_resultados: int = 5) -> list:
        try:
            url = "https://nominatim.openstreetmap.org/search"
            params = {
                "q": consulta,
                "format": "json",
                "addressdetails": 1,
                "limit": max_resultados,
                "accept-language": "es,en",
            }
            r = requests.get(
                url, params=params, headers=self._headers, timeout=self.timeout
            )
            if r.status_code != 200:
                return []
            data = r.json() or []
            out = []
            for item in data:
                display = item.get("display_name") or item.get("name") or consulta
                lat = item.get("lat")
                lon = item.get("lon")
                tipo = item.get("type") or "lugar"
                clase = item.get("class") or ""
                try:
                    lat_f = float(lat) if lat is not None else None
                    lon_f = float(lon) if lon is not None else None
                except (TypeError, ValueError):
                    lat_f = lon_f = None
                partes = [p.strip() for p in str(display).split(",")]
                corto = ", ".join(partes[:5]) if partes else display
                nombre_corto = item.get("name") or (partes[0] if partes else display)
                out.append({
                    "nombre": nombre_corto,
                    "direccion": corto,
                    "lat": lat_f,
                    "lon": lon_f,
                    "tipo": tipo,
                    "clase": clase,
                    "importancia": item.get("importance"),
                    "url_maps": _maps_url(
                        nombre=nombre_corto, lat=lat_f, lon=lon_f, query=corto
                    ),
                    "origen": "openstreetmap",
                })
            return out
        except Exception as e:
            print(f"[Alex] Nominatim error: {e}")
            return []

    def _google_places(self, consulta: str, max_resultados: int = 5) -> list:
        try:
            url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
            params = {
                "query": consulta,
                "key": self.google_key,
                "language": "es",
            }
            r = requests.get(url, params=params, timeout=self.timeout)
            if r.status_code != 200:
                return []
            data = r.json() or {}
            status = data.get("status")
            if status not in ("OK", "ZERO_RESULTS"):
                print(f"[Alex] Google Places status: {status} {data.get('error_message', '')}")
                return []
            out = []
            for item in (data.get("results") or [])[:max_resultados]:
                nombre = item.get("name") or consulta
                direccion = item.get("formatted_address") or ""
                loc = (item.get("geometry") or {}).get("location") or {}
                lat = loc.get("lat")
                lon = loc.get("lng")
                tipos = item.get("types") or []
                tipo = tipos[0] if tipos else "lugar"
                place_id = item.get("place_id") or ""
                if place_id:
                    maps = f"https://www.google.com/maps/place/?q=place_id:{place_id}"
                else:
                    maps = _maps_url(nombre=nombre, lat=lat, lon=lon, query=f"{nombre} {direccion}")
                out.append({
                    "nombre": nombre,
                    "direccion": direccion,
                    "lat": lat,
                    "lon": lon,
                    "tipo": tipo,
                    "clase": ",".join(tipos[:3]),
                    "rating": item.get("rating"),
                    "importancia": (item.get("rating") or 0) / 5.0 if item.get("rating") else 0.3,
                    "url_maps": maps,
                    "origen": "google_places",
                })
            return out
        except Exception as e:
            print(f"[Alex] Google Places error: {e}")
            return []

    def formatear_respuesta(self, consulta: str, resultados: list, idioma: str = "es") -> str:
        if not resultados:
            if idioma == "en":
                return (
                    f"I could not find places for '{consulta}'. "
                    f"Try a more specific query (city + place)."
                )
            return (
                f"No he encontrado lugares para '{consulta}'. "
                f"Prueba a ser mas concreto, por ejemplo: 'Brooklyn Bridge' o 'museos en Madrid'."
            )

        mejor = resultados[0]
        p = mejor.get("probabilidad")
        pct = int(round((p or 0) * 100))

        if idioma == "en":
            lineas = [
                f"Best match for '{consulta}' (~{pct}% confidence):",
                f"→ {mejor.get('nombre')}",
            ]
            if mejor.get("direccion"):
                lineas.append(f"  {mejor['direccion']}")
            if mejor.get("url_maps"):
                lineas.append(f"  Maps: {mejor['url_maps']}")
            if len(resultados) > 1:
                lineas.append("")
                lineas.append("Other candidates:")
                for i, r in enumerate(resultados[1:], 2):
                    pr = int(round((r.get("probabilidad") or 0) * 100))
                    lineas.append(f"{i}. {r.get('nombre')} (~{pr}%)")
                    if r.get("url_maps"):
                        lineas.append(f"   {r['url_maps']}")
            return "\n".join(lineas)

        origen = mejor.get("origen", "mapas")
        etiqueta = "Google Places" if origen == "google_places" else "OpenStreetMap"
        lineas = [
            f"Lo mas probable para '{consulta}' (confianza ~{pct}%, via {etiqueta}):",
            f"→ {mejor.get('nombre')}",
        ]
        if mejor.get("direccion") and mejor.get("direccion") != mejor.get("nombre"):
            lineas.append(f"  {mejor['direccion']}")
        if mejor.get("url_maps"):
            lineas.append(f"  Maps: {mejor['url_maps']}")

        if len(resultados) > 1:
            lineas.append("")
            lineas.append("Otras opciones (por probabilidad):")
            for i, r in enumerate(resultados[1:], 2):
                pr = int(round((r.get("probabilidad") or 0) * 100))
                lineas.append(f"{i}. {r.get('nombre')} (~{pr}%)")
                if r.get("direccion") and r.get("direccion") != r.get("nombre"):
                    lineas.append(f"   {r['direccion']}")
                if r.get("url_maps"):
                    lineas.append(f"   Maps: {r['url_maps']}")

        lineas.append("")
        lineas.append("Abre el enlace de Maps en el movil o el navegador si quieres ir.")
        return "\n".join(lineas)


def parece_consulta_lugar(texto: str) -> bool:
    t = (texto or "").strip().lower()
    if not t:
        return False
    if re.search(
        r"\b(donde esta|dónde está|donde queda|dónde queda|ubicacion|ubicación|"
        r"direccion de|dirección de|como llegar|cómo llegar|cerca de|"
        r"en el mapa|google maps|mapa de|localizar|localiza)\b",
        t,
    ):
        return True
    if re.search(
        r"\b(restaurantes?|cafeter[ií]as?|hoteles?|museos?|hospitales?|"
        r"farmacias?|parques?|playas?|estaciones?|aeropuertos?|tiendas?|"
        r"puente|torre|plaza|catedral)\b",
        t,
    ) and re.search(r"\b(en|cerca|de|del|por)\b", t):
        return True
    if re.search(r"\b(busca|buscar|encuentra|encontrar)\b.*\b(lugar|sitio|sitios|locales?)\b", t):
        return True
    # "el puente de Brooklyn" solo
    if re.search(r"\b(puente|torre|museo|estatua)\s+(de\s+|del\s+)?\w+", t):
        return True
    return False


def extraer_consulta_lugar(texto: str) -> str:
    t = (texto or "").strip()
    t = re.sub(r"^(puedes |me puedes |por favor |please )", "", t, flags=re.I)
    t = re.sub(
        r"^(busca|buscar|encuentra|encontrar|localiza|localizar|dime|digame|dónde está|donde esta|"
        r"dónde queda|donde queda|como llegar a|cómo llegar a|ubicación de|ubicacion de|"
        r"dirección de|direccion de)\s+",
        "",
        t,
        flags=re.I,
    )
    t = re.sub(r"\ben el mapa\b", "", t, flags=re.I)
    t = re.sub(r"\bgoogle maps\b", "", t, flags=re.I)
    return t.strip(" ?.!,;") or texto.strip()
