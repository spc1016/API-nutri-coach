# 🥗 NutriCoach API - Memoria del Proyecto y Guía de Uso

¡Bienvenido a **NutriCoach**! Una plataforma de software integral diseñada para conectar a **nutricionistas** y **clientes**, permitiendo una planificación nutricional avanzada, el diseño de rutinas de entrenamiento físico a medida, el seguimiento minucioso del progreso corporal y una red comunitaria interactiva.

Este repositorio contiene la arquitectura completa del proyecto, dividida en un robusto **Backend en Flask** con base de datos NoSQL en **MongoDB Atlas** y un **Cliente de terminal CLI** para interactuar de forma directa con todas las funcionalidades de la API.

---

## 🗺️ Índice
1. [🚀 Arquitectura y Tecnologías](#1--arquitectura-y-tecnologías)
2. [🔒 Sistema de Seguridad y Roles](#2--sistema-de-seguridad-y-roles)
3. [📁 Estructura del Código](#3--estructura-del-código)
4. [📊 Diseño de la Base de Datos (Modelos MongoDB)](#4--diseño-de-la-base-de-datos-modelos-mongodb)
5. [📈 Flujos de Trabajo Clave](#5--flujos-de-trabajo-clave)
6. [🛠️ Catálogo Completo de Endpoints (API Specs)](#6--catálogo-completo-of-endpoints-api-specs)
7. [💻 Cliente Interactivo (CLI)](#7--cliente-interactivo-cli)
8. [⚙️ Instalación y Puesta en Marcha](#8--instalación-y-puesta-en-marcha)

---

## 1. 🚀 Arquitectura y Tecnologías

El diseño del sistema sigue un modelo cliente-servidor desacoplado, estructurado en base a servicios web RESTful de alto rendimiento y bajo acoplamiento:

```mermaid
graph TD
    Client[💻 Cliente CLI / App Web] -->|HTTP REST + Bearer JWT| API[🐍 API Flask]
    
    subgraph Servidor Backend
        API -->|Controlador / Blueprints| Auth[🔑 Auth & Registro]
        API -->|Controlador / Blueprints| Users[👤 Gestión Usuarios]
        API -->|Controlador / Blueprints| Catalog[🥗 Catálogos]
        API -->|Controlador / Blueprints| Plans[📋 Dietas & Rutinas]
        API -->|Controlador / Blueprints| Follow[📊 Seguimiento & Historial]
        API -->|Controlador / Blueprints| Social[💬 Muro Comunidad]
    end

    Auth -->|Hilos Asíncronos| Mail[✉️ Google Apps Script Mailer]
    API -->|PyMongo| DB[(🍃 MongoDB Atlas)]
    API -->|Swagger UI| Docs[📝 Docs Interactiva /docs]
```

### 🛠️ Stack Tecnológico Utilizado
*   **Lenguaje de Programación:** Python 3.x
*   **Framework Web:** **Flask 3.1.2** como núcleo REST.
*   **Base de Datos:** **MongoDB Atlas** (Base de datos NoSQL en la nube) gestionada mediante **PyMongo 4.16.0**.
*   **Autenticación & Autorización:** **Flask-JWT-Extended 4.7.1** con tokens firmados y claims de rol personalizados.
*   **Validación de Datos:** **jsonschema 4.26.0** para la validación estricta en tiempo de ejecución de las cargas útiles (payloads) HTTP.
*   **Envío de Correos (OTP):** Google Apps Script Web App API para entrega inmediata y gratuita de correos corporativos en formato HTML interactivo.
*   **Documentación Interactiva:** **flask-swagger-ui 5.21.0** para renderizar la especificación **OpenAPI 3.0.3** en formato interactivo.

---

## 2. 🔒 Sistema de Seguridad y Roles

NutriCoach cuenta con una capa robusta de seguridad basada en **JSON Web Tokens (JWT)** y control de acceso basado en roles (**RBAC**). Al autenticarse con éxito, el servidor inyecta el rol del usuario (`cliente` o `nutricionista`) en los *claims* adicionales del token.

### 🛡️ Decoradores de Control de Acceso (En `utils.py`)

Para garantizar que los recursos permanezcan protegidos, se han implementado decoradores personalizados que interceptan las peticiones:

1.  `@check_auth('nutricionista')`: Restringe el acceso estrictamente a usuarios con rol de **nutricionista** (ej. creación de alimentos en el catálogo maestro, eliminación de clientes).
2.  `@check_auth_any()`: Permite el acceso a cualquier usuario con un JWT válido, ya sea cliente o nutricionista (ej. interactuar en la comunidad, ver catálogos maestros).
3.  `@check_auth_owner_or_nutricionista()`: Una regla dinámica avanzada. Permite el paso si el solicitante es un **nutricionista**, o bien si el solicitante es un **cliente** y su ID coincide exactamente con el ID del recurso que intenta modificar (ej. actualizar su propio peso, cambiar sus metas).

---

## 3. 📁 Estructura del Código

La API está estructurada modularmente mediante **Flask Blueprints**, lo que garantiza un desarrollo limpio, mantenible y escalable.

```bash
API_NutriCoach/
├── client/                      # Cliente interactivo para pruebas de la API
│   ├── main.py                  # Consola interactiva CLI (700+ líneas de lógica de negocio)
│   └── requirements.txt         # Dependencias del cliente (requests)
└── server/                      # Servidor API REST
    ├── blueprints/              # Módulos de rutas y controladores (Blueprints)
    │   ├── __init__.py
    │   ├── auth.py              # Login, registro y verificación por código OTP de correo
    │   ├── catalogos.py         # Catálogo maestro de alimentos y ejercicios
    │   ├── comunidad.py         # Posts, likes y comentarios
    │   ├── planes.py            # Gestión avanzada de dietas y rutinas (y sus subrecursos)
    │   ├── seguimiento.py       # Registro de peso corporal e historial de entrenamientos por series
    │   └── usuarios.py          # CRUD de clientes/nutricionistas y red de seguidores (follow)
    ├── application.py           # Punto de entrada de la aplicación Flask (configuraciones e inicializaciones)
    ├── config.py                # Variables de entorno y credenciales (MongoDB, JWT_Secret, etc.)
    ├── email_service.py         # Motor de envío OTP y validación temporal de pre-registro
    ├── utils.py                 # Conexión global a MongoDB y decoradores de autenticación
    ├── documentation.yaml       # Especificación completa OpenAPI 3.0.3 (Swagger)
    └── requirements.txt         # Dependencias de producción del servidor backend
```

---

## 4. 📊 Diseño de la Base de Datos (Modelos MongoDB)

MongoDB almacena los datos de forma flexible e hiper-optimizada. A continuación se detallan las estructuras (esquemas lógicos) de las colecciones principales en `NutricionDB`:

### 🟢 `clientes`
Almacena la información de los usuarios que consumen las dietas y rutinas.
```json
{
  "_id": "ObjectId('65fa3a4fb52b821a8c9b3e10')",
  "nombre": "Juan Pérez",
  "email": "juan@gmail.com",
  "password_hash": "pbkdf2:sha256:600000$...",
  "telefono": "612345678",
  "edad": 28,
  "peso": 78.5,
  "altura": 180.0,
  "genero": "Masculino",
  "objetivo": "Pérdida de grasa",
  "nutricionista_id": "ObjectId('65fa3a4fb52b821a8c9b3e01')"
}
```

### 🔵 `nutricionistas`
Profesionales que guían a los clientes y administran catálogos.
```json
{
  "_id": "ObjectId('65fa3a4fb52b821a8c9b3e01')",
  "nombre": "Dra. María López",
  "email": "maria@nutricoach.com",
  "password_hash": "pbkdf2:sha256:600000$...",
  "telefono": "699887766"
}
```

### 🟡 `verificaciones_pendientes` (Colección Temporal OTP)
Almacena de forma temporal los registros pre-validados mediante correo electrónico.
```json
{
  "_id": "ObjectId('65fa3c4fb52b821a8c9b3e99')",
  "email": "pedro.nuevo@gmail.com",
  "code": "847291",
  "nombre": "Pedro Nuevo",
  "password_hash": "pbkdf2:sha256:600000$...",
  "created_at": "ISODate('2026-05-28T17:03:31Z')" // Expira de forma automática tras 10 minutos
}
```

### 🟠 `dietas`
Diseño de planificación alimentaria con arrays de comidas y alimentos integrados de forma atómica.
```json
{
  "_id": "ObjectId('65fa4201b52b821a8c9b3f20')",
  "nombre": "Dieta Volumen Limpio",
  "cliente_id": "ObjectId('65fa3a4fb52b821a8c9b3e10')",
  "cliente": "Juan Pérez",
  "kcal_objetivo": 2800,
  "notas_generales": "Beber 3 litros de agua al día.",
  "activa": true,
  "publica": false,
  "comidas": [
    {
      "nombre": "Desayuno",
      "hora_sugerida": "08:30",
      "alimentos": [
        {
          "alimento_id": "ObjectId('65fa4001b52b821a8c9b3d05')",
          "nombre_snapshot": "Avena en hojuelas",
          "cantidad": 100.0,
          "unidad": "g"
        }
      ]
    }
  ]
}
```

### 🏋️ `rutinas`
Diseño de planificación de entrenamiento físico.
```json
{
  "_id": "ObjectId('65fa4301b52b821a8c9b3f50')",
  "nombre": "Rutina Push/Pull/Legs",
  "cliente_id": "ObjectId('65fa3a4fb52b821a8c9b3e10')",
  "cliente": "Juan Pérez",
  "activa": true,
  "publica": true,
  "dias": [
    {
      "nombre": "Día 1 - Empuje (Push)",
      "ejercicios": [
        {
          "ejercicio_id": "ObjectId('65fa4101b52b821a8c9b3e99')",
          "nombre_snapshot": "Press de Banca Inclinado",
          "series": 4,
          "repeticiones": 10,
          "descanso_segundos": 90
        }
      ]
    }
  ]
}
```

### 📊 `historial_entrenamientos`
Registro histórico detallado de los entrenamientos reales completados por el cliente.
```json
{
  "_id": "ObjectId('65fa4401b52b821a8c9b3f80')",
  "cliente_id": "ObjectId('65fa3a4fb52b821a8c9b3e10')",
  "rutina_nombre": "Rutina Push/Pull/Legs",
  "dia_nombre": "Día 1 - Empuje (Push)",
  "fecha": "2026-05-28",
  "ejercicios": [
    {
      "ejercicio_id": "ObjectId('65fa4101b52b821a8c9b3e99')",
      "nombre_snapshot": "Press de Banca Inclinado",
      "series": [
        { "repeticiones": "10", "peso": 80.0, "descanso_segundos": 90 },
        { "repeticiones": "8", "peso": 85.0, "descanso_segundos": 90 }
      ]
    }
  ]
}
```

### 💬 `posts` (Comunidad)
Red social integrada para compartir experiencias y planes.
```json
{
  "_id": "ObjectId('65fa4501b52b821a8c9b3fc0')",
  "autor_id": "ObjectId('65fa3a4fb52b821a8c9b3e10')",
  "autor_nombre": "Juan Pérez",
  "texto": "¡Hoy he completado mi entrenamiento de pierna! Comparto mi rutina pública.",
  "rutina_id": "ObjectId('65fa4301b52b821a8c9b3f50')",
  "dieta_id": null,
  "imagen_url": "http://res.cloudinary.com/imagen.jpg",
  "likes": 12,
  "liked_by": [
    "ObjectId('65fa3a4fb52b821a8c9b3e01')"
  ],
  "comentarios": [
    {
      "autor_id": "ObjectId('65fa3a4fb52b821a8c9b3e01')",
      "autor_nombre": "Dra. María López",
      "texto": "¡Excelente técnica de sentadilla hoy!",
      "fecha": "2026-05-28T18:04:12Z"
    }
  ],
  "fecha_creacion": "2026-05-28T17:55:00Z",
  "activa": true
}
```

---

## 5. 📈 Flujos de Trabajo Clave

### A. Registro de Clientes Seguro por Código OTP de Email
Evita la inyección de cuentas falsas o correos spam obligando al cliente a validar un código generado dinámicamente y enviado a su Gmail en tiempo real.

```mermaid
sequenceDiagram
    autonumber
    actor Cliente
    participant API as Servidor API
    participant DB as MongoDB Atlas
    participant GAS as Google Apps Script

    Cliente->>API: POST /register/send-code {nombre, email, password}
    Note over API: Valida que el email termine en @gmail.com
    API->>DB: Consultar duplicado en 'clientes' y 'nutricionistas'
    alt Email no duplicado
        API->>DB: Guarda registro temporal en 'verificaciones_pendientes' (Código OTP + Contraseña Hasheada)
        API->>GAS: HTTP POST Envío Correo OTP (Ejecución en segundo plano / Hilo)
        GAS-->>Cliente: Recibe Email Interactivo HTML con OTP
        API-->>Cliente: JSON {"message": "Código de verificación enviado"}
    else Email ya registrado
        API-->>Cliente: JSON {"error": "Este email ya está registrado"} (400)
    end

    Cliente->>API: POST /register/verify-code {email, code}
    API->>DB: Buscar OTP y comprobar expiración (< 10 minutos)
    alt OTP Válido e Índice Correcto
        API->>DB: Inserta documento final en colección 'clientes'
        API->>DB: Elimina registro temporal en 'verificaciones_pendientes'
        API-->>Cliente: JSON {"id": "cliente_id_creado"} (210)
    else OTP Inválido / Expirado
        API-->>Cliente: JSON {"error": "Código incorrecto o expirado"} (400)
    end
```

### B. Sistema de Muro Social y Compartición de Planes
Los usuarios pueden subir publicaciones al muro comunitario, vincular planes de dieta o rutinas que tengan marcadas como **públicas**, dar *likes* de forma interactiva (toggle on/off) y comentar en hilos dinámicos.

---

## 6. 🛠️ Catálogo Completo de Endpoints (API Specs)

La API cuenta con la documentación interactiva en el endpoint `/docs` (Swagger UI). A continuación se resumen todos los endpoints de la API ordenados por módulos y sus permisos:

### 🔑 Autenticación y Registro (`auth_bp`)

| Método | Endpoint | Permiso | Descripción |
| :--- | :--- | :--- | :--- |
| `POST` | `/login` | Público | Autentica al usuario (cliente/nutricionista). Retorna un JWT de acceso (válido 24 horas) y el rol. |
| `POST` | `/register/send-code` | Público | Valida datos básicos de registro y envía un código de 6 dígitos a un correo `@gmail.com` válido. |
| `POST` | `/register/verify-code` | Público | Valida el código temporal enviado. Si es correcto, da de alta al cliente de manera formal. |
| `POST` | `/register/resend-code` | Público | Genera y reenvía un nuevo código OTP a una solicitud pendiente de registro. |

### 👤 Usuarios y Seguimiento de Red (`usuarios_bp`)

| Método | Endpoint | Permiso | Descripción |
| :--- | :--- | :--- | :--- |
| `GET` | `/nutricionistas` | Público | Devuelve la lista completa de todos los nutricionistas disponibles. |
| `POST` | `/nutricionistas` | Nutricionista | Crea un nuevo nutricionista en el sistema (ideal para alta de colegas). |
| `PUT` | `/nutricionistas/<id>` | Nutricionista | Modifica los datos de perfil de un nutricionista. |
| `DELETE` | `/nutricionistas/<id>` | Nutricionista | Elimina el perfil de un nutricionista del sistema. |
| `GET` | `/nutricionistas/<id>/clientes` | Nutricionista | Devuelve todos los clientes que tienen asignado a este nutricionista. |
| `GET` | `/clientes` | Público | Devuelve la lista de clientes (excluye contraseña), incluyendo número de seguidores/seguidos. |
| `POST` | `/clientes` | Público | Creación directa de cliente sin verificación por email (bypass administrativo). |
| `GET` | `/clientes/<id>` | Público | Obtiene el perfil detallado de un cliente y su respectivo nutricionista. |
| `PUT` | `/clientes/<id>` | Propietario / Nutri | Modifica los datos de perfil de un cliente (edad, peso, altura, objetivo). |
| `DELETE` | `/clientes/<id>` | Nutricionista | Elimina a un cliente de la base de datos de manera irreversible. |
| `POST` | `/clientes/<id>/seguir` | Autenticado | Comienza a seguir a un cliente (sistema de red social interna). |
| `DELETE` | `/clientes/<id>/seguir` | Autenticado | Deja de seguir a un cliente. |
| `GET` | `/clientes/<id>/seguidores` | Público | Lista los seguidores del cliente. |
| `GET` | `/clientes/<id>/seguidos` | Público | Lista a los clientes que sigue el usuario. |

### 🥗 Catálogos Maestros (`catalogos_bp`)

| Método | Endpoint | Permiso | Descripción |
| :--- | :--- | :--- | :--- |
| `GET` | `/alimentos` | Público | Obtiene la lista completa del catálogo de alimentos y sus macronutrientes. |
| `GET` | `/alimentos/<id>` | Público | Obtiene el detalle de un alimento individual. |
| `POST` | `/alimentos` | Nutricionista | Registra un nuevo alimento con calorías, carbohidratos, grasas y proteínas. |
| `PUT` | `/alimentos/<id>` | Nutricionista | Modifica los macronutrientes o datos de un alimento. |
| `DELETE` | `/alimentos/<id>` | Nutricionista | Elimina un alimento del catálogo maestro. |
| `GET` | `/ejercicios` | Público | Lista todos los ejercicios cargados en el catálogo de entrenamiento. |
| `GET` | `/ejercicios/<id>` | Público | Obtiene la descripción e instrucciones de un ejercicio por ID. |
| `POST` | `/ejercicios` | Nutricionista | Crea un ejercicio especificando grupo muscular y duración recomendada. |
| `PUT` | `/ejercicios/<id>` | Nutricionista | Modifica los datos de un ejercicio. |
| `DELETE` | `/ejercicios/<id>` | Nutricionista | Elimina un ejercicio del catálogo de entrenamiento. |

### 📋 Gestión de Dietas y Rutinas (`planes_bp`)

> [!NOTE]
> Para la eliminación de dietas y rutinas, la API implementa **borrado lógico (soft delete)** marcando el atributo `activa: false`, de forma que los históricos de entrenamiento y muro social no pierdan la integridad de los datos.

| Método | Endpoint | Permiso | Descripción |
| :--- | :--- | :--- | :--- |
| `GET` | `/clientes/<id>/dietas` | Público | Obtiene todas las dietas del cliente (incluyendo inactivas e históricas). |
| `GET` | `/clientes/<id>/dietas-activas` | Público | Obtiene la planificación nutricional activa asignada al cliente. |
| `GET` | `/dietas/publicas` | Público | Lista global de todas las dietas compartidas como públicas por los usuarios. |
| `GET` | `/dietas/<id>` | Público | Detalle completo de una dieta y su desglose calórico. |
| `POST` | `/dietas` | Autenticado | Crea una dieta para un cliente (el cliente solo puede crear para sí mismo). |
| `PUT` | `/dietas/<id>` | Propietario / Nutri | Modifica las propiedades generales de una dieta. |
| `DELETE` | `/dietas/<id>` | Propietario / Nutri | Desactiva una dieta del sistema (Soft Delete / `activa: false`). |
| `POST` | `/dietas/<id>/comidas` | Propietario / Nutri | Agrega un menú de comida (ej. Cena, Post-entrenamiento) a una dieta. |
| `DELETE` | `/dietas/<id>/comidas/<idx>` | Propietario / Nutri | Elimina por completo una comida de la dieta mediante su índice numérico. |
| `POST` | `/dietas/<id>/comidas/<idx>/alimentos` | Propietario / Nutri | Agrega un alimento del catálogo a la comida, detallando cantidad y unidad. |
| `DELETE` | `/dietas/<id>/comidas/<c_idx>/alimentos/<a_idx>` | Propietario / Nutri | Elimina un alimento específico dentro de una comida según su índice. |
| `GET` | `/clientes/<id>/rutinas` | Público | Obtiene las rutinas del cliente (si es un tercero, solo devuelve las marcadas como públicas). |
| `GET` | `/clientes/<id>/rutinas-activas` | Público | Obtiene la planificación deportiva del cliente marcada como activa. |
| `GET` | `/rutinas/publicas` | Público | Lista global de todas las rutinas compartidas con la comunidad. |
| `GET` | `/rutinas/<id>` | Público | Detalle completo de una rutina y su orden diario de ejercicios. |
| `POST` | `/rutinas` | Autenticado | Crea una nueva rutina (el cliente solo puede crear para sí mismo). |
| `PUT` | `/rutinas/<id>` | Propietario / Nutri | Modifica atributos globales de la rutina. |
| `DELETE` | `/rutinas/<id>` | Propietario / Nutri | Desactiva una rutina del sistema (Soft Delete / `activa: false`). |
| `POST` | `/rutinas/<id>/dias` | Propietario / Nutri | Añade un día de entrenamiento (ej. Lunes - Pecho) a la rutina. |
| `DELETE` | `/rutinas/<id>/dias/<idx>` | Propietario / Nutri | Elimina un día de entrenamiento de la rutina mediante su índice. |
| `POST` | `/rutinas/<id>/dias/<idx>/ejercicios` | Propietario / Nutri | Añade un ejercicio al día de la rutina. **Previene duplicados en un mismo día.** |
| `DELETE` | `/rutinas/<id>/dias/<d_idx>/ejercicios/<e_idx>` | Propietario / Nutri | Quita un ejercicio del entrenamiento del día según su índice. |

### 📊 Seguimiento Físico e Historiales (`seguimiento_bp`)

| Método | Endpoint | Permiso | Descripción |
| :--- | :--- | :--- | :--- |
| `POST` | `/seguimientos` | Autenticado | Registra el peso actual de un cliente en una fecha específica para seguimiento de progreso. |
| `GET` | `/seguimientos/<id>` | Propietario / Nutri | Obtiene el detalle de un registro de progreso individual (peso y notas corporales). |
| `POST` | `/clientes/<id>/historial-entrenamientos` | Propietario / Nutri | Registra la finalización de un entrenamiento real, guardando pesos y repeticiones por serie. |
| `GET` | `/clientes/<id>/historial-entrenamientos` | Propietario / Nutri | Obtiene la lista histórica de todos los entrenamientos realizados, ordenados por los más recientes. |

### 💬 Comunidad e Interacción Social (`comunidad_bp`)

| Método | Endpoint | Permiso | Descripción |
| :--- | :--- | :--- | :--- |
| `GET` | `/posts` | Público | Lista todos los posts activos y públicos en la comunidad (orden descendente). |
| `GET` | `/posts/<id>` | Público | Obtiene un post en específico y sus comentarios. |
| `POST` | `/posts` | Autenticado | Crea una publicación con texto. Opcionalmente adjunta una imagen (Cloudinary URL) o planes públicos. |
| `DELETE` | `/posts/<id>` | Propietario | Realiza un borrado lógico del post del muro (`activa: false`). Solo permitido al autor del post. |
| `POST` | `/posts/<id>/like` | Autenticado | Sistema Toggle de Me Gusta (añade un like si no lo tenía, o lo quita si ya existía). |
| `POST` | `/posts/<id>/comentarios` | Autenticado | Agrega un comentario en formato de texto a la publicación. |
| `DELETE` | `/posts/<id>/comentarios/<idx>` | Autor Post / Autor Com | Elimina el comentario mediante su índice en el array. Solo permitido al autor del post o del comentario. |

---

## 7. 💻 Cliente Interactivo (CLI)

El proyecto incluye un completo **Cliente de Consola CLI** (`client/main.py`) programado en Python puro. Este cliente implementa un sistema interactivo mediante menús para interactuar con el 100% de la API de producción levantada en AWS Elastic Beanstalk o bien apuntando a un entorno de desarrollo local.

### 🌟 Características del Cliente
*   **Gestión de Sesión Fluida:** Permite hacer login y almacenar de forma transparente el token JWT Bearer para inyectarlo de manera automática en las peticiones posteriores.
*   **Gestión de Roles Dinámica:** El menú principal adapta y muestra el estado actual de tu sesión (`nutricionista`, `cliente` o `Sin sesión`).
*   **Consola Limpia y Asistida:** Formularios interactivos que validan tipos de datos (entero, decimal, obligatorios) antes de realizar peticiones HTTP REST.
*   **Formateo JSON Estilizado:** Las respuestas devueltas por el servidor se imprimen formateadas y con colores de depuración en la terminal para una rápida legibilidad.

---

## 8. ⚙️ Instalación y Puesta en Marcha

Sigue estos sencillos pasos para levantar el entorno de desarrollo en tu ordenador local:

### Requisitos Previos
*   Tener instalado **Python 3.8** o superior.
*   Contar con un clúster de base de datos en **MongoDB Atlas** (o una base de datos local MongoDB ejecutándose).

### A. Configuración y Ejecución del Servidor Backend

1.  Accede a la carpeta del servidor:
    ```bash
    cd server
    ```
2.  Instala todas las dependencias requeridas del sistema:
    ```bash
    pip install -r requirements.txt
    ```
3.  Crea tus variables de entorno en el sistema o configura directamente tu archivo `config.py` para enlazar tus servicios:
    *   `MONGODB_CONNECTION_STRING`: Tu URI de conexión a tu base de datos de MongoDB Atlas.
    *   `SECRET_KEY`: Una cadena segura para encriptar los tokens JWT del sistema.
    *   `GMAIL_WEB_APP_URL`: La URL del Web App de Google Apps Script para el envío automatizado de correos OTP.
4.  Levanta la aplicación localmente:
    ```bash
    python application.py
    ```
    *El servidor se levantará de forma automática en http://localhost:5000*
5.  **Verificación de Funcionamiento:**
    *   Abre tu navegador e ingresa a `http://localhost:5000/docs`. Deberías visualizar de forma automática el dashboard interactivo de **Swagger UI** con toda la especificación cargada correctamente.

### B. Ejecución del Cliente CLI

1.  Abre una terminal paralela y accede a la carpeta del cliente:
    ```bash
    cd client
    ```
2.  Asegúrate de tener instalada la librería de peticiones HTTP:
    ```bash
    pip install -r requirements.txt
    ```
3.  *(Opcional)* Edita el archivo `main.py` para cambiar la dirección de conexión base:
    *   Línea 7: Modifica `BASE_URL = "http://localhost:5000"` para pruebas de desarrollo local, o déjala por defecto apuntando al servidor cloud en producción.
4.  Ejecuta la consola interactiva en tu terminal:
    ```bash
    python main.py
    ```
5.  ¡Disfruta navegando y probando todas las funcionalidades interconectadas del sistema!

---

> [!TIP]
> **Autores del Proyecto:**
> Sergio Peralvarez & Jorge Moros
> *Desarrollo de Aplicaciones Multiplataforma (2º DAM)*
