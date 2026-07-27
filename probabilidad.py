# -*- coding: utf-8 -*-
"""
Módulo de Probabilidad para Alex.

Calcula la puntuación de relevancia de cada candidato de respuesta
combinando varias señales:
- Similitud semántica (Jaccard ponderada).
- Coincidencia de palabras clave.
- Contexto (historial reciente de la conversación).
- Historial del usuario (frecuencia con la que se tocó el tema).
- Información aprendida (si viene de memoria propia vs. deducción vs. web).
- Calidad/puntuación de resultados web.

Los pesos se pueden ajustar con el tiempo (aprendizaje de pesos simple).
"""

from alex import nlp


class MotorProbabilidad:
    def __init__(self, memoria):
        self.memoria = memoria
        # Pesos iniciales; se pueden adaptar con self.ajustar_pesos().
        self.pesos = self.memoria.get_preferencia("pesos_probabilidad", {
            "similitud": 0.35,
            "coincidencia_palabras": 0.20,
            "contexto": 0.15,
            "historial_usuario": 0.10,
            "info_aprendida": 0.10,
            "calidad_fuente": 0.10,
        })

    def guardar_pesos(self):
        self.memoria.set_preferencia("pesos_probabilidad", self.pesos)

    def puntuar_candidato(self, pregunta: str, candidato_texto: str, contexto_reciente: str = "",
                           origen: str = "memoria", calidad_fuente: float = 0.5) -> float:
        """
        Calcula una puntuación 0-1 para un candidato de respuesta/información,
        dada la pregunta del usuario.

        origen: "memoria" | "deduccion" | "web"
        calidad_fuente: 0-1, estimación de fiabilidad de la fuente (solo relevante si origen == "web").
        """
        frecuencias = self.memoria.frecuencias_counter()
        mapa_sin = self.memoria.mapa_sinonimos()

        similitud = nlp.similitud_ponderada(pregunta, candidato_texto, frecuencias, mapa_sin)
        coincidencias = nlp.contar_coincidencias(pregunta, candidato_texto, mapa_sin)
        max_posibles = max(len(nlp.palabras_clave(pregunta)), 1)
        coincidencia_norm = min(coincidencias / max_posibles, 1.0)

        contexto_sim = nlp.similitud_jaccard(contexto_reciente, candidato_texto, mapa_sin) if contexto_reciente else 0.0

        # Historial del usuario: cuántas veces se relacionó este tema antes.
        tema_conocido = self.memoria.buscar_conocimiento(pregunta)
        historial_score = min((tema_conocido.get("veces_usado", 0) / 5.0), 1.0) if tema_conocido else 0.0

        info_aprendida_score = {
            "memoria": 1.0,
            "deduccion": 0.5,
            "web": 0.3,
        }.get(origen, 0.3)

        calidad = calidad_fuente if origen == "web" else 1.0

        puntuacion = (
            self.pesos["similitud"] * similitud +
            self.pesos["coincidencia_palabras"] * coincidencia_norm +
            self.pesos["contexto"] * contexto_sim +
            self.pesos["historial_usuario"] * historial_score +
            self.pesos["info_aprendida"] * info_aprendida_score +
            self.pesos["calidad_fuente"] * calidad
        )
        return round(min(max(puntuacion, 0.0), 1.0), 4)

    def elegir_mejor(self, pregunta: str, candidatos: list, contexto_reciente: str = "") -> dict:
        """
        candidatos: lista de dicts {"texto":..., "origen":..., "calidad_fuente":...}
        Devuelve el candidato con mayor puntuación, con la puntuación añadida.
        """
        mejores = []
        for c in candidatos:
            score = self.puntuar_candidato(
                pregunta, c["texto"], contexto_reciente,
                origen=c.get("origen", "memoria"),
                calidad_fuente=c.get("calidad_fuente", 0.5),
            )
            mejores.append({**c, "puntuacion": score})
        mejores.sort(key=lambda x: x["puntuacion"], reverse=True)
        return mejores[0] if mejores else None

    def ajustar_pesos(self, retroalimentacion_positiva: bool, origen_usado: str):
        """
        Ajuste simple de pesos: si una respuesta fue buena, se refuerza un poco
        el peso de la señal dominante asociada a su origen; si fue mala, se reduce.
        """
        clave_relacionada = {
            "memoria": "info_aprendida",
            "deduccion": "info_aprendida",
            "web": "calidad_fuente",
        }.get(origen_usado, "info_aprendida")

        delta = 0.01 if retroalimentacion_positiva else -0.01
        self.pesos[clave_relacionada] = min(max(self.pesos[clave_relacionada] + delta, 0.01), 0.9)

        # Renormalizar para que la suma se mantenga razonable (no estrictamente 1, pero acotada).
        total = sum(self.pesos.values())
        if total > 0:
            factor = 1.0 / total
            self.pesos = {k: round(v * factor, 4) for k, v in self.pesos.items()}

        self.guardar_pesos()
