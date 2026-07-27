# -*- coding: utf-8 -*-
"""
Módulo de Aprendizaje para Alex.

Coordina el aprendizaje incremental:
- Registra cada mensaje del usuario para aprender vocabulario y relaciones.
- Detecta palabras desconocidas e intenta deducir su significado por contexto
  (heurística simple: usa las palabras vecinas como "pista" de significado).
- Detecta correcciones explícitas del usuario ("no, se dice...", "eso está mal...").
- Detecta definiciones explícitas del usuario ("X significa Y", "X es un/una ...").
- Actualiza el conocimiento adquirido tras una búsqueda web.
"""

import re
from alex import nlp

PATRONES_CORRECCION = [
    r"^no[,.]?\s*se dice\s+(.+)",
    r"^no[,.]?\s*es\s+(.+)",
    r"^está mal[,.]?\s*(?:es|sería)\s+(.+)",
    r"^se escribe\s+(.+)",
    r"^la forma correcta es\s+(.+)",
    r"^corrección:\s*(.+)",
]

PATRONES_SIGNIFICADO = [
    r"^(.+?)\s+significa\s+(.+)",
    r"^(.+?)\s+quiere decir\s+(.+)",
    r"^(.+?)\s+es\s+(?:un|una|el|la|lo)\s+(.+)",
    r"^(.+?)\s+es\s+(.+)",  # más genérico, al final
]

PATRONES_SINONIMO = [
    r"^(.+?)\s+es\s+sin[oó]nimo\s+de\s+(.+)",
    r"^(.+?)\s+es\s+sin[oó]nimo\s+(.+)",
    r"^(.+?)\s+y\s+(.+?)\s+son\s+sin[oó]nimos",
    r"^sin[oó]nimo\s+de\s+(.+?)\s*(?:es|:)\s*(.+)",
    r"^(.+?)\s*=\s*(.+)",  # forma corta: casa = hogar
]


class MotorAprendizaje:
    def __init__(self, memoria):
        self.memoria = memoria

    def procesar_mensaje_usuario(self, texto: str, mensaje_anterior_alex: str = None):
        """
        Se llama con cada mensaje entrante del usuario. Devuelve un dict con
        información útil para el resto del sistema, por ejemplo si se detectó
        una corrección, definición, sinónimo o sugerencia ortográfica.
        """
        resultado = {
            "correccion_detectada": False,
            "correccion_texto": None,
            "definicion_detectada": False,
            "definicion_palabra": None,
            "definicion_significado": None,
            "sinonimo_detectado": False,
            "sinonimo_palabra": None,
            "sinonimo_de": None,
            "sugerencias_ortograficas": {},  # palabra_mal -> [candidatos]
            "palabras_desconocidas": [],
        }

        # Vocabulario PREVIO (antes de aprender este mensaje) para ortografía.
        vocab_previo = self.memoria.vocabulario_conocido()

        # 1) Aprender vocabulario y relaciones de este mensaje.
        for palabra in nlp.palabras_clave(texto):
            self.memoria.aprender_palabra(palabra, contexto=texto)
        self.memoria.aprender_relaciones_de_texto(texto)

        # 2) ¿El usuario está definiendo el significado de algo?
        definicion = self._detectar_definicion(texto)
        if definicion:
            resultado["definicion_detectada"] = True
            resultado["definicion_palabra"] = definicion["palabra"]
            resultado["definicion_significado"] = definicion["significado"]

        # 3) ¿El usuario está enseñando un sinónimo?
        sinonimo = self._detectar_sinonimo(texto)
        if sinonimo:
            resultado["sinonimo_detectado"] = True
            resultado["sinonimo_palabra"] = sinonimo["palabra"]
            resultado["sinonimo_de"] = sinonimo["sinonimo"]

        # 4) ¿El usuario está corrigiendo la respuesta anterior de Alex?
        texto_norm = nlp.normalizar(texto)
        for patron in PATRONES_CORRECCION:
            m = re.match(patron, texto_norm)
            if m:
                correccion = m.group(1).strip()
                if mensaje_anterior_alex:
                    self.memoria.registrar_correccion(mensaje_anterior_alex, correccion)
                    self.memoria.actualizar_conocimiento_por_correccion(
                        mensaje_anterior_alex, correccion
                    )
                resultado["correccion_detectada"] = True
                resultado["correccion_texto"] = correccion
                break

        # 5) Detectar palabras desconocidas, deducir significado y sugerir ortografía.
        desconocidas = self.memoria.palabras_desconocidas(texto)
        for palabra in desconocidas:
            sugerencias = nlp.sugerir_correccion_ortografica(palabra, vocab_previo, max_distancia=2)
            if sugerencias:
                resultado["sugerencias_ortograficas"][palabra] = sugerencias
            self._deducir_significado_por_contexto(palabra, texto)

        resultado["palabras_desconocidas"] = desconocidas
        return resultado

    def _detectar_sinonimo(self, texto: str):
        """Detecta patrones del tipo 'X es sinónimo de Y' o 'X = Y'."""
        if nlp.es_pregunta(texto):
            return None
        texto_norm = nlp.normalizar(texto)
        for patron in PATRONES_SINONIMO:
            m = re.match(patron, texto_norm)
            if m:
                grupos = m.groups()
                if len(grupos) == 2:
                    a = grupos[0].strip().split(" ")[-1]
                    b = grupos[1].strip().split(" ")[-1]
                    if a and b and a != b and len(a) > 1 and len(b) > 1:
                        self.memoria.agregar_sinonimo(a, b)
                        return {"palabra": a, "sinonimo": b}
        return None

    def _detectar_definicion(self, texto: str):
        """
        Detecta patrones de definición del tipo:
          - "X significa Y"
          - "X quiere decir Y"
          - "X es un/una/el/la Y"
          - "X es Y"  (solo si no parece una pregunta)
        Si se detecta, marca la palabra como conocida, guarda el significado
        en el diccionario Y también como conocimiento consultable (para que
        preguntas posteriores del tipo "¿qué es X?" puedan recuperarlo).
        Devuelve dict con palabra y significado, o None.
        """
        # No tratar como definición si es claramente una pregunta.
        if nlp.es_pregunta(texto):
            return None

        texto_norm = nlp.normalizar(texto)
        # Evitar sujetos que son palabras interrogativas o muy cortos.
        interrogativos = {
            "que", "qué", "quien", "quién", "como", "cómo", "cuando", "cuándo",
            "donde", "dónde", "cual", "cuál", "cuanto", "cuánto", "por", "porqué",
        }

        for patron in PATRONES_SIGNIFICADO:
            m = re.match(patron, texto_norm)
            if m:
                grupos = m.groups()
                if len(grupos) == 2:
                    sujeto, significado = grupos
                    # Tomamos la última palabra del sujeto como la palabra definida
                    # (ej. "la fotosíntesis significa..." -> "fotosíntesis")
                    palabra = sujeto.strip().split(" ")[-1]
                    if not palabra or len(palabra) < 2:
                        continue
                    if palabra in interrogativos:
                        continue
                    significado = significado.strip()
                    if not significado or len(significado) < 2:
                        continue

                    self.memoria.marcar_palabra_conocida(palabra, significado)
                    # Guardar también como conocimiento consultable.
                    resumen = f"{palabra} significa {significado}"
                    self.memoria.guardar_conocimiento(
                        tema=palabra,
                        resumen=resumen,
                        fuente="definición del usuario",
                        puntuacion=0.95,
                    )
                    # También bajo formas de pregunta comunes para mejorar recall.
                    self.memoria.guardar_conocimiento(
                        tema=f"qué es {palabra}",
                        resumen=resumen,
                        fuente="definición del usuario",
                        puntuacion=0.95,
                    )
                    self.memoria.guardar_conocimiento(
                        tema=f"que es {palabra}",
                        resumen=resumen,
                        fuente="definición del usuario",
                        puntuacion=0.95,
                    )
                    return {"palabra": palabra, "significado": significado}
        return None

    def _deducir_significado_por_contexto(self, palabra: str, texto: str):
        """
        Heurística simple de deducción por contexto: toma las palabras clave
        vecinas en la misma frase como pista de campo semántico, y las guarda
        como relación. Cuantas más veces aparezca la palabra en contextos
        parecidos, más "segura" se vuelve la deducción (vía frecuencia).
        """
        vecinas = [p for p in nlp.palabras_clave(texto) if p != palabra]
        pista = ", ".join(vecinas[:5]) if vecinas else None
        significado_deducido = f"(relacionado con: {pista})" if pista else None
        self.memoria.aprender_palabra(palabra, contexto=texto, significado_deducido=significado_deducido)
        for v in vecinas:
            self.memoria.relacionar(palabra, v, peso=0.5)

    def integrar_conocimiento_web(self, tema: str, resumen: str, fuente: str, puntuacion: float):
        self.memoria.guardar_conocimiento(tema, resumen, fuente, puntuacion)
        for palabra in nlp.palabras_clave(tema):
            self.memoria.aprender_palabra(palabra, contexto=resumen[:200])
        self.memoria.aprender_relaciones_de_texto(tema + " " + resumen)
