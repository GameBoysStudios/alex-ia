# -*- coding: utf-8 -*-
"""
Alex Pro 2.0 — vision, PDF, RAE y red neuronal (gratis).

Imagen: BLIP gratis + Pillow local
PDF: pypdf + render escaneo
RAE: definiciones oficiales
Red neuronal:
  - MLP local (aprende intenciones)
  - Cerebro HF opcional (flan-t5, gratis con HF_TOKEN)
"""

import re

from alex.nucleo import Alex
from alex.vision import AnalizadorImagen
from alex.pdf_doc import AnalizadorPDF
from alex.vision_libre import VisionLibre
from alex.rae import DiccionarioRAE
from alex.red_neuronal import RedNeuronalPro
from alex import nlp

_STOP_RAE = {
    "de", "la", "que", "el", "en", "y", "a", "los", "del", "se", "las", "por",
    "un", "para", "con", "no", "una", "su", "al", "lo", "como", "mas", "pero",
    "sus", "le", "ya", "o", "este", "si", "porque", "esta", "muy", "sin",
    "sobre", "me", "hay", "todo", "eso", "esa", "ser", "estar", "tener",
    "hacer", "poder", "decir", "ver", "dar", "saber", "querer", "llegar",
    "pasar", "deber", "poner", "parecer", "quedar", "hablar", "llevar",
    "dejar", "seguir", "encontrar", "llamar", "venir", "pensar", "salir",
    "volver", "tomar", "conocer", "vivir", "sentir", "tratar", "mirar",
    "contar", "empezar", "esperar", "buscar", "existir", "entrar", "trabajar",
    "escribir", "perder", "producir", "ocurrir", "entender", "pedir",
    "recibir", "recordar", "terminar", "permitir", "aparecer", "conseguir",
    "comenzar", "servir", "sacar", "necesitar", "mantener", "resultar",
    "leer", "caer", "cambiar", "presentar", "crear", "abrir", "considerar",
    "oír", "oir", "acabar", "convertir", "ganar", "formar", "traer",
    "partir", "morir", "aceptar", "realizar", "suponer", "comprender",
    "lograr", "explicar", "preguntar", "tocar", "reconocer", "estudiar",
    "alcanzar", "nacer", "dirigir", "correr", "utilizar", "pagar",
    "ayudar", "gustar", "jugar", "escuchar", "cumplir", "ofrecer",
    "descubrir", "levantar", "intentar", "usar", "hola", "gracias",
    "porfa", "porfavor", "favor", "alex", "diego", "puedes", "quiero",
    "dime", "dame", "haz", "hacer", "lista", "texto", "nombre", "nombres",
    "what", "is", "are", "the", "this", "that", "with", "from", "have",
    "will", "would", "could", "should", "about", "into", "than", "then",
    "cuando", "donde", "quien", "cual", "como", "porque", "cuanto",
    "significa", "definicion", "definición", "explica", "explicame",
    "explícame", "que", "qué", "es",
}


class AlexPro(Alex):
    MODELO_ID = "pro"
    MODELO_NOMBRE = "Alex Pro 2.0"

    def __init__(self, directorio_datos: str = None):
        super().__init__(directorio_datos=directorio_datos)
        self.vision = AnalizadorImagen(modo_pro=True)
        self.pdf = AnalizadorPDF()
        self.vision_libre = VisionLibre()
        self.rae = DiccionarioRAE()
        self.red = RedNeuronalPro(memoria=self.memoria)
        self.gvision = None

    # ------------------------------------------------------------------ RAE
    def _ya_conocida(self, palabra: str) -> bool:
        p = (palabra or "").lower().strip()
        if not p:
            return True
        g = self.diccionario.glosa(p)
        if g:
            return True
        dic = self.memoria.datos.get("diccionario", {}) or {}
        info = dic.get(p) or {}
        if isinstance(info, dict) and (
            info.get("significado_deducido") or info.get("conocida")
        ):
            return True
        con = self.memoria.datos.get("conocimiento", {}) or {}
        if p in con or p.replace(".", "_") in con:
            return True
        return False

    def _registrar_rae(self, palabra: str, resultado: dict) -> None:
        resumen = resultado.get("resumen") or ""
        if not resumen:
            return
        defs = resultado.get("definiciones") or [resumen]
        texto_largo = resumen
        if len(defs) > 1:
            texto_largo = resumen + " | " + " · ".join(defs[1:3])
        if len(texto_largo) > 500:
            texto_largo = texto_largo[:497] + "..."

        try:
            self.diccionario._registrar(palabra, glosa=resumen[:240])
        except Exception:
            pass
        try:
            if hasattr(self.memoria, "marcar_palabra_conocida"):
                self.memoria.marcar_palabra_conocida(palabra, significado=resumen[:240])
        except Exception:
            pass
        try:
            self.aprendizaje.integrar_conocimiento_web(
                tema=palabra,
                resumen=f"{palabra}: {texto_largo}",
                fuente=resultado.get("fuente") or "RAE",
                puntuacion=0.95,
            )
        except Exception:
            try:
                self.memoria.guardar_conocimiento(
                    tema=palabra,
                    resumen=f"{palabra}: {texto_largo}",
                    fuente=resultado.get("fuente") or "RAE",
                    puntuacion=0.95,
                )
            except Exception as e:
                print(f"[Alex Pro] No se pudo guardar RAE '{palabra}': {e}")

    def _candidatas_rae(self, texto: str) -> list:
        toks = nlp.palabras_clave(texto) if hasattr(nlp, "palabras_clave") else []
        if not toks:
            toks = re.findall(r"[a-záéíóúñüA-ZÁÉÍÓÚÑÜ]{4,}", texto or "")
        out = []
        for t in toks:
            t = t.lower().strip()
            if t in _STOP_RAE or len(t) < 4:
                continue
            if self._ya_conocida(t):
                continue
            out.append(t)
            if len(out) >= 4:
                break
        m = re.search(
            r"(?:qu[eé]\s+es|qu[eé]\s+significa|define|definici[oó]n\s+de)\s+[«\"]?([a-záéíóúñüA-ZÁÉÍÓÚÑÜ\-]{3,})",
            texto or "",
            re.I,
        )
        if m:
            p = m.group(1).lower()
            if p not in _STOP_RAE and p not in out:
                out.insert(0, p)
        return out[:3]

    def enriquecer_con_rae(self, texto: str) -> list:
        hallazgos = []
        if not self.rae.disponible:
            return hallazgos
        for palabra in self._candidatas_rae(texto):
            try:
                r = self.rae.definir(palabra)
            except Exception as e:
                print(f"[Alex Pro] RAE error {palabra}: {e}")
                continue
            if not r.get("ok"):
                continue
            self._registrar_rae(palabra, r)
            hallazgos.append(r)
        try:
            if hallazgos:
                self.memoria.guardar()
        except Exception as e:
            print(f"[Alex Pro] guardar tras RAE: {e}")
        return hallazgos

    # -------------------------------------------------------------- vision/PDF
    def analizar_imagen(self, b64: str, idioma: str = None) -> str:
        idioma = idioma or self._idioma_actual or "es"
        partes = []

        cap = self.vision_libre.caption_base64(b64, idioma=idioma)
        if cap.get("ok") and cap.get("caption"):
            if idioma == "en":
                partes.append(f"I see (free AI caption): {cap['caption']}.")
            else:
                partes.append(f"Veo (descripcion gratuita): {cap['caption']}.")
        elif cap.get("descripcion") and cap.get("error") == "modelo_cargando":
            partes.append(cap["descripcion"])

        local = self.vision.analizar_base64(b64, idioma=idioma)
        if local.get("descripcion"):
            partes.append(local["descripcion"])

        if not partes:
            return local.get("error") or (
                "No pude analizar la imagen."
                if idioma != "en"
                else "Could not analyze the image."
            )
        return "\n\n".join(partes)

    def analizar_pdf(self, b64: str, idioma: str = None) -> dict:
        idioma = idioma or self._idioma_actual or "es"
        resultado = self.pdf.analizar_base64(b64, idioma=idioma)

        if resultado.get("ok") and not resultado.get("texto_vacio") and (
            resultado.get("resumen") or (resultado.get("caracteres") or 0) > 80
        ):
            return resultado

        raw_b64 = b64 or ""
        if "," in raw_b64 and raw_b64.strip().startswith("data:"):
            raw_b64 = raw_b64.split(",", 1)[1]
        import base64 as _b64

        try:
            raw = _b64.b64decode(raw_b64)
        except Exception as e:
            resultado["descripcion"] = (
                (resultado.get("descripcion") or "") + f"\nNo pude decodificar el PDF: {e}"
            )
            return resultado

        png = self.vision_libre.render_pdf_pagina(raw, pagina=0)
        if not png:
            extra = (
                " No pude renderizar paginas para analizar el escaneo "
                "(hace falta pypdfium2 en el servidor)."
                if idioma != "en"
                else " Could not render pages (need pypdfium2)."
            )
            resultado["descripcion"] = (resultado.get("descripcion") or "") + extra
            return resultado

        cap = self.vision_libre.caption_bytes(png, idioma=idioma)
        local = self.vision.analizar_bytes(png, idioma=idioma)
        lineas = [
            "PDF tipo escaneo — analisis gratuito de la pagina 1:"
            if idioma != "en"
            else "Scanned PDF — free analysis of page 1:"
        ]
        if cap.get("ok") and cap.get("caption"):
            lineas.append(
                ("Descripcion: " if idioma != "en" else "Caption: ") + cap["caption"]
            )
        elif cap.get("descripcion"):
            lineas.append(cap["descripcion"])
        if local.get("descripcion"):
            lineas.append(local["descripcion"])
        if resultado.get("descripcion"):
            lineas.append("—")
            lineas.append(resultado["descripcion"])
        resultado["ok"] = True
        resultado["motor_escaneo"] = "blip+local"
        resultado["descripcion"] = "\n".join(lineas)
        return resultado

    def responder(self, texto_usuario: str, cuota: dict = None) -> str:
        hallazgos_rae = []
        intent_nn = None
        try:
            intent_nn = self.red.analizar_intencion(texto_usuario)
        except Exception as e:
            print(f"[Alex Pro] NN intent: {e}")

        try:
            hallazgos_rae = self.enriquecer_con_rae(texto_usuario)
        except Exception as e:
            print(f"[Alex Pro] enriquecer RAE: {e}")

        respuesta = super().responder(texto_usuario, cuota=cuota)

        # RAE post-proceso
        try:
            if hallazgos_rae:
                pobre = (
                    not respuesta
                    or "no tengo informacion" in (respuesta or "").lower()
                    or "no se suficiente" in (respuesta or "").lower()
                    or "sin info" in (respuesta or "").lower()
                    or "relacionado con:" in (respuesta or "").lower()
                    or "ensename:" in (respuesta or "").lower()
                    or "enséñame:" in (respuesta or "").lower()
                )
                es_def = bool(
                    re.search(
                        r"\b(qu[eé]\s+es|qu[eé]\s+significa|define|definici[oó]n)\b",
                        texto_usuario or "",
                        re.I,
                    )
                )
                if pobre or es_def:
                    bloques = [
                        self.rae.formatear(h, idioma=self._idioma_actual or "es")
                        for h in hallazgos_rae
                    ]
                    bloques = [b for b in bloques if b]
                    if bloques:
                        nota = (
                            "\n\n(Definicion consultada en la RAE y guardada en mi memoria.)"
                            if (self._idioma_actual or "es") != "en"
                            else "\n\n(Definition fetched from RAE and stored in memory.)"
                        )
                        if pobre:
                            respuesta = "\n\n".join(bloques) + nota
                        else:
                            respuesta = "\n\n".join(bloques) + "\n\n" + respuesta + nota
        except Exception as e:
            print(f"[Alex Pro] post-RAE: {e}")

        # Red neuronal: si la respuesta sigue debil, cerebro HF
        usada_nn = False
        motor_nn = None
        try:
            mejor = self.red.mejorar_respuesta(
                texto_usuario,
                respuesta,
                idioma=self._idioma_actual or "es",
            )
            if mejor.get("usada_nn"):
                respuesta = mejor["respuesta"]
                usada_nn = True
                motor_nn = mejor.get("motor")
            elif mejor.get("intencion"):
                intent_nn = mejor["intencion"]
            # Aprende la intencion detectada (refuerzo debil positivo)
            if intent_nn and intent_nn.get("intencion"):
                self.red.reforzar(
                    texto_usuario,
                    intencion=intent_nn["intencion"],
                    positiva=True,
                )
        except Exception as e:
            print(f"[Alex Pro] NN mejorar: {e}")

        try:
            if self.conversacion.mensajes:
                ultimo = self.conversacion.mensajes[-1]
                if ultimo.get("rol") == "alex":
                    ultimo["texto"] = respuesta
                    extra = ultimo.setdefault("extra", {}) or {}
                    extra["modelo"] = self.MODELO_ID
                    extra["modelo_nombre"] = self.MODELO_NOMBRE
                    if hallazgos_rae:
                        extra["rae_palabras"] = [h.get("palabra") for h in hallazgos_rae]
                        extra["rae"] = True
                    if intent_nn:
                        extra["nn_intencion"] = intent_nn.get("intencion")
                        extra["nn_confianza"] = intent_nn.get("confianza")
                    if usada_nn:
                        extra["nn"] = True
                        extra["nn_motor"] = motor_nn
                    ultimo["extra"] = extra
                    self._ultimo_mensaje_alex = respuesta
        except Exception:
            pass
        return respuesta

    def retroalimentacion(self, positiva: bool):
        """Feedback del usuario: ajusta pesos de la red local + probabilidad base."""
        try:
            super().retroalimentacion(positiva)
        except Exception:
            pass
        try:
            # Aprende sobre el ultimo mensaje del usuario
            msgs = self.conversacion.mensajes or []
            ultimo_user = None
            for m in reversed(msgs):
                if m.get("rol") == "usuario":
                    ultimo_user = m.get("texto") or ""
                    break
            if ultimo_user:
                self.red.reforzar(ultimo_user, positiva=positiva)
                self.red.guardar_pesos()
        except Exception as e:
            print(f"[Alex Pro] NN feedback: {e}")

    def resumen_memoria(self) -> dict:
        d = super().resumen_memoria()
        d["modelo"] = self.MODELO_ID
        d["modelo_nombre"] = self.MODELO_NOMBRE
        d["vision_pro"] = True
        d["google_vision"] = False
        d["vision_libre"] = self.vision_libre.disponible
        d["rae"] = self.rae.disponible
        d["pdf"] = getattr(self.pdf, "disponible", False)
        d["red_neuronal"] = True
        d["nn_entrenamientos"] = getattr(self.red.mlp, "entrenamientos", 0)
        d["nn_hf"] = bool(getattr(self.red.hf, "token", None))
        d["nn_modelo_hf"] = getattr(self.red.hf, "modelo", "?")
        return d
