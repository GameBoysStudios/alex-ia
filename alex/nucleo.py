# -*- coding: utf-8 -*-
"""Nucleo de Alex: memoria, aprendizaje, NLP, probabilidad, Wikipedia y respuestas."""

import os

from alex.storage import AlmacenamientoJSON
from alex.memoria import Memoria
from alex.conversacion import Conversacion
from alex.aprendizaje import MotorAprendizaje
from alex.probabilidad import MotorProbabilidad
from alex.busqueda_web import BuscadorWeb
from alex.generador import GeneradorLenguaje
from alex import nlp

UMBRAL_USAR_MEMORIA_DIRECTA = 0.55
UMBRAL_MINIMO_ACEPTABLE = 0.20


class Alex:
    def __init__(self, directorio_datos: str = None):
        directorio_datos = directorio_datos or os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "data"
        )
        self.almacenamiento = AlmacenamientoJSON(directorio_datos)
        self.memoria = Memoria(self.almacenamiento)
        self.conversacion = Conversacion(self.almacenamiento)
        self.aprendizaje = MotorAprendizaje(self.memoria)
        self.probabilidad = MotorProbabilidad(self.memoria)
        self.buscador_web = BuscadorWeb()
        self.generador = GeneradorLenguaje(self.memoria)
        self._ultimo_mensaje_alex = None
        self.memoria.incrementar_estadistica("conversaciones_totales")
        self.memoria.guardar()

    def responder(self, texto_usuario: str) -> str:
        texto_usuario = texto_usuario.strip()
        if not texto_usuario:
            return "Puedes escribir algo? No he recibido ningun texto."

        self.conversacion.agregar_mensaje("usuario", texto_usuario)
        self.memoria.incrementar_estadistica("mensajes_totales")

        info = self.aprendizaje.procesar_mensaje_usuario(
            texto_usuario, mensaje_anterior_alex=self._ultimo_mensaje_alex
        )

        if info["correccion_detectada"]:
            respuesta = self.generador.correccion_aceptada()
            self._finalizar_turno(respuesta)
            return respuesta

        if info["definicion_detectada"]:
            respuesta = self.generador.definicion_aceptada(
                info["definicion_palabra"], info["definicion_significado"]
            )
            self._finalizar_turno(respuesta)
            return respuesta

        if info.get("sinonimo_detectado"):
            respuesta = self.generador.sinonimo_aceptado(
                info["sinonimo_palabra"], info["sinonimo_de"]
            )
            self._finalizar_turno(respuesta)
            return respuesta

        texto_norm = nlp.normalizar(texto_usuario)
        if texto_norm in {"hola", "buenas", "hey", "hola alex", "buenos dias", "buenos dias"}:
            respuesta = self.generador.saludo()
            self._finalizar_turno(respuesta)
            return respuesta

        contexto_reciente = self.conversacion.contexto_reciente()
        candidatos = []

        similares = self.memoria.buscar_conocimiento_similar(texto_usuario, top_n=3)
        for _, entrada in similares:
            candidatos.append({
                "texto": entrada["resumen"],
                "origen": "memoria",
                "fuente": entrada.get("fuente", "memoria interna"),
                "calidad_fuente": 1.0,
            })

        mejor_memoria = (
            self.probabilidad.elegir_mejor(texto_usuario, candidatos, contexto_reciente)
            if candidatos else None
        )

        usar_web = (not mejor_memoria) or (mejor_memoria["puntuacion"] < UMBRAL_USAR_MEMORIA_DIRECTA)
        candidato_elegido = mejor_memoria
        origen_final = "memoria"

        if usar_web:
            resultados_web = self.buscador_web.buscar(texto_usuario)

            # Palabras desconocidas: consultar Wikipedia y aprender
            for palabra in (info.get("palabras_desconocidas") or [])[:3]:
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
                for palabra in (info.get("palabras_desconocidas") or []):
                    if (
                        palabra.lower() in (tema or "").lower()
                        or palabra.lower() in mejor_web["texto"].lower()
                    ):
                        self.memoria.marcar_palabra_conocida(
                            palabra, significado=mejor_web["texto"][:200]
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
                partes.append(self.generador.respuesta_conocimiento(candidato_elegido["texto"]))
        else:
            partes.append(self.generador.respuesta_sin_info())
            if not self.buscador_web.disponible:
                partes.append("(No tengo acceso a internet ahora; solo uso mi memoria local.)")

        sugerencias = info.get("sugerencias_ortograficas") or {}
        for palabra_mal, cands in list(sugerencias.items())[:2]:
            if cands:
                partes.append(self.generador.sugerencia_ortografica(palabra_mal, cands[0]))

        respuesta_final = self.generador.combinar(partes)
        extra = {
            "origen": origen_final if candidato_elegido else "sin_info",
            "puntuacion": candidato_elegido["puntuacion"] if candidato_elegido else 0.0,
        }
        self._finalizar_turno(respuesta_final, extra)
        return respuesta_final

    def _finalizar_turno(self, respuesta: str, extra: dict = None):
        self.conversacion.agregar_mensaje("alex", respuesta, extra)
        self._ultimo_mensaje_alex = respuesta
        self.memoria.guardar()

    def retroalimentacion(self, positiva: bool):
        ultimo = self.conversacion.mensajes[-1] if self.conversacion.mensajes else None
        origen = (ultimo.get("extra", {}) or {}).get("origen", "memoria") if ultimo else "memoria"
        self.probabilidad.ajustar_pesos(positiva, origen)

    def borrar_memoria(self):
        self.memoria.borrar_todo()

    def exportar_conversacion(self, ruta_destino: str):
        self.conversacion.exportar(ruta_destino)

    def estadisticas(self) -> dict:
        return dict(self.memoria.datos.get("estadisticas", {}))
