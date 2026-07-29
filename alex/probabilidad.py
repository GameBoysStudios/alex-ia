# -*- coding: utf-8 -*-
"""Probabilidad de candidatos de respuesta (tolerante a datos raros)."""

from alex import nlp


class MotorProbabilidad:
    def __init__(self, memoria):
        self.memoria = memoria
        default = {
            "similitud": 0.35,
            "coincidencia_palabras": 0.20,
            "contexto": 0.15,
            "historial_usuario": 0.10,
            "info_aprendida": 0.10,
            "calidad_fuente": 0.10,
        }
        pesos = self.memoria.get_preferencia("pesos_probabilidad", default)
        if not isinstance(pesos, dict):
            pesos = default
        for k, v in default.items():
            pesos.setdefault(k, v)
        self.pesos = pesos

    def guardar_pesos(self):
        try:
            self.memoria.set_preferencia("pesos_probabilidad", self.pesos)
        except Exception:
            pass

    def puntuar_candidato(
        self,
        pregunta: str,
        candidato_texto: str,
        contexto_reciente: str = "",
        origen: str = "memoria",
        calidad_fuente: float = 0.5,
    ) -> float:
        try:
            candidato_texto = candidato_texto or ""
            pregunta = pregunta or ""
            frecuencias = self.memoria.frecuencias_counter()
            mapa_sin = self.memoria.mapa_sinonimos()

            similitud = nlp.similitud_ponderada(pregunta, candidato_texto, frecuencias, mapa_sin)
            coincidencias = nlp.contar_coincidencias(pregunta, candidato_texto, mapa_sin)
            max_posibles = max(len(nlp.palabras_clave(pregunta)), 1)
            coincidencia_norm = min(coincidencias / max_posibles, 1.0)

            contexto_sim = (
                nlp.similitud_jaccard(contexto_reciente, candidato_texto, mapa_sin)
                if contexto_reciente else 0.0
            )

            tema_conocido = self.memoria.buscar_conocimiento(pregunta)
            historial_score = 0.0
            if isinstance(tema_conocido, dict):
                historial_score = min((tema_conocido.get("veces_usado", 0) or 0) / 5.0, 1.0)

            info_aprendida_score = {
                "memoria": 1.0,
                "deduccion": 0.5,
                "web": 0.3,
                "wikipedia": 0.35,
            }.get(origen, 0.3)

            try:
                calidad = float(calidad_fuente) if origen in ("web", "wikipedia") else 1.0
            except (TypeError, ValueError):
                calidad = 0.5

            puntuacion = (
                self.pesos.get("similitud", 0.35) * similitud
                + self.pesos.get("coincidencia_palabras", 0.2) * coincidencia_norm
                + self.pesos.get("contexto", 0.15) * contexto_sim
                + self.pesos.get("historial_usuario", 0.1) * historial_score
                + self.pesos.get("info_aprendida", 0.1) * info_aprendida_score
                + self.pesos.get("calidad_fuente", 0.1) * calidad
            )
            return round(min(max(puntuacion, 0.0), 1.0), 4)
        except Exception as e:
            print(f"[Alex] Error puntuando candidato: {e}")
            return 0.0

    def elegir_mejor(self, pregunta: str, candidatos: list, contexto_reciente: str = "") -> dict:
        if not candidatos:
            return None
        mejores = []
        for c in candidatos:
            if not isinstance(c, dict):
                continue
            texto = c.get("texto") or c.get("resumen") or ""
            if not texto:
                continue
            score = self.puntuar_candidato(
                pregunta,
                str(texto),
                contexto_reciente or "",
                origen=c.get("origen", "memoria"),
                calidad_fuente=c.get("calidad_fuente", 0.5),
            )
            mejores.append({**c, "texto": str(texto), "puntuacion": score})
        if not mejores:
            return None
        mejores.sort(key=lambda x: x.get("puntuacion", 0), reverse=True)
        return mejores[0]

    def ajustar_pesos(self, retroalimentacion_positiva: bool, origen_usado: str):
        clave_relacionada = {
            "memoria": "info_aprendida",
            "deduccion": "info_aprendida",
            "web": "calidad_fuente",
            "wikipedia": "calidad_fuente",
        }.get(origen_usado, "info_aprendida")

        delta = 0.01 if retroalimentacion_positiva else -0.01
        self.pesos[clave_relacionada] = min(
            max(self.pesos.get(clave_relacionada, 0.1) + delta, 0.01), 0.9
        )

        total = sum(self.pesos.values()) or 1.0
        factor = 1.0 / total
        self.pesos = {k: round(v * factor, 4) for k, v in self.pesos.items()}
        self.guardar_pesos()
