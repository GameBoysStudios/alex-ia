# -*- coding: utf-8 -*-
"""Conocimiento base de alta prioridad para Alex (se siembra en Firebase/local)."""

# Cada entrada: (tema, resumen, puntuacion)
# puntuacion alta (0.9-1.0) para que gane frente a ruido web debil.

CONOCIMIENTO_BASE = [
    # ---- Identidad y estudio ----
    (
        "quien eres",
        "Alex es una IA local en cliente creada por Diego Ar para Game Boys Studios. "
        "Aprende de las conversaciones, guarda memoria (local o Firebase), consulta Wikipedia "
        "e internet cuando no sabe algo, y genera textos estructurados (listas, planes, "
        "explicaciones, emails). No depende de APIs de LLM como ChatGPT.",
        1.0,
    ),
    (
        "que es alex",
        "Alex es el asistente de inteligencia artificial de Game Boys Studios, creado por Diego Ar. "
        "Es una IA en cliente: memoria propia, aprendizaje incremental y busqueda web opcional.",
        1.0,
    ),
    (
        "diego ar",
        "Diego Ar es el creador de Alex y forma parte de Game Boys Studios. Diseno Alex como "
        "una IA local que puede aprender, recordar y ayudar a generar contenido.",
        1.0,
    ),
    (
        "game boys studios",
        "Game Boys Studios es el estudio detras de Alex y de proyectos web/creativos asociados. "
        "Su sitio publico esta en gameboysstudio.github.io/GameBoys. Alex es su asistente de IA local.",
        1.0,
    ),
    (
        "game boys",
        "Game Boys Studios (a veces llamado Game Boys) es el equipo de Diego Ar. Desarrollan "
        "proyectos digitales y a Alex, su IA local en cliente.",
        0.95,
    ),
    (
        "para que sirves",
        "Sirvo para explicar conceptos, buscar informacion (Wikipedia/internet), aprender "
        "definiciones y sinonimos que me ensenes, y generar estructuras: listas, planes, "
        "resumenes, emails e ideas. Todo con memoria persistente si Firebase esta activo.",
        1.0,
    ),
    (
        "como aprendes",
        "Aprendo de tres formas: 1) cuando me das definiciones o sinonimos, 2) cuando me "
        "corriges, 3) cuando consulto Wikipedia u otras fuentes y guardo el resumen en memoria "
        "(Firebase o disco). Luego reutilizo ese conocimiento en preguntas parecidas.",
        1.0,
    ),
    # ---- Capacidades ----
    (
        "wikipedia",
        "Puedo consultar la API publica de Wikipedia en espanol para obtener resumentes de "
        "articulos cuando no tengo suficiente informacion en memoria.",
        0.95,
    ),
    (
        "firebase",
        "Mi memoria puede guardarse en Firebase Realtime Database para no perderse cuando "
        "el servidor de Render se reinicia. La ruta tipica es alex/memoria_permanente.",
        0.95,
    ),
    (
        "render",
        "Puedo desplegarme como servicio web en Render. En el plan gratis el disco local es "
        "efimero; por eso Firebase es recomendable para memoria permanente.",
        0.9,
    ),
    # ---- Conceptos utiles (alta calidad, respuestas inmediatas) ----
    (
        "inteligencia artificial",
        "La inteligencia artificial (IA) es el campo de la informatica que busca crear sistemas "
        "capaces de realizar tareas que normalmente requieren inteligencia humana: aprender, "
        "razonar, percibir o generar lenguaje. Incluye aprendizaje automatico, redes neuronales "
        "y sistemas basados en reglas o memoria, como Alex.",
        0.95,
    ),
    (
        "ia",
        "IA significa inteligencia artificial: sistemas informaticos que aprenden o razonan "
        "para ayudar en tareas. Alex es un ejemplo de IA local en cliente.",
        0.95,
    ),
    (
        "aprendizaje automatico",
        "El aprendizaje automatico (machine learning) es una rama de la IA en la que los "
        "modelos mejoran a partir de datos, sin ser programados regla a regla para cada caso.",
        0.9,
    ),
    (
        "programacion",
        "La programacion es el proceso de escribir instrucciones (codigo) para que un ordenador "
        "ejecute tareas. Lenguajes habituales: Python, JavaScript, C#, etc. Alex esta escrito "
        "principalmente en Python.",
        0.9,
    ),
    (
        "python",
        "Python es un lenguaje de programacion de alto nivel, muy usado en IA, web y scripts. "
        "Alex esta implementado en Python.",
        0.9,
    ),
    (
        "javascript",
        "JavaScript es el lenguaje estandar de la web en el navegador. Se usa para interfaces "
        "interactivas; el front de Alex en el navegador puede hablar con la API en Python.",
        0.85,
    ),
    (
        "api",
        "Una API (Application Programming Interface) es un conjunto de rutas o funciones que "
        "permiten a un programa hablar con otro. Alex expone /api/chat, /api/stats, etc.",
        0.9,
    ),
    (
        "json",
        "JSON (JavaScript Object Notation) es un formato de texto para intercambiar datos "
        "estructurados. Alex guarda memoria en JSON (local o en Firebase).",
        0.9,
    ),
    (
        "github",
        "GitHub es una plataforma para alojar codigo con Git. El codigo de Alex esta en el "
        "repositorio GameBoysStudios/alex-ia y el sitio del estudio en GitHub Pages.",
        0.9,
    ),
    (
        "fotosintesis",
        "La fotosintesis es el proceso por el cual las plantas (y algunas bacterias) convierten "
        "luz, agua y dioxido de carbono en azucares y oxigeno. Es la base de gran parte de la "
        "energia de los ecosistemas.",
        0.95,
    ),
    (
        "gravedad",
        "La gravedad es la fuerza de atraccion entre masas. En la Tierra hace que los objetos "
        "caigan hacia el centro del planeta; en el espacio mantiene planetas en orbita.",
        0.9,
    ),
    (
        "internet",
        "Internet es la red global de ordenadores interconectados que permite intercambiar "
        "informacion (web, email, APIs). Alex puede usarla para consultar Wikipedia u otras fuentes.",
        0.9,
    ),
]

SINONIMOS_BASE = [
    ("ia", "inteligencia artificial"),
    ("ml", "aprendizaje automatico"),
    ("machine learning", "aprendizaje automatico"),
    ("codigo", "programacion"),
    ("gbs", "game boys studios"),
    ("gameboys", "game boys studios"),
]

PALABRAS_BASE = [
    "alex", "diego", "ar", "game", "boys", "studios", "firebase", "wikipedia",
    "python", "api", "json", "github", "render", "inteligencia", "artificial",
    "memoria", "aprendizaje", "fotosintesis", "programacion",
]


def sembrar_conocimiento(memoria, forzar: bool = False) -> int:
    """
    Inserta conocimiento base con puntuacion alta.
    Solo se ejecuta una vez (preferencia semilla_conocimiento_v1), salvo forzar=True.
    Devuelve cuantos temas nuevos o actualizados se escribieron.
    """
    preferencias = memoria.datos.setdefault("preferencias", {})
    if not forzar and preferencias.get("semilla_conocimiento_v1"):
        return 0

    escritos = 0
    for tema, resumen, puntuacion in CONOCIMIENTO_BASE:
        memoria.guardar_conocimiento(
            tema=tema,
            resumen=resumen,
            fuente="conocimiento_base",
            puntuacion=puntuacion,
        )
        # Alias de pregunta frecuente
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
    memoria.guardar()
    print(f"[Alex] Semilla de conocimiento aplicada: {escritos} temas base")
    return escritos
