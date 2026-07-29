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
        raw = self.almacenamiento.leer(ARCHIVO_MEMORIA, None)
        if not isinstance(raw, dict):
            raw = _memoria_vacia()
        self.datos = raw
        for clave, valor in _memoria_vacia().items():
            if clave not in self.datos or not isinstance(self.datos[clave], type(valor)):
                # Si Firebase devolvio algo raro, resetear esa clave
                if clave not in self.datos or self.datos[clave] is None:
                    self.datos[clave] = valor
                elif isinstance(valor, dict) and not isinstance(self.datos[clave], dict):
                    self.datos[clave] = valor
                elif isinstance(valor, list) and not isinstance(self.datos[clave], list):
                    self.datos[clave] = valor
                else:
                    self.datos.setdefault(clave, valor)

    def guardar(self):
        try:
            self.almacenamiento.escribir(ARCHIVO_MEMORIA, self.datos)
        except Exception as e:
            print(f"[Alex] Aviso: no se pudo persistir memoria ({e})")

    def aprender_palabra(self, palabra: str, contexto: str = "", significado_deducido: str = None):
        palabra = (palabra or "").lower().strip()
        if not palabra:
            return
        palabra = _INVALID.sub("", palabra) or palabra
        if not isinstance(self.datos.get("diccionario"), dict):
            self.datos["diccionario"] = {}
        entrada = self.datos["diccionario"].setdefault(palabra, {
            "frecuencia": 0,
            "contextos": [],
            "significado_deducido": None,
            "conocida": False,
        })
        if not isinstance(entrada, dict):
            entrada = {
                "frecuencia": 0,
                "contextos": [],
                "significado_deducido": None,
                "conocida": False,
            }
            self.datos["diccionario"][palabra] = entrada
        entrada["frecuencia"] = int(entrada.get("frecuencia") or 0) + 1
        if contexto:
            ctxs = entrada.get("contextos")
            if not isinstance(ctxs, list):
                ctxs = []
            ctxs.append(str(contexto)[:500])
            entrada["contextos"] = ctxs[-10:]
        if significado_deducido and not entrada.get("significado_deducido"):
            entrada["significado_deducido"] = significado_deducido

    def marcar_palabra_conocida(self, palabra: str, significado: str = None):
        palabra = (palabra or "").lower().strip()
        palabra = _INVALID.sub("", palabra) or palabra
        if not palabra:
            return
        if not isinstance(self.datos.get("diccionario"), dict):
            self.datos["diccionario"] = {}
        entrada = self.datos["diccionario"].setdefault(palabra, {
            "frecuencia": 0, "contextos": [], "significado_deducido": None, "conocida": False,
        })
        if not isinstance(entrada, dict):
            entrada = {"frecuencia": 0, "contextos": [], "significado_deducido": None, "conocida": False}
            self.datos["diccionario"][palabra] = entrada
        entrada["conocida"] = True
        if significado:
            entrada["significado_deducido"] = significado

    def es_palabra_conocida(self, palabra: str) -> bool:
        dic = self.datos.get("diccionario") or {}
        if not isinstance(dic, dict):
            return False
        entrada = dic.get((palabra or "").lower().strip())
        if not isinstance(entrada, dict):
            return False
        return bool(entrada.get("conocida") or int(entrada.get("frecuencia") or 0) >= 3)

    def palabras_desconocidas(self, texto: str) -> list:
        desconocidas = []
        for palabra in nlp.palabras_clave(texto or ""):
            if not self.es_palabra_conocida(palabra):
                desconocidas.append(palabra)
        return desconocidas

    def frecuencias_counter(self) -> Counter:
        dic = self.datos.get("diccionario") or {}
        if not isinstance(dic, dict):
            return Counter()
        out = {}
        for p, d in dic.items():
            if isinstance(d, dict):
                out[p] = int(d.get("frecuencia") or 0)
            elif isinstance(d, (int, float)):
                out[p] = int(d)
        return Counter(out)

    def relacionar(self, palabra_a: str, palabra_b: str, peso: float = 1.0):
        palabra_a, palabra_b = (palabra_a or "").lower(), (palabra_b or "").lower()
        if not palabra_a or not palabra_b or palabra_a == palabra_b:
            return
        if not isinstance(self.datos.get("relaciones"), dict):
            self.datos["relaciones"] = {}
        rel = self.datos["relaciones"]
        if not isinstance(rel.get(palabra_a), dict):
            rel[palabra_a] = {}
        if not isinstance(rel.get(palabra_b), dict):
            rel[palabra_b] = {}
        try:
            rel[palabra_a][palabra_b] = float(rel[palabra_a].get(palabra_b, 0) or 0) + peso
            rel[palabra_b][palabra_a] = float(rel[palabra_b].get(palabra_a, 0) or 0) + peso
        except Exception:
            pass

    def relacionadas_con(self, palabra: str, top_n: int = 5) -> list:
        rel = self.datos.get("relaciones") or {}
        vecinas = rel.get((palabra or "").lower(), {}) if isinstance(rel, dict) else {}
        if not isinstance(vecinas, dict):
            return []
        ordenadas = sorted(vecinas.items(), key=lambda kv: kv[1] if isinstance(kv[1], (int, float)) else 0, reverse=True)
        return [p for p, _ in ordenadas[:top_n]]

    def aprender_relaciones_de_texto(self, texto: str):
        claves = nlp.palabras_clave(texto or "")
        for i, a in enumerate(claves):
            for b in claves[i + 1:]:
                self.relacionar(a, b, peso=0.5)

    def agregar_sinonimo(self, palabra: str, sinonimo: str):
        palabra, sinonimo = (palabra or "").lower().strip(), (sinonimo or "").lower().strip()
        if not palabra or not sinonimo or palabra == sinonimo:
            return
        if not isinstance(self.datos.get("sinonimos"), dict):
            self.datos["sinonimos"] = {}
        sin = self.datos["sinonimos"]
        lista_a = sin.setdefault(palabra, [])
        if not isinstance(lista_a, list):
            lista_a = [lista_a] if lista_a else []
            sin[palabra] = lista_a
        if sinonimo not in lista_a:
            lista_a.append(sinonimo)
        lista_b = sin.setdefault(sinonimo, [])
        if not isinstance(lista_b, list):
            lista_b = [lista_b] if lista_b else []
            sin[sinonimo] = lista_b
        if palabra not in lista_b:
            lista_b.append(palabra)
        self.relacionar(palabra, sinonimo, peso=2.0)
        self.aprender_palabra(palabra)
        self.aprender_palabra(sinonimo)

    def obtener_sinonimos(self, palabra: str) -> list:
        raw = (self.datos.get("sinonimos") or {}).get((palabra or "").lower().strip(), [])
        if isinstance(raw, list):
            return list(raw)
        if isinstance(raw, str):
            return [raw]
        return []

    def mapa_sinonimos(self) -> dict:
        raw = self.datos.get("sinonimos") or {}
        if not isinstance(raw, dict):
            return {}
        out = {}
        for p, sins in raw.items():
            if isinstance(sins, list):
                out[p] = set(str(x) for x in sins if x)
            elif isinstance(sins, str):
                out[p] = {sins}
            elif isinstance(sins, dict):
                out[p] = set(str(x) for x in sins.keys())
            else:
                out[p] = set()
        return out

    def vocabulario_conocido(self) -> set:
        vocab = set()
        dic = self.datos.get("diccionario") or {}
        if isinstance(dic, dict):
            vocab.update(dic.keys())
        for p, sins in (self.datos.get("sinonimos") or {}).items() if isinstance(self.datos.get("sinonimos"), dict) else []:
            vocab.add(p)
            if isinstance(sins, list):
                vocab.update(sins)
            elif isinstance(sins, str):
                vocab.add(sins)
        return vocab

    def set_preferencia(self, clave: str, valor):
        if not isinstance(self.datos.get("preferencias"), dict):
            self.datos["preferencias"] = {}
        self.datos["preferencias"][clave] = valor

    def get_preferencia(self, clave: str, por_defecto=None):
        pref = self.datos.get("preferencias") or {}
        if not isinstance(pref, dict):
            return por_defecto
        return pref.get(clave, por_defecto)

    def registrar_correccion(self, original: str, correccion: str):
        if not isinstance(self.datos.get("errores_corregidos"), list):
            self.datos["errores_corregidos"] = []
        self.datos["errores_corregidos"].append({
            "original": original,
            "correccion": correccion,
            "fecha": self.almacenamiento.marca_tiempo(),
        })
        self.aprender_palabra(correccion, contexto=f"Correccion de: {original}")

    def buscar_correccion(self, texto: str):
        texto_norm = nlp.normalizar(texto or "")
        errs = self.datos.get("errores_corregidos") or []
        if not isinstance(errs, list):
            return None
        for item in reversed(errs):
            if not isinstance(item, dict):
                continue
            if nlp.normalizar(item.get("original") or "") == texto_norm:
                return item.get("correccion")
        return None

    def actualizar_conocimiento_por_correccion(self, original: str, correccion: str):
        original_norm = nlp.normalizar(original or "")
        correccion_limpia = (correccion or "").strip()
        actualizados = 0
        cono = self.datos.get("conocimiento") or {}
        if not isinstance(cono, dict):
            return

        for clave, entrada in list(cono.items()):
            if not isinstance(entrada, dict):
                continue
            resumen = entrada.get("resumen") or ""
            tema_original = entrada.get("tema") or clave
            palabras_tema = nlp.palabras_clave(str(tema_original))
            palabra_base = palabras_tema[-1] if palabras_tema else str(tema_original)
            similar = (
                nlp.similitud_jaccard(original or "", str(resumen)) > 0.3
                or nlp.normalizar(str(resumen)) in original_norm
                or original_norm in nlp.normalizar(str(resumen))
            )
            if similar:
                if "significa" in str(resumen).lower() or str(resumen).lower().startswith(palabra_base):
                    nuevo_resumen = f"{palabra_base} significa {correccion_limpia}"
                else:
                    nuevo_resumen = correccion_limpia
                entrada["resumen"] = nuevo_resumen
                entrada["fuente"] = "correccion del usuario"
                entrada["fecha"] = self.almacenamiento.marca_tiempo()
                entrada["puntuacion"] = max(float(entrada.get("puntuacion") or 0), 0.9)
                actualizados += 1

        if actualizados == 0:
            claves = nlp.palabras_clave(original or "")
            tema = claves[0] if claves else "correccion"
            self.guardar_conocimiento(
                tema=tema,
                resumen=correccion_limpia,
                fuente="correccion del usuario",
                puntuacion=0.9,
            )

    def guardar_conocimiento(self, tema: str, resumen: str, fuente: str = "", puntuacion: float = 0.0):
        if not isinstance(self.datos.get("conocimiento"), dict):
            self.datos["conocimiento"] = {}
        clave = _clave_segura(tema)
        entrada = self.datos["conocimiento"].setdefault(clave, {
            "tema": tema,
            "resumen": resumen,
            "fuente": fuente,
            "puntuacion": puntuacion,
            "veces_usado": 0,
            "fecha": self.almacenamiento.marca_tiempo(),
        })
        if not isinstance(entrada, dict):
            entrada = {
                "tema": tema,
                "resumen": resumen,
                "fuente": fuente,
                "puntuacion": puntuacion,
                "veces_usado": 0,
                "fecha": self.almacenamiento.marca_tiempo(),
            }
            self.datos["conocimiento"][clave] = entrada
        if float(puntuacion) >= float(entrada.get("puntuacion") or 0):
            entrada.update({
                "resumen": resumen,
                "fuente": fuente,
                "puntuacion": puntuacion,
                "fecha": self.almacenamiento.marca_tiempo(),
            })

    def buscar_conocimiento(self, tema: str):
        if not isinstance(self.datos.get("conocimiento"), dict):
            return None
        clave = _clave_segura(tema)
        entrada = self.datos["conocimiento"].get(clave)
        if isinstance(entrada, dict):
            entrada["veces_usado"] = int(entrada.get("veces_usado") or 0) + 1
            return entrada
        return None

    def buscar_conocimiento_similar(self, texto: str, top_n: int = 3):
        resultados = []
        cono = self.datos.get("conocimiento") or {}
        if not isinstance(cono, dict):
            return []
        try:
            frecuencias = self.frecuencias_counter()
            mapa_sin = self.mapa_sinonimos()
            for clave, entrada in cono.items():
                if not isinstance(entrada, dict):
                    continue
                tema = str(entrada.get("tema") or clave or "")
                resumen = str(entrada.get("resumen") or "")
                sim = nlp.similitud_ponderada(
                    texto or "",
                    tema + " " + resumen,
                    frecuencias,
                    mapa_sin,
                )
                if sim > 0:
                    resultados.append((sim, entrada))
            resultados.sort(key=lambda x: x[0], reverse=True)
        except Exception as e:
            print(f"[Alex] Error buscando conocimiento similar: {e}")
        return resultados[:top_n]

    def incrementar_estadistica(self, clave: str, cantidad: int = 1):
        if not isinstance(self.datos.get("estadisticas"), dict):
            self.datos["estadisticas"] = {}
        self.datos["estadisticas"][clave] = int(self.datos["estadisticas"].get(clave) or 0) + cantidad

    def borrar_todo(self):
        self.datos = _memoria_vacia()
        self.guardar()
