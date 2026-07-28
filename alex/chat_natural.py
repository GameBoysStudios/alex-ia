# -*- coding: utf-8 -*-
"""
Chat natural para Alex.

Detecta intenciones conversacionales (saludo, estado de animo, opiniones,
agradecimiento, despedida, acuerdo, etc.) y responde en tono de charla,
sin buscar en Wikipedia.
"""

import random
import re

# ---- Intenciones (orden importa: mas especificas primero) ----

INTENTOS = [
    (
        "despedida",
        re.compile(
            r"\b(adios|adiós|chao|hasta luego|hasta pronto|nos vemos|me voy|"
            r"bye|hasta mañana|hasta manana|cuidate|cuídate)\b",
            re.I,
        ),
        [
            "Hasta luego! Cuando quieras seguimos charlando.",
            "Adios! Aqui estare cuando vuelvas.",
            "Chao! Que te vaya genial.",
        ],
    ),
    (
        "gracias",
        re.compile(r"\b(gracias|muchas gracias|te lo agradezco|mil gracias)\b", re.I),
        [
            "De nada! Para eso estoy.",
            "Un placer. Si necesitas algo mas, dímelo.",
            "Encantado de ayudar.",
        ],
    ),
    (
        "como_estas",
        re.compile(
            r"\b(como estas|cómo estás|que tal estas|qué tal estás|como te va|"
            r"cómo te va|que tal|qué tal)\b",
            re.I,
        ),
        [
            "Bien, gracias por preguntar! Listo para lo que necesites. Y tu, que tal?",
            "Todo bien por aqui. Aprendiendo un poco cada dia. Tu como vas?",
            "Genial, gracias. Contento de hablar contigo. Como te encuentras tu?",
        ],
    ),
    (
        "bienestar_usuario_malo",
        re.compile(
            r"\b(estoy mal|me siento mal|estoy triste|estoy cansado|estoy cansada|"
            r"estoy agobiado|estoy agobiada|no me encuentro bien|que dia mas malo|"
            r"qué día más malo|estoy hecho polvo|estoy hecha polvo)\b",
            re.I,
        ),
        [
            "Siento que lo estes pasando mal. Si quieres contarme que pasa, te escucho.",
            "Animo. A veces ayuda hablarlo. Estoy aqui si te apetece desahogarte un poco.",
            "Lo siento. Cuida de ti. Si puedo ayudarte con algo concreto, dímelo.",
        ],
    ),
    (
        "bienestar_usuario_bueno",
        re.compile(
            r"\b(estoy bien|me siento bien|estoy genial|estoy feliz|todo bien|"
            r"estoy contento|estoy contenta|que bien|qué bien)\b",
            re.I,
        ),
        [
            "Me alegro mucho de oirlo!",
            "Genial, me alegra que estes bien.",
            "Que bueno! Se nota el buen rollo.",
        ],
    ),
    (
        "aburrido",
        re.compile(r"\b(estoy aburrido|estoy aburrida|me aburro|que aburrimiento)\b", re.I),
        [
            "Si quieres, podemos inventar una idea, un plan o una historia corta. Que te apetece?",
            "Aburrimiento nivel jefe, eh. Dime un tema y genero algo para matar el rato.",
            "Podemos charlar de lo que quieras o buscar un dato curioso. Tu eliges.",
        ],
    ),
    (
        "enojo",
        re.compile(r"\b(estoy enfadado|estoy enfadada|me molesta|que rabia|qué rabia|odio)\b", re.I),
        [
            "Se te nota cabreado. Si quieres desahogarte, adelante.",
            "Entiendo la rabia. A veces soltarlo ayuda. Cuentame si te apetece.",
        ],
    ),
    (
        "acuerdo",
        re.compile(r"\b(de acuerdo|vale|ok|okay|perfecto|exacto|claro|si|sí|ya)\b", re.I),
        [
            "Perfecto.",
            "Genial.",
            "Hecho, seguimos cuando quieras.",
            "Va, me parece bien.",
        ],
    ),
    (
        "desacuerdo",
        re.compile(r"\b(no estoy de acuerdo|para nada|ni de broma|eso no|no creo)\b", re.I),
        [
            "Vale, respeto tu punto de vista. Cuentame como lo ves tu.",
            "Entendido, no coincidimos del todo. Que pensarias tu entonces?",
        ],
    ),
    (
        "piensa_opinion",
        re.compile(
            r"\b(que piensas|qué piensas|que opinas|qué opinas|te gusta|"
            r"que te parece|qué te parece)\b",
            re.I,
        ),
        None,  # respuesta dinamica
    ),
    (
        "cumplido",
        re.compile(
            r"\b(eres genial|que listo|qué listo|me caes bien|me gustas|"
            r"muy bien|buen trabajo|ole|olé)\b",
            re.I,
        ),
        [
            "Gracias, se agradece! Tu tambien aportas mucho a la charla.",
            "Jaja, gracias. Intentare seguir estando a la altura.",
            "Me alegra que te sirva. Seguimos.",
        ],
    ),
    (
        "insulto_leve",
        re.compile(r"\b(tonto|idiota|inutil|inútil|estupido|estúpido)\b", re.I),
        [
            "Eh, con calma. Si algo no te gusto de mi respuesta, dimelo y lo corrijo.",
            "Puedo equivocarme, si. Mejor dime que falló y lo arreglo.",
        ],
    ),
    (
        "ayuda",
        re.compile(r"\b(ayudame|ayúdame|necesito ayuda|puedes ayudarme|socorro)\b", re.I),
        [
            "Claro. Dime en que te ayudo: explicar algo, generar un texto, una lista, un plan...",
            "Aqui estoy. Cuentame el problema o lo que quieres conseguir.",
        ],
    ),
    (
        "no_se",
        re.compile(r"\b(no se|no sé|ni idea|no tengo ni idea)\b", re.I),
        [
            "No pasa nada. Podemos ir poco a poco. Que es lo primero que te viene a la cabeza?",
            "Tranquilo. Si me das una pista, intento orientarte.",
        ],
    ),
    (
        "risa",
        re.compile(r"\b(jaja|jeje|haha|lol|xd)\b", re.I),
        [
            "Jaja, me alegro.",
            "Jeje, bueno era.",
            "Jaja, ok ok.",
        ],
    ),
    (
        "saludo",
        re.compile(
            r"^(hola|buenas|hey|hi|hello|buenos dias|buenos días|buenas tardes|"
            r"buenas noches|holi|ola)(\s|!|\.|$)",
            re.I,
        ),
        [
            "Hola! Que tal? En que te puedo echar una mano?",
            "Hey! Aqui estoy. Cuentame.",
            "Buenas! Que quieres hacer hoy: charlar, preguntar o generar algo?",
        ],
    ),
]

# Frases que SÍ merecen busqueda de conocimiento (no chat puro)
PATRON_PREGUNTA_CONOCIMIENTO = re.compile(
    r"\b(que es|qué es|quien es|quién es|que significa|qué significa|"
    r"define|definicion|definición|historia de|como funciona|cómo funciona|"
    r"por que|por qué|cuando|cuándo|donde queda|dónde queda|explica)\b",
    re.I,
)

# Mensajes cortos conversacionales (no lanzar Wikipedia)
def parece_charla(texto: str) -> bool:
    t = texto.strip()
    if len(t) <= 40 and not PATRON_PREGUNTA_CONOCIMIENTO.search(t):
        return True
    if re.search(r"[?!]", t) and len(t) < 25:
        return True
    return False


def detectar_intencion(texto: str):
    """Devuelve (nombre_intencion, respuesta) o (None, None)."""
    texto = texto.strip()
    if not texto:
        return None, None

    for nombre, patron, respuestas in INTENTOS:
        if not patron.search(texto):
            continue

        if nombre == "piensa_opinion":
            return nombre, _responder_opinion(texto)

        # "vale"/"si" solo si el mensaje es casi solo eso (evitar falsos positivos)
        if nombre in ("acuerdo",) and len(texto.split()) > 4:
            continue

        return nombre, random.choice(respuestas)

    return None, None


def _responder_opinion(texto: str) -> str:
    lower = texto.lower()
    # Extraer tema basico tras "de/sobre"
    m = re.search(r"(?:de|sobre|en)\s+(.+)$", texto.strip(), re.I)
    tema = m.group(1).strip(" ?.!") if m else "eso"

    opciones = [
        f"Sobre {tema}, me parece interesante. Que es lo que mas te llama la atencion a ti?",
        f"Depende del punto de vista, pero {tema} tiene su aquel. Tu que opinas?",
        f"No tengo una opinion tan humana como la tuya sobre {tema}, pero puedo ayudarte a ordenar ideas o buscar datos si quieres.",
        f"Buena pregunta. Si me dices que valoras tu de {tema}, te ayudo a matizarlo.",
    ]
    return random.choice(opciones)


def respuesta_eco_conversacional(texto: str) -> str:
    """
    Cuando no hay intencion clara ni conocimiento: responder como en una charla,
    recogiendo el tono (adjetivos / sentimiento) en lugar de ir a Wikipedia.
    """
    lower = texto.lower()

    positivos = ["bien", "genial", "fantástico", "fantastico", "increible", "increíble",
                 "guay", "cool", "feliz", "contento", "buena", "bueno", "mejor"]
    negativos = ["mal", "fatal", "horrible", "triste", "peor", "difícil", "dificil",
                 "aburrido", "cansado", "agotado"]

    if any(p in lower for p in positivos):
        return random.choice([
            "Se nota buen ambiente. Cuentame mas si quieres.",
            "Me alegra el tono positivo. Que mas hay?",
            "Genial. Seguimos por ahi si te apetece.",
        ])
    if any(n in lower for n in negativos):
        return random.choice([
            "Entiendo. Si quieres profundizar o desahogarte, aqui estoy.",
            "Tiene pinta de momento duro. En que te puedo echar un cable?",
            "Vale, lo pillo. Dime si prefieres hablarlo o cambiar de tema.",
        ])

    # Pregunta abierta corta
    if texto.strip().endswith("?") and len(texto) < 60 and not PATRON_PREGUNTA_CONOCIMIENTO.search(texto):
        return random.choice([
            "Buena pregunta. Cuentame un poco mas de contexto y te respondo mejor.",
            "Interesante. Que parte te preocupa o te interesa mas?",
            "Puedo contestarte a ojo o buscar datos. Que prefieres?",
        ])

    # Afirmacion corta / comentario
    if len(texto.split()) <= 8:
        return random.choice([
            "Te escucho. Sigue, me interesa.",
            "Ok, anotado. Que mas?",
            "Entiendo. Quieres que te diga algo al respecto o solo charlamos?",
            "Ya. Si quieres lo desarrollamos un poco mas.",
        ])

    return random.choice([
        "Te sigo. Si quieres, resume la idea principal y te respondo mas concreto.",
        "Interesante lo que comentas. Que te gustaria sacar en claro de esto?",
        "Vale. Puedo opinar en plan charla, ayudarte a estructurarlo o buscar info. Que te viene mejor?",
    ])


def es_pregunta_de_conocimiento(texto: str) -> bool:
    """True si conviene memoria/Wikipedia en vez de solo charlar."""
    if PATRON_PREGUNTA_CONOCIMIENTO.search(texto):
        return True
    # Frases largas con contenido tipicamente factual
    if len(texto.split()) >= 6 and re.search(r"\b(es|son|fue|fueron|significa)\b", texto, re.I):
        if texto.strip().endswith("?"):
            return True
    return False
