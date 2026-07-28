# -*- coding: utf-8 -*-
"""Generador de lenguaje para Alex."""

import random
import re

CREADOR = "Diego Ar"
NOMBRE = "Alex"

# Temas internos que no deben colarse en textos generados sobre otros asuntos
TEMAS_INTERNOS = {
    "alex", "diego", "firebase", "json", "render", "github", "api", "python",
    "javascript", "memoria", "quien eres", "game boys", "identidad",
}

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
    "Hola! Soy Alex (creado por Diego Ar). Puedo buscar info, explicar y generar textos.",
]

PLANTILLAS_IDENTIDAD = [
    "Soy Alex, una IA local en cliente creada por Diego Ar para Game Boys Studios. "
    "Aprendo contigo, consulto Wikipedia cuando hace falta y genero textos con la info relevante.",
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

    def _limpiar_pedido(self, pedido: str) -> str:
        pedido = pedido.strip()
        pedido = re.sub(
            r"^(genera|generame|genérame|escribe|escribeme|escríbeme|redacta|redactame|"
            r"haz|hazme|crea|creame|créame|inventa|inventame|dame|pon|prepara|preparame|"
            r"armame|arma|propon|propón|sugiere|explica|explicame|explícame|cuentame|"
            r"cuéntame|describe)\s+",
            "",
            pedido,
            flags=re.IGNORECASE,
        ).strip()
        # "un texto sobre X" / "texto sobre X" / "un articulo de X"
        m = re.search(
            r"(?:un |una )?(?:texto|articulo|artículo|parrafo|párrafo|redaccion|redacción)"
            r"\s+(?:sobre|de|acerca de)\s+(.+)$",
            pedido,
            re.I,
        )
        if m:
            return m.group(1).strip(" ?.!")
        m = re.search(r"^(?:sobre|acerca de)\s+(.+)$", pedido, re.I)
        if m:
            return m.group(1).strip(" ?.!")
        return pedido or pedido.strip()

    def _tokens(self, texto: str) -> set:
        return {t for t in re.findall(r"[a-záéíóúñü]{3,}", (texto or "").lower())}

    def _es_relevante(self, texto: str, tema: str) -> bool:
        """Evita colar JSON/Alex/Firebase en un texto sobre ecosistemas, etc."""
        if not texto:
            return False
        low = texto.lower()
        tema_toks = self._tokens(tema)
        # Bloquear ruido interno salvo que el tema sea sobre Alex
        if not (tema_toks & {"alex", "diego", "firebase", "json"}):
            for malo in TEMAS_INTERNOS:
                if malo in low and malo not in tema.lower():
                    # Si solo menciona de pasada y el tema principal no encaja, fuera
                    if not (tema_toks & self._tokens(low)):
                        return False
                    # Si habla de JSON y el tema no es informatica, fuera
                    if malo in {"json", "firebase", "alex", "diego", "render"} and not (
                        tema_toks & {"programacion", "python", "api", "web", "codigo", "ia"}
                    ):
                        return False
        if not tema_toks:
            return True
        text_toks = self._tokens(texto)
        solape = tema_toks & text_toks
        # Al menos 1 token del tema, o muy parecido por substring
        if solape:
            return True
        for t in tema_toks:
            if t in low or (len(t) > 4 and t[:5] in low):
                return True
        return False

    def _frases(self, texto: str, max_frases: int = 6) -> list:
        if not texto:
            return []
        partes = re.split(r"(?<=[\.\!\?])\s+", texto.strip())
        limpias = []
        for p in partes:
            p = p.strip()
            if len(p) < 25:
                continue
            if len(p) > 320:
                p = p[:317] + "..."
            limpias.append(p)
            if len(limpias) >= max_frases:
                break
        return limpias

    def _detectar_tipo(self, pedido: str) -> str:
        lower = pedido.lower()
        if any(w in lower for w in ("texto", "articulo", "artículo", "parrafo", "párrafo", "redact")):
            return "texto"
        if any(w in lower for w in ("lista", "listado", "puntos", "ideas", "pasos")):
            return "lista"
        if any(w in lower for w in ("email", "correo", "mensaje")):
            return "email"
        if any(w in lower for w in ("resumen", "resume", "sintesis", "síntesis")):
            return "resumen"
        if any(w in lower for w in ("historia", "cuento", "relato")):
            return "historia"
        if any(w in lower for w in ("explic", "que es", "qué es", "define", "definicion")):
            return "explicacion"
        if any(w in lower for w in ("plan", "guia", "guía", "tutorial")):
            return "plan"
        return "texto"  # por defecto: intentar prosa util, no plantilla generica

    def _recoger_puntos(self, investigacion: list, tema: str) -> tuple:
        puntos = []
        fuentes = []
        for item in investigacion:
            frag = (item.get("fragmento") or "").strip()
            titulo = (item.get("titulo") or "").strip()
            url = (item.get("url") or "").strip()
            origen = (item.get("origen") or "").strip()

            # Saltar identidad / conocimiento interno irrelevante
            bloque = f"{titulo} {frag}".lower()
            if origen in ("identidad",) or url in ("identidad", "conocimiento_base"):
                if not self._es_relevante(bloque, tema):
                    continue
            if not self._es_relevante(bloque, tema):
                continue

            if frag:
                for frase in self._frases(frag, max_frases=3):
                    if self._es_relevante(frase, tema):
                        puntos.append(frase)
            elif titulo and self._es_relevante(titulo, tema):
                puntos.append(titulo)

            if url and url not in fuentes and url not in ("identidad", "conocimiento_base", "memoria"):
                fuentes.append(url)
            elif url == "conocimiento_base" and url not in fuentes:
                pass  # no listar como fuente ruidosa

        unicos = []
        for p in puntos:
            if not any(p[:50].lower() in u.lower() or u[:50].lower() in p.lower() for u in unicos):
                unicos.append(p)
        return unicos[:6], fuentes[:4]

    def generar_tarea(self, pedido: str, investigacion: list = None) -> str:
        investigacion = investigacion or []
        tema = self._limpiar_pedido(pedido)
        tipo = self._detectar_tipo(pedido)
        puntos, fuentes = self._recoger_puntos(investigacion, tema)

        if tipo == "texto":
            return self._generar_texto(tema, puntos, fuentes)

        lineas = []

        if tipo == "lista":
            lineas.append(f"Ideas / lista sobre {tema}:")
            if puntos:
                for i, p in enumerate(puntos, 1):
                    lineas.append(f"{i}. {p}")
            else:
                lineas.append(f"1. Define que aspecto de {tema} te interesa mas.")
                lineas.append("2. Reune 2-3 datos fiables.")
                lineas.append("3. Escribe un borrador corto.")
                lineas.append("4. Revisa y deja una conclusion clara.")

        elif tipo == "email":
            lineas.append(f"Asunto: Sobre {tema}")
            lineas.append("")
            lineas.append("Hola,")
            lineas.append("")
            if puntos:
                lineas.append(f"Te escribo en relacion con {tema}. Algunos puntos:")
                for p in puntos[:3]:
                    lineas.append(f"- {p}")
            else:
                lineas.append(f"Te escribo en relacion con {tema}.")
            lineas.append("")
            lineas.append("Quedo atento a tu respuesta.")
            lineas.append("")
            lineas.append("Un saludo,")
            lineas.append("Alex")

        elif tipo == "resumen":
            lineas.append(f"Resumen sobre {tema}:")
            if puntos:
                for p in puntos[:4]:
                    lineas.append(f"- {p}")
            else:
                lineas.append("- Aun no tengo datos suficientes sobre este tema.")

        elif tipo == "explicacion":
            if puntos:
                lineas.append(puntos[0])
                for p in puntos[1:4]:
                    lineas.append(p)
            else:
                lineas.append(f"Todavia no tengo una explicacion solida de {tema}.")

        elif tipo == "plan":
            lineas.append(f"Plan sobre {tema}:")
            if puntos:
                lineas.append("Base:")
                for p in puntos[:2]:
                    lineas.append(f"- {p}")
            lineas.append("Pasos:")
            lineas.append("1. Aclara el objetivo.")
            lineas.append("2. Reune la informacion clave.")
            lineas.append("3. Divide el trabajo en bloques.")
            lineas.append("4. Ejecuta y revisa.")
            lineas.append("5. Cierra con un resumen.")

        elif tipo == "historia":
            if puntos:
                lineas.append(
                    f"En un lugar marcado por {tema}, alguien descubrio que {puntos[0]} "
                    f"Eso cambio su forma de ver el problema y avanzo con mas claro.")
            else:
                lineas.append(
                    f"Habia una vez un reto ligado a {tema}. Con paciencia y datos, "
                    f"alguien encontro una salida simple.")

        else:
            return self._generar_texto(tema, puntos, fuentes)

        if fuentes:
            lineas.append("")
            lineas.append("Fuentes:")
            for f in fuentes[:3]:
                lineas.append(f"- {f}")

        return "\n".join(lineas)

    def _generar_texto(self, tema: str, puntos: list, fuentes: list) -> str:
        """Prosa continua sobre el tema (no plantilla 1/2/3 con ruido)."""
        lineas = []
        titulo = tema[:1].upper() + tema[1:] if tema else "Tema"
        lineas.append(titulo)
        lineas.append("")

        if puntos:
            # Parrafo de introduccion + desarrollo
            intro = puntos[0]
            if not intro.endswith((".", "!", "?")):
                intro += "."
            lineas.append(intro)
            lineas.append("")
            if len(puntos) > 1:
                desarrollo = " ".join(
                    (p if p.endswith((".", "!", "?")) else p + ".") for p in puntos[1:4]
                )
                lineas.append(desarrollo)
            if len(puntos) > 4:
                lineas.append("")
                lineas.append(" ".join(
                    (p if p.endswith((".", "!", "?")) else p + ".") for p in puntos[4:6]
                ))
        else:
            lineas.append(
                f"Un texto sobre {tema} deberia explicar que es, por que importa y "
                f"algun ejemplo concreto. No he encontrado datos suficientemente "
                f"relevantes ahora mismo; si me das un enfoque (escolar, cientifico, "
                f"divulgativo), lo afino mejor. Tambien puedes pedirme: "
                f"'explica {tema}' para que busque informacion especifica."
            )

        if fuentes:
            lineas.append("")
            lineas.append("Fuentes:")
            for f in fuentes[:3]:
                lineas.append(f"- {f}")

        return "\n".join(lineas)

    def combinar(self, partes: list) -> str:
        return " ".join(p.strip() for p in partes if p and p.strip())
