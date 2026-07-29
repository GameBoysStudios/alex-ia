# -*- coding: utf-8 -*-
"""
Capa neuronal de Alex Pro 2.0 (gratis, sin APIs de pago).

1) Red local (MLP puro Python, sin numpy):
   - Clasifica intencion del mensaje
   - Aprende con retroalimentacion (+/-)
   - Pesos guardados en memoria/Firebase

2) Cerebro remoto opcional (Hugging Face Inference, gratis):
   - Si la respuesta base es pobre, genera texto con un modelo pequeno
   - Requiere HF_TOKEN (cuenta gratuita en huggingface.co)
   - Modelo por defecto: google/flan-t5-base (instrucciones)

No carga modelos gigantes en Render (no caben en free tier).
"""

from __future__ import annotations

import math
import os
import random
import re
from typing import Any, Dict, List, Optional, Tuple

try:
    import requests
    REQUESTS_OK = True
except ImportError:
    REQUESTS_OK = False

# -------- utilidades vectoriales (sin numpy) --------

def _dot(a: List[float], b: List[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def _sigmoid(x: float) -> float:
    if x >= 20:
        return 1.0
    if x <= -20:
        return 0.0
    return 1.0 / (1.0 + math.exp(-x))


def _softmax(xs: List[float]) -> List[float]:
    if not xs:
        return []
    m = max(xs)
    exps = [math.exp(x - m) for x in xs]
    s = sum(exps) or 1.0
    return [e / s for e in exps]


# Vocabulario / rasgos simples para el MLP local
_INTENCIONES = [
    "saludo",
    "despedida",
    "pregunta",
    "calculo",
    "definicion",
    "generacion",
    "lugar",
    "traduccion",
    "chat",
    "otro",
]

_LEX_RASGOS = [
    # saludo
    ("hola", 0), ("buenas", 0), ("hey", 0), ("hello", 0), ("hi", 0),
    # despedida
    ("adios", 1), ("chao", 1), ("bye", 1), ("hasta", 1),
    # pregunta / definicion
    ("que", 2), ("qué", 2), ("como", 2), ("cómo", 2), ("por", 2),
    ("why", 2), ("what", 2), ("how", 2), ("quien", 2), ("quién", 2),
    ("significa", 4), ("define", 4), ("definicion", 4), ("definición", 4),
    # calculo
    ("calcula", 3), ("cuanto", 3), ("cuánto", 3), ("suma", 3),
    ("multiplica", 3), ("divide", 3), ("raiz", 3), ("sqrt", 3),
    # generacion
    ("genera", 5), ("escribe", 5), ("lista", 5), ("hazme", 5),
    ("crea", 5), ("redacta", 5), ("historia", 5),
    # lugar
    ("donde", 6), ("dónde", 6), ("mapa", 6), ("calle", 6),
    ("ciudad", 6), ("lugar", 6), ("direccion", 6), ("dirección", 6),
    # traduccion
    ("traduce", 7), ("translate", 7), ("ingles", 7), ("inglés", 7),
    # chat
    ("gracias", 8), ("porfa", 8), ("ayuda", 8), ("ok", 8),
]

DIM_IN = 24  # rasgos fijos
DIM_H = 16


def _vectorizar(texto: str) -> List[float]:
    t = (texto or "").lower()
    v = [0.0] * DIM_IN
    # conteo por intencion heuristica
    for palabra, idx in _LEX_RASGOS:
        if palabra in t:
            slot = min(idx, DIM_IN - 5)
            v[slot] += 1.0
    # estadisticas del texto
    toks = re.findall(r"[a-záéíóúñüA-ZÁÉÍÓÚÑÜ0-9]+", t)
    n = max(len(toks), 1)
    v[10] = min(len(t) / 120.0, 1.5)
    v[11] = min(n / 20.0, 1.5)
    v[12] = 1.0 if "?" in (texto or "") or "¿" in (texto or "") else 0.0
    v[13] = 1.0 if re.search(r"\d", t) else 0.0
    v[14] = 1.0 if re.search(r"[+−\-*/^=%]", t) else 0.0
    v[15] = 1.0 if any(w in t for w in ("por favor", "please", "puedes")) else 0.0
    # bag de bigramas simples hash
    for i, tok in enumerate(toks[:12]):
        h = sum(ord(c) for c in tok) % 8
        v[16 + h] += 0.35
    # normalizar un poco
    norma = math.sqrt(sum(x * x for x in v)) or 1.0
    return [x / norma for x in v]


class MLPLocal:
    """Perceptron multicapa minimo: entrada -> oculta -> softmax intenciones."""

    def __init__(self, seed: int = 42):
        rng = random.Random(seed)
        self.W1 = [[rng.uniform(-0.3, 0.3) for _ in range(DIM_IN)] for _ in range(DIM_H)]
        self.b1 = [0.0] * DIM_H
        self.W2 = [[rng.uniform(-0.3, 0.3) for _ in range(DIM_H)] for _ in range(len(_INTENCIONES))]
        self.b2 = [0.0] * len(_INTENCIONES)
        self.lr = 0.08
        self.entrenamientos = 0

    def forward(self, x: List[float]) -> Tuple[List[float], List[float], List[float]]:
        h_raw = [_dot(self.W1[j], x) + self.b1[j] for j in range(DIM_H)]
        h = [_sigmoid(v) for v in h_raw]
        logits = [_dot(self.W2[k], h) + self.b2[k] for k in range(len(_INTENCIONES))]
        probs = _softmax(logits)
        return h, logits, probs

    def predecir(self, texto: str) -> Dict[str, Any]:
        x = _vectorizar(texto)
        _, _, probs = self.forward(x)
        mejor = max(range(len(probs)), key=lambda i: probs[i])
        ranking = sorted(
            [{"intencion": _INTENCIONES[i], "prob": round(probs[i], 4)} for i in range(len(probs))],
            key=lambda d: -d["prob"],
        )
        return {
            "intencion": _INTENCIONES[mejor],
            "confianza": round(probs[mejor], 4),
            "ranking": ranking[:5],
            "motor": "mlp_local",
        }

    def aprender(self, texto: str, intencion_objetivo: str, positiva: bool = True) -> None:
        if intencion_objetivo not in _INTENCIONES:
            return
        target_i = _INTENCIONES.index(intencion_objetivo)
        x = _vectorizar(texto)
        h, logits, probs = self.forward(x)

        # Gradiente softmax + cross-entropy (o empujar/alejar)
        dlogits = list(probs)
        if positiva:
            dlogits[target_i] -= 1.0
        else:
            # penalizar la intencion predicha si feedback negativo
            pred = max(range(len(probs)), key=lambda i: probs[i])
            dlogits[pred] += 0.5
            dlogits[target_i] -= 0.3

        # capa salida
        d_h = [0.0] * DIM_H
        for k in range(len(_INTENCIONES)):
            for j in range(DIM_H):
                self.W2[k][j] -= self.lr * dlogits[k] * h[j]
                d_h[j] += dlogits[k] * self.W2[k][j]
            self.b2[k] -= self.lr * dlogits[k]

        # capa oculta
        for j in range(DIM_H):
            grad = d_h[j] * h[j] * (1.0 - h[j])
            for i in range(DIM_IN):
                self.W1[j][i] -= self.lr * grad * x[i]
            self.b1[j] -= self.lr * grad

        self.entrenamientos += 1

    def serializar(self) -> dict:
        return {
            "W1": self.W1,
            "b1": self.b1,
            "W2": self.W2,
            "b2": self.b2,
            "entrenamientos": self.entrenamientos,
            "lr": self.lr,
        }

    def cargar(self, data: dict) -> None:
        if not data:
            return
        try:
            self.W1 = data.get("W1") or self.W1
            self.b1 = data.get("b1") or self.b1
            self.W2 = data.get("W2") or self.W2
            self.b2 = data.get("b2") or self.b2
            self.entrenamientos = int(data.get("entrenamientos") or 0)
            self.lr = float(data.get("lr") or self.lr)
        except Exception as e:
            print(f"[Alex NN] No se pudieron cargar pesos: {e}")


class CerebroHF:
    """Generacion de texto con Hugging Face Inference API (gratis)."""

    def __init__(self, timeout: int = 45):
        self.timeout = timeout
        self.token = (os.environ.get("HF_TOKEN") or os.environ.get("HUGGINGFACE_TOKEN") or "").strip()
        self.modelo = os.environ.get(
            "HF_TEXT_MODEL",
            "google/flan-t5-base",
        )
        self.disponible = REQUESTS_OK  # token opcional pero recomendado
        self.url = f"https://api-inference.huggingface.co/models/{self.modelo}"

    def _headers(self) -> dict:
        h = {"Content-Type": "application/json"}
        if self.token:
            h["Authorization"] = f"Bearer {self.token}"
        return h

    def generar(self, prompt: str, idioma: str = "es", max_new_tokens: int = 180) -> dict:
        if not self.disponible or not prompt:
            return {"ok": False, "error": "no_disponible"}

        if idioma == "en":
            instruccion = (
                "Answer clearly and helpfully in English. "
                "If you are unsure, say so briefly.\n\n"
                f"User: {prompt}\nAssistant:"
            )
        else:
            instruccion = (
                "Responde en espanol, claro y util. "
                "Si no estas seguro, dilo en una frase breve.\n\n"
                f"Usuario: {prompt}\nAsistente:"
            )

        payload = {
            "inputs": instruccion,
            "parameters": {
                "max_new_tokens": max_new_tokens,
                "temperature": 0.4,
                "return_full_text": False,
            },
            "options": {"wait_for_model": True},
        }

        try:
            r = requests.post(
                self.url,
                headers=self._headers(),
                json=payload,
                timeout=self.timeout,
            )
            if r.status_code == 503:
                return {
                    "ok": False,
                    "error": "modelo_cargando",
                    "texto": (
                        "La red neuronal en la nube se esta despertando. "
                        "Prueba de nuevo en 20-30 segundos."
                        if idioma != "en"
                        else "Cloud neural model is loading. Retry in 20-30s."
                    ),
                }
            if r.status_code == 401:
                return {
                    "ok": False,
                    "error": "token",
                    "texto": (
                        "Para el cerebro neuronal completo, anade HF_TOKEN "
                        "(gratis en huggingface.co) en Render."
                        if idioma != "en"
                        else "Set free HF_TOKEN on Render for full neural brain."
                    ),
                }
            if r.status_code != 200:
                return {"ok": False, "error": f"http_{r.status_code}", "texto": r.text[:200]}

            data = r.json()
            texto = ""
            if isinstance(data, list) and data:
                item = data[0]
                texto = (
                    item.get("generated_text")
                    or item.get("summary_text")
                    or item.get("translation_text")
                    or ""
                )
            elif isinstance(data, dict):
                if data.get("error"):
                    return {"ok": False, "error": str(data["error"]), "texto": str(data["error"])}
                texto = data.get("generated_text") or ""

            texto = (texto or "").strip()
            # Limpiar eco del prompt
            for sep in ("Asistente:", "Assistant:", "Respuesta:"):
                if sep in texto:
                    texto = texto.split(sep)[-1].strip()
            if not texto:
                return {"ok": False, "error": "vacio"}

            return {
                "ok": True,
                "texto": texto[:1200],
                "motor": f"hf:{self.modelo}",
            }
        except Exception as e:
            return {"ok": False, "error": str(e)}


class RedNeuronalPro:
    """Fachada: MLP local + cerebro HF opcional."""

    def __init__(self, memoria=None):
        self.memoria = memoria
        self.mlp = MLPLocal()
        self.hf = CerebroHF()
        self._cargar_pesos()

    def _cargar_pesos(self) -> None:
        if not self.memoria:
            return
        try:
            prefs = self.memoria.datos.get("preferencias", {}) or {}
            pesos = prefs.get("nn_pro_pesos")
            if pesos:
                self.mlp.cargar(pesos)
        except Exception as e:
            print(f"[Alex NN] carga: {e}")

    def guardar_pesos(self) -> None:
        if not self.memoria:
            return
        try:
            prefs = self.memoria.datos.setdefault("preferencias", {})
            prefs["nn_pro_pesos"] = self.mlp.serializar()
            self.memoria.guardar()
        except Exception as e:
            print(f"[Alex NN] guardar pesos: {e}")

    def analizar_intencion(self, texto: str) -> dict:
        return self.mlp.predecir(texto)

    def reforzar(self, texto: str, intencion: str = None, positiva: bool = True) -> None:
        pred = self.mlp.predecir(texto)
        obj = intencion or pred.get("intencion") or "otro"
        self.mlp.aprender(texto, obj, positiva=positiva)
        if self.mlp.entrenamientos % 3 == 0:
            self.guardar_pesos()

    def _respuesta_pobre(self, respuesta: str) -> bool:
        r = (respuesta or "").lower()
        if not r or len(r) < 12:
            return True
        marcas = (
            "no tengo informacion",
            "no se suficiente",
            "sin info",
            "relacionado con:",
            "ensename:",
            "enséñame:",
            "no encontre",
            "no encontré",
            "no pude",
            "i don't know",
            "i do not know",
            "no information",
        )
        return any(m in r for m in marcas)

    def mejorar_respuesta(
        self,
        texto_usuario: str,
        respuesta_base: str,
        idioma: str = "es",
        forzar_nn: bool = False,
    ) -> dict:
        """
        Si la respuesta base es debil, intenta el cerebro HF.
        Siempre anota la intencion del MLP local.
        """
        intent = self.analizar_intencion(texto_usuario)
        out = {
            "intencion": intent,
            "usada_nn": False,
            "respuesta": respuesta_base,
            "motor": "base",
        }

        if not forzar_nn and not self._respuesta_pobre(respuesta_base):
            return out

        # No sustituir calculos correctos ni respuestas RAE largas
        if respuesta_base and (
            respuesta_base.strip().startswith("Resultado:")
            or respuesta_base.strip().startswith("Result:")
            or "Segun la RAE" in respuesta_base
            or "Según la RAE" in respuesta_base
        ):
            return out

        gen = self.hf.generar(texto_usuario, idioma=idioma)
        if gen.get("ok") and gen.get("texto"):
            nota = (
                "\n\n— (respuesta asistida por red neuronal Pro)"
                if idioma != "en"
                else "\n\n— (Pro neural-assisted answer)"
            )
            out["respuesta"] = gen["texto"] + nota
            out["usada_nn"] = True
            out["motor"] = gen.get("motor", "hf")
            return out

        # Si HF fallo pero dejo mensaje util (modelo cargando / token)
        if gen.get("texto") and self._respuesta_pobre(respuesta_base):
            out["respuesta"] = (respuesta_base or "") + "\n\n" + gen["texto"]
            out["motor"] = "base+aviso_nn"
        return out
