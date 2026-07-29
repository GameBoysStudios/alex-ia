# -*- coding: utf-8 -*-
"""
Consulta de definiciones en la RAE (Diccionario de la lengua española).

Fuentes (gratis, sin tarjeta):
  1) https://rae-api.com/api/words/{palabra}  (anonimo ~100/dia)
  2) Fallback: scrape ligero de https://dle.rae.es/{palabra}

Uso en Alex Pro: si no conoce un termino, lo busca, lo registra en memoria
y lo usa para explicar.
"""

import re
from urllib.parse import quote

try:
    import requests
    REQUESTS_OK = True
except ImportError:
    REQUESTS_OK = False

UA = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; AlexPro/2.0; +https://gameboysstudios.github.io)"
    ),
    "Accept": "application/json, text/html;q=0.9,*/*;q=0.8",
}


def _limpiar_html(s: str) -> str:
    s = re.sub(r"<[^>]+>", " ", s or "")
    s = re.sub(r"\s+", " ", s).strip()
    return s


class DiccionarioRAE:
    def __init__(self, timeout: int = 12):
        self.timeout = timeout
        self.disponible = REQUESTS_OK
        self.cache = {}  # palabra -> dict resultado

    def definir(self, palabra: str) -> dict:
        """
        Devuelve:
          {
            ok, palabra, definiciones: [str, ...],
            resumen: str, fuente: str, etimologia: str
          }
        """
        palabra = (palabra or "").strip().lower()
        palabra = re.sub(r"[^a-záéíóúñü]", "", palabra)
        if not palabra or len(palabra) < 2:
            return {"ok": False, "error": "palabra_vacia"}
        if palabra in self.cache:
            return self.cache[palabra]
        if not self.disponible:
            return {"ok": False, "error": "sin_requests"}

        r = self._via_rae_api(palabra)
        if not r.get("ok"):
            r = self._via_dle_html(palabra)
        if r.get("ok"):
            self.cache[palabra] = r
        return r

    def _via_rae_api(self, palabra: str) -> dict:
        try:
            url = f"https://rae-api.com/api/words/{quote(palabra)}"
            resp = requests.get(url, headers=UA, timeout=self.timeout)
            if resp.status_code == 404:
                return {"ok": False, "error": "no_encontrada"}
            if resp.status_code != 200:
                return {"ok": False, "error": f"http_{resp.status_code}"}
            data = resp.json() if resp.content else {}

            # Formatos posibles segun version de la API
            defs = []
            etim = ""
            lema = data.get("word") or data.get("lema") or palabra

            # Estructura tipo { meanings: [ { senses: [...] } ] }
            meanings = data.get("meanings") or data.get("definitions") or []
            if isinstance(meanings, list):
                for m in meanings:
                    if isinstance(m, str):
                        defs.append(_limpiar_html(m))
                        continue
                    if not isinstance(m, dict):
                        continue
                    if m.get("etymology") and not etim:
                        etim = _limpiar_html(str(m.get("etymology")))
                    senses = m.get("senses") or m.get("definitions") or []
                    if isinstance(senses, str):
                        defs.append(_limpiar_html(senses))
                    for s in senses if isinstance(senses, list) else []:
                        if isinstance(s, str):
                            defs.append(_limpiar_html(s))
                        elif isinstance(s, dict):
                            t = s.get("raw") or s.get("definition") or s.get("sense") or s.get("text") or ""
                            t = _limpiar_html(str(t))
                            if t:
                                defs.append(t)

            # Otra forma: data['data']['definitions']
            if not defs and isinstance(data.get("data"), dict):
                for d in data["data"].get("definitions") or []:
                    if isinstance(d, str):
                        defs.append(_limpiar_html(d))
                    elif isinstance(d, dict):
                        t = _limpiar_html(str(d.get("definition") or d.get("text") or ""))
                        if t:
                            defs.append(t)

            # Lista plana 'entries'
            if not defs:
                for e in data.get("entries") or []:
                    if isinstance(e, dict):
                        for d in e.get("definitions") or []:
                            t = _limpiar_html(str(d if isinstance(d, str) else d.get("definition", "")))
                            if t:
                                defs.append(t)

            defs = [d for d in defs if d and len(d) > 3][:8]
            if not defs:
                return {"ok": False, "error": "sin_definiciones"}

            resumen = defs[0]
            if len(resumen) > 320:
                resumen = resumen[:317] + "..."

            return {
                "ok": True,
                "palabra": lema,
                "definiciones": defs,
                "resumen": resumen,
                "etimologia": etim,
                "fuente": "rae-api.com",
            }
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def _via_dle_html(self, palabra: str) -> dict:
        """Fallback: parse basico de dle.rae.es."""
        try:
            url = f"https://dle.rae.es/{quote(palabra)}"
            resp = requests.get(url, headers=UA, timeout=self.timeout)
            if resp.status_code != 200:
                return {"ok": False, "error": f"dle_{resp.status_code}"}
            html = resp.text or ""

            # Avisos de no encontrado
            if re.search(r"no est[aá] en el Diccionario", html, re.I):
                return {"ok": False, "error": "no_encontrada"}

            defs = []
            # Clases tipicas: .j (acepcion), p.j, etc.
            for m in re.finditer(
                r"<(?:p|div)[^>]*class=\"[^"]*\bj\b[^"]*\"[^>]*>(.*?)</(?:p|div)>",
                html,
                re.I | re.S,
            ):
                t = _limpiar_html(m.group(1))
                # quitar numeros de acepcion al inicio
                t = re.sub(r"^\d+\.\s*", "", t)
                if t and len(t) > 8:
                    defs.append(t)
                if len(defs) >= 6:
                    break

            if not defs:
                # meta description a veces trae algo
                m = re.search(
                    r'<meta\s+name="description"\s+content="([^"]+)"',
                    html,
                    re.I,
                )
                if m:
                    t = _limpiar_html(m.group(1))
                    if t and palabra in t.lower():
                        defs.append(t)

            if not defs:
                return {"ok": False, "error": "sin_definiciones_html"}

            resumen = defs[0]
            if len(resumen) > 320:
                resumen = resumen[:317] + "..."

            return {
                "ok": True,
                "palabra": palabra,
                "definiciones": defs,
                "resumen": resumen,
                "etimologia": "",
                "fuente": "dle.rae.es",
            }
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def formatear(self, resultado: dict, idioma: str = "es") -> str:
        if not resultado or not resultado.get("ok"):
            return ""
        p = resultado.get("palabra", "")
        defs = resultado.get("definiciones") or []
        fuente = resultado.get("fuente", "RAE")
        if idioma == "en":
            lineas = [f"RAE definition of '{p}' (via {fuente}):"]
        else:
            lineas = [f"Segun la RAE, '{p}' ({fuente}):"]
        for i, d in enumerate(defs[:5], 1):
            lineas.append(f"{i}. {d}")
        if resultado.get("etimologia"):
            lineas.append(f"Etimologia: {resultado['etimologia']}")
        return "\n".join(lineas)
