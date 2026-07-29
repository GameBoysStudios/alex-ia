# -*- coding: utf-8 -*-
"""
Busqueda de lugares para Alex.

1) OpenStreetMap Nominatim (gratis, sin clave) — por defecto
2) Google Places API (si hay GOOGLE_MAPS_API_KEY o GOOGLE_PLACES_API_KEY)

Tambien genera enlaces a Google Maps para abrir en el movil/navegador.
"""

import os
import re
from urllib.parse import quote_plus

try:
    import requests
    REQUESTS_OK = True
except ImportError:
    REQUESTS_OK = False


def _maps_url(nombre: str = "", lat=None, lon=None, query: str = "") -> str:
    if lat is not None and lon is not None:
        return f"https://www.google.com/maps/search/?api=1&query={lat},{lon}"
    q = query or nombre or ""
    return f"https://www.google.com/maps/search/?api=1&query={quote_plus(q)}"


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
            "Accept-Language": "es",
        }

    def buscar(self, consulta: str, max_resultados: int = 5, cerca_de: str = "") -> list:
        """Devuelve lista de dicts: nombre, direccion, lat, lon, tipo, url_maps, origen."""
        consulta = (consulta or "").strip()
        if not self.disponible or not consulta:
            return []

        q = consulta
        if cerca_de:
            q = f"{consulta} {cerca_de}".strip()

        resultados = []
        if self.google_key:
            resultados = self._google_places(q, max_resultados=max_resultados)
        if not resultados:
            resultados = self._nominatim(q, max_resultados=max_resultados)
        return resultados

    def _nominatim(self, consulta: str, max_resultados: int = 5) -> list:
        try:
            url = "https://nominatim.openstreetmap.org/search"
            params = {
                "q": consulta,
                "format": "json",
                "addressdetails": 1,
                "limit": max_resultados,
                "accept-language": "es",
            }
            r = requests.get(
                url, params=params, headers=self._headers, timeout=self.timeout
            )
            if r.status_code != 200:
                return []
            data = r.json() or []
            out = []
            for item in data[:max_resultados]:
                nombre = item.get("display_name") or item.get("name") or consulta
                lat = item.get("lat")
                lon = item.get("lon")
                tipo = item.get("type") or item.get("class") or "lugar"
                try:
                    lat_f = float(lat) if lat is not None else None
                    lon_f = float(lon) if lon is not None else None
                except (TypeError, ValueError):
                    lat_f = lon_f = None
                # Direccion corta: primeras partes del display_name
                partes = [p.strip() for p in str(nombre).split(",")]
                corto = ", ".join(partes[:4]) if partes else nombre
                out.append({
                    "nombre": partes[0] if partes else nombre,
                    "direccion": corto,
                    "lat": lat_f,
                    "lon": lon_f,
                    "tipo": tipo,
                    "url_maps": _maps_url(nombre=corto, lat=lat_f, lon=lon_f, query=corto),
                    "origen": "openstreetmap",
                })
            return out
        except Exception as e:
            print(f"[Alex] Nominatim error: {e}")
            return []

    def _google_places(self, consulta: str, max_resultados: int = 5) -> list:
        """Places API (Text Search). Requiere clave con Places habilitado."""
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
                    "rating": item.get("rating"),
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
                f"Prueba a ser mas concreto (ciudad + sitio), por ejemplo: "
                f"'museos en Madrid' o 'donde esta la Torre Eiffel'."
            )

        if idioma == "en":
            lineas = [f"Places for '{consulta}' (via {resultados[0].get('origen', 'maps')}):"]
        else:
            origen = resultados[0].get("origen", "mapas")
            etiqueta = "Google Places" if origen == "google_places" else "OpenStreetMap"
            lineas = [f"Lugares para '{consulta}' (via {etiqueta}):"]

        for i, r in enumerate(resultados, 1):
            nombre = r.get("nombre") or "Lugar"
            dir_ = r.get("direccion") or ""
            maps = r.get("url_maps") or ""
            rating = r.get("rating")
            extra = f" · ★ {rating}" if rating is not None else ""
            lineas.append(f"{i}. {nombre}{extra}")
            if dir_ and dir_ != nombre:
                lineas.append(f"   {dir_}")
            if maps:
                lineas.append(f"   Maps: {maps}")

        if idioma != "en":
            lineas.append("")
            lineas.append("Puedes abrir el enlace de Maps en el navegador o en el movil.")
        return "\n".join(lineas)


def parece_consulta_lugar(texto: str) -> bool:
    """Heuristica: el usuario pide sitios, direcciones o mapas."""
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
        r"farmacias?|parques?|playas?|estaciones?|aeropuertos?|tiendas?)\b",
        t,
    ) and re.search(r"\b(en|cerca|de|por)\b", t):
        return True
    if re.search(r"\b(busca|buscar|encuentra|encontrar)\b.*\b(lugar|sitio|sitios|sitios|locales?)\b", t):
        return True
    return False


def extraer_consulta_lugar(texto: str) -> str:
    """Limpia verbos para dejar la query geografica."""
    t = (texto or "").strip()
    t = re.sub(
        r"^(puedes |me puedes |por favor |please )", "", t, flags=re.I
    )
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
