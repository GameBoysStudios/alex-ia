# -*- coding: utf-8 -*-
"""
Núcleo de Alex: conecta memoria, conversación, aprendizaje, NLP, probabilidad,
búsqueda web y generación de lenguaje para producir una respuesta ante cada
mensaje del usuario.

Flujo por cada mensaje del usuario:
1. Se registra el mensaje y se pasa por el motor de aprendizaje
   (vocabulario, relaciones, detección de corrección / definición).
2. Se buscan candidatos de respuesta:
   a) Conocimiento ya guardado en memoria (buscar_conocimiento_similar).
   b) Si la similitud es baja, se realiza una búsqueda web y se generan
      candidatos a partir de los resultados.
3. Cada candidato se puntúa con el MotorProbabilidad.
4. Se elige el candidato con mayor puntuación y se redacta la respuesta
   final con el GeneradorLenguaje.
5. Se guarda el resumen aprendido (si vino de la web) y se actualiza
   la conversación / estadísticas.
"""

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

    # ------------------------------------------------------------------
    def responder(self, texto_usuario: str) -> str:
        texto_usuario = texto_usuario.strip()
        if not texto_usuario:
            return "¿Puedes escribir algo? No he recibido ningún texto."

        self.conversacion.agregar_mensaje("usuario", texto_usuario)
        self.memoria.incrementar_estadistica("mensajes_totales")

        # 1) Aprendizaje incremental sobre el mensaje entrante.
        info_aprendizaje = self.aprendizaje.procesar_mensaje_usuario(
            texto_usuario, mensaje_anterior_alex=self._ultimo_mensaje_alex
        )

        # Si el usuario está corrigiendo, respondemos y terminamos el turno.
        if info_aprendizaje["correccion_detectada"]:
            respuesta = self.generador.correccion_aceptada()
            self._finalizar_turno(respuesta)
            return respuesta

        # Si el usuario está enseñando una definición, confirmamos y terminamos.
        if info_aprendizaje["definicion_detectada"]:
            respuesta = self.generador.definicion_aceptada(
                info_aprendizaje["definicion_palabra"],
                info_aprendizaje["definicion_significado"],
            )
            self._finalizar_turno(respuesta)
            return respuesta

        # Si el usuario está enseñando un sinónimo, confirmamos y terminamos.
        if info_aprendizaje.get("sinonimo_detectado"):
            respuesta = self.generador.sinonimo_aceptado(
                info_aprendizaje["sinonimo_palabra"],
                info_aprendizaje["sinonimo_de"],
            )
            self._finalizar_turno(respuesta)
            return respuesta

        # Saludo simple (heurística básica).
        texto_norm = nlp.normalizar(texto_usuario)
        if texto_norm in {"hola", "buenas", "hey", "hola alex", "buenos dias", "buenos días"}:
            respuesta = self.generador.saludo()
            self._finalizar_turno(respuesta)
            return respuesta

        # 2) Buscar candidatos en memoria.
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

        mejor_memoria = self.probabilidad.elegir_mejor(texto_usuario, candidatos, contexto_reciente) \
            if candidatos else None

        usar_web = (not mejor_memoria) or (mejor_memoria["puntuacion"] < UMBRAL_USAR_MEMORIA_DIRECTA)

        candidato_elegido = mejor_memoria
        origen_final = "memoria"

        # 3) Si la memoria no es suficiente, buscar en internet.
        if usar_web:
            resultados_web = self.buscador_web.buscar(texto_usuario)
            candidatos_web = []
            for r in resultados_web:
                texto_candidato = r["fragmento"] or r["titulo"]
                if not texto_candidato:
                    continue
                candidatos_web.append({
                    "texto": texto_candidato,
                    "origen": "web",
                    "fuente": r["url"],
                    "calidad_fuente": r["calidad_fuente"],
                })

            mejor_web = self.probabilidad.elegir_mejor(texto_usuario, candidatos_web, contexto_reciente) \
                if candidatos_web else None

            if mejor_web and (not mejor_memoria or mejor_web["puntuacion"] > mejor_memoria["puntuacion"]):
                candidato_elegido = mejor_web
                origen_final = "web"
                # Guardar el conocimiento aprendido de la web para el futuro.
                self.aprendizaje.integrar_conocimiento_web(
                    tema=texto_usuario,
                    resumen=mejor_web["texto"],
                    fuente=mejor_web["fuente"],
                    puntuacion=mejor_web["puntuacion"],
                )

        # 4) Redactar respuesta final.
        partes_respuesta = []
        if candidato_elegido and candidato_elegido["puntuacion"] >= UMBRAL_MINIMO_ACEPTABLE:
            if origen_final == "web":
                partes_respuesta.append(
                    self.generador.respuesta_web(candidato_elegido["texto"], candidato_elegido["fuente"])
                )
            else:
                partes_respuesta.append(
                    self.generador.respuesta_conocimiento(candidato_elegido["texto"])
                )
        else:
            partes_respuesta.append(self.generador.respuesta_sin_info())
            if not self.buscador_web.disponible:
                partes_respuesta.append(
                    "(No tengo acceso a internet en este momento, así que solo uso mi memoria local.)"
                )

        # Sugerencias ortográficas (si las hay).
        sugerencias = info_aprendizaje.get("sugerencias_ortograficas") or {}
        for palabra_mal, candidatos in list(sugerencias.items())[:2]:
            if candidatos:
                partes_respuesta.append(
                    self.generador.sugerencia_ortografica(palabra_mal, candidatos[0])
                )

        # Mencionar si aprendió una palabra nueva en este turno (solo si no era definición/sinónimo).
        if (info_aprendizaje.get("palabras_desconocidas")
                and not info_aprendizaje.get("definicion_detectada")
                and not info_aprendizaje.get("sinonimo_detectado")
                and not sugerencias):
            palabra_nueva = info_aprendizaje["palabras_desconocidas"][0]
            partes_respuesta.append(self.generador.nota_palabra_nueva(palabra_nueva))

        respuesta_final = self.generador.combinar(partes_respuesta)

        extra = {
            "origen": origen_final if candidato_elegido else "sin_info",
            "puntuacion": candidato_elegido["puntuacion"] if candidato_elegido else 0.0,
        }
        self._finalizar_turno(respuesta_final, extra)

        return respuesta_final

    # ------------------------------------------------------------------
    def _finalizar_turno(self, respuesta: str, extra: dict = None):
        self.conversacion.agregar_mensaje("alex", respuesta, extra)
        self._ultimo_mensaje_alex = respuesta
        self.memoria.guardar()

    def retroalimentacion(self, positiva: bool):
        """Permite ajustar los pesos de probabilidad según si la última respuesta fue útil."""
        ultimo = self.conversacion.mensajes[-1] if self.conversacion.mensajes else None
        origen = (ultimo.get("extra", {}) or {}).get("origen", "memoria") if ultimo else "memoria"
        self.probabilidad.ajustar_pesos(positiva, origen)

    def borrar_memoria(self):
        self.memoria.borrar_todo()

    def exportar_conversacion(self, ruta_destino: str):
        self.conversacion.exportar(ruta_destino)

    def estadisticas(self) -> dict:
        return dict(self.memoria.datos.get("estadisticas", {}))
