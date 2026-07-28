# -*- coding: utf-8 -*-
"""Deteccion de idioma y respuestas alineadas al idioma del usuario."""

import re

# Palabras muy frecuentes por idioma
_ES = {
    "hola", "que", "qué", "como", "cómo", "gracias", "por", "para", "con", "una",
    "los", "las", "del", "que", "esta", "está", "bien", "malo", "porque", "también",
    "tambien", "hola", "adios", "adiós", "quiero", "puedes", "explicame", "explica",
    "texto", "sobre", "ayuda", "favor", "buenas", "dias", "días", "noches",
}
_EN = {
    "hello", "hi", "the", "what", "how", "thanks", "please", "with", "from", "this",
    "that", "have", "will", "would", "could", "should", "about", "write", "text",
    "help", "explain", "goodbye", "yes", "no", "good", "bad", "because", "also",
}
_FR = {
    "bonjour", "salut", "merci", "oui", "non", "avec", "pour", "dans", "quoi",
    "comment", "aide", "écrire", "ecrire", "texte", "sur", "bonsoir",
}
_PT = {
    "ola", "olá", "obrigado", "obrigada", "sim", "nao", "não", "com", "para",
    "que", "como", "ajuda", "texto", "sobre", "bom", "dia",
}


def detectar_idioma(texto: str) -> str:
    """Devuelve codigo ISO corto: es, en, fr, pt (por defecto es)."""
    if not texto or not texto.strip():
        return "es"
    low = texto.lower()
    tokens = set(re.findall(r"[a-záéíóúñüàèìòùâêîôûçãõ]{2,}", low))

    scores = {
        "es": len(tokens & _ES),
        "en": len(tokens & _EN),
        "fr": len(tokens & _FR),
        "pt": len(tokens & _PT),
    }
    # Señales ortograficas
    if re.search(r"[ñáéíóúü¿¡]", low):
        scores["es"] += 3
    if re.search(r"\b(the|what|how|please|thanks)\b", low):
        scores["en"] += 2
    if re.search(r"[àâçéèêëïôùû]", low) and "que" not in tokens:
        scores["fr"] += 2
    if re.search(r"[ãõç]", low):
        scores["pt"] += 2

    mejor = max(scores, key=scores.get)
    if scores[mejor] == 0:
        return "es"
    return mejor


# Mensajes del sistema por idioma
MSG = {
    "es": {
        "vacio": "Puedes escribir algo? No he recibido ningun texto.",
        "sin_info": "No estoy seguro de eso todavia. Si me lo explicas, lo aprendo.",
        "sin_info_dict": "No tenia esa palabra en mi diccionario; la he anotado como '{palabra}'.",
        "aprendido_dict": "He consultado el diccionario: '{palabra}' se relaciona con: {glosa}.",
        "idioma_ok": "De acuerdo, te respondo en espanol.",
    },
    "en": {
        "vacio": "Can you type something? I did not get any text.",
        "sin_info": "I am not sure about that yet. If you explain it, I will learn it.",
        "sin_info_dict": "I did not have that word; I noted '{palabra}'.",
        "aprendido_dict": "Dictionary lookup: '{palabra}' relates to: {glosa}.",
        "idioma_ok": "Okay, I will answer in English.",
    },
    "fr": {
        "vacio": "Peux-tu ecrire quelque chose? Je n'ai rien recu.",
        "sin_info": "Je ne suis pas encore sur. Si tu m'expliques, j'apprends.",
        "sin_info_dict": "Je n'avais pas ce mot; j'ai note '{palabra}'.",
        "aprendido_dict": "Dictionnaire: '{palabra}' se rapporte a: {glosa}.",
        "idioma_ok": "D'accord, je reponds en francais.",
    },
    "pt": {
        "vacio": "Podes escrever algo? Nao recebi texto.",
        "sin_info": "Ainda nao tenho a certeza. Se me explicares, aprendo.",
        "sin_info_dict": "Nao tinha essa palavra; anotei '{palabra}'.",
        "aprendido_dict": "Dicionario: '{palabra}' relaciona-se com: {glosa}.",
        "idioma_ok": "Certo, respondo em portugues.",
    },
}


def msg(idioma: str, clave: str, **kwargs) -> str:
    bloque = MSG.get(idioma) or MSG["es"]
    plantilla = bloque.get(clave) or MSG["es"].get(clave, "")
    try:
        return plantilla.format(**kwargs)
    except Exception:
        return plantilla
