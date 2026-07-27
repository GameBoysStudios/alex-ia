# -*- coding: utf-8 -*-
"""Generador de lenguaje para Alex."""

import random

PLANTILLAS_CONOCIMIENTO = [
    "Segun lo que se, {resumen}",
    "Por lo que tengo entendido, {resumen}",
    "Puedo decirte que {resumen}",
    "Esto es lo que se al respecto: {resumen}",
]

PLANTILLAS_WEB = [
    "He buscado informacion y encontre que {resumen} (fuente: {fuente}).",
    "Segun lo que encontre en internet, {resumen} (fuente: {fuente}).",
    "No lo sabia con certeza, asi que lo busque: {resumen} (fuente: {fuente}).",
]

PLANTILLAS_WIKIPEDIA = [
    "Segun Wikipedia: {resumen}",
    "He consultado Wikipedia y esto es lo que dice: {resumen}",
    "Acabo de informarme en Wikipedia: {resumen}",
]

PLANTILLAS_SIN_INFO = [
    "Todavia no tengo suficiente informacion sobre eso. Podrias explicarmelo?",
    "No he encontrado nada util en mi memoria ni en Wikipedia. Me lo explicas para aprenderlo?",
    "Aun no se responder eso con seguridad. Si me lo explicas, lo recordare.",
]

PLANTILLAS_SALUDO = [
    "Hola! Soy Alex. En que puedo ayudarte hoy?",
    "Hola de nuevo. Que te gustaria saber o comentar?",
    "Buenas! Aqui estoy, listo para aprender contigo.",
]

PLANTILLAS_CORRECCION_ACEPTADA = [
    "Entendido, gracias por corregirme. Lo tendre en cuenta.",
    "Anotado, lo he corregido en mi memoria. Gracias por ensenarme!",
    "Perfecto, actualizo lo aprendido con tu correccion.",
]

PLANTILLAS_DEFINICION_ACEPTADA = [
    "Perfecto, he aprendido que {palabra} significa: {significado}. Gracias!",
    "Anotado: {palabra} = {significado}. Ya lo recordare la proxima vez.",
    "Entendido. He guardado la definicion de {palabra} en mi memoria.",
]

PLANTILLAS_PALABRA_NUEVA = [
    "Por cierto, no conocia la palabra {palabra}. La he anotado.",
    "He detectado una palabra nueva para mi: {palabra}.",
]

PLANTILLAS_SINONIMO_ACEPTADO = [
    "Anotado: {palabra} y {sinonimo} son sinonimos. Gracias!",
    "Perfecto, he aprendido que {palabra} es sinonimo de {sinonimo}.",
]

PLANTILLAS_SUGERENCIA_ORTOGRAFICA = [
    "Quizas quisiste decir {sugerencia} en lugar de {palabra}?",
    "Detecte una posible errata: {palabra} -> {sugerencia}?",
]


class GeneradorLenguaje:
    def __init__(self, memoria):
        self.memoria = memoria

    def _elegir_plantilla(self, lista):
        return random.choice(lista)

    def respuesta_conocimiento(self, resumen: str) -> str:
        return self._elegir_plantilla(PLANTILLAS_CONOCIMIENTO).format(resumen=resumen)

    def respuesta_web(self, resumen: str, fuente: str) -> str:
        return self._elegir_plantilla(PLANTILLAS_WEB).format(resumen=resumen, fuente=fuente)

    def respuesta_wikipedia(self, resumen: str, fuente: str = "") -> str:
        texto = self._elegir_plantilla(PLANTILLAS_WIKIPEDIA).format(resumen=resumen)
        if fuente:
            texto += f" (fuente: {fuente})"
        return texto

    def respuesta_sin_info(self) -> str:
        return self._elegir_plantilla(PLANTILLAS_SIN_INFO)

    def saludo(self) -> str:
        return self._elegir_plantilla(PLANTILLAS_SALUDO)

    def correccion_aceptada(self) -> str:
        return self._elegir_plantilla(PLANTILLAS_CORRECCION_ACEPTADA)

    def definicion_aceptada(self, palabra: str, significado: str) -> str:
        return self._elegir_plantilla(PLANTILLAS_DEFINICION_ACEPTADA).format(
            palabra=palabra, significado=significado
        )

    def sinonimo_aceptado(self, palabra: str, sinonimo: str) -> str:
        return self._elegir_plantilla(PLANTILLAS_SINONIMO_ACEPTADO).format(
            palabra=palabra, sinonimo=sinonimo
        )

    def sugerencia_ortografica(self, palabra: str, sugerencia: str) -> str:
        return self._elegir_plantilla(PLANTILLAS_SUGERENCIA_ORTOGRAFICA).format(
            palabra=palabra, sugerencia=sugerencia
        )

    def nota_palabra_nueva(self, palabra: str) -> str:
        return self._elegir_plantilla(PLANTILLAS_PALABRA_NUEVA).format(palabra=palabra)

    def combinar(self, partes: list) -> str:
        return " ".join(p.strip() for p in partes if p and p.strip())
