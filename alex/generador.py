# -*- coding: utf-8 -*-
"""Generador de lenguaje para Alex."""

import random
import re

CREADOR = "Diego Ar"
NOMBRE = "Alex"

PLANTILLAS_CONOCIMIENTO = [
    "Segun lo que se, {resumen}",
    "Por lo que tengo entendido, {resumen}",
    "Puedo decirte que {resumen}",
]

PLANTILLAS_WEB = [
    "He buscado informacion y encontre que {resumen} (fuente: {fuente}).",
    "Segun lo que encontre en internet, {resumen} (fuente: {fuente}).",
]

PLANTILLAS_WIKIPEDIA = [
    "Segun Wikipedia: {resumen}",
    "He consultado Wikipedia y esto es lo que dice: {resumen}",
]

PLANTILLAS_SIN_INFO = [
    "Todavia no tengo suficiente informacion sobre eso. Puedes darme mas contexto?",
    "No he encontrado nada util. Si me lo explicas, lo aprendo.",
]

PLANTILLAS_SALUDO = [
    "Hola! Soy Alex, la IA local de Diego Ar. En que puedo ayudarte?",
    "Hola! Soy Alex (creado por Diego Ar). Puedo buscar info, explicar y generar textos estructurados.",
]

PLANTILLAS_IDENTIDAD = [
    "Soy Alex, una IA local en cliente creada por Diego Ar para Game Boys Studios. "
    "Aprendo contigo, consulto Wikipedia/internet y genero estructuras con la info que encuentro.",
]

PLANTILLAS_CORRECCION_ACEPTADA = [
    "Entendido, gracias por corregirme.",
    "Anotado. He actualizado mi memoria.",
]

PLANTILLAS_DEFINICION_ACEPTADA = [
    "Perfecto, he aprendido que {palabra} significa: {significado}.",
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

    # ------------------------------------------------------------------
    # Extraccion y estructura dinamica
    # ------------------------------------------------------------------
    def _limpiar_pedido(self, pedido: str) -> str:
        pedido = pedido.strip()
        return re.sub(
            r"^(genera|generame|generame|escribe|escribeme|escribeme|redacta|redactame|"
            r"haz|hazme|crea|creame|inventa|inventame|dame|pon|prepara|preparame|"
            r"armame|arma|propon|propón|sugiere|explica|explicame|cuentame|describe)\s+",
            "",
            pedido,
            flags=re.IGNORECASE,
        ).strip() or pedido.strip()

    def _frases(self, texto: str, max_frases: int = 6) -> list:
        if not texto:
            return []
        partes = re.split(r"(?<=[\.\!\?])\s+", texto.strip())
        limpias = []
        for p in partes:
            p = p.strip()
            if len(p) < 20:
                continue
            # Evitar frases demasiado largas
            if len(p) > 280:
                p = p[:277] + "..."
            limpias.append(p)
            if len(limpias) >= max_frases:
                break
        return limpias

    def _detectar_tipo(self, pedido: str) -> str:
        lower = pedido.lower()
        if any(w in lower for w in ("lista", "listado", "puntos", "ideas", "pasos")):
            return "lista"
        if any(w in lower for w in ("email", "correo", "mensaje")):
            return "email"
        if any(w in lower for w in ("resumen", "resume", "sintesis")):
            return "resumen"
        if any(w in lower for w in ("historia", "cuento", "relato")):
            return "historia"
        if any(w in lower for w in ("explic", "que es", "qué es", "define", "definicion")):
            return "explicacion"
        if any(w in lower for w in ("plan", "guia", "guía", "tutorial", "como", "cómo")):
            return "plan"
        return "estructura"

    def generar_tarea(self, pedido: str, investigacion: list = None) -> str:
        """
        Construye una respuesta estructurada usando info de internet/Wikipedia
        (investigacion = lista de {titulo, fragmento, url, origen}).
        La estructura se arma dinamicamente segun el tipo de pedido y los datos hallados.
        """
        investigacion = investigacion or []
        tema = self._limpiar_pedido(pedido)
        tipo = self._detectar_tipo(pedido)

        # Reunir material de investigacion
        puntos = []
        fuentes = []
        for item in investigacion[:5]:
            frag = (item.get("fragmento") or "").strip()
            titulo = (item.get("titulo") or "").strip()
            url = (item.get("url") or "").strip()
            if frag:
                for frase in self._frases(frag, max_frases=2):
                    puntos.append(frase)
            elif titulo:
                puntos.append(titulo)
            if url and url not in fuentes:
                fuentes.append(url)

        # Deduplicar puntos parecidos (muy basico)
        unicos = []
        for p in puntos:
            if not any(p[:40].lower() in u.lower() or u[:40].lower() in p.lower() for u in unicos):
                unicos.append(p)
        puntos = unicos[:6]

        lineas = []
        lineas.append(f"Pedido: {tema}")
        lineas.append("")

        if tipo == "lista":
            lineas.append(f"Lista / ideas sobre: {tema}")
            if puntos:
                for i, p in enumerate(puntos, 1):
                    lineas.append(f"{i}. {p}")
            else:
                lineas.append("1. Define el objetivo.")
                lineas.append("2. Reune referencias.")
                lineas.append("3. Escribe un borrador.")
                lineas.append("4. Revisa y mejora.")

        elif tipo == "email":
            lineas.append("Asunto: " + (tema[:60] or "Consulta"))
            lineas.append("")
            lineas.append("Hola,")
            lineas.append("")
            if puntos:
                lineas.append(f"Te escribo sobre {tema}. Algunos datos utiles:")
                for p in puntos[:3]:
                    lineas.append(f"- {p}")
            else:
                lineas.append(f"Te escribo en relacion con: {tema}.")
            lineas.append("")
            lineas.append("Quedo atento a tu respuesta.")
            lineas.append("")
            lineas.append("Un saludo,")
            lineas.append("Alex (Game Boys Studios)")

        elif tipo == "resumen":
            lineas.append(f"Resumen sobre: {tema}")
            lineas.append("")
            if puntos:
                for i, p in enumerate(puntos[:4], 1):
                    lineas.append(f"- {p}")
            else:
                lineas.append("- No encontre datos suficientes; dame el texto a resumir.")

        elif tipo == "explicacion":
            lineas.append(f"Explicacion: {tema}")
            lineas.append("")
            if puntos:
                lineas.append("Que es / contexto:")
                lineas.append(puntos[0])
                if len(puntos) > 1:
                    lineas.append("")
                    lineas.append("Detalles importantes:")
                    for i, p in enumerate(puntos[1:], 1):
                        lineas.append(f"{i}. {p}")
            else:
                lineas.append("No encontre una explicacion solida aun. Puedes darme mas pistas?")

        elif tipo == "plan":
            lineas.append(f"Plan / guia: {tema}")
            lineas.append("")
            if puntos:
                lineas.append("Base informativa:")
                for p in puntos[:2]:
                    lineas.append(f"- {p}")
                lineas.append("")
            lineas.append("Pasos sugeridos:")
            pasos_base = [
                "Aclara el objetivo concreto.",
                "Reune la informacion clave (ya buscada arriba si habia datos).",
                "Ordena el trabajo en bloques pequenos.",
                "Ejecuta el primer bloque y revisa el resultado.",
                "Ajusta y cierra con un resumen de lo hecho.",
            ]
            # Mezclar con puntos como pasos si hay muchos
            for i, paso in enumerate(pasos_base, 1):
                lineas.append(f"{i}. {paso}")

        elif tipo == "historia":
            lineas.append(f"Historia corta inspirada en: {tema}")
            lineas.append("")
            if puntos:
                lineas.append(
                    f"En un escenario donde '{tema}' importa, alguien descubrio esto: {puntos[0]} "
                    f"Con ese conocimiento decidio actuar paso a paso y al final logro avanzar."
                )
            else:
                lineas.append(
                    f"Habia un reto llamado '{tema}'. Con paciencia y aprendizaje, "
                    f"alguien encontro una salida simple. Moraleja: investigar ayuda a decidir mejor."
                )

        else:  # estructura generica dinamica
            lineas.append(f"Estructura generada sobre: {tema}")
            lineas.append("")
            lineas.append("1) Contexto")
            if puntos:
                lineas.append(puntos[0])
            else:
                lineas.append(f"Tema solicitado: {tema}.")
            lineas.append("")
            lineas.append("2) Puntos clave")
            if len(puntos) > 1:
                for i, p in enumerate(puntos[1:4], 1):
                    lineas.append(f"   {i}. {p}")
            else:
                lineas.append("   1. Define el objetivo.")
                lineas.append("   2. Busca 2-3 datos fiables.")
                lineas.append("   3. Resume y aplica.")
            lineas.append("")
            lineas.append("3) Siguiente paso practico")
            lineas.append("   Elige un punto clave y conviertelo en una accion concreta hoy.")

        if fuentes:
            lineas.append("")
            lineas.append("Fuentes:")
            for f in fuentes[:3]:
                lineas.append(f"- {f}")
        elif not puntos:
            lineas.append("")
            lineas.append("(No pude ampliar con internet; la estructura es orientativa.)")

        return "\n".join(lineas)

    def combinar(self, partes: list) -> str:
        return " ".join(p.strip() for p in partes if p and p.strip())
