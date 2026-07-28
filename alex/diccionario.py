# -*- coding: utf-8 -*-
"""
Diccionario + codigos de palabra para Alex.

Idea:
  palabra legible  <->  codigo interno (entero)
  Alex puede componer respuestas como lista de codigos y decodificarlas a texto.

Fuentes de glosas (sin copiar la RAE completa, protegida por derechos):
  - Lexico local ampliado (espanol / ingles basico)
  - API publica de Wiktionary (open data) como consulta externa

RAE: no podemos redistribuir el DLE completo; usamos equivalentes abiertos.
"""

import re
from urllib.parse import quote

try:
    import requests
    REQUESTS_OK = True
except ImportError:
    REQUESTS_OK = False

# Lexico base: palabra -> glosa corta (es)
LEXICO_ES = {
    "ecosistema": "conjunto de seres vivos y el medio donde interactuan",
    "ecosistemas": "conjuntos de seres vivos y su entorno",
    "planta": "ser vivo que hace fotosintesis",
    "plantas": "seres vivos que hacen fotosintesis",
    "animal": "ser vivo que se alimenta de otros organismos",
    "agua": "liquido esencial para la vida",
    "tierra": "planeta o suelo",
    "aire": "mezcla de gases de la atmosfera",
    "fuego": "combustion con luz y calor",
    "sol": "estrella del sistema solar",
    "luna": "satelite natural de la tierra",
    "cielo": "espacio visible sobre la tierra",
    "mar": "gran masa de agua salada",
    "rio": "corriente natural de agua dulce",
    "montana": "gran elevacion natural del terreno",
    "bosque": "extension grande de arboles",
    "desierto": "region muy seca con poca vida vegetal",
    "ciudad": "nucleo urbano grande",
    "pueblo": "nucleo de poblacion menor que una ciudad",
    "casa": "edificio para habitar",
    "hogar": "casa o ambito familiar",
    "familia": "grupo de personas emparentadas",
    "amigo": "persona con quien se tiene amistad",
    "amor": "sentimiento de afecto profundo",
    "odio": "sentimiento intenso de rechazo",
    "alegria": "sentimiento de placer o felicidad",
    "tristeza": "sentimiento de pena",
    "miedo": "sensacion de amenaza o peligro",
    "valor": "cualidad de quien afronta el riesgo",
    "tiempo": "duracion o clima",
    "dia": "periodo de 24 horas o parte luminosa",
    "noche": "parte oscura del dia",
    "trabajo": "actividad productiva o empleo",
    "juego": "actividad lúdica",
    "musica": "arte de combinar sonidos",
    "arte": "expresion creativa humana",
    "ciencia": "conocimiento sistematico del mundo",
    "tecnologia": "aplicacion practica del conocimiento",
    "orden": "organizacion o mandato",
    "caos": "desorden total",
    "vida": "estado de los seres vivos",
    "muerte": "fin de la vida",
    "salud": "estado de bienestar fisico y mental",
    "enfermedad": "alteracion de la salud",
    "comida": "alimento",
    "pan": "alimento basico de harina",
    "libro": "conjunto de paginas encuadernadas",
    "palabra": "unidad de lenguaje con significado",
    "idioma": "lengua de una comunidad",
    "lengua": "sistema de signos para comunicar",
    "codigo": "sistema de signos o transformacion simbolica",
    "numero": "simbolo de cantidad",
    "color": "cualidad visual de la luz reflejada",
    "rojo": "color como la sangre",
    "azul": "color como el cielo despejado",
    "verde": "color como la hierba",
    "grande": "de tamano elevado",
    "pequeno": "de tamano reducido",
    "rapido": "que se mueve con velocidad",
    "lento": "que se mueve con poca velocidad",
    "fuerte": "con mucha fuerza o intensidad",
    "debil": "con poca fuerza",
    "nuevo": "recien hecho o reciente",
    "viejo": "de mucha edad o antigüedad",
    "bueno": "de calidad positiva o moral correcta",
    "malo": "de calidad negativa o moral incorrecta",
    "verdad": "lo que coincide con la realidad",
    "mentira": "afirmacion falsa",
    "pregunta": "acto de pedir informacion",
    "respuesta": "acto de contestar",
    "aprender": "adquirir conocimiento o habilidad",
    "ensenar": "transmitir conocimiento",
    "pensar": "usar la mente para razonar",
    "sentir": "experimentar emociones o sensaciones",
    "hablar": "comunicar con palabras",
    "escuchar": "prestar atencion al sonido",
    "ver": "percibir con la vista",
    "correr": "desplazarse rapido a pie",
    "caminar": "desplazarse a pie sin correr",
    "comer": "ingerir alimento",
    "beber": "ingerir liquido",
    "dormir": "estado de reposo con perdida de consciencia vigil",
    "sonar": "emitir sonido; o tener suenos",
    "energia": "capacidad de realizar trabajo",
    "materia": "lo que ocupa espacio y tiene masa",
    "atomo": "unidad basica de la materia quimica",
    "celula": "unidad basica de los seres vivos",
    "gen": "unidad de informacion hereditaria",
    "adn": "molecula que guarda la informacion genetica",
    "planeta": "cuerpo celeste que orbita una estrella",
    "estrella": "esfera de gas que emite luz propia",
    "galaxia": "conjunto enorme de estrellas y materia",
    "universo": "totalidad del espacio-tiempo y su contenido",
    "historia": "relato del pasado o disciplina que lo estudia",
    "futuro": "lo que aun no ha ocurrido",
    "pasado": "lo que ya ocurrio",
    "presente": "el momento actual",
    "sistema": "conjunto de elementos relacionados",
    "red": "estructura de nodos conectados",
    "dato": "hecho o valor que se puede analizar",
    "informacion": "datos con significado",
    "conocimiento": "informacion comprendida y aplicable",
    "sabiduria": "conocimiento profundo aplicado con juicio",
    "inteligencia": "capacidad de aprender y resolver problemas",
    "memoria": "capacidad de reteners informacion",
    "atencion": "concentracion de la mente en algo",
    "creatividad": "capacidad de generar ideas nuevas",
    "logica": "reglas del razonamiento valido",
    "matematica": "ciencia de numeros, estructuras y patrones",
    "fisica": "ciencia de la materia y la energia",
    "quimica": "ciencia de las sustancias y sus cambios",
    "biologia": "ciencia de los seres vivos",
    "geografia": "estudio de la tierra y sus territorios",
    "filosofia": "reflexion sobre la existencia y el conocimiento",
    "etica": "reflexion sobre lo correcto y lo justo",
    "libertad": "capacidad de actuar sin coerción indebida",
    "justicia": "principio de dar a cada uno lo debido",
    "paz": "ausencia de conflicto violento",
    "guerra": "conflicto armado entre grupos",
    "economia": "sistema de produccion e intercambio",
    "dinero": "medio de intercambio aceptado",
    "mercado": "espacio de compraventa",
    "empresa": "organizacion que produce bienes o servicios",
    "cliente": "quien compra o recibe un servicio",
    "producto": "bien o servicio ofrecido",
    "idea": "representacion mental o propuesta",
    "proyecto": "plan organizado para lograr un objetivo",
    "objetivo": "meta que se quiere alcanzar",
    "problema": "situacion que requiere solucion",
    "solucion": "respuesta que resuelve un problema",
    "error": "desviacion respecto a lo esperado",
    "exito": "logro del objetivo buscado",
    "fracaso": "no alcanzar el objetivo",
    "practica": "ejercicio repetido para mejorar",
    "teoria": "marco explicativo abstracto",
    "ejemplo": "caso concreto que ilustra una idea",
    "regla": "norma que guía la accion",
    "excepcion": "caso que se sale de la regla",
}

LEXICO_EN = {
    "ecosystem": "living beings and their environment interacting together",
    "water": "liquid essential for life",
    "fire": "combustion with heat and light",
    "earth": "the planet or soil",
    "air": "mixture of gases in the atmosphere",
    "sun": "the star of the solar system",
    "moon": "earth natural satellite",
    "friend": "person you have friendship with",
    "love": "deep affection",
    "word": "language unit with meaning",
    "code": "system of symbols or encoded form",
    "learn": "acquire knowledge or skill",
    "think": "use the mind to reason",
    "help": "give assistance",
    "question": "request for information",
    "answer": "reply to a question",
    "system": "set of related elements",
    "data": "facts or values that can be analyzed",
    "knowledge": "understood and usable information",
    "memory": "ability to retain information",
    "language": "system of signs used to communicate",
    "dictionary": "collection of words and meanings",
    "computer": "machine that processes information",
    "program": "set of instructions for a computer",
    "network": "structure of connected nodes",
    "energy": "capacity to do work",
    "matter": "what has mass and occupies space",
    "life": "state of living beings",
    "world": "the earth or a domain of experience",
    "good": "positive quality",
    "bad": "negative quality",
    "big": "large in size",
    "small": "little in size",
    "fast": "moving with speed",
    "slow": "moving with little speed",
}


class DiccionarioCodigos:
    """
    Mapa bidireccional palabra <-> codigo.
    Los codigos son enteros estables derivados del lexico + memoria aprendida.
    """

    def __init__(self, memoria=None):
        self.memoria = memoria
        self.palabra_a_codigo = {}
        self.codigo_a_palabra = {}
        self.glosas = {}
        self._siguiente = 1000
        self._cargar_lexico_base()
        if memoria:
            self._cargar_desde_memoria()

    def _cargar_lexico_base(self):
        for i, (pal, glosa) in enumerate(sorted(LEXICO_ES.items()), start=1):
            self._registrar(pal, codigo=i, glosa=glosa, idioma="es")
        base = len(LEXICO_ES) + 1
        for j, (pal, glosa) in enumerate(sorted(LEXICO_EN.items()), start=base):
            self._registrar(pal, codigo=j, glosa=glosa, idioma="en")
        self._siguiente = max(self.codigo_a_palabra.keys(), default=1000) + 1

    def _cargar_desde_memoria(self):
        dic = self.memoria.datos.get("diccionario", {})
        for palabra, info in dic.items():
            if palabra not in self.palabra_a_codigo:
                glosa = info.get("significado_deducido") or ""
                self._registrar(palabra, glosa=glosa or None)
            elif info.get("significado_deducido"):
                self.glosas[palabra] = info["significado_deducido"]

    def _registrar(self, palabra: str, codigo: int = None, glosa: str = None, idioma: str = None):
        palabra = (palabra or "").lower().strip()
        if not palabra:
            return None
        if palabra in self.palabra_a_codigo:
            if glosa:
                self.glosas[palabra] = glosa
            return self.palabra_a_codigo[palabra]
        if codigo is None:
            codigo = self._siguiente
            self._siguiente += 1
        self.palabra_a_codigo[palabra] = codigo
        self.codigo_a_palabra[codigo] = palabra
        if glosa:
            self.glosas[palabra] = glosa
        return codigo

    def codificar_palabra(self, palabra: str) -> int:
        palabra = (palabra or "").lower().strip()
        if not palabra:
            return 0
        if palabra in self.palabra_a_codigo:
            return self.palabra_a_codigo[palabra]
        return self._registrar(palabra)

    def decodificar_codigo(self, codigo: int) -> str:
        return self.codigo_a_palabra.get(int(codigo), f"#{codigo}")

    def codificar_frase(self, texto: str) -> list:
        tokens = re.findall(r"[a-záéíóúñüA-ZÁÉÍÓÚÑÜ]+", texto or "")
        return [self.codificar_palabra(t) for t in tokens]

    def decodificar_frase(self, codigos: list) -> str:
        return " ".join(self.decodificar_codigo(c) for c in codigos if c)

    def glosa(self, palabra: str) -> str:
        palabra = (palabra or "").lower().strip()
        if palabra in self.glosas:
            return self.glosas[palabra]
        # singular muy basico
        if palabra.endswith("s") and palabra[:-1] in self.glosas:
            return self.glosas[palabra[:-1]]
        return ""

    def explicar(self, palabra: str, idioma: str = "es") -> str:
        g = self.glosa(palabra)
        if g:
            if idioma == "en":
                return f"'{palabra}' means: {g}"
            return f"'{palabra}' significa: {g}"
        return ""

    def buscar_externo(self, palabra: str, idioma: str = "es") -> str:
        """Consulta Wiktionary (datos abiertos). Devuelve glosa corta o ''."""
        if not REQUESTS_OK or not palabra:
            return ""
        lang = {"es": "es", "en": "en", "fr": "fr", "pt": "pt"}.get(idioma, "es")
        try:
            url = (
                f"https://{lang}.wiktionary.org/api/rest_v1/page/definition/"
                + quote(palabra.lower())
            )
            r = requests.get(
                url,
                headers={"User-Agent": "AlexLocalAI/1.0"},
                timeout=6,
            )
            if r.status_code != 200:
                return ""
            data = r.json()
            # Estructura: { "es": [ { "definitions": [ {"definition": "..."} ] } ] }
            for _, grupos in (data or {}).items():
                for grupo in grupos or []:
                    for d in grupo.get("definitions") or []:
                        defi = re.sub(r"<[^>]+>", "", d.get("definition") or "")
                        defi = re.sub(r"\s+", " ", defi).strip()
                        if defi and len(defi) > 5:
                            # Guardar
                            self._registrar(palabra, glosa=defi[:240], idioma=idioma)
                            if self.memoria:
                                self.memoria.marcar_palabra_conocida(palabra, significado=defi[:240])
                                self.memoria.guardar_conocimiento(
                                    tema=palabra,
                                    resumen=f"{palabra} significa {defi[:240]}",
                                    fuente="wiktionary",
                                    puntuacion=0.88,
                                )
                            return defi[:240]
        except Exception:
            return ""
        return ""

    def resolver_desconocida(self, palabra: str, idioma: str = "es") -> str:
        """Glosa local, si no externa, si no mensaje de registro por codigo."""
        palabra = (palabra or "").lower().strip()
        if not palabra:
            return ""
        g = self.glosa(palabra)
        if g:
            return self.explicar(palabra, idioma)
        g = self.buscar_externo(palabra, idioma)
        if g:
            return self.explicar(palabra, idioma)
        # Registrar codigo aunque no haya glosa
        codigo = self.codificar_palabra(palabra)
        if idioma == "en":
            return (
                f"I coded '{palabra}' as [{codigo}]. "
                f"I do not have a definition yet; teach me: {palabra} means ..."
            )
        return (
            f"He codificado '{palabra}' como [{codigo}]. "
            f"Aun no tengo definicion; ensename: {palabra} significa ..."
        )

    def responder_con_codigos(self, texto_usuario: str, idioma: str = "es") -> str:
        """
        Transforma la frase a codigos y reconstruye una respuesta legible
        usando glosas de las palabras clave.
        """
        codigos = self.codificar_frase(texto_usuario)
        palabras = [self.decodificar_codigo(c) for c in codigos]
        explicadas = []
        for p in palabras:
            if len(p) < 4:
                continue
            g = self.glosa(p)
            if not g:
                g = self.buscar_externo(p, idioma)
            if g:
                explicadas.append((p, g))
            if len(explicadas) >= 3:
                break

        if not explicadas:
            return ""

        if idioma == "en":
            partes = [f"From your words (codes {codigos[:8]}): "]
            for p, g in explicadas:
                partes.append(f"'{p}' → {g}.")
            return " ".join(partes)

        partes = [f"Leyendo tus palabras (codigos {codigos[:8]}): "]
        for p, g in explicadas:
            partes.append(f"'{p}' → {g}.")
        return " ".join(partes)

    def estadisticas(self) -> dict:
        return {
            "entradas": len(self.palabra_a_codigo),
            "con_glosa": len(self.glosas),
            "siguiente_codigo": self._siguiente,
        }
