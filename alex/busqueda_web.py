# -*- coding: utf-8 -*-
"""
Modulo de Busqueda Web para Alex.

Fuentes (sin API keys de LLM):
1. Wikipedia en espanol (prioridad) - API publica.
2. DuckDuckGo HTML (respaldo).

Si no hay internet o falla requests, Alex sigue solo con memoria local.
"""

import html
import re
from urllib.parse import quote

try:
    import requests
    REQUESTS_DISPONIBLE = True
except ImportError:
    REQUESTS_DISPONIBLE = False


class BuscadorWeb:
    def __init__(self, timeout: int = 8):
        self.timeout = timeout
        self.disponible = REQUESTS_DISPONIBLE
        self._headers = {
            "User-Agent": "AlexLocalAI/1.0 (GameBoysStudios; educational bot)",
            "Accept": "application/json",
        }

    def buscar(self, consulta: str, max_resultados: int = 5) -> list:
        if not self.disponible or not consulta.strip():
            return []
        resultados = self.buscar_wikipedia(consulta, max_resultados=max_resultados)
        if resultados:
            return resultados
        return self._buscar_duckduckgo(consulta, max_resultados=max_resultados)

    def buscar_wikipedia(self, consulta: str, max_resultados: int = 3) -> list:
        if not self.disponible or not consulta.strip():
            return []
        resultados = []
        directo = self._wikipedia_resumen(consulta.strip())
        if directo:
            resultados.append(directo)
        titulos = self._wikipedia_buscar_titulos(consulta, limite=max_resultados + 2)
        for titulo in titulos:
            if any(r.get("titulo") == titulo for r in resultados):
                continue
            resumen = self._wikipedia_resumen(titulo)
            if resumen:
                resultados.append(resumen)
            if len(resultados) >= max_resultados:
                break
        return resultados[:max_resultados]

    def explicar_palabra(self, palabra: str):
        palabra = (palabra or "").strip()
        if not palabra:
            return None
        resultados = self.buscar_wikipedia(palabra, max_resultados=1)
        return resultados[0] if resultados else None

    def _wikipedia_buscar_titulos(self, consulta: str, limite: int = 5) -> list:
        try:
            url = "https://es.wikipedia.org/w/api.php"
            params = {
                "action": "query",
                "list": "search",
                "srsearch": consulta,
                "srlimit": limite,
                "srnamespace": 0,
                "format": "json",
            }
            resp = requests.get(url, params=params, headers=self._headers, timeout=self.timeout)
            resp.raise_for_status()
            data = resp.json()
            return [item["title"] for item in data.get("query", {}).get("search", [])]
        except Exception:
            return []

    def _wikipedia_resumen(self, titulo: str):
        try:
            slug = quote(titulo.replace(" ", "_"), safe="")
            url = f"https://es.wikipedia.org/api/rest_v1/page/summary/{slug}"
            resp = requests.get(url, headers=self._headers, timeout=self.timeout)
            if resp.status_code == 404:
                return None
            resp.raise_for_status()
            data = resp.json()
            tipo = data.get("type", "")
            extracto = (data.get("extract") or "").strip()
            if not extracto:
                return None
            if tipo == "disambiguation" and len(extracto) < 40:
                return None
            titulo_real = data.get("title") or titulo
            page_url = (
                data.get("content_urls", {}).get("desktop", {}).get("page")
                or f"https://es.wikipedia.org/wiki/{slug}"
            )
            return {
                "titulo": titulo_real,
                "fragmento": extracto,
                "url": page_url,
                "calidad_fuente": 0.95,
                "origen": "wikipedia",
            }
        except Exception:
            return None

    def _buscar_duckduckgo(self, consulta: str, max_resultados: int = 5) -> list:
        try:
            resp = requests.post(
                "https://html.duckduckgo.com/html/",
                data={"q": consulta},
                headers={"User-Agent": "Mozilla/5.0 (AlexLocalAI/1.0)"},
                timeout=self.timeout,
            )
            resp.raise_for_status()
        except Exception:
            return []
        return self._parsear_ddg(resp.text, max_resultados)

    def _parsear_ddg(self, html_text: str, max_resultados: int) -> list:
        resultados = []
        bloques = re.findall(
            r'<a[^>]*class="result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>.*?'
            r'class="result__snippet"[^>]*>(.*?)</a>',
            html_text,
            re.DOTALL,
        )
        for url, titulo_html, fragmento_html in bloques[:max_resultados]:
            titulo = self._limpiar_html(titulo_html)
            fragmento = self._limpiar_html(fragmento_html)
            if not titulo and not fragmento:
                continue
            resultados.append({
                "titulo": titulo,
                "fragmento": fragmento,
                "url": url,
                "calidad_fuente": self._estimar_calidad_fuente(url),
                "origen": "web",
            })
        return resultados

    @staticmethod
    def _limpiar_html(fragmento: str) -> str:
        texto = re.sub(r"<[^>]+>", "", fragmento)
        texto = html.unescape(texto)
        return texto.strip()

    @staticmethod
    def _estimar_calidad_fuente(url: str) -> float:
        url_low = url.lower()
        if "wikipedia.org" in url_low:
            return 0.95
        if any(d in url_low for d in (".edu", ".gob", ".gov", "rae.es", "bbc.com")):
            return 0.9
        if any(d in url_low for d in (".org", ".com", ".net")):
            return 0.6
        return 0.4
