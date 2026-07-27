# -*- coding: utf-8 -*-
"""
Módulo de Procesamiento del Lenguaje Natural (NLP) para Alex.

Responsabilidades:
- Tokenización de texto.
- Normalización (minúsculas, quitar tildes opcional, limpieza de puntuación).
- Eliminación de palabras vacías (stopwords) en español.
- Cálculo de similitud entre frases (basado en conjuntos de palabras / Jaccard
  y una variante ponderada por frecuencia), con soporte de sinónimos.
- Detección de palabras "desconocidas" respecto al diccionario de Alex.
- Corrección ortográfica básica (distancia de Levenshtein).
"""

import re
import unicodedata
from collections import Counter

# Stopwords básicas en castellano (se puede ampliar con el tiempo).
STOPWORDS_ES = {
    "de", "la", "que", "el", "en", "y", "a", "los", "del", "se", "las",
    "por", "un", "para", "con", "no", "una", "su", "al", "lo", "como",
    "más", "pero", "sus", "le", "ya", "o", "este", "sí", "porque", "esta",
    "entre", "cuando", "muy", "sin", "sobre", "también", "me", "hasta",
    "hay", "donde", "quien", "desde", "todo", "nos", "durante", "todos",
    "uno", "les", "ni", "contra", "otros", "ese", "eso", "ante", "ellos",
    "e", "esto", "mí", "antes", "algunos", "qué", "unos", "yo", "otro",
    "otras", "otra", "él", "tanto", "esa", "estos", "mucho", "quienes",
    "nada", "muchos", "cual", "poco", "ella", "estar", "estas", "algunas",
    "algo", "nosotros", "mi", "mis", "tú", "te", "ti", "tu", "tus", "ellas",
    "nosotras", "vosotros", "vosotras", "os", "mío", "mía", "míos", "mías",
    "tuyo", "tuya", "tuyos", "tuyas", "suyo", "suya", "suyos", "suyas",
    "es", "son", "soy", "eres", "somos", "sois", "ser", "fue", "era",
}


def quitar_tildes(texto: str) -> str:
    """Elimina acentos/tildes de un texto, conservando la ñ."""
    nfkd = unicodedata.normalize("NFD", texto)
    sin_tildes = "".join(
        c for c in nfkd
        if unicodedata.category(c) != "Mn" or c == "\u0303"
    )
    return unicodedata.normalize("NFC", sin_tildes)


def normalizar(texto: str, quitar_tildes_flag: bool = False) -> str:
    """Normaliza texto: minúsculas, espacios, sin tildes (opcional)."""
    texto = texto.strip().lower()
    if quitar_tildes_flag:
        texto = quitar_tildes(texto)
    texto = re.sub(r"\s+", " ", texto)
    return texto


def tokenizar(texto: str) -> list:
    """
    Convierte una cadena de texto en una lista de tokens (palabras),
    eliminando puntuación pero conservando letras con tildes, ñ, etc.
    """
    texto = normalizar(texto)
    # Conserva letras (incluyendo acentuadas), números y guiones internos.
    tokens = re.findall(r"[a-záéíóúüñ0-9]+(?:-[a-záéíóúüñ0-9]+)*", texto)
    return tokens


def quitar_stopwords(tokens: list) -> list:
    """Filtra palabras vacías de una lista de tokens."""
    return [t for t in tokens if t not in STOPWORDS_ES]


def palabras_clave(texto: str) -> list:
    """
    Extrae las palabras clave de un texto: tokeniza y quita stopwords.
    Devuelve la lista en orden de aparición, sin duplicados.
    """
    tokens = quitar_stopwords(tokenizar(texto))
    vistos = set()
    resultado = []
    for t in tokens:
        if t not in vistos:
            vistos.add(t)
            resultado.append(t)
    return resultado


def distancia_levenshtein(a: str, b: str) -> int:
    """Distancia de edición de Levenshtein entre dos cadenas."""
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)
    # Optimización: si la diferencia de longitudes ya es grande, no hace falta
    if abs(len(a) - len(b)) > 3:
        return abs(len(a) - len(b))

    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        curr = [i]
        for j, cb in enumerate(b, 1):
            coste = 0 if ca == cb else 1
            curr.append(min(
                curr[j - 1] + 1,      # inserción
                prev[j] + 1,          # borrado
                prev[j - 1] + coste,  # sustitución
            ))
        prev = curr
    return prev[-1]


def sugerir_correccion_ortografica(palabra: str, vocabulario: set, max_distancia: int = 2) -> list:
    """
    Dada una palabra y un vocabulario conocido, devuelve candidatos de corrección
    ordenados por distancia de Levenshtein (más cercanos primero).
    Solo considera palabras de longitud similar (±2) para eficiencia.
    """
    palabra = palabra.lower().strip()
    if not palabra or palabra in vocabulario:
        return []

    candidatos = []
    long_p = len(palabra)
    for v in vocabulario:
        if abs(len(v) - long_p) > max_distancia:
            continue
        d = distancia_levenshtein(palabra, v)
        if 0 < d <= max_distancia:
            candidatos.append((d, v))
    candidatos.sort(key=lambda x: (x[0], x[1]))
    return [c[1] for c in candidatos[:5]]


def expandir_con_sinonimos(tokens: set, mapa_sinonimos: dict) -> set:
    """
    Amplía un conjunto de tokens con todos sus sinónimos conocidos.
    mapa_sinonimos: palabra -> set de sinónimos.
    """
    expandido = set(tokens)
    for t in tokens:
        sinonimos = mapa_sinonimos.get(t, set())
        expandido.update(sinonimos)
    return expandido


def similitud_jaccard(a: str, b: str, mapa_sinonimos: dict = None) -> float:
    """
    Similitud de Jaccard entre dos textos: |intersección| / |unión|
    sobre el conjunto de palabras clave de cada texto.
    Si se pasa mapa_sinonimos, se expanden ambos conjuntos.
    """
    set_a = set(palabras_clave(a))
    set_b = set(palabras_clave(b))
    if mapa_sinonimos:
        set_a = expandir_con_sinonimos(set_a, mapa_sinonimos)
        set_b = expandir_con_sinonimos(set_b, mapa_sinonimos)
    if not set_a and not set_b:
        return 0.0
    interseccion = set_a & set_b
    union = set_a | set_b
    if not union:
        return 0.0
    return len(interseccion) / len(union)


def similitud_ponderada(a: str, b: str, frecuencias: Counter = None,
                        mapa_sinonimos: dict = None) -> float:
    """
    Similitud que además pondera por la frecuencia global de cada palabra
    (palabras más "conocidas"/frecuentes en la memoria de Alex pesan más
    a la hora de decidir coincidencia, ya que sugieren conceptos afianzados).
    Soporta expansión por sinónimos.
    """
    tokens_a = set(palabras_clave(a))
    tokens_b = set(palabras_clave(b))
    if mapa_sinonimos:
        tokens_a = expandir_con_sinonimos(tokens_a, mapa_sinonimos)
        tokens_b = expandir_con_sinonimos(tokens_b, mapa_sinonimos)
    if not tokens_a or not tokens_b:
        return 0.0

    interseccion = tokens_a & tokens_b
    if not interseccion:
        return 0.0

    frecuencias = frecuencias or Counter()
    peso_interseccion = sum(1 + frecuencias.get(w, 0) for w in interseccion)
    peso_union = sum(1 + frecuencias.get(w, 0) for w in (tokens_a | tokens_b))

    if peso_union == 0:
        return 0.0
    return peso_interseccion / peso_union


def contar_coincidencias(a: str, b: str, mapa_sinonimos: dict = None) -> int:
    """Cuenta cuántas palabras clave del texto A aparecen en el texto B (con sinónimos)."""
    set_b = set(palabras_clave(b))
    if mapa_sinonimos:
        set_b = expandir_con_sinonimos(set_b, mapa_sinonimos)
    return sum(1 for w in palabras_clave(a) if w in set_b)


def es_pregunta(texto: str) -> bool:
    """Heurística simple para detectar si un texto es una pregunta."""
    texto = texto.strip()
    if texto.endswith("?") or texto.startswith("¿"):
        return True
    primeras = tokenizar(texto)[:1]
    palabras_pregunta = {
        "que", "qué", "quien", "quién", "como", "cómo", "cuando", "cuándo",
        "donde", "dónde", "cual", "cuál", "cuanto", "cuánto", "por"
    }
    return bool(primeras) and primeras[0] in palabras_pregunta
