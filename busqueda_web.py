# -*- coding: utf-8 -*-
"""
Módulo de Búsqueda Web para Alex.

Este módulo es opcional: si no hay conexión a internet o falla la librería
`requests`, Alex simplemente informa que no pudo buscar y sigue funcionando
con su memoria local.

IMPORTANTE:
- No se usa ninguna API de IA/LLM externa. Solo se usa un motor de búsqueda
  público (DuckDuckGo HTML, que no requiere API key) para obtener resultados
  de texto, que luego Alex analiza con sus propios módulos de NLP y
  probabilidad para decidir qué usar.
- Si quieres desactivar por completo el acceso a internet, basta con no
  llamar a este módulo (Alex funcionará solo con su memoria local).
"""

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
        """
        Devuelve una lista de dicts: {"titulo":.., "fragmento":.., "url":.., "calidad_fuente": float}
        Si no hay internet o falla la búsqueda, devuelve lista vacía.
        """
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

    def _parsear_resultados(self, html: str, max_resultados: int) -> list:
        resultados = []
        bloques = re.findall(
            r'<a[^>]*class="result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>.*?'
            r'class="result__snippet"[^>]*>(.*?)</a>',
            html, re.DOTALL,
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
        texto = texto.replace("&amp;", "&").replace("&quot;", '"').replace("&#x27;", "'")
        return texto.strip()

    @staticmethod
    def _estimar_calidad_fuente(url: str) -> float:
        """Heurística simple de calidad de fuente según el dominio."""
        dominios_alta_calidad = (
            "wikipedia.org", ".edu", ".gob", ".gov", "rae.es",
            "bbc.com", "un.org", "who.int",
        )
        dominios_media_calidad = (".org", ".com", ".net")

        url_low = url.lower()
        if any(d in url_low for d in dominios_alta_calidad):
            return 0.9
        if any(d in url_low for d in dominios_media_calidad):
            return 0.6
        return 0.4
