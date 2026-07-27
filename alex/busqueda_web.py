# -*- coding: utf-8 -*-
"""
Modulo de Busqueda Web para Alex.

Opcional: si no hay internet o falla requests, Alex sigue con memoria local.
Usa DuckDuckGo HTML (sin API key). No usa APIs de LLM.
"""

import html
import re

try:
    import requests
    REQUESTS_DISPONIBLE = True
except ImportError:
    REQUESTS_DISPONIBLE = False


class BuscadorWeb:
    def __init__(self, timeout: int = 6):
        self.timeout = timeout
        self.disponible = REQUESTS_DISPONIBLE

    def buscar(self, consulta: str, max_resultados: int = 5) -> list:
        if not self.disponible:
            return []
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
        return self._parsear_resultados(resp.text, max_resultados)

    def _parsear_resultados(self, html_text: str, max_resultados: int) -> list:
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
            })
        return resultados

    @staticmethod
    def _limpiar_html(fragmento: str) -> str:
        texto = re.sub(r"<[^>]+>", "", fragmento)
        texto = html.unescape(texto)
        return texto.strip()

    @staticmethod
    def _estimar_calidad_fuente(url: str) -> float:
        dominios_alta = (
            "wikipedia.org", ".edu", ".gob", ".gov", "rae.es",
            "bbc.com", "un.org", "who.int",
        )
        dominios_media = (".org", ".com", ".net")
        url_low = url.lower()
        if any(d in url_low for d in dominios_alta):
            return 0.9
        if any(d in url_low for d in dominios_media):
            return 0.6
        return 0.4
