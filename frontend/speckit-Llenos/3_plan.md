# Plan técnico — MVP de "La mesa de la abuela"

> CÓMO construir lo especificado en [2_spec.md](2_spec.md), bajo las reglas de
> [1_constitution.md](1_constitution.md). El porqué de cada decisión:
> [4_research.md](4_research.md) · entidades: [5_data_model.md](5_data_model.md)
> · contratos exactos: [6_contracts.md](6_contracts.md) · orden:
> [8_tasks.md](8_tasks.md).
>
> Este plan **no inventa arquitectura**: toma los tres contenedores del C4
> nivel 2, los componentes del nivel 3 y las clases y patrones del nivel 4 del
> Entregable, y los baja a carpetas, archivos y reglas de dependencia.

---

## 1. Stack

| Pieza | Elección | Por qué |
|---|---|---|
| Lenguaje | **Python 3.11+** | Es el lenguaje del contenedor "API Backend" en el C4 nivel 2 |
| Framework de la API | **FastAPI** + **uvicorn** | Valida las entradas con tipos (RNF-09, Art. 7) y su sistema de dependencias deja ver la inyección de dependencias de SOLID |
| Base de datos | **PostgreSQL** | Es la tecnología del contenedor "Base de Datos Relacional" en el C4 nivel 2 |
| Acceso a datos | **psycopg 3** con consultas parametrizadas | SQL visible y escrito por el equipo, sin ORM (Art. 2 de la constitución) |
| Abstracciones | **`abc.ABC`** | Las clases `<<abstract>>` e `<<interface>>` del diagrama se escriben igual en el código |
| Claves de usuario | **`hashlib.scrypt`** (librería estándar) con sal por usuario | Hash sin dependencias extra (Art. 6) |
| Pruebas | **pytest** + **pytest-cov** + **httpx** (cliente de pruebas de FastAPI) | RNF-10: cobertura mayor al 70 % |
| Front | **HTML / CSS / JavaScript** (el ya existente) | Es el contenedor "Aplicación web" del C4 nivel 2 |
| Cliente de la API en el front | **`fetch`** de JavaScript, en un solo archivo | El C4 nivel 3 lo define como "único punto de comunicación con el backend" |
| Servidor del front | Servidor estático estándar (`python -m http.server 5500`) | Sin instalar nada extra; el front solo son archivos |
| Servicios externos | **Simulados** (aviso en pantalla y pago con Proxy) | El spec los declara simulados; telefonía y push real son proyectados |

Dependencias del backend (`requirements.txt`): `fastapi`, `uvicorn`,
`psycopg[binary]`, `pytest`, `pytest-cov`, `httpx`. Nada más.

## 2. Estructura de carpetas

Un módulo por componente del C4 nivel 3. Los componentes **Inventario** y
**Calificaciones** son proyectados y **no se crean** en el MVP.

```
(raíz del proyecto)
├── README.md                         # cómo instalar y ejecutar cada pieza (RNF-15)
├── .gitignore                        # entorno virtual, __pycache__, archivos de IDE
├── db/
│   ├── crear_tablas.sql              # las tablas del MVP
│   └── datos_ejemplo.sql             # menú, usuarios de prueba y reservas de ejemplo
├── frontend/                         # Aplicación web (puerto 5500) — el front existente
│   ├── (vistas HTML/CSS ya hechas, por rol)
│   └── js/
│       ├── cliente_api.js            # ÚNICA pieza que habla HTTP con el backend
│       ├── autenticacion.js          # registro, inicio de sesión y pantallas según rol
│       └── notificaciones.js         # recepción de avisos (simulada con sondeo)
└── backend/                          # API Backend (puerto 8000)
    ├── requirements.txt
    ├── app/
    │   ├── main.py                   # punto ÚNICO de ensamblaje: arma todo y registra las rutas
    │   ├── config.py                 # variables de entorno (conexión, CORS, plazos)
    │   ├── compartido/
    │   │   ├── conexion.py           # abre la conexión a PostgreSQL
    │   │   ├── seguridad.py          # hash de claves, sesiones, control de rol
    │   │   ├── reloj.py              # IReloj (ABC) y RelojSistema: la hora, para poder probar los 5 minutos
    │   │   └── excepciones.py        # errores de negocio que las rutas traducen a HTTP
    │   ├── autenticacion/            # componente "Autenticación de usuarios"
    │   ├── pedidos/                  # componente "Pedidos"
    │   │   ├── estados/              #   patrón State
    │   │   └── creadores/            #   patrón Factory Method
    │   ├── cocina/                   # componente "Cocina"  (patrón Command)
    │   ├── domicilios/               # componente "Domicilios"
    │   ├── ventas_pagos/             # componente "Ventas y pagos"  (patrón Proxy)
    │   ├── menu/                     # componente "Menú y productos"
    │   ├── reservas/                 # componente "Reservas"  (solo consulta)
    │   ├── notificaciones/           # componente "Notificaciones"  (patrón Observer)
    │   └── integraciones/            # componente "Integraciones externas"  (simuladas)
    └── pruebas/                      # pytest: reglas, patrones y capas
```

**Dentro de cada módulo** (autenticación, pedidos, cocina, domicilios,
ventas_pagos, menu, reservas y notificaciones) hay siempre los mismos archivos:

```
rutas.py         ← CAPA DE RUTAS: recibe la petición HTTP, valida su forma, delega
servicio.py      ← CAPA DE NEGOCIO: el "Gestor…" con las reglas de negocio
repositorio.py   ← el contrato de acceso a datos (clase abstracta)
repositorio_postgres.py ← la implementación con psycopg y SQL parametrizado
modelos.py       ← las clases de dominio del nivel 4 del C4 (o una carpeta si son varias)
```

## 3. Arquitectura en capas (notación C4)

Los nombres son los del C4 del Entregable: personas, contenedores (nivel 2) y
componentes (nivel 3).

```
[Persona]  Cliente · Mesero · Chef · Domiciliario · Administrador
     │  usa
     ▼
[Contenedor]  Aplicación web                    [JavaScript · HTML · CSS]  :5500
  componentes: Autenticación y sesión · Vistas del cliente · Vistas del mesero ·
               Vistas del chef · Vistas del domiciliario · Vistas del administrador ·
               Recepción de notificaciones · Cliente de la API
     │  JSON / HTTP  — el Cliente de la API es el único punto de comunicación
     │  (HTTPS en el entorno desplegado: RNF-02 es proyectado)
     ▼
[Contenedor]  API Backend                       [Python · FastAPI]  :8000
  componentes: Autenticación de usuarios · Pedidos · Cocina · Domicilios ·
               Ventas y pagos · Menú y productos · Reservas · Notificaciones ·
               Integraciones externas
     │  SQL parametrizado (psycopg)                 │  usa (simulado)
     ▼                                              ▼
[Contenedor]  Base de Datos Relacional      [Sistema externo]  Servicio de
              [PostgreSQL]  :5432                              notificaciones push
```

**Dentro de cada componente `[Python]` del API Backend** hay tres capas, que se
repiten igual en todos:

```
  CAPA DE RUTAS     rutas.py          valida la forma, exige sesión y rol, traduce errores a HTTP
     ↓
  CAPA DE NEGOCIO   servicio.py       Gestor…: reglas de negocio (RN-01 a RN-10), patrones
     ↓              + modelos.py      clases de dominio: Pedido, estados, comandos, proxy…
  CAPA DE DATOS     repositorio.py    contrato (ABC) — el servicio no sabe qué hay detrás
                    repositorio_postgres.py   psycopg + consultas parametrizadas
```

**Regla de dependencias:** ruta → servicio → contrato del repositorio. Las
clases concretas solo las conoce `main.py`.

**Las flechas que no existen:**
- De la Aplicación web a la Base de Datos Relacional no hay ninguna: el
  navegador solo habla con la API.
- Del repositorio al servicio, ni de la ruta al repositorio: las capas solo
  se conocen hacia abajo.

**Qué va en cada capa:**

| Capa | Hace | No hace |
|---|---|---|
| Rutas | Leer la petición, validar su forma (tipos, campos obligatorios), exigir sesión y rol, traducir excepciones a HTTP | Reglas de negocio, SQL |
| Negocio (servicio + dominio) | Aplicar las reglas (plazo de 5 minutos, producto agotado, quién puede qué), coordinar los patrones | Conocer HTTP o SQL |
| Datos (repositorio) | Guardar y leer con SQL parametrizado; reconstruir las clases de dominio | Decidir reglas |

## 4. Del C4 al código

| Componente C4 | Carpeta | Clases del nivel 4 | Patrón | RF |
|---|---|---|---|---|
| Autenticación de usuarios | `autenticacion/` | `IUsuario` (abstracta), `Cliente`, `IEmpleado` (abstracta), `Mesero`, `Domiciliario`, `Administrador` | — | RF-01 |
| Pedidos | `pedidos/` | `GestorPedidos`, `IPedido` (abstracta), `PedidoMesa`, `PedidoDomicilio`, `DetallePedido`, `TipoPedido` | State · Factory Method | RF-03, 04, 05, 06, 16 |
| (estados) | `pedidos/estados/` | `IEstadoPedido` + `EstadoRecibido`, `EstadoEnCocina`, `EstadoEnCamino`, `EstadoEntregado` | State | RN-01, RN-04 |
| (creadores) | `pedidos/creadores/` | `ICreadorPedidos`, `CreadorPedidoMesa`, `CreadorPedidoDomicilio` | Factory Method | RF-16, RF-03 |
| Cocina | `cocina/` | `Chef`, `IComandoCocina`, `ComandoMarcarListo`, `ComandoCancelarPedido`, `IVisualizadorPedidos` | Command | RF-18, 19, 20 |
| Domicilios | `domicilios/` | `Domicilio` | — | RF-21, 23, 24 |
| Ventas y pagos | `ventas_pagos/` | `Pago`, `IServicioPago`, `ServicioPagoReal`, `ServicioPagoProxy` | Proxy | RF-07, RF-10 |
| Menú y productos | `menu/` | `Producto` | — | RF-02, 12, 13, 14 |
| Reservas | `reservas/` | `Reserva`, `Mesa`, `IVerificable` | — | RF-11 |
| Notificaciones | `notificaciones/` | `IObservadorPedido`, `Mesero`, `Domiciliario` | Observer | RF-17, RF-24 |
| Integraciones externas | `integraciones/` | `ServicioPush` (simulado) | — | RF-17, RF-24 |
| Inventario · Calificaciones | *(no se crean)* | — | — | RF-15, RF-09 (proyectados) |

> Los nombres son los del nivel 4 del C4, con dos convenciones del código:
> las clases abstractas e interfaces llevan el prefijo `I` (la interfaz
> `EstadoPedido` del diagrama se escribe `IEstadoPedido` en el código), y los observadores `Mesero` y
> `Domiciliario` del componente Notificaciones viven en `notificaciones/` y se
> importan por el nombre del módulo, para no confundirlos con los empleados de
> Autenticación. El nivel 4 dibuja solo dominio y patrones; las rutas, los
> gestores y los repositorios son la capa que el código agrega alrededor, **sin
> modificar los diagramas**.

## 5. Decisiones de diseño clave

### 5.1 Abstracciones con `ABC` y prefijo `I`
Las clases abstractas e interfaces del diagrama llevan el prefijo `I` en el código:

```python
from abc import ABC, abstractmethod

class IEstadoPedido(ABC):
    @abstractmethod
    def modificar(self, pedido, reloj): ...
    @abstractmethod
    def cancelar(self, pedido, reloj) -> bool: ...
    @abstractmethod
    def siguiente(self, pedido): ...
    @abstractmethod
    def obtenerEstado(self) -> str: ...
```

Los repositorios siguen la misma idea: `IRepositorioPedidos` es la clase
abstracta y `RepositorioPedidosPostgres` la implementación. El gestor recibe
la abstracta por constructor.

### 5.2 Los cinco patrones, dónde viven y qué hacen

| Patrón | Dónde | Cómo funciona en el código |
|---|---|---|
| **State** | `pedidos/estados/` | `IPedido` guarda un `IEstadoPedido`. Cada estado decide qué puede hacer: `EstadoRecibido` permite modificar o cancelar solo si pasaron menos de 5 minutos (RN-01); `EstadoEnCocina` rechaza cancelar (RN-04). No hay cadenas de `if` por estado |
| **Factory Method** | `pedidos/creadores/` | `GestorPedidos` guarda un mapa `TipoPedido → ICreadorPedidos` y llama `crearPedido()`. `CreadorPedidoMesa` produce un `PedidoMesa` y `CreadorPedidoDomicilio` un `PedidoDomicilio` |
| **Observer** | `pedidos/` (sujeto) y `notificaciones/` (observadores) | `IPedido` mantiene una lista de `IObservadorPedido`. Cuando el chef marca el pedido como listo (pasa de `EnCocina` a `EnCamino`) llama `notificarObservadores()`: `Mesero` o `Domiciliario` envían el aviso por `ServicioPush` |
| **Proxy** | `ventas_pagos/` | `GestorPedidos` usa la abstracta `IServicioPago`. `ServicioPagoProxy` valida el pedido con `esValido()`, registra la transacción y recién entonces delega en `ServicioPagoReal` |
| **Command** | `cocina/` | Cada acción del chef es un objeto con `ejecutar()`. `ComandoMarcarListo` y `ComandoCancelarPedido` guardan `pedido`, `ejecutadoPor` y `fechaHora`: eso es la auditoría |

### 5.3 Dónde viven las reglas de negocio
Las reglas viven en la **capa de negocio**, que incluye el gestor (servicio) y
las clases de dominio que este usa. Con el patrón State, las reglas RN-01 y
RN-04 están dentro de las clases de estado, y el gestor las invoca. Nunca están
en la ruta ni en el repositorio.

| Regla | Dónde se aplica |
|---|---|
| RN-01 (5 minutos) | `EstadoRecibido.modificar()` y `EstadoRecibido.cancelar()` |
| RN-04 (en cocina no se cancela) | `EstadoEnCocina.cancelar()` |
| RN-05 (producto agotado) | `GestorPedidos` al armar el pedido |
| RN-07 (domicilio sin teléfono) | `CreadorPedidoDomicilio` |
| RN-08 (no reasignar "En camino") | `Domicilio.asignarDomiciliario()` |
| RN-09 y RN-10 (rol Administrador) | La ruta exige el rol y el gestor lo verifica |

### 5.4 La ventana de 5 minutos y la hora (`IReloj`)
- Todo pedido nace en **Recibido**, con su fecha y hora de creación.
- Mientras esté en Recibido y hayan pasado **menos de 5 minutos**, se puede
  modificar y cancelar. Pasados 5 minutos, ya no (RN-01, criterio 11 del spec).
- `Recibido → EnCocina` ocurre cuando **el chef toma el pedido de su cola**
  (evento `enviarACocina()` de la máquina de estados). No pasa solo a los 5
  minutos. Desde que está "En cocina", no se modifica ni se cancela (RN-04).
- Los estados no llaman a `datetime.now()`: reciben un **`IReloj`** (clase
  abstracta). En producción es `RelojSistema`; en las pruebas es un reloj
  falso al que se le adelanta la hora para comprobar el plazo sin esperar.

### 5.5 Flujo de un pedido (los cuatro estados del nivel 4)

```
Recibido ──(chef lo toma)──▶ EnCocina ──(chef lo marca listo)──▶ EnCamino ──▶ Entregado (cobro)
   │
   └─ (cancelar, menos de 5 min: el pedido se elimina)
```

- Los estados son las cuatro clases del nivel 4: `EstadoRecibido`,
  `EstadoEnCocina`, `EstadoEnCamino` y `EstadoEntregado`. El cliente ve esos
  mismos cuatro (RF-05).
- **Marcar listo** (`ComandoMarcarListo`) avanza el pedido con `siguiente()` de
  `EnCocina` a `EnCamino`, y ahí se notifica al mesero o al domiciliario. En un
  pedido de mesa el pedido termina en "En camino" (el plato sale hacia la mesa):
  servir y cobrar en caja no se modelan en el MVP.
- **Cancelar** solo se permite en `Recibido` con menos de 5 minutos y **elimina
  el pedido** (con su detalle, su domicilio y su pago pendiente). El
  `ComandoCancelarPedido` conserva quién y cuándo, pero en la base no queda
  rastro.
- **Entregado** se alcanza cuando el domiciliario cierra la entrega: registra el
  cobro a través del Proxy y es lo que convierte al pedido en venta.
- **Devuelto** no es un estado del pedido: lo registra el `Domicilio`
  (`estado_entrega` = "Devuelto", con su motivo). El pedido sigue "En camino", no
  hay cobro y no cuenta como venta.

### 5.6 Asignación automática del domiciliario
En `GestorDomicilios`, cuando `ComandoMarcarListo` avanza un pedido a domicilio
a "En camino", el gestor elige al domiciliario con **menos pedidos activos**, lo
guarda en el `Domicilio` y el Observer le envía el aviso. Si no hay
domiciliarios, el pedido queda pendiente de asignar. Un pedido "En camino" no
se reasigna (RN-08).

### 5.7 Avisos simulados
`ServicioPush` es la única clase de `integraciones/`. En el MVP **simula** el
envío: guarda el aviso en la tabla `aviso` (destinatario, mensaje, fecha,
leído). El front lo recibe con un **sondeo cada pocos segundos** desde
`notificaciones.js` y lo muestra en la pantalla del rol. La telefonía
enmascarada (RF-22) es proyectada y no se crea.

### 5.8 Sesión y seguridad
- Registro e inicio de sesión: la clave se guarda con `scrypt` y sal propia;
  nunca en texto plano. Mínimo 12 caracteres para todos (RNF-01).
- Al iniciar sesión se crea un **token de sesión** (`secrets.token_urlsafe`)
  que la API guarda **en memoria** junto con su último acceso. Cada petición lo
  envía en la cabecera `Authorization` y actualiza el último acceso. Si el
  servidor se reinicia, las sesiones se pierden y hay que iniciar sesión de nuevo.
- Si pasan **30 minutos** sin actividad, la sesión expira (RNF-03).
- La ruta usa una dependencia `requiere_rol(...)` que rechaza al usuario sin
  sesión (no autenticado) o con un rol que no corresponde (sin permiso).
- El administrador crea las cuentas del personal; el cliente se registra solo y
  debe aceptar el tratamiento de datos (RNF-14).
- El front **habilita pantallas según el rol** solo por comodidad; la
  seguridad real la impone el backend.

### 5.9 Acceso a datos (psycopg, siempre parametrizado)
- Una conexión por petición, abierta en `compartido/conexion.py` y entregada
  a los repositorios.
- Todos los valores van como parámetros (`%s` con una tupla), **nunca**
  concatenados en el texto SQL.
- Cuando una operación escribe en varias tablas (crear un pedido con su
  detalle; registrar el cobro y cerrar la entrega), el repositorio la ejecuta
  en **una sola transacción**.
- Los repositorios devuelven **clases de dominio** (`PedidoMesa`, `Producto`...), no
  filas sueltas.
- Tablas del MVP: `usuario`, `producto`, `pedido`, `detalle_pedido`,
  `domicilio`, `pago`, `reserva`, `mesa`, `aviso`.
  `datos_ejemplo.sql` carga el menú, usuarios de prueba y las reservas de
  ejemplo (RF-11). El detalle va en [5_data_model.md](5_data_model.md).

### 5.10 Traducción de errores a HTTP (en la capa de rutas)

| Situación | Excepción | HTTP |
|---|---|---|
| Datos con forma inválida (tipo, campo faltante) | Validación del framework | 422 |
| Sin sesión, credenciales inválidas o sesión expirada | `NoAutenticadoError` | 401 |
| Rol sin permiso (RN-09, RN-10) | `SinPermisoError` | 403 |
| Pedido, producto o usuario inexistente | `NoEncontradoError` | 404 |
| Regla de negocio violada (RN-01, RN-04, RN-05, RN-07, RN-08) | `ReglaNegocioError` | 409 |
| Error inesperado | cualquier otra | 500 con mensaje genérico, sin detalles internos |

El mensaje que ve el usuario es siempre claro y en español; el detalle técnico
queda en el registro del servidor, no en la respuesta (Art. 7).

### 5.11 Ensamblaje (`main.py`)
Es el único lugar que conoce las clases concretas:

```python
reloj = RelojSistema()
servicio_push = ServicioPush(conexion)
repo_pedidos = RepositorioPedidosPostgres(conexion)
pago = ServicioPagoProxy(ServicioPagoReal(repo_pagos))   # Proxy delante del real
gestor_pedidos = GestorPedidos(repo_pedidos, creadores, pago, reloj)
```

Si mañana cambia el motor de base de datos o el servicio de pago, solo cambia
este archivo.

### 5.12 El front y su cliente de la API
- `cliente_api.js` es la **única** pieza que usa `fetch`. Arma la petición, añade
  el token de sesión y **traduce los errores a mensajes en español**. Las
  vistas nunca llaman a la API por su cuenta.
- Devuelve siempre la misma forma (`ok`, `datos`, `errores`), para que una vista
  pregunte "¿salió bien?" y no por códigos HTTP.
- Las vistas no muestran verbos HTTP, rutas ni códigos al usuario.
- El **carrito** vive en el front hasta que el cliente confirma el pedido;
  el backend recalcula el total (incluido el IVA del 19 %) y es el que manda.
- Se conserva el front que ya existe: este plan solo le agrega los tres archivos
  de `js/`.

## 6. Ejecución (sin depender de contenedores)

Por RNF-15 el proyecto se ejecuta con comandos estándar en Linux, macOS y
Windows. El `README.md` lo explica paso a paso:

1. Crear la base `mesa_abuela` y cargar `db/crear_tablas.sql` y
   `db/datos_ejemplo.sql`.
2. `cd backend` · crear el entorno virtual · `pip install -r requirements.txt`.
3. Definir las variables de entorno (conexión a la base, origen permitido del front).
4. `uvicorn app.main:app --port 8000`.
5. `cd frontend` · `python -m http.server 5500` · abrir `http://localhost:5500`.
6. Pruebas: `pytest --cov=app` (usa la base `mesa_abuela_test`).

Docker es opcional y **no es parte del MVP**: si el equipo lo agrega, es una
alternativa que no reemplaza estos pasos.

## 7. Pruebas

| Qué se prueba | Cómo |
|---|---|
| Reglas de negocio | El gestor con un repositorio **falso en memoria** y un `IReloj` falso: sin base de datos corriendo |
| Cada patrón | State (transiciones válidas e inválidas), Factory (mesa y domicilio), Observer (quién recibe el aviso), Proxy (valida y registra antes de delegar), Command (guarda quién y cuándo) |
| Flujos alternativos | Una prueba por regla violada (RN-01, 04, 05, 07, 08, 09, 10) |
| Rutas | Cliente de pruebas de FastAPI: códigos y mensajes |
| Recorrido completo | Criterio 21 del spec, con la base de pruebas |

Meta: **cobertura superior al 70 %** (RNF-10), medida con `pytest-cov`.

## 8. Convenciones

Las de la constitución: dominio en español sin tildes ni `ñ`, clases en
PascalCase, funciones, variables y módulos en snake_case, las clases abstractas
con prefijo `I` y heredando de `ABC`, y un comentario de
apertura en cada archivo que explica su papel en la arquitectura.

## 9. Chequeo de constitución

> **Compuerta 2:** antes de pasar a `8_tasks.md` se revisa la constitución
> **artículo por artículo**. Si algo no cumple, o se corrige el plan, o se
> enmienda la constitución. Nunca se deja pasar "por esta vez".

| Artículo | Cómo lo cumple este plan |
|---|---|
| **1** — La documentación manda | Cada módulo es un componente del C4 y cada clase sale del nivel 4, sin modificar los diagramas. El código solo agrega el prefijo `I` a las abstractas y la capa de rutas, gestores y repositorios |
| **2** — Tres contenedores y capas | Web → API → PostgreSQL (§3). Dentro de la API, ruta → servicio → repositorio por módulo, con SQL parametrizado y sin ORM |
| **3** — Reglas de negocio en el backend | RN-01 a RN-10 en la capa de negocio (§5.3); el front no decide nada |
| **4** — Cinco patrones GoF | State, Factory Method, Observer, Proxy y Command, cada uno en su módulo (§5.2) |
| **5** — SOLID | Clases abstractas con `ABC`, dependencias inyectadas por constructor y ensamblaje único en `main.py` (§5.1, §5.11) |
| **6** — Seguridad | Hash `scrypt`, clave de 12 caracteres, sesión de 30 minutos, rol en cada petición, consentimiento de datos (§5.8). HTTPS/TLS es proyectado (RNF-02) |
| **7** — Calidad | Validación en rutas, errores controlados (§5.10), pytest con más del 70 % (§7) |
| **8** — Rendimiento y fiabilidad | Metas de RNF-04 y RNF-05 verificables con una prueba básica; RNF-06 y RNF-07 proyectados |
| **9** — Ejecución portable | Comandos estándar, sin contenedores obligatorios (§6) |
| **10** — Alcance del MVP | Implementa lo del spec; Inventario, Calificaciones, reservar mesa, pasarela, ruta y telefonía no se crean |
| **11** — Convenciones | Puertos 8000/5500/5432, nombres y estructura según §2 y §8 |
| **12** — Git | Cada integrante con mínimo 5 commits propios y descriptivos |

**Complejidad justificada:** la única desviación es de redacción: el Artículo 3
decía que las reglas viven "en la capa de servicio", y con el patrón State
algunas están en las clases de estado que el servicio invoca. Se **enmendó la
constitución** para decir "capa de negocio" (servicio y dominio). No hay otras
desviaciones.
