# -*- coding: utf-8 -*-
"""
Modulo de Memoria para Alex.
"""

import re
from collections import Counter
from alex.storage import AlmacenamientoJSON
from alex import nlp

ARCHIVO_MEMORIA = "memoria_permanente.json"
_INVALID = re.compile(r"[.$\[\]#/]")


def _clave_segura(texto: str) -> str:
    """Clave apta para Firebase RTDB (sin . $ # [ ] /)."""
    s = nlp.normalizar(texto or "")
    s = _INVALID.sub("_", s)
    s = re.sub(r"\s+", "_", s).strip("_")
    return s or "_sin_tema"


def _memoria_vacia() -> dict:
    return {
        "diccionario": {},
        "relaciones": {},
        "sinonimos": {},
        "preferencias": {},
        "errores_corregidos": [],
        "conocimiento": {},
        "estadisticas": {
            "conversaciones_totales": 0,
            "mensajes_totales": 0,
        },
    }


class Memoria:
    def __init__(self, almacenamiento: AlmacenamientoJSON):
        self.almacenamiento = almacenamiento
        self.datos = self.almacenamiento.leer(ARCHIVO_MEMORIA, _memoria_vacia())
        for clave, valor in _memoria_vacia().items():
            self.datos.setdefault(clave, valor)

    def guardar(self):
        try:
            self.almacenamiento.escribir(ARCHIVO_MEMORIA, self.datos)
        except Exception as e:
            print(f"[Alex] Aviso: no se pudo persistir memoria ({e})")

    def aprender_palabra(self, palabra: str, contexto: str = "", significado_deducido: str = None):
        palabra = palabra.lower().strip()
        if not palabra:
            return
        palabra = _INVALID.sub("", palabra) or palabra
        entrada = self.datos["diccionario"].setdefault(palabra, {
            "frecuencia": 0,
            "contextos": [],
            "significado_deducido": None,
            "conocida": False,
        })
        entrada["frecuencia"] += 1
        if contexto:
            entrada["contextos"].append(contexto)
            entrada["contextos"] = entrada["contextos"][-10:]
        if significado_deducido and not entrada["significado_deducido"]:
            entrada["significado_deducido"] = significado_deducido

    def marcar_palabra_conocida(self, palabra: str, significado: str = None):
        palabra = palabra.lower().strip()
        palabra = _INVALID.sub("", palabra) or palabra
        entrada = self.datos["diccionario"].setdefault(palabra, {
            "frecuencia": 0, "contextos": [], "significado_deducido": None, "conocida": False,
        })
        entrada["conocida"] = True
        if significado:
            entrada["significado_deducido"] = significado

    def es_palabra_conocida(self, palabra: str) -> bool:
        entrada = self.datos["diccionario"].get(palabra.lower().strip())
        return bool(entrada and (entrada.get("conocida") or entrada.get("frecuencia", 0) >= 3))

    def palabras_desconocidas(self, texto: str) -> list:
        desconocidas = []
        for palabra in nlp.palabras_clave(texto):
            if not self.es_palabra_conocida(palabra):
                desconocidas.append(palabra)
        return desconocidas

    def frecuencias_counter(self) -> Counter:
        return Counter({p: d.get("frecuencia", 0) for p, d in self.datos["diccionario"].items()})

    def relacionar(self, palabra_a: str, palabra_b: str, peso: float = 1.0):
        palabra_a, palabra_b = palabra_a.lower(), palabra_b.lower()
        if palabra_a == palabra_b:
            return
        rel = self.datos["relaciones"]
        rel.setdefault(palabra_a, {})
        rel.setdefault(palabra_b, {})
        rel[palabra_a][palabra_b] = rel[palabra_a].get(palabra_b, 0) + peso
        rel[palabra_b][palabra_a] = rel[palabra_b].get(palabra_a, 0) + peso

    def relacionadas_con(self, palabra: str, top_n: int = 5) -> list:
        vecinas = self.datos["relaciones"].get(palabra.lower(), {})
        ordenadas = sorted(vecinas.items(), key=lambda kv: kv[1], reverse=True)
        return [p for p, _ in ordenadas[:top_n]]

    def aprender_relaciones_de_texto(self, texto: str):
        claves = nlp.palabras_clave(texto)
        for i, a in enumerate(claves):
            for b in claves[i + 1:]:
                self.relacionar(a, b, peso=0.5)

    def agregar_sinonimo(self, palabra: str, sinonimo: str):
        palabra, sinonimo = palabra.lower().strip(), sinonimo.lower().strip()
        if not palabra or not sinonimo or palabra == sinonimo:
            return
        sin = self.datos.setdefault("sinonimos", {})
        lista_a = sin.setdefault(palabra, [])
        if sinonimo not in lista_a:
            lista_a.append(sinonimo)
        lista_b = sin.setdefault(sinonimo, [])
        if palabra not in lista_b:
            lista_b.append(palabra)
        self.relacionar(palabra, sinonimo, peso=2.0)
        self.aprender_palabra(palabra)
        self.aprender_palabra(sinonimo)

    def obtener_sinonimos(self, palabra: str) -> list:
        return list(self.datos.get("sinonimos", {}).get(palabra.lower().strip(), []))

    def mapa_sinonimos(self) -> dict:
        raw = self.datos.get("sinonimos", {})
        return {p: set(sins) for p, sins in raw.items()}

    def vocabulario_conocido(self) -> set:
        vocab = set(self.datos.get("diccionario", {}).keys())
        for p, sins in self.datos.get("sinonimos", {}).items():
            vocab.add(p)
            vocab.update(sins)
        return vocab

    def set_preferencia(self, clave: str, valor):
        self.datos["preferencias"][clave] = valor

    def get_preferencia(self, clave: str, por_defecto=None):
        return self.datos["preferencias"].get(clave, por_defecto)

    def registrar_correccion(self, original: str, correccion: str):
        self.datos["errores_corregidos"].append({
            "original": original,
            "correccion": correccion,
            "fecha": self.almacenamiento.marca_tiempo(),
        })
        self.aprender_palabra(correccion, contexto=f"Correccion de: {original}")

    def buscar_correccion(self, texto: str):
        texto_norm = nlp.normalizar(texto)
        for item in reversed(self.datos["errores_corregidos"]):
            if nlp.normalizar(item["original"]) == texto_norm:
                return item["correccion"]
        return None

    def actualizar_conocimiento_por_correccion(self, original: str, correccion: str):
        original_norm = nlp.normalizar(original)
        correccion_limpia = correccion.strip()
        actualizados = 0

        for clave, entrada in list(self.datos["conocimiento"].items()):
            resumen = entrada.get("resumen", "")
            tema_original = entrada.get("tema", clave)
            palabras_tema = nlp.palabras_clave(tema_original)
            palabra_base = palabras_tema[-1] if palabras_tema else tema_original
            similar = (
                nlp.similitud_jaccard(original, resumen) > 0.3
                or nlp.normalizar(resumen) in original_norm
                or original_norm in nlp.normalizar(resumen)
            )
            if similar:
                if "significa" in resumen.lower() or resumen.lower().startswith(palabra_base):
                    nuevo_resumen = f"{palabra_base} significa {correccion_limpia}"
                else:
                    nuevo_resumen = correccion_limpia
                entrada["resumen"] = nuevo_resumen
                entrada["fuente"] = "correccion del usuario"
                entrada["fecha"] = self.almacenamiento.marca_tiempo()
                entrada["puntuacion"] = max(entrada.get("puntuacion", 0), 0.9)
                actualizados += 1

        if actualizados == 0:
            claves = nlp.palabras_clave(original)
            tema = claves[0] if claves else "correccion"
            self.guardar_conocimiento(
                tema=tema,
                resumen=correccion_limpia,
                fuente="correccion del usuario",
                puntuacion=0.9,
            )

    def guardar_conocimiento(self, tema: str, resumen: str, fuente: str = "", puntuacion: float = 0.0):
        clave = _clave_segura(tema)
        entrada = self.datos["conocimiento"].setdefault(clave, {
            "tema": tema,
            "resumen": resumen,
            "fuente": fuente,
            "puntuacion": puntuacion,
            "veces_usado": 0,
            "fecha": self.almacenamiento.marca_tiempo(),
        })
        if puntuacion >= entrada.get("puntuacion", 0):
            entrada.update({
                "resumen": resumen,
                "fuente": fuente,
                "puntuacion": puntuacion,
                "fecha": self.almacenamiento.marca_tiempo(),
            })

    def buscar_conocimiento(self, tema: str):
        clave = _clave_segura(tema)
        entrada = self.datos["conocimiento"].get(clave)
        if entrada:
            entrada["veces_usado"] = entrada.get("veces_usado", 0) + 1
        return entrada

    def buscar_conocimiento_similar(self, texto: str, top_n: int = 3):
        resultados = []
        frecuencias = self.frecuencias_counter()
        mapa_sin = self.mapa_sinonimos()
        for clave, entrada in self.datos["conocimiento"].items():
            sim = nlp.similitud_ponderada(
                texto,
                entrada.get("tema", "") + " " + entrada.get("resumen", ""),
                frecuencias,
                mapa_sin,
            )
            if sim > 0:
                resultados.append((sim, entrada))
        resultados.sort(key=lambda x: x[0], reverse=True)
        return resultados[:top_n]

    def incrementar_estadistica(self, clave: str, cantidad: int = 1):
        self.datos["estadisticas"][clave] = self.datos["estadisticas"].get(clave, 0) + cantidad

    def borrar_todo(self):
        self.datos = _memoria_vacia()
        self.guardar()
