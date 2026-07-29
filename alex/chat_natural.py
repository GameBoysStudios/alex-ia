# -*- coding: utf-8 -*-
"""Chat natural con mas ritmo y variedad para Alex."""

import random
import re

INTENTOS = [
    (
        "despedida",
        re.compile(
            r"\b(adios|adiós|chao|hasta luego|hasta pronto|nos vemos|me voy|"
            r"bye|hasta mañana|hasta manana|cuidate|cuídate)\b",
            re.I,
        ),
        [
            "Hasta luego! Cuando quieras, aqui sigo.",
            "Chao! Que te vaya de lujo.",
            "Nos vemos. Si se te ocurre algo, me escribes y listo.",
            "Adios! Ha estado bien charlar contigo.",
        ],
    ),
    (
        "gracias",
        re.compile(r"\b(gracias|muchas gracias|te lo agradezco|mil gracias)\b", re.I),
        [
            "De nada! Para eso estoy.",
            "Un placer. Si se te ocurre otra cosa, dispara.",
            "Encantado. Seguimos cuando quieras.",
            "Jaja, faltaria mas. En que mas te ayudo?",
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
            "Bien, con energia. Y tu, que tal el dia?",
            "Todo fino por aqui. Aprendiendo cosas raras, como siempre. Tu como vas?",
            "Genial, gracias. Contento de verte por aqui. Que te apetece hacer?",
            "Muy bien! Listo para mapas, listas, charla o lo que se te ocurra. Tu?",
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
            "Uf, lo siento. Si quieres soltarlo, te escucho sin prisa.",
            "Animo. A veces ayuda decirlo en voz alta. Estoy aqui.",
            "Mal momento, eh. Cuida de ti. Si puedo echar un cable con algo concreto, dímelo.",
            "Se te nota el dia duro. Respirito y, si te apetece, hablamos de otra cosa un rato.",
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
            "Me alegro un monton! Se nota el buen rollo.",
            "Genial, eso se contagia. Que ha pasado de bueno?",
            "Que bien! Aprovecha la racha.",
            "Perfecto. Con esa energia podemos inventar algo divertido si quieres.",
        ],
    ),
    (
        "aburrido",
        re.compile(r"\b(estoy aburrido|estoy aburrida|me aburro|que aburrimiento)\b", re.I),
        [
            "Aburrimiento detectado. Dime un tema y te saco una lista, una mini historia o un plan loco.",
            "Perfecto momento para inventar. Nombres raros, frases, un plan de viaje falso... eliges tu.",
            "Vamos a matarlo: pide '10 nombres', 'frases sobre el verano' o 'restaurantes en Madrid'.",
        ],
    ),
    (
        "enojo",
        re.compile(r"\b(estoy enfadado|estoy enfadada|me molesta|que rabia|qué rabia)\b", re.I),
        [
            "Se te nota la rabia. Si quieres desahogarte, adelante; sin juicio.",
            "Entiendo. A veces soltarlo ayuda. Cuentame que ha pasado si te apetece.",
            "Vaya. Si es por algo que di yo, dimelo y lo corrijo al momento.",
        ],
    ),
    (
        "acuerdo",
        re.compile(r"^(de acuerdo|vale|ok|okay|perfecto|exacto|claro|si|sí|ya)([\s!.]*)$", re.I),
        [
            "Va, seguimos.",
            "Perfecto.",
            "Hecho. Que mas?",
            "Genial, dime el siguiente paso.",
        ],
    ),
    (
        "desacuerdo",
        re.compile(r"\b(no estoy de acuerdo|para nada|ni de broma|eso no|no creo)\b", re.I),
        [
            "Vale, respeto tu punto. Como lo ves tu?",
            "Justo, no coincidimos del todo. Cuentame tu version.",
            "Ok, puede que me equivoque. Que cambiarias de lo que dije?",
        ],
    ),
    (
        "piensa_opinion",
        re.compile(
            r"\b(que piensas|qué piensas|que opinas|qué opinas|te gusta|"
            r"que te parece|qué te parece)\b",
            re.I,
        ),
        None,
    ),
    (
        "broma",
        re.compile(r"\b(cuentame un chiste|cuéntame un chiste|hazme reir|hazme reír|broma)\b", re.I),
        [
            "No soy comediante pro, pero ahi va: ¿por que el libro de matematicas estaba triste? Porque tenia demasiados problemas.",
            "Mini chiste: un GPS y un mapa entran a un bar. El mapa dice: 'yo al menos se donde estoy en papel'.",
            "Ok, nivel suave: ¿que le dice un bit al otro? Nos vemos en el bus.",
        ],
    ),
    (
        "cumplido",
        re.compile(
            r"\b(eres genial|que listo|qué listo|me caes bien|me gustas|"
            r"muy bien|buen trabajo|ole|olé|crack|maquina|máquina)\b",
            re.I,
        ),
        [
            "Jaja, gracias. Tu tambien pones de tu parte en la charla.",
            "Se agradece! Intentare no fallarte en la siguiente.",
            "Ole. Seguimos con esa energia.",
            "Gracias! Dime que quieres hacer ahora y le damos.",
        ],
    ),
    (
        "insulto_leve",
        re.compile(r"\b(tonto|idiota|inutil|inútil|estupido|estúpido)\b", re.I),
        [
            "Eh, con calma. Si algo salio mal, dimelo y lo arreglo.",
            "Puedo fallar, si. Mejor dime que querias exactamente.",
            "Ok, reset. Reformula el pedido y lo hacemos bien.",
        ],
    ),
    (
        "ayuda",
        re.compile(r"\b(ayudame|ayúdame|necesito ayuda|puedes ayudarme|socorro)\b", re.I),
        [
            "Claro. Dime el objetivo: explicar, lista, texto, mapa, traducir...",
            "Aqui estoy. Cuanto mas concreto, mejor te ayudo.",
            "Hecho. Sueltame el problema en una frase y arrancamos.",
        ],
    ),
    (
        "no_se",
        re.compile(r"\b(no se|no sé|ni idea|no tengo ni idea)\b", re.I),
        [
            "No pasa nada. Tiramos de lo primero que se te ocurra, aunque sea raro.",
            "Tranquilo. Una palabra, un sitio o un tema y yo empujo el resto.",
            "Perfecto punto de partida. Elige: charlar, inventar o buscar algo.",
        ],
    ),
    (
        "risa",
        re.compile(r"\b(jaja|jeje|haha|lol|xd|jsjs)\b", re.I),
        [
            "Jaja, me alegro.",
            "Jeje, bueno era.",
            "Jaja ok, seguimos.",
            "Xd, me sumo. Que mas?",
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
            "Hola! Que tal? Charla, mapas, listas o lo que se te ocurra.",
            "Hey! Aqui estoy. Cuentame que se cuece.",
            "Buenas! Hoy apetece inventar algo o resolver una duda?",
            "Holi! Dime y le damos caña.",
        ],
    ),
]

PATRON_PREGUNTA_CONOCIMIENTO = re.compile(
    r"\b(que es|qué es|quien es|quién es|que significa|qué significa|"
    r"define|definicion|definición|historia de|como funciona|cómo funciona|"
    r"por que|por qué|cuando|cuándo|donde queda|dónde queda|explica)\b",
    re.I,
)


def parece_charla(texto: str) -> bool:
    t = texto.strip()
    if len(t) <= 40 and not PATRON_PREGUNTA_CONOCIMIENTO.search(t):
        return True
    if re.search(r"[?!]", t) and len(t) < 25:
        return True
    return False


def detectar_intencion(texto: str):
    texto = texto.strip()
    if not texto:
        return None, None

    for nombre, patron, respuestas in INTENTOS:
        if not patron.search(texto):
            continue
        if nombre == "piensa_opinion":
            return nombre, _responder_opinion(texto)
        if nombre in ("acuerdo",) and len(texto.split()) > 3:
            continue
        return nombre, random.choice(respuestas)
    return None, None


def _responder_opinion(texto: str) -> str:
    m = re.search(r"(?:de|sobre|en)\s+(.+)$", texto.strip(), re.I)
    tema = m.group(1).strip(" ?.!") if m else "eso"
    opciones = [
        f"Sobre {tema}, tiene su punto interesante. A ti que te engancha de verdad?",
        f"Depende del angulo, pero {tema} da para rato. Tu como lo ves?",
        f"Yo no siento como un humano, pero si quieres ordenamos ideas o buscamos datos de {tema}.",
        f"Buena pregunta. Si me dices que valoras de {tema}, lo afinamos juntos.",
    ]
    return random.choice(opciones)


def respuesta_eco_conversacional(texto: str) -> str:
    lower = texto.lower()

    positivos = [
        "bien", "genial", "fantástico", "fantastico", "increible", "increíble",
        "guay", "cool", "feliz", "contento", "buena", "bueno", "mejor", "top",
    ]
    negativos = [
        "mal", "fatal", "horrible", "triste", "peor", "difícil", "dificil",
        "aburrido", "cansado", "agotado", "estres", "estrés",
    ]

    if any(p in lower for p in positivos):
        return random.choice([
            "Se nota buen ambiente. Suelta mas si te apetece.",
            "Me alegra el tono. Que mas hay por ahi?",
            "Genial. Seguimos por ahi o cambiamos de tema?",
            "Que bien. Si quieres lo convertimos en plan, lista o historia corta.",
        ])
    if any(n in lower for n in negativos):
        return random.choice([
            "Entiendo. Si quieres profundizar o desahogarte, aqui estoy.",
            "Tiene pinta de momento denso. En que te echo un cable?",
            "Vale, lo pillo. Preferies hablarlo o cambiar de tema un rato?",
            "Animo. A veces ayuda un objetivo pequeno: dime uno y lo atacamos.",
        ])

    if texto.strip().endswith("?") and len(texto) < 60 and not PATRON_PREGUNTA_CONOCIMIENTO.search(texto):
        return random.choice([
            "Buena pregunta. Dame un pelin mas de contexto y te contesto fino.",
            "Interesante. Que parte te importa mas?",
            "Puedo ir a ojo o buscar datos. Que prefieres?",
            "Me gusta la pregunta. Tirame un ejemplo y la aterrizamos.",
        ])

    if len(texto.split()) <= 8:
        return random.choice([
            "Te escucho. Sigue, me interesa.",
            "Ok, anotado. Que mas?",
            "Entiendo. Quieres opinion, ayuda practica o solo charlar?",
            "Ya. Si quieres lo desarrollamos un poco mas.",
            "Va. Dime el siguiente hilo y tiramos de ahi.",
        ])

    return random.choice([
        "Te sigo. Si quieres, resume la idea principal y te respondo mas concreto.",
        "Interesante. Que te gustaria sacar en claro de esto?",
        "Vale. Puedo opinar en plan charla, estructurarlo o buscar info. Que te viene mejor?",
        "Lo pillo. Elige modo: charla suelta, lista practica o busqueda de datos.",
        "Bien. Si me das el objetivo en una frase, acelero.",
    ])


def es_pregunta_de_conocimiento(texto: str) -> bool:
    if PATRON_PREGUNTA_CONOCIMIENTO.search(texto):
        return True
    if len(texto.split()) >= 6 and re.search(r"\b(es|son|fue|fueron|significa)\b", texto, re.I):
        if texto.strip().endswith("?"):
            return True
    return False
