# Modelo de datos — MVP de "La mesa de la abuela"

> CÓMO se guardan los datos del MVP en el contenedor **Base de Datos
> Relacional (PostgreSQL)**. Parte del C4 nivel 3 (componentes de la base de
> datos) y del nivel 4 (clases y atributos), y respeta [2_spec.md](2_spec.md)
> y [3_plan.md](3_plan.md). Los contratos exactos están en
> [6_contracts.md](6_contracts.md).
>
> **Decisión clave:** la base **no tiene lógica**: ni triggers ni
> procedimientos almacenados. Las reglas de negocio viven en la capa de
> negocio de la API (Artículo 3 de la constitución); la base solo guarda los
> datos y garantiza su integridad.

---

## 1. Los scripts de la base de datos

El MVP trae dos scripts en la carpeta `db/` (ver [3_plan.md](3_plan.md) §2):

| Script | Qué hace |
|---|---|
| `crear_tablas.sql` | Crea las 9 tablas del MVP, con sus llaves y restricciones |
| `datos_ejemplo.sql` | Carga los productos del menú con sus categorías, mesas, usuarios de prueba (para poder entrar con cada rol) y las reservas de ejemplo (RF-11) |

Las tablas se agrupan en los **componentes de la base de datos del C4 nivel 3**:

```
Usuarios y roles:     usuario
Productos y menú:     producto
Pedidos:              pedido · detalle_pedido
Domicilios:           domicilio
Pagos:                pago
Reservas y mesas:     mesa · reserva
(fuera del C4):       aviso
```

**No se crean** los componentes **Calificaciones** e **Inventario** del C4: son
requisitos proyectados (RF-09 y RF-15).

> `aviso` no aparece en el C4 nivel 3 de la base de datos: la agrega el plan
> ([3_plan.md](3_plan.md) §5.7) para guardar los avisos simulados. Las sesiones
> (RNF-03) no tienen tabla: la API las maneja en memoria ([3_plan.md](3_plan.md)
> §5.8).

## 2. Convenciones de este modelo

- **Nombres:** tablas en singular. Cada columna lleva el nombre del atributo del
  nivel 4 en `snake_case`, sin tildes ni `ñ` (constitución, Artículo 11): por
  ejemplo `Pedido.estadoPedido` es `estado_pedido` y `Usuario.contraseña` es
  `contrasena`. La columna "Nombre en el C4" dice de qué atributo sale cada una;
  las llaves foráneas salen de las relaciones del diagrama.
- **Tipos:** `int` del diagrama es `INTEGER`; `String`, `VARCHAR`; `boolean`,
  `BOOLEAN`; `date`, `DATE`; `time`, `TIME`; y `double`, `NUMERIC(12,2)` para
  que los valores de dinero sean exactos.
- **Llaves primarias:** `INTEGER GENERATED ALWAYS AS IDENTITY`.
- **Catálogos:** los valores permitidos de `tipo_cargo`, `tipo_pedido`,
  `estado_pedido`, `estado_entrega` y `estado_pago` se limitan con `CHECK`. Eso solo evita datos
  fuera del catálogo: la regla de negocio la aplica la capa de negocio.

## 3. Las tablas del MVP

### 3.1 Usuarios y roles

El nivel 4 define `Usuario` (abstracta) con `Cliente` y `Empleado` (abstracta),
y esta con `Chef`, `Mesero`, `Domiciliario` y `Administrador`. Toda la jerarquía
se guarda en **una sola tabla**, `usuario`: los clientes tienen vacías
`id_empleado`, `tipo_cargo` y `estado`; los empleados tienen las tres, y
`tipo_cargo` dice si es Chef, Mesero, Domiciliario o Administrador.

**`usuario`**

| Columna | Tipo | Restricción | Nombre en el C4 |
|---|---|---|---|
| `id_usuario` | INTEGER | **PK** | `Usuario.idUsuario` |
| `nombre` | VARCHAR(100) | NOT NULL | `Usuario.nombre` |
| `telefono` | VARCHAR(20) | NOT NULL | `Usuario.telefono` |
| `email` | VARCHAR(100) | NOT NULL, UNIQUE | `Usuario.email` |
| `contrasena` | VARCHAR(255) | NOT NULL | `Usuario.contraseña` (guarda el hash `scrypt` con sal, nunca la contraseña en texto plano) |
| `direccion` | VARCHAR(200) | NULL | `Cliente.direccion` (solo clientes) |
| `id_empleado` | INTEGER | NULL, UNIQUE | `Empleado.idEmpleado` (solo empleados; se asigna al crear la cuenta del empleado) |
| `tipo_cargo` | VARCHAR(20) | NULL, CHECK en (`Chef`, `Mesero`, `Domiciliario`, `Administrador`) | `Empleado.tipoCargo` (solo empleados; vacío significa que es `Cliente`) |
| `estado` | BOOLEAN | NULL | `Empleado.estado` (solo empleados; falso = no está activo) |

### 3.2 Productos y menú

**`producto`**

| Columna | Tipo | Restricción | Nombre en el C4 |
|---|---|---|---|
| `id_producto` | INTEGER | **PK** | `Producto.idProducto` |
| `nombre` | VARCHAR(100) | NOT NULL | `Producto.nombre` |
| `descripcion` | VARCHAR(300) | NULL | `Producto.descripcion` |
| `precio` | NUMERIC(12,2) | NOT NULL | `Producto.precio` |
| `disponible` | BOOLEAN | NOT NULL, por defecto verdadero | `Producto.disponible` (falso = "Agotado", RN-05) |
| `categoria` | VARCHAR(50) | NOT NULL | `Producto.categoria` |
| `imagen` | VARCHAR(200) | NULL | Ruta de la foto del producto (RF-02 y RF-13) |

### 3.3 Pedidos

El nivel 4 define `Pedido` (abstracta) con `PedidoMesa` y `PedidoDomicilio`,
`DetallePedido` y la enumeración `TipoPedido`. Los dos tipos de pedido se guardan
en **una sola tabla**, `pedido`, que distingue el tipo con `tipo_pedido`.

**`pedido`**

| Columna | Tipo | Restricción | Nombre en el C4 |
|---|---|---|---|
| `id_pedido` | INTEGER | **PK** | `Pedido.idPedido` |
| `tipo_pedido` | VARCHAR(20) | NOT NULL, CHECK en (`EN_RESTAURANTE`, `DOMICILIO`) | `TipoPedido` |
| `estado_pedido` | VARCHAR(20) | NOT NULL, CHECK en los estados de la sección 4 | `Pedido.estadoPedido` |
| `fecha` | TIMESTAMP | NOT NULL | `Pedido.fecha` |
| `total` | NUMERIC(12,2) | NOT NULL | `Pedido.total` (en el diagrama es el atributo derivado `/total`, que calcula `calcularTotal()` con el IVA del 19 %, constante de la clase que no se guarda; se guarda el resultado porque el C4 nivel 3 dice que la base almacena el total) |
| `id_cliente` | INTEGER | NULL, **FK** → `usuario` | El `Cliente` que hizo el pedido; vacío en los pedidos de mesa |
| `numero_mesa` | INTEGER | NULL, **FK** → `mesa` (`numero_mesa`) | `PedidoMesa.numeroMesa`; relación `Mesa` se sirve en `PedidoMesa`; vacío en los pedidos a domicilio |
| `id_chef` | INTEGER | NULL, **FK** → `usuario` | Relación `Chef` gestiona `Pedido`; se llena cuando el chef toma el pedido |

> `fecha` es `TIMESTAMP` y no `DATE` como en el diagrama, porque RN-01 mide
> minutos: se necesita la hora exacta de creación.

**`detalle_pedido`**

> `/subtotal` es un atributo derivado del diagrama (lo calcula `calcularSubtotal()`:
> cantidad por precio unitario), por eso no tiene columna.

| Columna | Tipo | Restricción | Nombre en el C4 |
|---|---|---|---|
| `id_pedido` | INTEGER | **PK** (parte 1), **FK** → `pedido` | Relación `Pedido` 1 — 1..* `DetallePedido` |
| `id_producto` | INTEGER | **PK** (parte 2), **FK** → `producto` | Relación `DetallePedido` contiene `Producto` |
| `cantidad` | INTEGER | NOT NULL | `DetallePedido.cantidad` |
| `precio_unitario` | NUMERIC(12,2) | NOT NULL | `DetallePedido.precioUnitario` |
| `observaciones_especiales` | VARCHAR(300) | NULL | `DetallePedido.observacionesEspeciales` |

### 3.4 Domicilios

**`domicilio`**

| Columna | Tipo | Restricción | Nombre en el C4 |
|---|---|---|---|
| `id_domicilio` | INTEGER | **PK** | `Domicilio.idDomicilio` |
| `id_pedido` | INTEGER | NOT NULL, UNIQUE, **FK** → `pedido` | Relación `PedidoDomicilio` entrega en `Domicilio` (1 a 1: el domicilio se crea junto con el pedido) |
| `id_domiciliario` | INTEGER | NULL, **FK** → `usuario` | El `Domiciliario` que lleva el pedido; vacío mientras el pedido está pendiente de asignar |
| `direccion` | VARCHAR(200) | NOT NULL | `Domicilio.direccion` y `PedidoDomicilio.dirección` (es la misma dirección) |
| `estado_entrega` | VARCHAR(20) | NULL, CHECK en (`Entregado`, `Devuelto`) | `Domicilio.estadoEntrega`; vacío mientras la entrega está en curso |
| `fecha_entrega` | DATE | NULL | `Domicilio.fechaEntrega` |
| `motivo_devolucion` | VARCHAR(300) | NULL | `Domicilio.motivoDevolucion`; se exige cuando la entrega es "Devuelto" |

### 3.5 Pagos

**`pago`**

| Columna | Tipo | Restricción | Nombre en el C4 |
|---|---|---|---|
| `id_pago` | INTEGER | **PK** | `Pago.idPago` |
| `id_pedido` | INTEGER | NOT NULL, UNIQUE, **FK** → `pedido` | Relación `Pago` pertenece a `Pedido` |
| `id_cliente` | INTEGER | NULL, **FK** → `usuario` | Relación `Cliente` efectúa `Pago`; vacío en los pagos de pedidos de mesa |
| `estado_pago` | VARCHAR(30) | NOT NULL, CHECK en (`Pendiente de Cobro`, `Cobrado`) | `Pago.estadoPago` |
| `fecha` | DATE | NOT NULL | `Pago.fecha`; se actualiza al registrar el cobro |
| `monto` | NUMERIC(12,2) | NOT NULL | `Pago.monto` |

### 3.6 Reservas y mesas

**`mesa`**

| Columna | Tipo | Restricción | Nombre en el C4 |
|---|---|---|---|
| `id_mesa` | INTEGER | **PK** | `Mesa.idMesa` |
| `numero_mesa` | INTEGER | NOT NULL, UNIQUE | `Mesa.númeroMesa` |
| `capacidad_personas` | INTEGER | NOT NULL | `Mesa.capacidadPersonas` |
| `disponibilidad` | BOOLEAN | NOT NULL, por defecto verdadero | `Mesa.Disponibilidad` |

**`reserva`**

| Columna | Tipo | Restricción | Nombre en el C4 |
|---|---|---|---|
| `id_reserva` | INTEGER | **PK** | `Reserva.idReserva` |
| `id_mesa` | INTEGER | NOT NULL, **FK** → `mesa` | Relación `Reserva` contiene `Mesa` |
| `id_cliente` | INTEGER | NULL, **FK** → `usuario` | Relación `Cliente` registra `Reserva`; vacío en las reservas de ejemplo |
| `nombre_titular` | VARCHAR(100) | NOT NULL | `Reserva.nombreTitular` |
| `telefono_titular` | VARCHAR(20) | NOT NULL | `Reserva.telefonoTitular` (el diagrama lo declara `int`; se guarda como texto porque un teléfono no cabe en un entero de 32 bits) |
| `hora_reserva` | TIME | NOT NULL | `Reserva.horaReserva` |
| `fecha_reserva` | DATE | NOT NULL | `Reserva.fechaReserva` |

### 3.7 Avisos (simulados)

**`aviso`** (ver [3_plan.md](3_plan.md) §5.7)

| Columna | Tipo | Restricción | Descripción |
|---|---|---|---|
| `id_aviso` | INTEGER | **PK** | Identificador |
| `id_usuario` | INTEGER | NOT NULL, **FK** → `usuario` | Destinatario del aviso (mesero o domiciliario) |
| `mensaje` | VARCHAR(300) | NOT NULL | Texto que se muestra en la pantalla del rol |
| `fecha` | TIMESTAMP | NOT NULL | Cuándo se generó |
| `leido` | BOOLEAN | NOT NULL, por defecto falso | Si el destinatario ya lo vio |

## 4. Estados y catálogos

### Estados del pedido (`pedido.estado_pedido`)

Son las cuatro clases de estado del nivel 4 del C4 (`EstadoRecibido`,
`EstadoEnCocina`, `EstadoEnCamino` y `EstadoEntregado`):

| Estado | Qué significa | Pasa a |
|---|---|---|
| `Recibido` | El pedido se registró; se puede modificar o cancelar si pasaron menos de 5 minutos (RN-01) | `EnCocina` (el chef lo toma, `enviarACocina()`) |
| `EnCocina` | Se está preparando; no se cancela (RN-04) | `EnCamino` (el chef lo marca listo) |
| `EnCamino` | Salió de cocina y se notificó al mesero o al domiciliario | `Entregado` (cierre de la entrega) |
| `Entregado` | Pedido a domicilio entregado y cobrado | final |

- **Cancelar** no es un estado: elimina el pedido (solo en `Recibido`, con menos
  de 5 minutos).
- **Devuelto** no es un estado del pedido: se registra en `domicilio` con
  `estado_entrega` y `motivo_devolucion`, y el pedido sigue en `EnCamino`.
- Un pedido de mesa termina en `EnCamino` en el MVP.

### Otros catálogos

| Columna | Valores |
|---|---|
| `usuario.tipo_cargo` | `Chef`, `Mesero`, `Domiciliario`, `Administrador` (vacío: `Cliente`) |
| `pedido.tipo_pedido` | `EN_RESTAURANTE`, `DOMICILIO` |
| `domicilio.estado_entrega` | `Entregado`, `Devuelto` (vacío: en curso) |
| `pago.estado_pago` | `Pendiente de Cobro`, `Cobrado` |

## 5. Relaciones

```
usuario (Cliente)   1 ── 0..* pedido           El cliente hace pedidos a domicilio
usuario (Chef)      1 ── 0..* pedido           El chef gestiona pedidos
mesa                1 ── 0..* pedido           La mesa donde se sirve un pedido de mesa
pedido              1 ── 1..* detalle_pedido   Cada pedido contiene sus líneas
producto            1 ── 0..* detalle_pedido   Cada línea es de un producto
pedido (DOMICILIO)  1 ── 1 domicilio           La entrega de un pedido a domicilio
usuario (Domiciliario) 1 ── 0..* domicilio     El domiciliario lleva varios domicilios
pedido              1 ── 0..1 pago             El pago de un pedido
usuario (Cliente)   1 ── 0..* pago             El cliente efectúa pagos
mesa                1 ── 0..* reserva          Las reservas de una mesa
usuario (Cliente)   1 ── 0..* reserva          El cliente registra reservas
usuario             1 ── 0..* aviso            Los avisos que recibe un usuario
```

## 6. Notas para la API

- **Categorías:** `producto.categoria` es texto, como en el nivel 4. Las
  categorías válidas son las que ya existen en el menú (se cargan en
  `datos_ejemplo.sql`): las historias de administración parten del supuesto de
  que las categorías ya están creadas. Al crear o editar un producto, la capa de
  negocio rechaza una categoría que no exista (RF-12 y RF-13).
- **Productos:** no se eliminan. El MVP solo los crea, los edita y los marca
  como "Agotado" (RF-12, RF-13 y RF-14), así que `disponible` es lo que cambia.
- **Valores no negativos:** que `precio` no sea negativo y que `cantidad` sea al
  menos 1 lo garantiza la validación de la ruta y la capa de negocio, no la base.
- **Dinero:** `psycopg` entrega `NUMERIC` como `Decimal`; el repositorio lo
  convierte al construir las clases de dominio.
- **Una venta** (RF-10) es un pedido en estado `Entregado` cuyo pago está en
  `Cobrado`. Un pedido devuelto (`estado_entrega` = `Devuelto`) no es venta; uno cancelado ya
  no existe.
- **Cancelar un pedido lo elimina:** se borran el pedido, su detalle, su domicilio
  y su pago pendiente, en una sola transacción.
- **Escrituras en varias tablas:** crear un pedido con su detalle, y registrar
  el cobro al cerrar la entrega, se hacen en una sola transacción
  ([3_plan.md](3_plan.md) §5.9).
- **Contraseñas:** `contrasena` guarda el hash, nunca la contraseña. La longitud mínima de
  12 caracteres se valida antes de calcular el hash (RNF-01).

## 7. Montar la base de datos

Por RNF-15 no se depende de contenedores; la base es un PostgreSQL que el
equipo tiene instalado (ver [3_plan.md](3_plan.md) §6):

1. Crear la base `mesa_abuela` (y `mesa_abuela_test` para las pruebas).
2. Cargar `db/crear_tablas.sql` y después `db/datos_ejemplo.sql`.

La conexión usa el servidor local, el puerto **5432** y las variables de entorno
que lee `config.py`.

**Verificación:** un cliente SQL debe ver **9 tablas**, y las tablas `producto`, `mesa`,
`reserva` y `usuario` deben traer los datos de ejemplo.

## 8. Qué componente usa cada grupo de tablas

Tal como lo define el C4 nivel 3 de la base de datos:

| Componente de la base de datos | Módulos del sistema que lo utilizan |
|---|---|
| Usuarios y roles | Autenticación de usuarios |
| Pedidos | Pedidos, Cocina, Domicilios y Ventas y pagos |
| Productos y menú | Menú y productos, Pedidos |
| Reservas y mesas | Reservas |
| Domicilios | Domicilios |
| Pagos | Ventas y pagos |
| `aviso` (fuera del C4) | Notificaciones e Integraciones externas |

Las tablas de **Calificaciones** e **Inventario** no existen en el MVP; los
módulos del mismo nombre son proyectados.
