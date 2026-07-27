# -*- coding: utf-8 -*-
"""
Módulo Generador de Lenguaje para Alex.

Se encarga de construir frases en castellano combinando plantillas propias
con la información elegida (de memoria, deducción o web), evitando devolver
texto "pegado" sin más. Con el tiempo, las plantillas usadas con éxito se
pueden reforzar (aprendizaje de estilo simple vía preferencias).
"""

import random

PLANTILLAS_CONOCIMIENTO = [
    "Según lo que sé, {resumen}",
    "Por lo que tengo entendido, {resumen}",
    "Puedo decirte que {resumen}",
    "Esto es lo que sé al respecto: {resumen}",
]

PLANTILLAS_WEB = [
    "He buscado un poco de información y encontré que {resumen} (fuente: {fuente}).",
    "Según lo que encontré en internet, {resumen} (fuente: {fuente}).",
    "No lo sabía con certeza, así que lo busqué: {resumen} (fuente: {fuente}).",
]

PLANTILLAS_SIN_INFO = [
    "Todavía no tengo suficiente información sobre eso. ¿Podrías explicármelo o darme más contexto?",
    "No he encontrado nada útil en mi memoria ni en internet sobre eso. ¿Me lo explicas para que pueda aprenderlo?",
    "Aún no sé responder eso con seguridad. Si me lo explicas, lo recordaré para la próxima vez.",
]

PLANTILLAS_SALUDO = [
    "¡Hola! Soy Alex. ¿En qué puedo ayudarte hoy?",
    "Hola de nuevo. ¿Qué te gustaría saber o comentar?",
    "¡Buenas! Aquí estoy, listo para aprender contigo.",
]

PLANTILLAS_CORRECCION_ACEPTADA = [
    "Entendido, gracias por corregirme. Lo tendré en cuenta a partir de ahora.",
    "Anotado, lo he corregido en mi memoria. ¡Gracias por enseñarme!",
    "Perfecto, actualizo lo aprendido con tu corrección.",
]

PLANTILLAS_DEFINICION_ACEPTADA = [
    "Perfecto, he aprendido que {palabra} significa: {significado}. ¡Gracias!",
    "Anotado: {palabra} = {significado}. Ya lo recordaré la próxima vez.",
    "Entendido. He guardado la definición de \"{palabra}\" en mi memoria.",
]

PLANTILLAS_PALABRA_NUEVA = [
    "Por cierto, no conocía la palabra \"{palabra}\". La he anotado para aprender más sobre ella.",
    "He detectado una palabra nueva para mí: \"{palabra}\". Seguiré aprendiendo su significado con el uso.",
]

PLANTILLAS_SINONIMO_ACEPTADO = [
    "Anotado: \"{palabra}\" y \"{sinonimo}\" son sinónimos. ¡Gracias!",
    "Perfecto, he aprendido que \"{palabra}\" es sinónimo de \"{sinonimo}\".",
    "Entendido. Guardé la relación de sinonimia entre \"{palabra}\" y \"{sinonimo}\".",
]

PLANTILLAS_SUGERENCIA_ORTOGRAFICA = [
    "¿Quizá quisiste decir \"{sugerencia}\" en lugar de \"{palabra}\"?",
    "Detecté una posible errata: \"{palabra}\" → ¿\"{sugerencia}\"?",
]


class GeneradorLenguaje:
    def __init__(self, memoria):
        self.memoria = memoria

    def _elegir_plantilla(self, lista):
        return random.choice(lista)

    def respuesta_conocimiento(self, resumen: str) -> str:
        plantilla = self._elegir_plantilla(PLANTILLAS_CONOCIMIENTO)
        return plantilla.format(resumen=resumen)

    def respuesta_web(self, resumen: str, fuente: str) -> str:
        plantilla = self._elegir_plantilla(PLANTILLAS_WEB)
        return plantilla.format(resumen=resumen, fuente=fuente)

    def respuesta_sin_info(self) -> str:
        return self._elegir_plantilla(PLANTILLAS_SIN_INFO)

    def saludo(self) -> str:
        return self._elegir_plantilla(PLANTILLAS_SALUDO)

    def correccion_aceptada(self) -> str:
        return self._elegir_plantilla(PLANTILLAS_CORRECCION_ACEPTADA)

    def definicion_aceptada(self, palabra: str, significado: str) -> str:
        plantilla = self._elegir_plantilla(PLANTILLAS_DEFINICION_ACEPTADA)
        return plantilla.format(palabra=palabra, significado=significado)

    def sinonimo_aceptado(self, palabra: str, sinonimo: str) -> str:
        plantilla = self._elegir_plantilla(PLANTILLAS_SINONIMO_ACEPTADO)
        return plantilla.format(palabra=palabra, sinonimo=sinonimo)

    def sugerencia_ortografica(self, palabra: str, sugerencia: str) -> str:
        plantilla = self._elegir_plantilla(PLANTILLAS_SUGERENCIA_ORTOGRAFICA)
        return plantilla.format(palabra=palabra, sugerencia=sugerencia)

    def nota_palabra_nueva(self, palabra: str) -> str:
        return self._elegir_plantilla(PLANTILLAS_PALABRA_NUEVA).format(palabra=palabra)

    def combinar(self, partes: list) -> str:
        """Une varias partes de respuesta en un único texto natural, sin duplicar espacios."""
        texto = " ".join(p.strip() for p in partes if p and p.strip())
        return texto
