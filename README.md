# Alex — IA local en castellano

IA local creada por Diego Ar (Game Boys Studios). Aprende, consulta Wikipedia y genera estructuras. Memoria en JSON local o **Firebase**.

## Uso local

```bash
pip install -r requirements.txt
python main.py
python web_server.py
```

## Render

- Build: `pip install -r requirements.txt`
- Start: `python web_server.py`

## Firebase (memoria persistente)

En el plan Free de Render el disco se borra al reiniciar. Con Firebase la memoria se conserva.

### 1. Crear proyecto Firebase

1. [Firebase Console](https://console.firebase.google.com/) → Create project
2. Build → **Realtime Database** → Create Database (modo test o reglas restringidas)
3. Copia la URL, ej: `https://TU-PROYECTO-default-rtdb.europe-west1.firebasedatabase.app`

### 2. Cuenta de servicio

1. Project settings → Service accounts → **Generate new private key**
2. Se descarga un JSON

### 3. Variables en Render

Environment → Add:

| Variable | Valor |
|----------|--------|
| `FIREBASE_DATABASE_URL` | `https://TU-PROYECTO-default-rtdb....firebasedatabase.app` |
| `FIREBASE_CREDENTIALS` | Contenido **entero** del JSON de la cuenta de servicio |
| `FIREBASE_ROOT` | `alex` (opcional) |

**Importante:** pega el JSON de credenciales en una sola variable (Render acepta multilinea). No subas ese JSON al repo.

### 4. Reglas RTDB (ejemplo basico servidor)

Con cuenta de servicio el servidor bypasea reglas; aun asi evita dejar todo publico en produccion.

### 5. Comprobar

Tras redeploy, en logs debe salir:

```text
[Alex] Backend FIREBASE -> firebase://alex
[Alex] Guardado FIREBASE OK: memoria_permanente
```

Y en `/api/memoria`:

```json
{ "backend": "firebase", "palabras": 5, "temas": 3 }
```

## API

| Metodo | Ruta | Descripcion |
|--------|------|-------------|
| POST | `/api/chat` | Chat |
| GET | `/api/stats` o `/api/memoria` | Stats + backend |
| POST | `/api/feedback` | Feedback |
| POST | `/api/borrar_memoria` | Borra memoria |

Hecho para Game Boys Studios.
