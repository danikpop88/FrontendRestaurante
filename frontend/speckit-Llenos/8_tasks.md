# Tareas — MVP de "La mesa de la abuela" (front + API + PostgreSQL)

> El orden de construcción, partiendo de CERO. Cada fase termina en algo
> **verificable**. Requisitos: [2_spec.md](2_spec.md) · técnica:
> [3_plan.md](3_plan.md) · datos: [5_data_model.md](5_data_model.md) ·
> contratos: [6_contracts.md](6_contracts.md) · validación final:
> [7_quickstart.md](7_quickstart.md).
>
> **Cada fase se construye por capas**, de abajo hacia arriba: modelos y
> contrato del repositorio → repositorio PostgreSQL → servicio (el `Gestor…`) →
> ruta. Y cada módulo se registra en `main.py`, el único que conoce las clases
> concretas.

**Qué se puede repartir.** Cuando termine la Fase 1, las Fases 2, 3, 4 y la parte
de reservas de la Fase 8 no dependen entre sí. La Fase 5 necesita la 3 y la 4; la
6 necesita la 5; la 7 necesita la 5 y la 6. El front puede empezar por
`cliente_api.js` en cuanto exista la Fase 2.

---

## Fase 0 — Base de datos y esqueleto
- [ ] `db/crear_tablas.sql`: las **9 tablas** de [5_data_model.md](5_data_model.md)
      §3 (`usuario`, `producto`, `pedido`, `detalle_pedido`, `domicilio`, `pago`,
      `mesa`, `reserva`, `aviso`), con llaves, `UNIQUE` y los `CHECK` de los
      catálogos. **Sin triggers ni procedimientos almacenados.**
- [ ] `db/datos_ejemplo.sql`: los productos del menú con sus categorías, las
      mesas, los usuarios de prueba (para poder entrar con cada rol) y las
      reservas de ejemplo (RF-11). Las claves de los usuarios de prueba se
      completan en la Fase 2.
- [ ] Crear las bases `mesa_abuela` y `mesa_abuela_test` y cargar los dos scripts
      en cada una ([7_quickstart.md](7_quickstart.md) §1.1).
- [ ] Crear `backend/` con la estructura de [3_plan.md](3_plan.md) §2: `app/`
      (`main.py`, `config.py`, `compartido/`, y las carpetas `autenticacion/`,
      `pedidos/` con `estados/` y `creadores/`, `cocina/`, `domicilios/`,
      `ventas_pagos/`, `menu/`, `reservas/`, `notificaciones/` e
      `integraciones/`), `pruebas/` y `requirements.txt` (`fastapi`, `uvicorn`,
      `psycopg[binary]`, `pytest`, `pytest-cov`, `httpx`).
- [ ] Crear `frontend/js/` (vacía por ahora) y dejar las vistas que ya existen
      donde están. **Ahora, no al final**: una carpeta vacía a la vista recuerda
      que falta la mitad del trabajo.
- [ ] `README.md` con el título y los puertos (8000, 5500 y 5432), y un
      `.gitignore` (entorno virtual, `__pycache__`, archivos de IDE).

**Verificar:** `\dt` en `mesa_abuela` lista las **9 tablas**; `producto`, `mesa`,
`reserva` y `usuario` traen datos; `pip install -r requirements.txt` termina sin
errores dentro de un entorno virtual.

## Fase 1 — El núcleo compartido
- [ ] `config.py`: lee las variables de entorno (`DB_HOST`, `DB_PUERTO`,
      `DB_NOMBRE`, `DB_USUARIO`, `DB_CLAVE` y `ORIGEN_FRONT`).
- [ ] `compartido/conexion.py`: abre una conexión por petición con `psycopg`.
- [ ] `compartido/excepciones.py`: `NoAutenticadoError`, `SinPermisoError`,
      `NoEncontradoError` y `ReglaNegocioError`.
- [ ] `compartido/reloj.py`: `IReloj` (clase abstracta con `ABC`), `RelojSistema`
      y un reloj falso al que se le puede adelantar la hora (para las pruebas).
- [ ] `compartido/seguridad.py`: hash de claves con `hashlib.scrypt` y sal por
      usuario; sesiones **en memoria** con token (`secrets.token_urlsafe`),
      último acceso y vencimiento a los **30 minutos** (recibe un `IReloj`); y la
      dependencia `requiere_rol(...)`.
- [ ] `main.py` mínimo: crea la aplicación FastAPI, activa CORS **solo para**
      `ORIGEN_FRONT` y registra los manejadores que traducen cada excepción a su
      código HTTP ([3_plan.md](3_plan.md) §5.10), con el envoltorio de error de
      [6_contracts.md](6_contracts.md) §0.

**Verificar:** `uvicorn app.main:app --port 8000` arranca y
<http://localhost:8000/docs> abre. Un test comprueba que el hash nunca coincide
con la clave en texto plano y que una sesión **vence a los 30 minutos** con el
reloj falso; otro, que cada excepción produce su código (401, 403, 404 y 409).

## Fase 2 — Autenticación de usuarios (RF-01, RF-06)
- [ ] `modelos.py`: `IUsuario` (abstracta), `Cliente`, `IEmpleado` (abstracta),
      `Mesero`, `Domiciliario` y `Administrador`, con los atributos del nivel 4.
      (`Chef` es del componente Cocina y se crea en la Fase 7.)
- [ ] `repositorio.py`: `IRepositorioUsuarios`. `repositorio_postgres.py`:
      `RepositorioUsuariosPostgres` con consultas parametrizadas sobre `usuario`.
- [ ] `servicio.py`: `GestorAutenticacion`: registro del cliente (clave de al
      menos 12 caracteres, consentimiento de datos, email único → 409), crear
      cuentas del personal (solo `Administrador`), iniciar y cerrar sesión, y
      guardar la dirección del cliente.
- [ ] `rutas.py`: las cinco rutas de [6_contracts.md](6_contracts.md) §1, con
      validación de la forma y `requiere_rol`.
- [ ] Generar con la función de hash de `seguridad.py` las claves de los usuarios
      de prueba y completarlas en `db/datos_ejemplo.sql`; volver a cargar los
      scripts.
- [ ] Registrar el módulo en `main.py`.

**Verificar (criterios 1 a 5):** [7_quickstart.md](7_quickstart.md) §2.1: registro
válido (201), clave corta y datos sin aceptar (422), email repetido (409), clave
equivocada (401), Mesero pidiendo ventas (403) y cuenta del personal solo por el
administrador.

## Fase 3 — Menú y productos (RF-02, RF-12, RF-13, RF-14)
- [ ] `modelos.py`: `Producto` con `actualizarDisponibilidad()`.
- [ ] `repositorio.py` y `repositorio_postgres.py`: `IRepositorioProductos` y su
      implementación (listar con filtro de `categoria`, crear, editar, cambiar
      disponibilidad).
- [ ] `servicio.py`: `GestorMenu`: la categoría debe existir entre las del menú,
      el precio no puede ser negativo, el nombre no puede estar vacío y solo el
      `Administrador` modifica (RN-09).
- [ ] `rutas.py`: las cuatro rutas de [6_contracts.md](6_contracts.md) §2.
- [ ] Registrar el módulo en `main.py`.

**Verificar (criterio 18, y la mitad del 6):** [7_quickstart.md](7_quickstart.md)
§2.2: listar y filtrar por categoría, precio negativo (422), y marcar un producto
agotado y verlo con `disponible: false`.

## Fase 4 — Ventas y pagos: el patrón Proxy (RF-07)
- [ ] `modelos.py`: `Pago` con `confirmarPago()`.
- [ ] `ServicioPago`: `IServicioPago` (abstracta), `ServicioPagoReal` (guarda el
      `Pago` en el repositorio) y **`ServicioPagoProxy`**, que recibe el real,
      valida el pedido con `esValido()`, registra la transacción y **recién
      entonces delega**.
- [ ] `repositorio.py` y `repositorio_postgres.py`: `IRepositorioPagos` y su
      implementación. El pago nace en `Pendiente de Cobro`.

**Verificar:** `pytest pruebas -k proxy` (con un pedido falso): un pedido válido se
registra y llega al servicio real; **uno inválido no llega**.

## Fase 5 — Pedidos: los patrones State y Factory Method (RF-03 a RF-06, RF-16)
- [ ] `modelos.py`: `TipoPedido` (`EN_RESTAURANTE` y `DOMICILIO`), `DetallePedido`
      (con `calcularSubtotal()`), `IPedido` (abstracta, con `IVA = 0.19`, la lista
      de observadores, `agregarProducto`, `eliminarProducto`, `calcularTotal`,
      `siguiente`, `cancelar`, `obtenerEstado`, `setEstadoPedido`,
      `notificarObservadores` y `esValido`), `PedidoMesa` y `PedidoDomicilio`.
- [ ] `estados/`: **State**. `IEstadoPedido` con `modificar`, `cancelar`,
      `siguiente` y `obtenerEstado`, y las cuatro clases del nivel 4:
      `EstadoRecibido` (modificar y cancelar solo con menos de 5 minutos, usando
      el `IReloj`: RN-01), `EstadoEnCocina` (no se cancela: RN-04),
      `EstadoEnCamino` y `EstadoEntregado`.
- [ ] `creadores/`: **Factory Method**. `ICreadorPedidos`, `CreadorPedidoMesa`
      (el `numero_mesa` debe existir) y `CreadorPedidoDomicilio` (dirección, método
      de pago `CONTRA_ENTREGA` y teléfono del cliente: RN-07).
- [ ] `repositorio.py` y `repositorio_postgres.py`: `IRepositorioPedidos` y su
      implementación. Crear un pedido con su detalle (y, si es a domicilio, su
      `domicilio` sin domiciliario y su pago pendiente) va en **una sola
      transacción**; cancelar elimina todo eso.
- [ ] `servicio.py`: `GestorPedidos` recibe por constructor el mapa
      `TipoPedido → creador`, el `IServicioPago`, el repositorio y el `IReloj`.
      Resumen y total con IVA, crear, listar según el rol, obtener, modificar
      (solo `Mesero`) y cancelar (RN-05: producto agotado).
- [ ] `rutas.py`: las cinco rutas de [6_contracts.md](6_contracts.md) §3.
- [ ] Registrar el módulo en `main.py`.

**Verificar (criterios 6 a 11):** `pytest pruebas -k "state or factory"`, y
[7_quickstart.md](7_quickstart.md) §2.2 y §2.3 hasta el criterio 11: pedido
agotado (409), carrito vacío (422), pedido a domicilio que nace `Recibido`, orden
de mesa, y modificar y cancelar dentro del plazo. El criterio 12 se cierra en la
Fase 7, cuando exista el estado "En cocina" por la API.

## Fase 6 — Domicilios (RF-21, RF-23, RF-24)
- [ ] `modelos.py`: `Domicilio` con `asignarDomiciliario()` y
      `actualizarEstado(estado, motivo)`.
- [ ] `repositorio.py` y `repositorio_postgres.py`: `IRepositorioDomicilios` y su
      implementación, con la consulta del domiciliario que tiene **menos pedidos
      activos**.
- [ ] `servicio.py`: `GestorDomicilios`: asignar automáticamente (si no hay
      domiciliarios, el pedido queda pendiente de asignar y un pedido "En camino"
      no se reasigna: RN-08), listar los domicilios de quien consulta con el
      teléfono y la dirección del cliente, y cerrar la entrega: `Entregado`
      pasa el pedido a `Entregado` y **registra el cobro** por el `IServicioPago`;
      `Devuelto` exige el motivo, no cobra y deja el pedido en "En camino".
- [ ] `rutas.py`: las dos rutas de [6_contracts.md](6_contracts.md) §5.
- [ ] Registrar el módulo en `main.py`.

**Verificar:** pruebas del gestor con repositorio falso y reloj falso: la
asignación elige al de menos pedidos, la reasignación se rechaza, `Entregado`
cobra y `Devuelto` no. El recorrido por la API se cierra en la Fase 7.

## Fase 7 — Cocina y Notificaciones: los patrones Command y Observer (RF-17 a RF-20, RF-24)
- [ ] `integraciones/`: `ServicioPush` **simulado**: guarda el aviso en la tabla
      `aviso`.
- [ ] `notificaciones/`: **Observer**. `IObservadorPedido` con
      `actualizar(pedido)`, y los observadores `Mesero` y `Domiciliario`, que
      envían el aviso por `ServicioPush`; `IRepositorioAvisos`, su implementación y
      `GestorNotificaciones`.
- [ ] `cocina/`: **Command**. `Chef` (extiende `IEmpleado`, con
      `visualizarPedidos()` y `ejecutarComando()`), `IComandoCocina`,
      `ComandoMarcarListo` y `ComandoCancelarPedido` (cada uno guarda el pedido,
      quién lo ejecutó y la fecha y hora), e `IVisualizadorPedidos`.
- [ ] `servicio.py`: `GestorCocina`: la cola ordenada por llegada, **tomar** el
      pedido (`Recibido → EnCocina`, guarda `id_chef`) y **marcar listo**
      (`EnCocina → EnCamino`): notifica a los observadores y, si es a domicilio,
      llama a la asignación de la Fase 6.
- [ ] `rutas.py`: las tres rutas de cocina de [6_contracts.md](6_contracts.md) §4
      y las dos de notificaciones de §6.
- [ ] Registrar los módulos en `main.py`, armando los observadores y el
      `ServicioPush` en el ensamblaje.

**Verificar (criterios 12 a 17):** [7_quickstart.md](7_quickstart.md) §2.3 y §2.4:
cancelar un pedido en cocina (409), marcar listo y ver el aviso **solo** en
quien corresponde, marcar listo por segunda vez (409), el domicilio asignado con
teléfono y dirección, y la entrega con su cobro. Y `pytest pruebas -k "observer or
comando"`.

## Fase 8 — Ventas y reservas (RF-10, RF-11)
- [ ] `ventas_pagos/servicio.py`: `GestorVentas`: las ventas por rango de fechas
      (un pedido `Entregado` con pago `Cobrado`), con el total; solo
      `Administrador` (RN-10).
- [ ] `reservas/`: `Reserva`, `Mesa` e `IVerificable`; `IRepositorioReservas` y su
      implementación; `GestorReservas`: las reservas vigentes (fecha de hoy o
      posterior), solo para el `Administrador`.
- [ ] `rutas.py` de ambos módulos: [6_contracts.md](6_contracts.md) §7 y §8.
- [ ] Registrar los módulos en `main.py`.

**Verificar (criterios 19 y 20):** [7_quickstart.md](7_quickstart.md) §2.4:
ventas con solo lo entregado y cobrado, rango inválido (422), reservas de
ejemplo, y 403 para quien no es administrador.

## Fase 9 — El ensamblaje y el contrato
- [ ] Revisar `main.py`: es el **único** lugar con las clases concretas
      ([3_plan.md](3_plan.md) §5.11). Ninguna ruta ni servicio importa un
      repositorio de PostgreSQL.
- [ ] Comparar las rutas de <http://localhost:8000/docs> con la tabla de
      [6_contracts.md](6_contracts.md) §9: ninguna falta y ninguna sobra.

**Verificar:** cada fila de la tabla §9 existe en `/docs`; y una búsqueda de
`repositorio_postgres` fuera de `main.py` y de los propios repositorios no
encuentra nada.

## Fase 10 — Pruebas: reglas, patrones y cobertura (RNF-10)
- [ ] Cada regla de negocio (RN-01, 04, 05, 07, 08, 09 y 10) tiene **dos pruebas**:
      una que demuestra que se cumple y otra que demuestra qué pasa cuando se
      viola.
- [ ] Los tests de cada patrón llevan su nombre (`state`, `factory`, `observer`,
      `proxy` y `comando`) para correrlos por separado con `-k`
      ([7_quickstart.md](7_quickstart.md) §3.2). Los criterios que la API no puede
      mostrar a mano llevan el suyo: `sesion` (criterio 3), `telefono` (8) y
      `reasignacion` (16).
- [ ] Las pruebas de reglas usan repositorios falsos en memoria y el reloj falso:
      no necesitan PostgreSQL.
- [ ] Las pruebas de rutas usan el cliente de pruebas de FastAPI sobre
      `mesa_abuela_test`.

**Verificar:** `pytest --cov=app --cov-fail-under=70` termina en verde. Con
PostgreSQL apagado, `pytest pruebas -k "reglas or capas"` también pasa: **la prueba
de capas**.

## Fase 11 — El front: conectar las vistas
> Se conservan las vistas HTML/CSS/JavaScript que ya existen: aquí solo se les
> da vida. Todo se construye **contra la API que ya responde**.

- [ ] `frontend/js/cliente_api.js`: la **única** pieza que usa `fetch`. Arma la
      petición, añade el token, devuelve siempre `{ ok, datos, errores }`, traduce
      cada respuesta con la tabla de [6_contracts.md](6_contracts.md) §12 y
      distingue **«no respondió»** de «respondió con error».
- [ ] `frontend/js/autenticacion.js`: registro, inicio y cierre de sesión, guardar
      el token y mostrar las pantallas según el rol (la seguridad real la pone el
      backend).
- [ ] `frontend/js/notificaciones.js`: pide los avisos cada pocos segundos y los
      muestra en la pantalla del rol; al verlos, los marca como leídos.
- [ ] Conectar las vistas de [6_contracts.md](6_contracts.md) §11, una por rol:
      cliente (menú, carrito, confirmar, mis pedidos), mesero, chef,
      domiciliario y administrador.
- [ ] Ninguna vista llama a la API por su cuenta, ni muestra verbos, rutas o
      códigos HTTP al usuario.

**Verificar (criterios del spec vistos por una persona):** el recorrido de
[7_quickstart.md](7_quickstart.md) §4, incluida la **prueba de los dos
procesos**: con PostgreSQL encendido y la API apagada, la pantalla sigue en pie,
dice que el servicio no está disponible y **no muestra un solo dato**.

> Si la pantalla siguiera mostrando datos con la API apagada, la arquitectura
> estaría mal aunque todo lo demás funcione: querría decir que el front llegó a la
> base por su cuenta.

## Fase 12 — Cierre del MVP
- [ ] `README.md` completo: cómo instalar y ejecutar cada pieza en Linux, macOS y
      Windows, **sin depender de contenedores** (RNF-15).
- [ ] Correr el smoke test completo de [7_quickstart.md](7_quickstart.md): los
      **21** criterios de aceptación de [2_spec.md](2_spec.md) §5.
- [ ] Revisar la constitución **artículo por artículo** contra el código
      ([3_plan.md](3_plan.md) §9).
- [ ] Cada integrante con **al menos 5 commits significativos**, de su propia
      cuenta y con mensajes descriptivos (Artículo 12). Un commit al terminar cada
      fase es una buena costumbre.
- [ ] Commit final y tag `mvp`.

**El MVP está TERMINADO** cuando los 21 criterios pasan, incluidos los flujos
alternativos, la demostración funcional es estable y cada integrante tiene sus
commits ([2_spec.md](2_spec.md) §7).
