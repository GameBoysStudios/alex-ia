# -*- coding: utf-8 -*-
"""Nucleo de Alex: idioma del usuario, diccionario/codigos, chat, memoria, web."""

import re

from alex.storage import crear_almacenamiento
from alex.memoria import Memoria
from alex.conversacion import Conversacion
from alex.aprendizaje import MotorAprendizaje
from alex.probabilidad import MotorProbabilidad
from alex.busqueda_web import BuscadorWeb
from alex.generador import GeneradorLenguaje
from alex.conocimiento_base import sembrar_conocimiento
from alex.diccionario import DiccionarioCodigos
from alex import chat_natural
from alex import idioma as mod_idioma
from alex import nlp

UMBRAL_USAR_MEMORIA_DIRECTA = 0.55
UMBRAL_MINIMO_ACEPTABLE = 0.28

PATRON_IDENTIDAD = re.compile(
    r"\b(quien eres|quién eres|que eres|qué eres|quien te (creo|creó|hizo|programo|programó)|"
    r"quién te (creo|creó|hizo|programo|programó)|tu creador|quién es diego|quien es diego|"
    r"qué es alex|que es alex|presentate|preséntate|tu nombre|para que sirves|para qué sirves|"
    r"who are you|what are you|who created you)\b",
    re.IGNORECASE,
)

PATRON_TAREA = re.compile(
    r"^(genera|generame|genérame|escribe|escribeme|escríbeme|redacta|redactame|"
    r"haz|hazme|crea|creame|créame|inventa|inventame|dame|prepara|preparame|"
    r"armame|arma|propón|propon|sugiere|explica|explicame|explícame|"
    r"planifica|plan|guia|guía|write|generate|create|explain|make)\b|"
    r"\b(un texto|texto sobre|articulo sobre|artículo sobre|a text about)\b",
    re.IGNORECASE,
)


class Alex:
    def __init__(self, directorio_datos: str = None):
        self.almacenamiento = crear_almacenamiento(directorio_datos)
        self.directorio_datos = getattr(self.almacenamiento, "directorio_base", "?")
        self.backend = getattr(self.almacenamiento, "backend", "local")
        self.memoria = Memoria(self.almacenamiento)
        self.conversacion = Conversacion(self.almacenamiento)
        self.aprendizaje = MotorAprendizaje(self.memoria)
        self.probabilidad = MotorProbabilidad(self.memoria)
        self.buscador_web = BuscadorWeb()
        self.generador = GeneradorLenguaje(self.memoria)
        self.diccionario = DiccionarioCodigos(self.memoria)
        self._ultimo_mensaje_alex = None
        self._idioma_actual = "es"

        stats = self.memoria.datos.get("estadisticas", {})
        if stats.get("conversaciones_totales", 0) == 0 and stats.get("mensajes_totales", 0) == 0:
            self.memoria.incrementar_estadistica("conversaciones_totales")

        sembrar_conocimiento(self.memoria, forzar=False)

    def _investigar(self, consulta: str, max_resultados: int = 4) -> list:
        hallazgos = []
        tema = (consulta or "").strip()

        if self.buscador_web.disponible and tema:
            for r in self.buscador_web.buscar_wikipedia(tema, max_resultados=max_resultados):
                hallazgos.append(r)
                frag = r.get("fragmento") or ""
                if frag:
                    self.aprendizaje.integrar_conocimiento_web(
                        tema=r.get("titulo") or tema,
                        resumen=frag,
                        fuente=r.get("url", "web"),
                        puntuacion=r.get("calidad_fuente", 0.9),
                    )
            if not hallazgos:
                for r in self.buscador_web.buscar(tema, max_resultados=max_resultados):
                    hallazgos.append(r)

        tema_toks = set(nlp.palabras_clave(tema))
        for sim, entrada in self.memoria.buscar_conocimiento_similar(tema, top_n=5):
            if sim < 0.15:
                continue
            resumen = entrada.get("resumen", "")
            fuente = entrada.get("fuente", "memoria")
            if fuente in ("identidad",) and not (tema_toks & {"alex", "diego"}):
                continue
            res_toks = set(nlp.palabras_clave(resumen + " " + entrada.get("tema", "")))
            if tema_toks and not (tema_toks & res_toks):
                continue
            hallazgos.append({
                "titulo": entrada.get("tema", tema),
                "fragmento": resumen,
                "url": fuente,
                "origen": "memoria",
            })

        return hallazgos

    def responder(self, texto_usuario: str) -> str:
        texto_usuario = texto_usuario.strip()
        lang = mod_idioma.detectar_idioma(texto_usuario)
        self._idioma_actual = lang

        if not texto_usuario:
            return mod_idioma.msg(lang, "vacio")

        self.conversacion.agregar_mensaje("usuario", texto_usuario)
        self.memoria.incrementar_estadistica("mensajes_totales")

        # Codificar mensaje (aprendizaje estructural palabra->codigo)
        self.diccionario.codificar_frase(texto_usuario)

        info = self.aprendizaje.procesar_mensaje_usuario(
            texto_usuario, mensaje_anterior_alex=self._ultimo_mensaje_alex
        )
        self.memoria.guardar()

        if info["correccion_detectada"]:
            respuesta = self.generador.correccion_aceptada()
            self._finalizar_turno(respuesta, {"origen": "aprendizaje", "idioma": lang})
            return respuesta

        if info["definicion_detectada"]:
            # Registrar tambien en diccionario de codigos
            self.diccionario._registrar(
                info["definicion_palabra"],
                glosa=info["definicion_significado"],
            )
            respuesta = self.generador.definicion_aceptada(
                info["definicion_palabra"], info["definicion_significado"]
            )
            self._finalizar_turno(respuesta, {"origen": "aprendizaje", "idioma": lang})
            return respuesta

        if info.get("sinonimo_detectado"):
            respuesta = self.generador.sinonimo_aceptado(
                info["sinonimo_palabra"], info["sinonimo_de"]
            )
            self._finalizar_turno(respuesta, {"origen": "aprendizaje", "idioma": lang})
            return respuesta

        if PATRON_IDENTIDAD.search(texto_usuario):
            if lang == "en":
                respuesta = (
                    "I am Alex, a local client-side AI created by Diego Ar for Game Boys Studios. "
                    "I learn, use a word-code dictionary, and look up knowledge when needed."
                )
            else:
                respuesta = self.generador.identidad()
            self._finalizar_turno(respuesta, {"origen": "identidad", "idioma": lang})
            return respuesta

        # Chat natural (es principalmente; en otros idiomas eco simple)
        if lang == "es":
            intencion, respuesta_chat = chat_natural.detectar_intencion(texto_usuario)
            if respuesta_chat:
                self._finalizar_turno(
                    respuesta_chat, {"origen": "chat", "intencion": intencion, "idioma": lang}
                )
                return respuesta_chat
        else:
            # Mini-chat en ingles
            low = texto_usuario.lower()
            if re.search(r"\b(hi|hello|hey)\b", low):
                r = "Hi! I am Alex. How can I help you?"
                self._finalizar_turno(r, {"origen": "chat", "idioma": lang})
                return r
            if re.search(r"\b(thanks|thank you)\b", low):
                r = "You are welcome!"
                self._finalizar_turno(r, {"origen": "chat", "idioma": lang})
                return r
            if re.search(r"\b(bye|goodbye)\b", low):
                r = "Goodbye! See you later."
                self._finalizar_turno(r, {"origen": "chat", "idioma": lang})
                return r
            if re.search(r"\b(how are you)\b", low):
                r = "I am doing well, thanks! Ready to help. And you?"
                self._finalizar_turno(r, {"origen": "chat", "idioma": lang})
                return r

        if PATRON_TAREA.search(texto_usuario.strip()):
            tema = self.generador._limpiar_pedido(texto_usuario)
            investigacion = self._investigar(tema or texto_usuario, max_resultados=4)
            respuesta = self.generador.generar_tarea(texto_usuario, investigacion=investigacion)
            self._finalizar_turno(respuesta, {"origen": "generacion", "idioma": lang})
            return respuesta

        contexto_reciente = self.conversacion.contexto_reciente()
        candidatos = []
        similares = self.memoria.buscar_conocimiento_similar(texto_usuario, top_n=3)
        for sim, entrada in similares:
            if sim < 0.12:
                continue
            candidatos.append({
                "texto": entrada["resumen"],
                "origen": "memoria",
                "fuente": entrada.get("fuente", "memoria interna"),
                "calidad_fuente": 1.0,
                "sim": sim,
            })

        mejor_memoria = (
            self.probabilidad.elegir_mejor(texto_usuario, candidatos, contexto_reciente)
            if candidatos else None
        )

        es_conocimiento = chat_natural.es_pregunta_de_conocimiento(texto_usuario)
        # En ingles, detectar what is / who is
        if lang == "en" and re.search(r"\b(what is|who is|what's|define)\b", texto_usuario, re.I):
            es_conocimiento = True

        usar_web = es_conocimiento and (
            (not mejor_memoria) or (mejor_memoria["puntuacion"] < UMBRAL_USAR_MEMORIA_DIRECTA)
        )

        candidato_elegido = mejor_memoria
        origen_final = "memoria"

        if usar_web:
            resultados_web = self.buscador_web.buscar(texto_usuario)
            for palabra in (info.get("palabras_desconocidas") or [])[:2]:
                extra = self.buscador_web.explicar_palabra(palabra)
                if extra:
                    resultados_web.append(extra)

            candidatos_web = []
            for r in resultados_web:
                texto_candidato = r.get("fragmento") or r.get("titulo")
                if not texto_candidato:
                    continue
                candidatos_web.append({
                    "texto": texto_candidato,
                    "origen": r.get("origen", "web"),
                    "fuente": r.get("url", ""),
                    "calidad_fuente": r.get("calidad_fuente", 0.5),
                    "titulo": r.get("titulo", ""),
                })

            mejor_web = (
                self.probabilidad.elegir_mejor(texto_usuario, candidatos_web, contexto_reciente)
                if candidatos_web else None
            )

            if mejor_web and (not mejor_memoria or mejor_web["puntuacion"] > mejor_memoria["puntuacion"]):
                candidato_elegido = mejor_web
                origen_final = mejor_web.get("origen", "web")
                tema = mejor_web.get("titulo") or texto_usuario
                self.aprendizaje.integrar_conocimiento_web(
                    tema=tema,
                    resumen=mejor_web["texto"],
                    fuente=mejor_web["fuente"],
                    puntuacion=max(mejor_web["puntuacion"], 0.85),
                )

        partes = []
        if candidato_elegido and candidato_elegido["puntuacion"] >= UMBRAL_MINIMO_ACEPTABLE:
            if origen_final == "wikipedia":
                partes.append(
                    self.generador.respuesta_wikipedia(
                        candidato_elegido["texto"], candidato_elegido.get("fuente", "")
                    )
                )
            elif origen_final == "web":
                partes.append(
                    self.generador.respuesta_web(
                        candidato_elegido["texto"], candidato_elegido["fuente"]
                    )
                )
            else:
                resumen = candidato_elegido["texto"]
                if len(resumen) < 180:
                    partes.append(resumen)
                else:
                    partes.append(self.generador.respuesta_conocimiento(resumen))
        else:
            # 1) Intentar diccionario / codigos sobre palabras clave
            respuesta_dict = self.diccionario.responder_con_codigos(texto_usuario, idioma=lang)
            if respuesta_dict:
                partes.append(respuesta_dict)
            else:
                # 2) Palabras desconocidas: resolver una a una
                descs = info.get("palabras_desconocidas") or []
                if descs:
                    partes.append(
                        self.diccionario.resolver_desconocida(descs[0], idioma=lang)
                    )
                elif not es_conocimiento or chat_natural.parece_charla(texto_usuario):
                    if lang == "es":
                        partes.append(chat_natural.respuesta_eco_conversacional(texto_usuario))
                    else:
                        partes.append(mod_idioma.msg(lang, "sin_info"))
                else:
                    partes.append(mod_idioma.msg(lang, "sin_info"))

        respuesta_final = self.generador.combinar(partes)
        extra = {
            "origen": origen_final if candidato_elegido else "dict_o_chat",
            "puntuacion": candidato_elegido["puntuacion"] if candidato_elegido else 0.0,
            "idioma": lang,
            "codigos": self.diccionario.codificar_frase(texto_usuario)[:12],
        }
        self._finalizar_turno(respuesta_final, extra)
        return respuesta_final

    def _finalizar_turno(self, respuesta: str, extra: dict = None):
        self.conversacion.agregar_mensaje("alex", respuesta, extra)
        self._ultimo_mensaje_alex = respuesta
        try:
            self.memoria.guardar()
        except Exception as e:
            print(f"[Alex] No se pudo guardar memoria: {e}")

    def retroalimentacion(self, positiva: bool):
        ultimo = self.conversacion.mensajes[-1] if self.conversacion.mensajes else None
        origen = (ultimo.get("extra", {}) or {}).get("origen", "memoria") if ultimo else "memoria"
        self.probabilidad.ajustar_pesos(positiva, origen)
        self.memoria.guardar()

    def borrar_memoria(self):
        self.memoria.borrar_todo()
        sembrar_conocimiento(self.memoria, forzar=True)
        self.diccionario = DiccionarioCodigos(self.memoria)

    def resembrar_conocimiento(self):
        return sembrar_conocimiento(self.memoria, forzar=True)

    def exportar_conversacion(self, ruta_destino: str):
        self.conversacion.exportar(ruta_destino)

    def estadisticas(self) -> dict:
        return dict(self.memoria.datos.get("estadisticas", {}))

    def resumen_memoria(self) -> dict:
        d = self.memoria.datos
        return {
            "backend": self.backend,
            "ruta_datos": str(self.directorio_datos),
            "idioma_ultimo": self._idioma_actual,
            "mensajes_totales": d.get("estadisticas", {}).get("mensajes_totales", 0),
            "conversaciones_totales": d.get("estadisticas", {}).get("conversaciones_totales", 0),
            "palabras": len(d.get("diccionario", {})),
            "temas": len(d.get("conocimiento", {})),
            "sinonimos": sum(len(v) for v in d.get("sinonimos", {}).values()) // 2,
            "diccionario_codigos": self.diccionario.estadisticas(),
            "temas_ejemplo": list(d.get("conocimiento", {}).keys())[:15],
            "palabras_ejemplo": list(d.get("diccionario", {}).keys())[:15],
            "semilla": bool(d.get("preferencias", {}).get("semilla_conocimiento_v1")),
        }
