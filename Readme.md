# 🚀 Galactum Core API - Documentación de Integración

Este repositorio contiene el backend unificado para el ecosistema **Galactum** desarrollado en **FastAPI** y **SQLAlchemy**, conectado nativamente a una base de datos distribuida en la nube **Neon DB (PostgreSQL)**.

---

## 🏗️ Arquitectura de Software Implementada 

El proyecto sigue un patrón de diseño desacoplado y orientado a servicios para facilitar que cualquier equipo de Frontend consuma los recursos de forma independiente:

* **`app/models/` (Capa de Persistencia):** Mapeo directo a tablas físicas en Neon DB. Contiene las entidades clave del negocio como `user.py`, `alianzas.py`, `tripulante.py`, `misiones.py` y `server.py`.
* **`app/schemas/` (Capa de Validación):** Esquemas de Pydantic que actúan como contratos de datos estrictos (ej: `user.py`, `alianzas.py`). Filtran e inspeccionan los JSON entrantes.
* **`app/services/` (Capa de Negocio):** Aquí reside el "cerebro" del simulador. Archivos como `auth.py`, `alianzas_service.py` y `misiones_service.py` procesan las reglas del juego, validaciones lógicas y transacciones.
* **`app/api/routes/` (Endpoints HTTP):** Controladores encargados de exponer los servicios al exterior de manera estructurada (rutas base `/api/v1`).

---

## 📖 Instrucciones para el Equipo Frontend (Empresa)

### 1. Contratos de Datos e Interfaz de Pruebas
La API cuenta con documentación automatizada viva bajo el estándar OpenAPI. Al levantar el servidor local, el catálogo completo de endpoints (Misiones, Alianzas, Tripulantes, Conflictos) y sus respectivos esquemas JSON de entrada/salida están disponibles en:
👉 **`http://127.0.0.1:8000/docs`**

### 2. Flujo de Autenticación y Seguridad (JWT)
El sistema utiliza el estándar industrial **OAuth2 con Bearer Tokens (JWT)** gestionado por el servicio `auth.py`. 

1. **Autenticación inicial:** El cliente debe enviar un `POST` a `/api/v1/auth/login` con las credenciales básicas (`username`, `password`).
2. **Uso del Token:** Si las credenciales son válidas, el backend responderá con un JSON que contiene un string plano en `access_token`. El Frontend debe capturar este string y almacenarlo de forma segura (LocalStore, memoria de estado, etc.).
3. **Peticiones Protegidas:** Para consumir recursos restringidos (como los servicios de `alianzas.py` o `tripulantes.py`), el Frontend debe inyectar obligatoriamente el token en los encabezados HTTP de cada petición:
   * **Header Key:** `Authorization`
   * **Header Value:** `Bearer <TU_TOKEN_JWT_AQUÍ>`

### 3. Habilitación de CORS
El archivo `app/main.py` tiene configurado el middleware de CORS permitiendo orígenes cruzados (`allow_origins=["*"]`) para facilitar la etapa de desarrollo local desde aplicaciones móviles, WebApps o prototipos de simulación (Godot). Para el despliegue en producción final, se recomienda restringir esta lista a los dominios oficiales de la empresa.

---

## 🛠️ Despliegue Rápido del Servidor

1. Instalar el entorno virtual y dependencias:
   ```bash
   pip install -r requirements.txt
Configurar la cadena de conexión en el archivo .env apuntando al clúster asignado de Neon DB:

Fragmento de código
DATABASE_URL=postgresql://<USUARIO>:<CLAVE>@<CLUSTER>.neon.tech/main?sslmode=require
Ejecutar el punto de entrada de la aplicación:

Bash
uvicorn app.main:app --reload

---

## 🎮 En el Frontend de Godot: Dejar el APIManager Limpio

Para que la transición sea transparente, asegúrate de que el script **`APIManager.gd`** que maneja las peticiones HTTP en Godot tenga las variables mapeadas de forma limpia hacia el prefijo unificado de su backend (`/api/v1/`). 

Debe quedar con una estructura modular como esta:

```gdscript
extends Node

# URL del servidor local de desarrollo. Cambiar por la URL de producción cuando corresponda.
const BASE_URL = "http://127.0.0.1:8000/api/v1"

# Rutas exactas mapeadas de los endpoints del backend
var url_login = BASE_URL + "/auth/login"
var url_register = BASE_URL + "/auth/register"
var url_alianzas = BASE_URL + "/alianzas/buscar"

# Variable global para guardar el token una vez que el login sea exitoso
var token_jwt: String = ""

func guardar_token(nuevo_token: String):
	token_jwt = nuevo_token

func obtener_headers_protegidos() -> PackedStringArray:
	# Esta función genera automáticamente el encabezado que el backend pide en el README
	return PackedStringArray([
		"Content-Type: application/json",
		"Authorization: Bearer " + token_jwt
	])