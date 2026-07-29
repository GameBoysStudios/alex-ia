# -*- coding: utf-8 -*-
"""Conocimiento base de alta prioridad para Alex (se siembra en Firebase/local)."""

CONOCIMIENTO_BASE = [
    (
        "quien eres",
        "Soy Alex 2.0, una IA local en cliente creada por Diego Ar para Game Boys Studios. "
        "Aprendo de las conversaciones, guardo memoria (local o Firebase), consulto Wikipedia "
        "e internet cuando hace falta, traduzco textos, analizo imagenes de forma basica "
        "(colores, brillo, tamano) y genero textos estructurados. No soy ChatGPT: trabajo con "
        "memoria propia, diccionario de codigos y busqueda web. Puedo decirte tu suscripcion "
        "(Invitado, Normal o Premium) si me preguntas por tu plan o cuota.",
        1.0,
    ),
    (
        "que es alex",
        "Alex es el asistente de inteligencia artificial de Game Boys Studios, creado por Diego Ar. "
        "Version actual: Alex 2.0. Planes: Invitado (10 msgs/12h), Normal con cuenta Firebase "
        "(50 msgs/12h) y Premium (ilimitado, por UID en alex/premium).",
        1.0,
    ),
    (
        "alex 2.0",
        "Alex 2.0 es la version actual: cuotas por cuenta Firebase, traductor "
        "(Google Translate o MyMemory), vision casera de imagenes, diccionario con codigos, "
        "deteccion de idioma y conocimiento base ampliado. Alex Pro esta planeado.",
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
        "imagenes de forma basica, generar listas, planes, textos o emails, y decirte tu "
        "suscripcion o mensajes restantes.",
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
        "Alex tiene tres planes de suscripcion: Invitado (sin sesion) 10 mensajes cada 12 horas; "
        "Normal (cuenta Firebase de Game Boys) 50 mensajes cada 12 horas; Premium (UID en "
        "Firebase alex/premium/{uid}=true) mensajes ilimitados. Pregunta 'mi plan' o "
        "'mi suscripcion' para ver el tuyo.",
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
        "Tu suscripcion es el plan de uso en Alex: Invitado, Normal o Premium. Se muestra en "
        "la barra de alex.html y tambien te la digo si preguntas 'mi plan', 'mi suscripcion' "
        "o 'cuantos mensajes me quedan'.",
        1.0,
    ),
    (
        "mi plan",
        "Si preguntas por tu plan o suscripcion, te respondo con el tier actual (Invitado, "
        "Normal o Premium) y los mensajes que te quedan en la ventana de 12 horas.",
        1.0,
    ),
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
        "Puedo traducir textos. Escribe: traduce: hello al espanol. Uso Google Translate si "
        "hay GOOGLE_TRANSLATE_API_KEY; si no, MyMemory como alternativa gratuita.",
        0.95,
    ),
    (
        "imagenes",
        "Puedo analizar imagenes de forma casera (sin red neuronal pesada): tamano, "
        "orientacion, brillo medio y colores dominantes. No reconozco objetos concretos "
        "con alta precision.",
        0.95,
    ),
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
        "aunque cambia de forma.",
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
        "en la mayoria de los seres vivos. Tiene forma de doble helice.",
        0.9,
    ),
    (
        "celula",
        "La celula es la unidad basica de los seres vivos. Puede ser procariota (sin nucleo) "
        "o eucariota (con nucleo).",
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
        "muchos anos. No es lo mismo que el tiempo de un dia concreto.",
        0.85,
    ),
    (
        "cambio climatico",
        "El cambio climatico actual se refiere sobre todo al calentamiento global impulsado por "
        "gases de efecto invernadero de origen humano (CO2, metano, etc.).",
        0.9,
    ),
    (
        "matematicas",
        "Las matematicas estudian numeros, estructuras, espacio y cambio: aritmetica, algebra, "
        "geometria, calculo, probabilidad, etc.",
        0.85,
    ),
    (
        "historia",
        "La historia estudia el pasado humano mediante fuentes escritas, orales y materiales. "
        "Ayuda a entender como las sociedades cambian.",
        0.85,
    ),
    (
        "filosofia",
        "La filosofia reflexiona sobre el conocimiento, la existencia, la etica, la mente y el "
        "lenguaje. No sustituye a la ciencia, pero aclara preguntas y supuestos.",
        0.85,
    ),
    (
        "musica",
        "La musica organiza sonido en el tiempo: ritmo, melodia, armonia y timbre. Es arte, "
        "comunicacion e identidad cultural.",
        0.85,
    ),
    (
        "cine",
        "El cine combina imagen en movimiento, sonido y narrativa. Game Boys Studios tambien "
        "trabaja contenido audiovisual en su web.",
        0.85,
    ),
    # ---- Mas contexto general (v3) ----
    (
        "sol",
        "El Sol es la estrella del sistema solar. Es una esfera de gas (sobre todo hidrogeno y "
        "helio) que produce energia por fusion nuclear. Su luz y calor hacen posible la vida en la Tierra.",
        0.9,
    ),
    (
        "tierra",
        "La Tierra es el tercer planeta del sistema solar y el unico conocido con vida. Tiene "
        "atmosfera, agua liquida y un campo magnetico que nos protege de parte de la radiacion solar.",
        0.9,
    ),
    (
        "luna",
        "La Luna es el satelite natural de la Tierra. Influye en las mareas y refleja la luz del Sol; "
        "su superficie esta llena de crateres por impactos.",
        0.85,
    ),
    (
        "agua",
        "El agua (H2O) es esencial para la vida. Cubre gran parte de la Tierra en oceanos, rios y "
        "glaciares. En los seres vivos transporta nutrientes y regula temperatura.",
        0.9,
    ),
    (
        "oxigeno",
        "El oxigeno es un elemento quimico esencial. En la atmosfera terrestre lo respiran muchos "
        "seres vivos; gran parte del oxigeno libre proviene de la fotosintesis.",
        0.85,
    ),
    (
        "carbono",
        "El carbono es la base de la quimica organica: forma cadenas y anillos en moleculas de "
        "la vida (azucares, proteinas, ADN, combustibles fosiles, etc.).",
        0.85,
    ),
    (
        "electricidad",
        "La electricidad es el flujo de carga electrica (normalmente electrones). Mueve motores, "
        "ilumina, alimenta ordenadores y es central en la tecnologia moderna.",
        0.85,
    ),
    (
        "ordenador",
        "Un ordenador procesa informacion segun instrucciones (programas). Tiene hardware "
        "(CPU, memoria, disco) y software. Alex corre en servidores y se usa desde el navegador.",
        0.85,
    ),
    (
        "navegador",
        "Un navegador web (Chrome, Firefox, Safari, Edge...) muestra paginas HTML y ejecuta "
        "JavaScript. Desde el navegador usas alex.html para hablar con Alex.",
        0.85,
    ),
    (
        "seguridad",
        "La seguridad informatica protege datos y sistemas frente a accesos indebidos. Incluye "
        "contrasenas fuertes, cifrado, actualizaciones y no compartir claves de admin.",
        0.85,
    ),
    (
        "privacidad",
        "La privacidad es el derecho a controlar la informacion personal. En Alex, las cuentas "
        "usan Firebase Auth; el premium se gestiona por UID sin exponer contrasenas en el chat.",
        0.85,
    ),
    (
        "salud",
        "La salud es el estado de bienestar fisico, mental y social. Depende de alimentacion, "
        "sueno, ejercicio, relaciones y acceso a cuidados medicos. No sustituyo consejo medico profesional.",
        0.85,
    ),
    (
        "educacion",
        "La educacion transmite conocimientos y habilidades. Puede ser formal (escuela) o informal. "
        "Alex puede ayudar a explicar temas, pero conviene contrastar con fuentes fiables.",
        0.85,
    ),
    (
        "economia",
        "La economia estudia como se producen, distribuyen y consumen bienes y servicios. "
        "Incluye mercados, dinero, trabajo y politicas publicas.",
        0.8,
    ),
    (
        "democracia",
        "La democracia es un sistema en el que el poder politico deriva del pueblo, normalmente "
        "mediante elecciones y derechos civiles. Hay muchas variantes institucionales.",
        0.8,
    ),
    (
        "derechos humanos",
        "Los derechos humanos son principios que buscan proteger la dignidad de todas las "
        "personas: vida, libertad, igualdad ante la ley, expresion, etc.",
        0.8,
    ),
    (
        "universo",
        "El universo es el conjunto del espacio-tiempo, la materia y la energia. Se observa en "
        "expansion; incluye galaxias, estrellas, planetas y materia oscura aun poco comprendida.",
        0.85,
    ),
    (
        "galaxia",
        "Una galaxia es un enorme sistema de estrellas, gas, polvo y materia oscura unidos por "
        "gravedad. La Via Lactea es nuestra galaxia.",
        0.85,
    ),
    (
        "via lactea",
        "La Via Lactea es la galaxia espiral donde esta el sistema solar. Contiene miles de "
        "millones de estrellas.",
        0.85,
    ),
    (
        "tiempo",
        "El tiempo puede referirse a la dimension en la que ocurren los sucesos, o al clima "
        "meteorologico. En fisica relativista esta unido al espacio en el espacio-tiempo.",
        0.8,
    ),
    (
        "luz",
        "La luz visible es radiacion electromagnetica que el ojo humano detecta. Viaja a unos "
        "300.000 km/s en el vacio y es la base de la vision y de muchas tecnologias (fibra optica, lasers).",
        0.85,
    ),
    (
        "sonido",
        "El sonido es una onda mecanica que se propaga en un medio (aire, agua, solidos). "
        "Frecuencia se percibe como tono; amplitud como volumen.",
        0.8,
    ),
    (
        "color",
        "El color es la percepcion visual de distintas longitudes de onda de la luz. En imagenes "
        "digitales suele codificarse en RGB (rojo, verde, azul).",
        0.8,
    ),
    (
        "comida",
        "Los alimentos aportan energia y nutrientes. Una dieta variada ayuda a la salud; las "
        "necesidades exactas dependen de cada persona y conviene consultar profesionales de la salud.",
        0.8,
    ),
    (
        "deporte",
        "El deporte combina actividad fisica, reglas y a menudo competicion. Beneficia cuerpo y "
        "mente; el descanso y la tecnica reducen lesiones.",
        0.8,
    ),
    (
        "amistad",
        "La amistad es un vinculo de afecto, confianza y apoyo mutuo. Es importante para el "
        "bienestar emocional.",
        0.8,
    ),
    (
        "trabajo",
        "El trabajo es la actividad productiva o profesional. Puede ser empleo, proyecto propio "
        "o colaboracion. Organizar tareas y descansar mejora el rendimiento.",
        0.8,
    ),
    (
        "creatividad",
        "La creatividad es la capacidad de generar ideas o soluciones nuevas y utiles. Se "
        "entrena con practica, curiosidad y combinando conocimientos distintos.",
        0.8,
    ),
    (
        "logica",
        "La logica estudia el razonamiento valido: como se relacionan premisas y conclusiones. "
        "Es base de las matematicas, la programacion y el pensamiento critico.",
        0.8,
    ),
    (
        "probabilidad",
        "La probabilidad mide la incertidumbre de un suceso (de 0 imposible a 1 seguro). Se usa "
        "en estadistica, juegos, ciencia y en como Alex elige entre respuestas candidatas.",
        0.85,
    ),
    (
        "estadistica",
        "La estadistica resume y analiza datos: medias, variaciones, correlaciones e inferencias. "
        "Ayuda a no confundir casualidad con patron real.",
        0.8,
    ),
    (
        "idioma",
        "Un idioma es un sistema de signos para comunicar. Alex detecta el idioma del usuario "
        "(es, en, fr, pt...) e intenta responder en el mismo.",
        0.9,
    ),
    (
        "espanol",
        "El espanol (castellano) es una lengua romance hablada por cientos de millones de "
        "personas. Es el idioma principal de Alex y de la web de Game Boys Studios.",
        0.9,
    ),
    (
        "ingles",
        "El ingles es una lengua germanica de uso global en ciencia, tecnologia y negocios. "
        "Alex puede conversar y traducir entre espanol e ingles.",
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
    ("mi cuota", "suscripcion"),
    ("traduccion", "traducir"),
    ("foto", "imagenes"),
    ("imagen", "imagenes"),
    ("pc", "ordenador"),
    ("computadora", "ordenador"),
]

PALABRAS_BASE = [
    "alex", "diego", "ar", "game", "boys", "studios", "firebase", "wikipedia",
    "python", "api", "json", "github", "render", "inteligencia", "artificial",
    "memoria", "aprendizaje", "fotosintesis", "programacion", "ecosistema",
    "premium", "suscripcion", "traducir", "imagen", "biodiversidad", "energia",
    "atomo", "adn", "celula", "clima", "cine", "musica", "sol", "tierra", "luna",
    "agua", "oxigeno", "universo", "galaxia", "probabilidad", "idioma", "espanol",
]


def sembrar_conocimiento(memoria, forzar: bool = False) -> int:
    """
    Inserta conocimiento base con puntuacion alta.
    Semilla v3: mas contexto general + planes/suscripcion claros.
    """
    preferencias = memoria.datos.setdefault("preferencias", {})
    if not forzar and preferencias.get("semilla_conocimiento_v3"):
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
    preferencias["semilla_conocimiento_v3"] = True
    memoria.guardar()
    print(f"[Alex] Semilla v3 de conocimiento aplicada: {escritos} temas base")
    return escritos
