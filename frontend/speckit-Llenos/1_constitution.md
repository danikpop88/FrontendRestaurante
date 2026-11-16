# Constitución del Proyecto "La mesa de la abuela"

> Principios **innegociables** que gobiernan el desarrollo del backend.
> Esta constitución es **permanente**: describe el sistema al que se quiere
> llegar y no cambia entre versiones de la especificación.
>
> El sistema se construye a partir de un **MVP** (ver Artículo 10). Lo que
> está fuera del MVP se considera **proyectado**: puede aparecer en los
> diagramas, pero se identifica como tal y no se implementa todavía.

---

## Artículo 1 — La documentación manda

El código, los diagramas UML, la arquitectura C4 y las historias de usuario
deben decir lo mismo.

- No se implementa ningún componente, servicio o tecnología que no esté en el
  modelo C4, salvo que se identifique expresamente como elemento proyectado.
- Si una decisión de implementación obliga a cambiar el diseño, **se actualiza
  el diagrama o documento afectado en el mismo cambio**; no después.
- Todo requisito (RF, RNF) y toda regla de negocio (RN) debe poder rastrearse
  hasta su historia de usuario y hasta el código que la cumple.

**Por qué:** el entregable evalúa la coherencia entre código fuente, UML y C4.
Un diseño que el código contradice deja de servir como documentación.

## Artículo 2 — Arquitectura por capas con tres contenedores

```
CAPA 1: APLICACIÓN WEB (HTML / CSS / JavaScript)  — pinta pantallas y llama a la API; NUNCA toca la BD
CAPA 2: API BACKEND (Python + FastAPI)            — autenticación, reglas de negocio, validaciones, integración externa
CAPA 3: BASE DE DATOS RELACIONAL (PostgreSQL)     — persistencia
```

- La aplicación web solo habla con la API. **Solo la API** se comunica con la
  base de datos y con los servicios externos (notificaciones, mensajería).
- La API devuelve datos (JSON); no genera HTML.
- El backend se organiza **en un módulo por componente C4** (autenticación,
  pedidos, cocina, domicilios, ventas y pagos, menú, reservas, notificaciones,
  integraciones). Inventario y calificaciones son proyectados y no se crean.
  Dentro
  de cada módulo hay tres capas, que se comunican mediante abstracciones:
  **ruta (controlador) → servicio → repositorio** (RNF-11).
  - La **ruta** recibe la petición HTTP, valida el formato y delega.
  - El **servicio** contiene las reglas de negocio.
  - El **repositorio** es el único que accede a la base de datos.
- El acceso a datos usa **psycopg con consultas parametrizadas**: el SQL queda
  visible y escrito por el equipo, sin ORM que lo esconda.

**Por qué:** separar capas permite cambiar la pantalla o la base de datos sin
reescribir las reglas del negocio, y los nombres de los módulos coinciden con
los del diagrama de componentes.

## Artículo 3 — Las reglas de negocio viven en el backend

Las reglas RN-01 a RN-10 se validan **siempre en el backend**, aunque el front
también las muestre o las anticipe.

- Una regla se escribe en un solo lugar de la **capa de negocio** (el servicio y
  las clases de dominio que este usa, como los estados del pedido). Nunca en la
  ruta ni en el repositorio.
- Cada regla tiene su flujo alternativo implementado: cuando se viola, la API
  responde con un error controlado y un mensaje claro, no con una falla.
- Cada regla tiene al menos una prueba que demuestra que se cumple y otra que
  demuestra qué pasa cuando se viola.

**Por qué:** el front se puede saltar; el backend no. Y la entrega exige que
los flujos alternativos estén implementados y se puedan demostrar.

## Artículo 4 — Cinco patrones GoF, ni uno más ni uno menos

El diseño usa exactamente estos cinco patrones, cada uno con un problema real:

| Patrón | Módulo | Problema que resuelve |
|---|---|---|
| State | Gestión de pedidos | El comportamiento del pedido cambia según su estado |
| Proxy | Domicilios / Pagos | Controla el acceso a servicios externos y datos sensibles |
| Factory Method | Gestión de pedidos | Crea pedidos de mesa y de domicilio |
| Observer | Cocina / Notificaciones | Avisa automáticamente a varios actores |
| Command | Administración de cocina | Encapsula acciones para auditoría y colas |

- Los patrones no se repiten ni se agregan otros sin justificar una necesidad
  real del MVP (se descartaron Flyweight y Strategy por sobreingeniería).
- Cada patrón en el código es identificable por el nombre de sus clases.

## Artículo 5 — Principios SOLID

- Cada clase tiene una sola razón para cambiar.
- Las capas se comunican mediante **clases abstractas (`ABC`)**, no mediante
  clases concretas (inversión de dependencias).
- Las dependencias concretas se arman en un único punto de ensamblaje
  (`main.py`).

## Artículo 6 — Seguridad

- Contraseñas de todos los usuarios (clientes y personal) de **mínimo 12
  caracteres** (RNF-01), almacenadas siempre con **hash**, nunca en texto plano.
- Toda comunicación entre la interfaz y el backend viaja por **HTTPS con
  TLS 1.3** (RNF-02) en el entorno desplegado.
- Las sesiones expiran tras **30 minutos de inactividad** (RNF-03).
- Cada petición valida el **rol** del usuario. Solo el rol Administrador
  modifica el menú (RN-09) y ve reportes de ventas y pagos (RN-10).
- Los valores en consultas SQL van siempre **parametrizados**, nunca
  concatenados.
- Los datos personales exigen **consentimiento explícito previo** al registro
  (RNF-14).

## Artículo 7 — Calidad: validar, probar y fallar con control

- Toda entrada se valida en el backend antes de procesarse.
- Los errores se manejan de forma controlada: nunca se expone un error interno
  al usuario.
- Cobertura de pruebas unitarias del backend **superior al 70 %** (RNF-10),
  usando **pytest** y **pytest-cov**.
- Las pruebas usan una base de datos separada (`mesa_abuela_test`) para no
  alterar los datos de desarrollo.

## Artículo 8 — Metas de rendimiento y fiabilidad

- Consulta del menú categorizado: máximo **800 ms** con 50 usuarios
  concurrentes (RNF-04).
- Reportes consolidados de ventas: máximo **3 s** con menos de 100.000
  registros (RNF-05).
- Disponibilidad de **98,5 %** en horario operativo (RNF-06).
- Respaldos automáticos diarios de la base de datos sin interrumpir los
  módulos activos (RNF-07).

## Artículo 9 — Ejecución portable

- Backend, frontend y base de datos se empaquetan por separado (RNF-15).
- El proyecto debe poder ejecutarse con comandos estándar de instalación de
  dependencias (`pip install -r requirements.txt`) en **Linux, macOS y
  Windows**, **sin depender exclusivamente de contenedores**. Si se ofrece
  Docker, es una alternativa y no el único camino.
- El `README.md` explica paso a paso cómo instalar y ejecutar cada pieza.

## Artículo 10 — Alcance del MVP

**Incluido:** el recorrido completo del pedido, de mesa y a domicilio:
registro e inicio de sesión por roles · menú categorizado y carrito ·
pedidos del cliente y comandas del mesero (con modificación y cancelación
dentro de los primeros 5 minutos) · pago contra entrega · cola de cocina y
aviso de plato listo · asignación automática de domiciliario y cierre de la
entrega con cobro · administración del menú · consulta de ventas y de
reservas (con datos de ejemplo).

**Simulado:** el cobro del pago contra entrega (mediante el Proxy de pago) y
los avisos de pedido listo (se muestran en pantalla, sin notificación push).

**Fuera del MVP (proyectado):** pagos en línea con pasarela · ruta optimizada
para domiciliarios · comunicación entre domiciliario y cliente · calificación
del servicio · creación de reservas por el cliente · inventario de insumos.

Lo proyectado se deja identificado en diagramas y documentos, y no se programa.

## Artículo 11 — Convenciones fijas

| Cosa | Convención |
|---|---|
| Idioma | Español para el dominio (`Pedido`, `Comanda`, `EstadoPedido`); sin tildes ni `ñ` en identificadores. Comentarios y mensajes al usuario en español |
| Lenguaje y framework | Python 3.11+ con FastAPI |
| Puertos | Backend **8000** · Frontend **5500** · PostgreSQL **5432** |
| CORS | El backend permite únicamente el origen del frontend |
| Base de datos | PostgreSQL: `mesa_abuela` (desarrollo) · `mesa_abuela_test` (pruebas) |
| Nombres en el código | Clases en PascalCase; funciones, variables y módulos en snake_case; las clases abstractas e interfaces llevan el prefijo `I` (por ejemplo `IEstadoPedido`) y heredan de `ABC`; el resto de nombres coincide con el diagrama |
| Estructura del backend | Un módulo por componente C4: ruta · servicio · repositorio |
| Estructura del frontend | HTML / CSS / JavaScript (ya existente en `FrontendRestaurante`) |

```
backend/
  app/
    main.py              ← punto único de ensamblaje
    config.py
    compartido/          ← seguridad, excepciones, conexión a BD
    autenticacion/  pedidos/  cocina/  domicilios/  ventas_pagos/
    menu/  reservas/  notificaciones/  integraciones/
  pruebas/
  requirements.txt
frontend/
db/                      ← script SQL de creación y datos de ejemplo
README.md
```

