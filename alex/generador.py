# -*- coding: utf-8 -*-
"""Generador de lenguaje para Alex."""

import random
import re

# Identidad fija de Alex
CREADOR = "Diego Ar"
NOMBRE = "Alex"
DESCRIPCION = (
    "soy Alex, una IA local creada por Diego Ar para Game Boys Studios. "
    "Funciono en cliente (sin APIs de LLM externas): aprendo de ti, "
    "consulto Wikipedia cuando no se algo, y puedo ayudarte a generar textos, "
    "ideas, explicaciones y tareas sencillas."
)

PLANTILLAS_CONOCIMIENTO = [
    "Segun lo que se, {resumen}",
    "Por lo que tengo entendido, {resumen}",
    "Puedo decirte que {resumen}",
    "Esto es lo que se al respecto: {resumen}",
]

PLANTILLAS_WEB = [
    "He buscado informacion y encontre que {resumen} (fuente: {fuente}).",
    "Segun lo que encontre en internet, {resumen} (fuente: {fuente}).",
]

PLANTILLAS_WIKIPEDIA = [
    "Segun Wikipedia: {resumen}",
    "He consultado Wikipedia y esto es lo que dice: {resumen}",
    "Me he informado en Wikipedia: {resumen}",
]

PLANTILLAS_SIN_INFO = [
    "Todavia no tengo suficiente informacion sobre eso. Puedes darme mas contexto o ensenarmelo?",
    "No he encontrado nada util en mi memoria ni en Wikipedia. Si me lo explicas, lo aprendo.",
]

PLANTILLAS_SALUDO = [
    "Hola! Soy Alex, la IA local de Diego Ar. En que puedo ayudarte?",
    "Hola! Soy Alex (creado por Diego Ar). Puedo explicar cosas, buscar en Wikipedia y generar textos. Que necesitas?",
    "Buenas! Alex a tu servicio. Dime que quieres generar o saber.",
]

PLANTILLAS_IDENTIDAD = [
    "Soy Alex, una IA local en cliente creada por Diego Ar para Game Boys Studios. "
    "No dependo de ChatGPT ni APIs de LLM: aprendo contigo, guardo memoria y consulto Wikipedia cuando hace falta.",
    "Me llamo Alex. Me creo Diego Ar. Soy una IA en cliente: ligera, con memoria propia y capaz de generar textos e ideas cuando me lo pides.",
]

PLANTILLAS_CORRECCION_ACEPTADA = [
    "Entendido, gracias por corregirme. Lo tendre en cuenta.",
    "Anotado. He actualizado mi memoria. Gracias!",
]

PLANTILLAS_DEFINICION_ACEPTADA = [
    "Perfecto, he aprendido que {palabra} significa: {significado}.",
    "Anotado: {palabra} = {significado}. Ya lo recordare.",
]

PLANTILLAS_PALABRA_NUEVA = [
    "No conocia bien la palabra {palabra}; la he anotado.",
]

PLANTILLAS_SINONIMO_ACEPTADO = [
    "Anotado: {palabra} y {sinonimo} son sinonimos.",
]

PLANTILLAS_SUGERENCIA_ORTOGRAFICA = [
    "Quizas quisiste decir {sugerencia} en lugar de {palabra}?",
]

PLANTILLAS_TAREA_OK = [
    "Claro, aqui tienes lo que me pediste:\n\n{contenido}",
    "Hecho. Resultado:\n\n{contenido}",
    "Generado:\n\n{contenido}",
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

    def identidad(self) -> str:
        return self._elegir_plantilla(PLANTILLAS_IDENTIDAD)

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

    def respuesta_tarea(self, contenido: str) -> str:
        return self._elegir_plantilla(PLANTILLAS_TAREA_OK).format(contenido=contenido)

    def generar_tarea(self, pedido: str) -> str:
        """Genera un texto util a partir de un pedido del usuario (plantillas + estructura)."""
        pedido_limpio = pedido.strip()
        # Quitar verbos de orden al inicio
        pedido_limpio = re.sub(
            r"^(genera|generame|escribe|escribeme|redacta|redactame|haz|hazme|"
            r"crea|creame|inventa|inventame|dame|pon|prepara|preparame)\s+",
            "",
            pedido_limpio,
            flags=re.IGNORECASE,
        ).strip()

        lower = pedido.lower()

        if any(w in lower for w in ("lista", "listado", "puntos", "ideas")):
            tema = pedido_limpio or "el tema pedido"
            lineas = [
                f"Ideas sobre: {tema}",
                "1. Define el objetivo principal con claridad.",
                "2. Reune 3 referencias o ejemplos utiles.",
                "3. Escribe un borrador corto y revisalo.",
                "4. Pide feedback y mejora una version final.",
                "5. Resume lo esencial en pocas lineas.",
            ]
            return self.respuesta_tarea("\n".join(lineas))

        if any(w in lower for w in ("email", "correo", "mensaje")):
            return self.respuesta_tarea(
                "Asunto: Consulta / seguimiento\n\n"
                "Hola,\n\n"
                f"Te escribo en relacion con: {pedido_limpio or 'el tema indicado'}.\n\n"
                "Quedo atento a tu respuesta.\n\n"
                "Un saludo,\nAlex (asistente de Game Boys Studios)"
            )

        if any(w in lower for w in ("resumen", "resume", "sintesis")):
            return self.respuesta_tarea(
                f"Resumen solicitado sobre: {pedido_limpio}\n\n"
                "- Punto clave 1: contexto general.\n"
                "- Punto clave 2: idea central.\n"
                "- Punto clave 3: conclusion practica.\n\n"
                "Si me das el texto original, puedo resumirlo con mas precision."
            )

        if any(w in lower for w in ("historia", "cuento", "relato")):
            tema = pedido_limpio or "una aventura corta"
            return self.respuesta_tarea(
                f"Habia una vez un reto llamado '{tema}'. "
                "Alguien decidio intentarlo con calma, aprendio de cada error "
                "y, al final, encontro una solucion simple que nadie habia visto. "
                "Moraleja: preguntar y aprender tambien es avanzar."
            )

        # Generico: estructura clara para cualquier pedido de generacion
        return self.respuesta_tarea(
            f"Pedido: {pedido_limpio}\n\n"
            f"Propuesta de Alex:\n"
            f"1) Objetivo: resolver lo que pediste sobre '{pedido_limpio}'.\n"
            f"2) Borrador: desarrolla el tema en 3-5 frases claras.\n"
            f"3) Detalle: anade un ejemplo concreto si es posible.\n"
            f"4) Cierre: termina con una frase practica o siguiente paso.\n\n"
            f"Si me das mas detalles (tono, longitud, publico), lo afino mejor."
        )

    def combinar(self, partes: list) -> str:
        return " ".join(p.strip() for p in partes if p and p.strip())
