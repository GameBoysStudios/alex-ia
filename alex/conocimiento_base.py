# -*- coding: utf-8 -*-
"""Conocimiento base de alta prioridad para Alex (se siembra en Firebase/local)."""

CONOCIMIENTO_BASE = [
    # ---- Identidad ----
    (
        "quien eres",
        "Soy Alex 2.0, una IA local en cliente creada por Diego Ar para Game Boys Studios. "
        "Aprendo de las conversaciones, guardo memoria (local o Firebase), consulto Wikipedia "
        "e internet cuando hace falta, traduzco textos, analizo imagenes de forma basica "
        "(colores, brillo, tamano) y genero textos estructurados. No soy ChatGPT: trabajo con "
        "memoria propia, diccionario de codigos y busqueda web.",
        1.0,
    ),
    (
        "que es alex",
        "Alex es el asistente de inteligencia artificial de Game Boys Studios, creado por Diego Ar. "
        "Version actual: Alex 2.0. Tiene planes de uso: invitado (10 msgs/12h), cuenta normal "
        "(50 msgs/12h) y premium (ilimitado). Memoria, aprendizaje y busqueda web opcionales.",
        1.0,
    ),
    (
        "alex 2.0",
        "Alex 2.0 es la version actual del asistente: cuotas por cuenta Firebase, traductor "
        "(Google Translate o MyMemory), vision casera de imagenes, diccionario con codigos de "
        "palabra, deteccion de idioma y conocimiento base ampliado. Alex Pro esta planeado.",
        1.0,
    ),
    (
        "diego ar",
        "Diego Ar es el creador de Alex y forma parte de Game Boys Studios. Diseno Alex como "
        "una IA local que puede aprender, recordar, traducir y ayudar a generar contenido.",
        1.0,
    ),
    (
        "game boys studios",
        "Game Boys Studios es el estudio detras de Alex, peliculas, comics y proyectos web. "
        "Sitio: gameboysstudio.github.io/GameBoys. Las cuentas de la web (Firebase Auth) "
        "sirven tambien para Alex (mismos UID).",
        1.0,
    ),
    (
        "game boys",
        "Game Boys Studios (Game Boys) es el equipo de Diego Ar. Desarrollan proyectos digitales, "
        "contenido audiovisual y a Alex, su IA local en cliente.",
        0.95,
    ),
    (
        "para que sirves",
        "Sirvo para: charlar, explicar conceptos, buscar en Wikipedia/internet, aprender "
        "definiciones y sinonimos, traducir (ej. 'traduce: hello al espanol'), analizar "
        "imagenes de forma basica, y generar listas, planes, textos o emails. Mi memoria "
        "persiste si Firebase esta activo.",
        1.0,
    ),
    (
        "como aprendes",
        "Aprendo asi: 1) definiciones ('X significa Y'), 2) sinonimos ('casa = hogar'), "
        "3) correcciones del usuario, 4) resumentes de Wikipedia/web que guardo en memoria. "
        "Luego reutilizo ese conocimiento en preguntas parecidas.",
        1.0,
    ),
    (
        "planes",
        "Alex tiene tres planes: Invitado (sin sesion) 10 mensajes cada 12 horas; Normal "
        "(cuenta Firebase de Game Boys) 50 mensajes cada 12 horas; Premium (marcado por "
        "UID en Firebase alex/premium/{uid}) mensajes ilimitados.",
        1.0,
    ),
    (
        "premium",
        "El plan Premium de Alex da mensajes ilimitados. Se activa poniendo el UID de Firebase "
        "Auth en alex/premium/{UID}=true en Realtime Database, o via API admin con ALEX_ADMIN_KEY.",
        1.0,
    ),
    (
        "suscripcion",
        "La suscripcion de Alex es el plan de uso: invitado, normal o premium. Se ve en la "
        "barra lateral de alex.html. Premium lo gestiona el administrador por UID en Firebase.",
        1.0,
    ),
    # ---- Capacidades tecnicas ----
    (
        "wikipedia",
        "Consulto la API publica de Wikipedia (sobre todo en espanol) para resumentes cuando "
        "no tengo bastante informacion en memoria.",
        0.95,
    ),
    (
        "firebase",
        "La memoria y las cuotas pueden guardarse en Firebase Realtime Database para no "
        "perderse al reiniciar Render. Rutas tipicas: alex/memoria_permanente, alex/cuotas, "
        "alex/premium/{uid}.",
        0.95,
    ),
    (
        "render",
        "Alex se despliega como servicio web en Render. En el plan gratis el disco es efimero; "
        "por eso Firebase es recomendable para memoria y premium permanentes.",
        0.9,
    ),
    (
        "traducir",
        "Puedo traducir textos. Escribe por ejemplo: traduce: hello al espanol. Uso Google "
        "Translate si hay GOOGLE_TRANSLATE_API_KEY; si no, MyMemory como alternativa gratuita.",
        0.95,
    ),
    (
        "imagenes",
        "Puedo analizar imagenes de forma casera (sin red neuronal pesada): tamano, "
        "orientacion, brillo medio y colores dominantes. No reconozco objetos concretos "
        "como 'un gato' con alta precision.",
        0.95,
    ),
    # ---- Ciencia y cultura general ----
    (
        "inteligencia artificial",
        "La inteligencia artificial (IA) es el campo de la informatica que busca sistemas "
        "capaces de tareas que suelen requerir inteligencia humana: aprender, razonar, "
        "percibir o generar lenguaje. Incluye aprendizaje automatico, redes neuronales y "
        "sistemas basados en reglas o memoria, como Alex.",
        0.95,
    ),
    (
        "ia",
        "IA significa inteligencia artificial: sistemas que aprenden o razonan para ayudar "
        "en tareas. Alex es un ejemplo de IA local en cliente con memoria propia.",
        0.95,
    ),
    (
        "aprendizaje automatico",
        "El aprendizaje automatico (machine learning) es una rama de la IA en la que los "
        "modelos mejoran a partir de datos, sin programar a mano cada regla para cada caso.",
        0.9,
    ),
    (
        "red neuronal",
        "Una red neuronal artificial es un modelo inspirado en el cerebro: capas de unidades "
        "conectadas que aprenden patrones a partir de ejemplos. Se usa en vision, lenguaje y mas.",
        0.9,
    ),
    (
        "programacion",
        "La programacion es escribir instrucciones (codigo) para que un ordenador ejecute "
        "tareas. Lenguajes habituales: Python, JavaScript, C#, Java, etc. Alex esta en Python.",
        0.9,
    ),
    (
        "python",
        "Python es un lenguaje de alto nivel, claro y muy usado en IA, web, datos y scripts. "
        "Alex esta implementado principalmente en Python.",
        0.9,
    ),
    (
        "javascript",
        "JavaScript es el lenguaje estandar del navegador. Sirve para interfaces interactivas; "
        "la pagina alex.html habla con la API de Alex en Python.",
        0.85,
    ),
    (
        "api",
        "Una API es un conjunto de rutas o funciones para que un programa hable con otro. "
        "Alex expone /api/chat, /api/cuota, /api/traducir, /api/analizar_imagen, etc.",
        0.9,
    ),
    (
        "json",
        "JSON es un formato de texto para datos estructurados. Alex guarda memoria y cuotas "
        "en JSON (disco local o Firebase).",
        0.9,
    ),
    (
        "github",
        "GitHub aloja codigo con Git. Alex esta en GameBoysStudios/alex-ia y el sitio del "
        "estudio en GameBoysStudios/GameBoys (GitHub Pages).",
        0.9,
    ),
    (
        "ecosistema",
        "Un ecosistema es el conjunto de seres vivos (biocenosis) y el medio fisico (biotopo) "
        "donde interactuan: intercambio de energia, materia y relaciones alimentarias. "
        "Ejemplos: bosque, arrecife, desierto, ciudad vista como socioecosistema.",
        0.95,
    ),
    (
        "ecosistemas",
        "Los ecosistemas son sistemas naturales o modificados por el humano formados por "
        "organismos y su entorno. La energia suele entrar por la fotosintesis y fluye por "
        "cadenas y redes troficas; los nutrientes se reciclan.",
        0.95,
    ),
    (
        "fotosintesis",
        "La fotosintesis es el proceso por el cual plantas, algas y algunas bacterias convierten "
        "luz, agua y dioxido de carbono en azucares y oxigeno. Es la base energetica de la "
        "mayoria de los ecosistemas terrestres y muchos acuaticos.",
        0.95,
    ),
    (
        "biodiversidad",
        "La biodiversidad es la variedad de vida: genes, especies y ecosistemas. Es clave para "
        "la estabilidad de los ecosistemas y para servicios como polinizacion, agua limpia y alimentos.",
        0.9,
    ),
    (
        "gravedad",
        "La gravedad es la atraccion entre masas. En la Tierra hace caer los objetos hacia el "
        "centro del planeta; en el espacio mantiene planetas y satelites en orbita.",
        0.9,
    ),
    (
        "energia",
        "La energia es la capacidad de realizar trabajo o producir cambios. Formas: cinetica, "
        "potencial, termica, quimica, electrica, luminosa, etc. Se conserva en sistemas aislados "
        "(primer principio de la termodinamica) aunque cambia de forma.",
        0.9,
    ),
    (
        "atomo",
        "Un atomo es la unidad basica de la materia quimica: nucleo (protones y neutrones) y "
        "electrones alrededor. Los elementos se distinguen por el numero de protones.",
        0.9,
    ),
    (
        "adn",
        "El ADN (acido desoxirribonucleico) es la molecula que guarda la informacion genetica "
        "en la mayoria de los seres vivos. Tiene forma de doble helice y se replica al dividirse la celula.",
        0.9,
    ),
    (
        "celula",
        "La celula es la unidad basica de los seres vivos. Puede ser procariota (sin nucleo, "
        "como bacterias) o eucariota (con nucleo, como plantas y animales).",
        0.9,
    ),
    (
        "internet",
        "Internet es la red global de ordenadores interconectados. Permite web, email, APIs y "
        "mucho mas. Alex puede usarla para Wikipedia, traducir o buscar informacion.",
        0.9,
    ),
    (
        "clima",
        "El clima es el patron promedio del tiempo meteorologico en una region a lo largo de "
        "muchos anos (temperatura, lluvia, viento). No es lo mismo que el tiempo de un dia concreto.",
        0.85,
    ),
    (
        "cambio climatico",
        "El cambio climatico actual se refiere sobre todo al calentamiento global impulsado por "
        "gases de efecto invernadero de origen humano (CO2, metano, etc.), con efectos en "
        "ecosistemas, nivel del mar y fenomenos extremos.",
        0.9,
    ),
    (
        "matematicas",
        "Las matematicas estudian numeros, estructuras, espacio y cambio. Son el lenguaje de "
        "la ciencia y la ingenieria: aritmetica, algebra, geometria, calculo, probabilidad, etc.",
        0.85,
    ),
    (
        "historia",
        "La historia estudia el pasado humano mediante fuentes (escritas, orales, materiales). "
        "Sirve para entender como las sociedades cambian y por que el presente es como es.",
        0.85,
    ),
    (
        "filosofia",
        "La filosofia reflexiona sobre el conocimiento, la existencia, la etica, la mente y el "
        "lenguaje. No sustituye a la ciencia, pero ayuda a aclarar preguntas y supuestos.",
        0.85,
    ),
    (
        "musica",
        "La musica organiza sonido en el tiempo: ritmo, melodia, armonia y timbre. Es arte, "
        "comunicacion y a menudo parte de la identidad cultural.",
        0.85,
    ),
    (
        "cine",
        "El cine combina imagen en movimiento, sonido y narrativa. Game Boys Studios tambien "
        "trabaja contenido audiovisual en su web.",
        0.85,
    ),
]

SINONIMOS_BASE = [
    ("ia", "inteligencia artificial"),
    ("ml", "aprendizaje automatico"),
    ("machine learning", "aprendizaje automatico"),
    ("codigo", "programacion"),
    ("gbs", "game boys studios"),
    ("gameboys", "game boys studios"),
    ("plan", "suscripcion"),
    ("plan premium", "premium"),
    ("subscripcion", "suscripcion"),
    ("traduccion", "traducir"),
    ("foto", "imagenes"),
    ("imagen", "imagenes"),
]

PALABRAS_BASE = [
    "alex", "diego", "ar", "game", "boys", "studios", "firebase", "wikipedia",
    "python", "api", "json", "github", "render", "inteligencia", "artificial",
    "memoria", "aprendizaje", "fotosintesis", "programacion", "ecosistema",
    "premium", "suscripcion", "traducir", "imagen", "biodiversidad", "energia",
    "atomo", "adn", "celula", "clima", "cine", "musica",
]


def sembrar_conocimiento(memoria, forzar: bool = False) -> int:
    """
    Inserta conocimiento base con puntuacion alta.
    Semilla v2: se reaplica una vez aunque existiera v1 (mas contexto).
    """
    preferencias = memoria.datos.setdefault("preferencias", {})
    if not forzar and preferencias.get("semilla_conocimiento_v2"):
        return 0

    escritos = 0
    for tema, resumen, puntuacion in CONOCIMIENTO_BASE:
        memoria.guardar_conocimiento(
            tema=tema,
            resumen=resumen,
            fuente="conocimiento_base",
            puntuacion=puntuacion,
        )
        memoria.guardar_conocimiento(
            tema=f"que es {tema}",
            resumen=resumen,
            fuente="conocimiento_base",
            puntuacion=puntuacion,
        )
        escritos += 1

    for a, b in SINONIMOS_BASE:
        memoria.agregar_sinonimo(a, b)

    for palabra in PALABRAS_BASE:
        memoria.marcar_palabra_conocida(palabra)

    preferencias["semilla_conocimiento_v1"] = True
    preferencias["semilla_conocimiento_v2"] = True
    memoria.guardar()
    print(f"[Alex] Semilla v2 de conocimiento aplicada: {escritos} temas base")
    return escritos
