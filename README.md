# Alex — IA local en castellano

IA local sin APIs de LLM externas. Aprende definiciones, sinónimos y correcciones; guarda memoria en JSON; opcionalmente busca en DuckDuckGo.

## Estructura

```
alex/           → núcleo (NLP, memoria, aprendizaje, probabilidad…)
static/         → interfaz web oscura
web_server.py   → servidor HTTP (API + UI)
main.py         → interfaz de consola
requirements.txt
```

## Uso local

```bash
pip install -r requirements.txt
python main.py          # consola
python web_server.py    # web en http://127.0.0.1:8765
```

## Despliegue en Render

1. New → Web Service → conecta este repo
2. **Build Command:** `pip install -r requirements.txt`
3. **Start Command:** `python web_server.py`
4. Plan **Free**

La URL será algo como `https://alex-ia.onrender.com`.

## API

| Método | Ruta | Body | Descripción |
|--------|------|------|-------------|
| POST | `/api/chat` | `{"mensaje": "..."}` | Respuesta de Alex |
| GET | `/api/stats` | — | Estadísticas de memoria |
| POST | `/api/feedback` | `{"positiva": true/false}` | Ajusta pesos |
| POST | `/api/borrar_memoria` | — | Borra memoria permanente |

## Enseñar a Alex

- Definición: `fotosíntesis significa proceso por el cual las plantas…`
- Sinónimo: `casa = hogar`
- Corrección: `no, se dice …`
- Pregunta: `qué es fotosíntesis`

Hecho para Game Boys Studios.
