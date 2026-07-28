# -*- coding: utf-8 -*-
"""Nucleo de Alex: memoria, aprendizaje, Wikipedia y generacion con investigacion."""

import os
import re

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

PATRON_IDENTIDAD = re.compile(
    r"\b(quien eres|quién eres|que eres|qué eres|quien te (creo|creó|hizo|programo|programó)|"
    r"quién te (creo|creó|hizo|programo|programó)|tu creador|quién es diego|quien es diego|"
    r"qué es alex|que es alex|presentate|preséntate|tu nombre)\b",
    re.IGNORECASE,
)

PATRON_TAREA = re.compile(
    r"^(genera|generame|genérame|escribe|escribeme|escríbeme|redacta|redactame|"
    r"haz|hazme|crea|creame|créame|inventa|inventame|dame|prepara|preparame|"
    r"armame|arma|propón|propon|sugiere|explica|explicame|explícame|cuentame|"
    r"cuéntame|describe|planifica|plan|guia|guía)\b",
    re.IGNORECASE,
)


def _ruta_datos_por_defecto() -> str:
    # 1) Variable de entorno (Render disk o ruta custom)
    env = os.environ.get("ALEX_DATA_DIR") or os.environ.get("DATA_DIR")
    if env:
        return env
    # 2) Carpeta data/ en la raiz del proyecto (junto a web_server.py)
    raiz = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(raiz, "data")


class Alex:
    def __init__(self, directorio_datos: str = None):
        directorio_datos = directorio_datos or _ruta_datos_por_defecto()
        self.directorio_datos = directorio_datos
        self.almacenamiento = AlmacenamientoJSON(directorio_datos)
        self.memoria = Memoria(self.almacenamiento)
        self.conversacion = Conversacion(self.almacenamiento)
        self.aprendizaje = MotorAprendizaje(self.memoria)
        self.probabilidad = MotorProbabilidad(self.memoria)
        self.buscador_web = BuscadorWeb()
        self.generador = GeneradorLenguaje(self.memoria)
        self._ultimo_mensaje_alex = None

        # Solo contar conversacion nueva si el archivo no existia con datos
        stats = self.memoria.datos.get("estadisticas", {})
        if stats.get("conversaciones_totales", 0) == 0 and stats.get("mensajes_totales", 0) == 0:
            self.memoria.incrementar_estadistica("conversaciones_totales")

        # Sembrar identidad sin usar buscar_conocimiento (no inflar contadores)
        conoc = self.memoria.datos.setdefault("conocimiento", {})
        if "quien eres" not in conoc and "quién eres" not in conoc:
            self.memoria.guardar_conocimiento(
                tema="quien eres",
                resumen=(
                    "Alex es una IA local en cliente creada por Diego Ar para Game Boys Studios. "
                    "Aprende, consulta Wikipedia/internet y genera estructuras con la info hallada."
                ),
                fuente="identidad",
                puntuacion=1.0,
            )
            self.memoria.guardar_conocimiento(
                tema="diego ar",
                resumen="Diego Ar es el creador de Alex, la IA local de Game Boys Studios.",
                fuente="identidad",
                puntuacion=1.0,
            )
        self.memoria.guardar()

    def _investigar(self, consulta: str, max_resultados: int = 4) -> list:
        hallazgos = []
        for _, entrada in self.memoria.buscar_conocimiento_similar(consulta, top_n=2):
            hallazgos.append({
                "titulo": entrada.get("tema", consulta),
                "fragmento": entrada.get("resumen", ""),
                "url": entrada.get("fuente", "memoria"),
                "origen": "memoria",
            })
        if self.buscador_web.disponible:
            for r in self.buscador_web.buscar(consulta, max_resultados=max_resultados):
                hallazgos.append(r)
                frag = r.get("fragmento") or ""
                if frag:
                    self.aprendizaje.integrar_conocimiento_web(
                        tema=r.get("titulo") or consulta,
                        resumen=frag,
                        fuente=r.get("url", "web"),
                        puntuacion=r.get("calidad_fuente", 0.8),
                    )
        return hallazgos

    def responder(self, texto_usuario: str) -> str:
        texto_usuario = texto_usuario.strip()
        if not texto_usuario:
            return "Puedes escribir algo? No he recibido ningun texto."

        self.conversacion.agregar_mensaje("usuario", texto_usuario)
        self.memoria.incrementar_estadistica("mensajes_totales")

        info = self.aprendizaje.procesar_mensaje_usuario(
            texto_usuario, mensaje_anterior_alex=self._ultimo_mensaje_alex
        )
        # Guardar aprendizaje inmediato (vocabulario, definiciones, etc.)
        self.memoria.guardar()

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

        if PATRON_IDENTIDAD.search(texto_usuario):
            respuesta = self.generador.identidad()
            self._finalizar_turno(respuesta)
            return respuesta

        if PATRON_TAREA.search(texto_usuario.strip()):
            tema = self.generador._limpiar_pedido(texto_usuario)
            investigacion = self._investigar(tema or texto_usuario, max_resultados=4)
            respuesta = self.generador.generar_tarea(texto_usuario, investigacion=investigacion)
            self._finalizar_turno(respuesta, {"origen": "generacion"})
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
                partes.append("(Sin internet ahora; solo memoria local.)")

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

    def exportar_conversacion(self, ruta_destino: str):
        self.conversacion.exportar(ruta_destino)

    def estadisticas(self) -> dict:
        return dict(self.memoria.datos.get("estadisticas", {}))

    def resumen_memoria(self) -> dict:
        d = self.memoria.datos
        return {
            "ruta_datos": self.directorio_datos,
            "mensajes_totales": d.get("estadisticas", {}).get("mensajes_totales", 0),
            "conversaciones_totales": d.get("estadisticas", {}).get("conversaciones_totales", 0),
            "palabras": len(d.get("diccionario", {})),
            "temas": len(d.get("conocimiento", {})),
            "sinonimos": sum(len(v) for v in d.get("sinonimos", {}).values()) // 2,
            "temas_ejemplo": list(d.get("conocimiento", {}).keys())[:10],
            "palabras_ejemplo": list(d.get("diccionario", {}).keys())[:10],
        }
