# Contratos — MVP de "La mesa de la abuela"

> **Este documento ES el contrato publicado** entre la Aplicación web y el API
> Backend. Parte de [2_spec.md](2_spec.md) (qué debe poder hacerse), de
> [3_plan.md](3_plan.md) (módulos y capas) y de [5_data_model.md](5_data_model.md)
> (nombres de los campos).
>
> | Parte | Base | Secciones |
> |---|---|---|
> | **La API** (lo que devuelve) | `http://localhost:8000` | §0 a §10 |
> | **El front** (lo que se ve) | `http://localhost:5500` | §11 y §12 |
>
> Las dos partes están en el mismo documento a propósito: la §11 es la
> **tabla de traducción** entre una y otra, y separarlas haría que se
> desincronizaran.

---

## 0. Convenciones

- Todas las respuestas son JSON (`Content-Type: application/json`).
- **Un módulo por componente del C4**: la ruta empieza por el nombre del
  componente (`/api/pedidos`, `/api/cocina`, `/api/domicilios`...).
- Los nombres de los campos son los del modelo de datos, en `snake_case`
  (`id_pedido`, `estado_pedido`, `numero_mesa`...).
- Las fechas van en formato ISO 8601 (`2026-11-14T15:30:00`) y el dinero como
  número (`47600.00`).
- **Sesión:** todas las rutas, salvo el registro y el inicio de sesión, exigen
  la cabecera `Authorization: Bearer <token>`. El token se obtiene al iniciar
  sesión y expira tras 30 minutos sin actividad (RNF-03).
- **Roles:** `Cliente`, `Chef`, `Mesero`, `Domiciliario` y `Administrador`. El
  rol de un usuario es su `tipo_cargo`; si no tiene, es `Cliente`.

**Las tres vías de envío de datos:**

| Vía | Dónde viaja | Ejemplo | Se usa para |
|---|---|---|---|
| Parámetro de **ruta** | en la URL, parte del camino | `/api/pedidos/15` | Identificar UN recurso |
| **Query string** | en la URL, después de `?` | `/api/cocina/pedidos?tipo_pedido=DOMICILIO` | Filtros de una consulta |
| **Body** JSON | en el cuerpo de la petición | `{"cantidad": 2}` | Los datos del recurso |

**Los verbos:**

| Verbo | Semántica | Uso en el MVP |
|---|---|---|
| GET | Leer (nunca modifica) | Consultar menú, pedidos, avisos, ventas, reservas |
| POST | Crear un recurso o ejecutar una acción | Registrarse, iniciar sesión, hacer un pedido, tomar o marcar listo |
| PUT | Reemplazar los campos editables completos | Editar un producto, modificar una orden de mesa, guardar la dirección |
| PATCH | Actualizar solo lo enviado | Disponibilidad de un producto, entrega, aviso leído |
| DELETE | Eliminar o terminar un recurso | Cancelar un pedido, cerrar sesión |

**Errores:** siempre con esta envoltura, con el mensaje en español:

```json
{ "estado": 409, "mensaje": "La orden ya no se puede modificar: pasaron más de 5 minutos.", "errores": [] }
```

| Origen | HTTP |
|---|---|
| Datos con forma inválida (tipo, campo faltante o vacío, categoría inexistente, clave de menos de 12 caracteres) | **422** con `errores: [ "...", ... ]` |
| Sin sesión, credenciales inválidas o sesión expirada | **401** |
| Rol sin permiso (RN-09, RN-10) | **403** |
| Pedido, producto o usuario inexistente | **404** |
| Regla de negocio violada (RN-01, RN-04, RN-05, RN-07, RN-08) o dato ya registrado | **409** |
| Error inesperado | **500** con un mensaje genérico, **sin detalles internos** |

En un error de credenciales el mensaje nunca dice cuál de los dos datos falló.

## 1. Autenticación de usuarios (RF-01, RF-06)

### `POST /api/autenticacion/registro` — El cliente crea su cuenta

Público. Body: `nombre`, `telefono`, `email`, `contrasena` (mínimo 12 caracteres)
y `acepta_tratamiento_datos` (debe ser `true`, RNF-14). `direccion` es opcional.

```
POST /api/autenticacion/registro
body { "nombre": "Ana Pérez", "telefono": "3001234567", "email": "ana@correo.com",
       "contrasena": "una-clave-larga-123", "acepta_tratamiento_datos": true }
→ 201 { "estado": 201, "mensaje": "Cuenta creada exitosamente.", "id_usuario": 12 }
→ 422 si falta un campo, la clave tiene menos de 12 caracteres o no acepta el tratamiento de datos
→ 409 si el email ya está registrado
```

### `POST /api/autenticacion/empleados` — El administrador crea cuentas del personal

Solo `Administrador` (RN-09). Body: `nombre`, `telefono`, `email`,
`contrasena` (mínimo 12 caracteres) y `tipo_cargo` (`Chef`, `Mesero`,
`Domiciliario` o `Administrador`).

```
→ 201 { "estado": 201, "mensaje": "Cuenta creada exitosamente.", "id_usuario": 13, "id_empleado": 4 }
→ 422 datos inválidos o clave corta · 409 email ya registrado · 403 si no es Administrador
```

### `POST /api/autenticacion/sesion` — Iniciar sesión (`Usuario.iniciarSesion()`)

Público. Body: `email` y `contrasena`.

```
→ 200 { "token": "…", "rol": "Mesero",
        "usuario": { "id_usuario": 13, "nombre": "Luis Gómez", "direccion": null } }
→ 401 { "estado": 401, "mensaje": "Credenciales inválidas.", "errores": [] }
```

### `DELETE /api/autenticacion/sesion` — Cerrar sesión (`Usuario.cerrarSesion()`)

```
→ 200 { "estado": 200, "mensaje": "Sesión cerrada." }
→ 401 si no hay sesión
```

### `PUT /api/autenticacion/direccion` — Guardar la dirección de entrega (RF-06)

Solo `Cliente` (`Cliente.registrarDireccion()` y `modificarDireccion()`).
Body: `direccion` (obligatoria, no vacía).

```
→ 200 { "estado": 200, "mensaje": "Dirección guardada." }
→ 422 si la dirección viene vacía
```

## 2. Menú y productos (RF-02, RF-12, RF-13, RF-14)

### `GET /api/menu/productos` — Consultar el menú (RF-02)

Cualquier usuario con sesión. Query opcional: `categoria`.

```
GET /api/menu/productos?categoria=Postres
→ 200 { "total": 2, "datos": [
        { "id_producto": 7, "nombre": "Plato de ejemplo", "descripcion": "…",
          "precio": 12000.00, "disponible": true, "categoria": "Postres",
          "imagen": "…" }, … ] }
→ 200 con "datos": [] si la categoría no tiene productos (no es un error)
→ 401 sin sesión
```

Un producto con `disponible: false` es un producto "Agotado" (RN-05).

### `POST /api/menu/productos` — Crear un producto (RF-13)

Solo `Administrador` (RN-09). Body: `nombre`, `categoria`, `precio` (≥ 0),
`descripcion` (opcional) e `imagen` (opcional; el texto con la ruta de la
foto, `Producto.imagen`).

```
→ 201 { "estado": 201, "mensaje": "Producto creado exitosamente.", "id_producto": 9 }
→ 422 nombre vacío, precio negativo o categoría que no existe
→ 403 si no es Administrador
```

### `PUT /api/menu/productos/{id_producto}` — Editar un producto (RF-12)

Solo `Administrador`. Body: `nombre`, `categoria`, `precio` y `descripcion`:
**los campos editables completos**; `disponible` no se cambia aquí.

```
→ 200 { "estado": 200, "mensaje": "Producto actualizado exitosamente." }
→ 422 datos inválidos · 404 el producto no existe · 403 si no es Administrador
```

### `PATCH /api/menu/productos/{id_producto}/disponibilidad` — Marcar como Agotado (RF-14)

Solo `Administrador` (`Producto.actualizarDisponibilidad()`). Body: `disponible`
(`true` o `false`).

```
PATCH /api/menu/productos/7/disponibilidad     body { "disponible": false }
→ 200 { "estado": 200, "mensaje": "Producto marcado como agotado." }
→ 422 si falta `disponible` o no es booleano · 404 · 403
```

> El C4 define `Administrador.EliminarProductos()`, pero ningún requisito del
> MVP lo pide (RF-12, RF-13 y RF-14), así que no hay endpoint para eliminar.

## 3. Pedidos (RF-03, RF-04, RF-05, RF-06, RF-07, RF-16)

**El pedido** (lo que devuelven estas rutas):

```json
{ "id_pedido": 15, "tipo_pedido": "DOMICILIO", "estado_pedido": "Recibido",
  "fecha": "2026-11-14T15:30:00", "total": 47600.00, "numero_mesa": null,
  "direccion": "Calle 10 # 20-30",
  "detalle": [ { "id_producto": 7, "nombre": "Plato de ejemplo", "cantidad": 2,
                 "precio_unitario": 20000.00, "observaciones_especiales": null,
                 "subtotal": 40000.00 } ] }
```

`total` y `subtotal` son derivados: los calcula el backend (el total con el IVA
del 19 %) y es el que manda. El carrito vive en el front hasta confirmar.

**Cuerpo para crear o resumir un pedido:**

| Campo | Cuándo | Regla |
|---|---|---|
| `tipo_pedido` | siempre | `DOMICILIO` (lo hace el `Cliente`) o `EN_RESTAURANTE` (lo hace el `Mesero`) |
| `items` | siempre | Lista no vacía de `{ id_producto, cantidad, observaciones_especiales? }`; `cantidad` ≥ 1 |
| `direccion` | `DOMICILIO` | Obligatoria |
| `metodo_pago` | `DOMICILIO` | Obligatorio, y el único valor es `CONTRA_ENTREGA` (RF-07) |
| `numero_mesa` | `EN_RESTAURANTE` | Obligatorio, de una mesa que exista |

### `POST /api/pedidos/resumen` — Ver el resumen y el total (RF-03, RF-04)

Roles `Cliente` y `Mesero`. Mismo cuerpo que crear; **no guarda nada**.

```
→ 200 { "total": 47600.00, "detalle": [ … ] }
→ 422 carrito vacío o cantidad menor que 1
→ 409 si algún producto está "Agotado" (RN-05)
```

### `POST /api/pedidos` — Hacer el pedido (`GestorPedidos.crearPedido(tipo, datos)`)

Un `Cliente` solo crea pedidos `DOMICILIO` y un `Mesero` solo `EN_RESTAURANTE`
(si no, 403). El pedido nace en estado `Recibido`. Un pedido a domicilio nace
con su pago en `Pendiente de Cobro` (RF-07) y su domicilio sin domiciliario.

```
POST /api/pedidos
body { "tipo_pedido": "DOMICILIO", "direccion": "Calle 10 # 20-30",
       "metodo_pago": "CONTRA_ENTREGA",
       "items": [ { "id_producto": 7, "cantidad": 2 } ] }
→ 201 el pedido (estado_pedido: "Recibido")
→ 422 carrito vacío, cantidad menor que 1, falta la dirección, la mesa o el método de pago
→ 409 producto "Agotado" (RN-05) · cliente sin teléfono (RN-07)
→ 403 si el rol no corresponde al tipo de pedido
```

### `GET /api/pedidos` — Mis pedidos (RF-05, RF-16)

Query opcional: `estado_pedido`. Un `Cliente` ve **sus** pedidos; un `Mesero`
ve las órdenes de mesa.

```
→ 200 { "total": 2, "datos": [ el pedido, … ] }      (con "datos": [] si no hay)
→ 401 sin sesión · 403 si el rol no es Cliente ni Mesero
```

### `GET /api/pedidos/{id_pedido}` — El estado de un pedido (RF-05)

```
→ 200 el pedido
→ 404 si no existe · 403 si es de otro cliente
```

### `PUT /api/pedidos/{id_pedido}` — Modificar una orden de mesa (RF-16)

Solo `Mesero`, solo órdenes `EN_RESTAURANTE`. Body: `items` (la lista completa
nueva) y, opcionalmente, `numero_mesa`.

```
→ 200 el pedido actualizado
→ 409 pasados 5 minutos (RN-01) · la orden ya está en cocina (RN-04) · producto agotado (RN-05)
→ 422 datos inválidos · 404 · 403
```

### `DELETE /api/pedidos/{id_pedido}` — Cancelar (RF-05, RF-16; `Pedido.cancelar()`)

Un `Cliente` cancela su pedido y un `Mesero` una orden de mesa. Solo si el
pedido está `Recibido` y no han pasado más de 5 minutos. **Cancelar elimina el
pedido**: después, consultarlo da 404.

```
→ 200 { "estado": 200, "mensaje": "Pedido cancelado." }
→ 409 pasados 5 minutos (RN-01) · el pedido ya está en cocina (RN-04)
→ 404 · 403
```

## 4. Cocina (RF-18, RF-19, RF-20)

Solo `Chef`.

### `GET /api/cocina/pedidos` — La cola de cocina (`Chef.visualizarPedidos()`)

Query opcional: `tipo_pedido` (`EN_RESTAURANTE` para RF-18, `DOMICILIO` para
RF-19). Devuelve los pedidos `Recibido` y `EnCocina`, **ordenados por llegada**.

```
→ 200 { "total": 3, "datos": [ el pedido, … ] }      (con "datos": [] si la cola está vacía)
→ 401 sin sesión · 403 si no es Chef
```

### `POST /api/cocina/pedidos/{id_pedido}/tomar` — Tomar el pedido

Pasa `Recibido → EnCocina` (evento `enviarACocina()`) y guarda al chef en
`id_chef`.

```
→ 200 el pedido (estado_pedido: "EnCocina")
→ 409 si el pedido no está en estado Recibido
→ 404 · 403
```

### `POST /api/cocina/pedidos/{id_pedido}/marcar-listo` — Avisar que está listo (RF-20)

Ejecuta `ComandoMarcarListo`: pasa `EnCocina → EnCamino` (la orden sale de
cocina) y notifica a los observadores. En un pedido de mesa genera el aviso al mesero (con el número de
mesa). En uno a domicilio, el sistema **asigna el domiciliario con menos pedidos
activos** y genera su aviso; si no hay domiciliarios, queda pendiente de asignar
(RF-24).

```
→ 200 el pedido (estado_pedido: "EnCamino")
→ 409 si el pedido no está en estado EnCocina (no se duplica el aviso)
→ 404 · 403
```

## 5. Domicilios (RF-21, RF-23)

Solo `Domiciliario`.

### `GET /api/domicilios` — Mis domicilios (`Domiciliario.visualizarPedidos()`, RF-23)

Devuelve los domicilios asignados a quien consulta, con los datos de contacto.

```
→ 200 { "total": 1, "datos": [
        { "id_domicilio": 3, "id_pedido": 15, "estado_pedido": "EnCamino",
          "estado_entrega": null, "direccion": "Calle 10 # 20-30",
          "cliente": { "nombre": "Ana Pérez", "telefono": "3001234567" },
          "total": 47600.00 } ] }
→ 401 sin sesión · 403 si no es Domiciliario
```

### `PATCH /api/domicilios/{id_domicilio}/estado-entrega` — Cerrar la entrega (RF-21; `Domiciliario.ActualizarEstadoEntrega()`)

Body: `estado_entrega` (`Entregado` o `Devuelto`) y `motivo_devolucion`
(obligatorio si es `Devuelto`).

- **`Entregado`:** el pedido pasa a `Entregado`, **se registra el cobro** (el
  pago queda `Cobrado`, con la fecha) y el pedido cuenta como venta.
- **`Devuelto`:** la entrega queda `Devuelto` con su motivo y el pedido **sigue
  `EnCamino`**; no hay cobro y no cuenta como venta.

```
PATCH /api/domicilios/3/estado-entrega     body { "estado_entrega": "Entregado" }
→ 200 { "estado": 200, "mensaje": "Entrega registrada.", "estado_pedido": "Entregado" }
→ 422 si falta `motivo_devolucion` en un Devuelto, o el valor no es válido
→ 409 si el pedido no está EnCamino o su entrega ya se cerró
→ 404 · 403 (también si el domicilio es de otro domiciliario)
```

## 6. Notificaciones (RF-17, RF-24 — simuladas)

Roles `Mesero` y `Domiciliario`. Los avisos se guardan y el front los pide
cada pocos segundos; **no hay notificación push real**.

### `GET /api/notificaciones` — Mis avisos

Query opcional: `leido` (`true` o `false`).

```
GET /api/notificaciones?leido=false
→ 200 { "total": 1, "datos": [
        { "id_aviso": 31, "mensaje": "El pedido de la mesa 4 está listo.",
          "fecha": "2026-11-14T15:42:00", "leido": false } ] }
→ 401 sin sesión · 403 si no es Mesero ni Domiciliario
```

### `PATCH /api/notificaciones/{id_aviso}` — Marcar como leído

Body: `leido` (`true`).

```
→ 200 { "estado": 200, "mensaje": "Aviso marcado como leído." }
→ 404 si no existe o no es del usuario
```

## 7. Ventas y pagos (RF-10)

### `GET /api/ventas-pagos` — Consultar ventas y pagos

Solo `Administrador` (RN-10; `Administrador.VisualizarPagos()`). Query:
`desde` y `hasta` (fechas `AAAA-MM-DD`, obligatorias). Una **venta** es un
pedido `Entregado` cuyo pago está `Cobrado`.

```
GET /api/ventas-pagos?desde=2026-11-01&hasta=2026-11-14
→ 200 { "desde": "2026-11-01", "hasta": "2026-11-14", "cantidad": 2, "total_ventas": 95200.00,
        "datos": [ { "id_pedido": 15, "fecha": "2026-11-14T15:30:00", "total": 47600.00,
                     "id_pago": 15, "estado_pago": "Cobrado", "monto": 47600.00,
                     "fecha_pago": "2026-11-14" }, … ] }
→ 200 con "datos": [] y "total_ventas": 0 si no hay ventas en el periodo
→ 422 si falta una fecha, no tiene formato válido o `desde` es posterior a `hasta`
→ 403 si no es Administrador
```

## 8. Reservas (RF-11)

### `GET /api/reservas` — Reservas vigentes

Solo `Administrador` (`Administrador.VisualizarReservas()`). Una reserva es
**vigente** si su `fecha_reserva` es hoy o posterior. En el MVP son datos de
ejemplo; crear reservas es un requisito proyectado.

```
→ 200 { "total": 2, "datos": [
        { "id_reserva": 1, "nombre_titular": "Carlos Ruiz", "telefono_titular": "3109876543",
          "fecha_reserva": "2026-11-20", "hora_reserva": "19:30:00", "numero_mesa": 5 } ] }
→ 200 con "datos": [] si no hay reservas vigentes
→ 403 si no es Administrador
```

## 9. Resumen: qué ruta atiende cada requisito

| Ruta | RF | Quién | En el C4 |
|---|---|---|---|
| `POST /api/autenticacion/registro` | RF-01 | Público | `Cliente` |
| `POST /api/autenticacion/empleados` | RF-01 | Administrador | `Empleado` |
| `POST` y `DELETE /api/autenticacion/sesion` | RF-01 | Público · con sesión | `Usuario.iniciarSesion()` · `cerrarSesion()` |
| `PUT /api/autenticacion/direccion` | RF-06 | Cliente | `Cliente.registrarDireccion()` |
| `GET /api/menu/productos` | RF-02 | Con sesión | `Cliente.consultarMenú()` |
| `POST /api/menu/productos` | RF-13 | Administrador | `Administrador.RegistrarProductos()` |
| `PUT /api/menu/productos/{id_producto}` | RF-12 | Administrador | `Administrador.ModificarProductos()` |
| `PATCH …/disponibilidad` | RF-14 | Administrador | `Producto.actualizarDisponibilidad()` |
| `POST /api/pedidos/resumen` | RF-03, RF-04 | Cliente, Mesero | `Pedido.agregarProducto()` · `calcularTotal()` |
| `POST /api/pedidos` | RF-03, 06, 07, 16 | Cliente, Mesero | `GestorPedidos.crearPedido()` |
| `GET /api/pedidos` y `/{id_pedido}` | RF-05, RF-16 | Cliente, Mesero | `Cliente.consultarSeguimientoPedido()` · `Mesero.visualizarPedidos()` |
| `PUT /api/pedidos/{id_pedido}` | RF-16 | Mesero | `Pedido.agregarProducto()` · `eliminarProducto()` |
| `DELETE /api/pedidos/{id_pedido}` | RF-05, RF-16 | Cliente, Mesero | `Pedido.cancelar()` |
| `GET /api/cocina/pedidos` | RF-18, RF-19 | Chef | `Chef.visualizarPedidos()` |
| `POST …/tomar` | RF-18, RF-19 | Chef | evento `enviarACocina()` |
| `POST …/marcar-listo` | RF-20, RF-24 | Chef | `ComandoMarcarListo.ejecutar()` |
| `GET` y `PATCH /api/notificaciones` | RF-17, RF-24 | Mesero, Domiciliario | `IObservadorPedido.actualizar()` |
| `GET /api/domicilios` | RF-23 | Domiciliario | `Domiciliario.visualizarPedidos()` |
| `PATCH …/estado-entrega` | RF-21 | Domiciliario | `Domiciliario.ActualizarEstadoEntrega()` |
| `GET /api/ventas-pagos` | RF-10 | Administrador | `Administrador.VisualizarPagos()` |
| `GET /api/reservas` | RF-11 | Administrador | `Administrador.VisualizarReservas()` |

**Sin ruta en el MVP (proyectados):** RF-08 (reservar una mesa), RF-09
(calificar el servicio), RF-15 (inventario) y RF-22 (comunicación con el
cliente).

## 10. Estabilidad de este contrato

Estas rutas **no cambian** mientras el MVP exista. Si un cambio futuro rompiera
el contrato, es una decisión mayor y debe quedar registrada en la spec.

Hay una consecuencia que se puede comprobar: el cliente de la API es el único
lugar del front que conoce estas rutas. Si la API cambia, se corrige en un solo
archivo y **ninguna vista** se entera.

---

# El front (`http://localhost:5500`)

## 11. Las vistas, y la traducción

Aquí no hay verbos ni códigos de estado: **el usuario no sabe qué es un 409**.
Esta tabla es el contrato de la pantalla y, leída de izquierda a derecha, la
lista de lo que el front traduce. Las vistas son las del C4 nivel 3 (Vistas del
cliente, del mesero, del chef, del domiciliario y del administrador).

| Vista | Qué ve la persona | Qué le pide a la API |
|---|---|---|
| Registro | El formulario para crear su cuenta | `POST /api/autenticacion/registro` |
| Inicio de sesión | El formulario; entra a las pantallas de su rol | `POST /api/autenticacion/sesion` |
| Cerrar sesión | Vuelve al inicio de sesión | `DELETE /api/autenticacion/sesion` |
| **Cliente:** menú | Los productos por categoría; los agotados bloqueados | `GET /api/menu/productos` |
| **Cliente:** carrito | Productos, cantidades y total | `POST /api/pedidos/resumen` |
| **Cliente:** confirmar pedido | Dirección y pago contra entrega; el pedido hecho | `PUT /api/autenticacion/direccion`, `POST /api/pedidos` |
| **Cliente:** mis pedidos | El estado de cada pedido y el botón de cancelar | `GET /api/pedidos`, `DELETE /api/pedidos/{id_pedido}` |
| **Mesero:** nueva orden | La mesa y los platos | `GET /api/menu/productos`, `POST /api/pedidos` |
| **Mesero:** órdenes y avisos | Las órdenes de mesa y el aviso de plato listo | `GET /api/pedidos`, `PUT /api/pedidos/{id_pedido}`, `GET /api/notificaciones` |
| **Chef:** cola de cocina | Las órdenes por llegada; "Tomar" y "Marcar listo" | `GET /api/cocina/pedidos`, `POST …/tomar`, `POST …/marcar-listo` |
| **Domiciliario:** mis domicilios | Pedido, dirección y teléfono del cliente; avisos | `GET /api/domicilios`, `GET /api/notificaciones` |
| **Domiciliario:** entrega | "Entregado" o "Devuelto" con motivo | `PATCH …/estado-entrega` |
| **Administrador:** menú | Crear, editar y marcar agotado | `POST` / `PUT /api/menu/productos`, `PATCH …/disponibilidad` |
| **Administrador:** cuentas | Crear cuentas del personal | `POST /api/autenticacion/empleados` |
| **Administrador:** ventas y reservas | Ventas y pagos por fechas, y las reservas vigentes | `GET /api/ventas-pagos`, `GET /api/reservas` |

**Los avisos:** `notificaciones.js` pide `GET /api/notificaciones?leido=false`
cada pocos segundos y los muestra en la pantalla del rol; al verlos, los marca
como leídos con `PATCH`.

## 12. Cómo se traduce lo que responde la API

Un solo archivo del front (`cliente_api.js`) conoce esta tabla. Ninguna vista
la conoce, y por eso el día que la API cambie el sobre se corrige en un sitio.
Siempre devuelve la misma forma: `ok`, `datos` y `errores`.

| Lo que responde la API | Lo que hace el front | Lo que ve la persona |
|---|---|---|
| `200` / `201` con datos | `ok = true` y se queda con los datos | La pantalla llena, o el aviso verde tras guardar |
| `200` con `datos: []` | `ok = true` con la lista **vacía** | «Todavía no hay …» (no es un error) |
| `422` con `errores: […]` | Se queda con la lista `errores` | Los motivos, uno por línea, junto al formulario |
| `409` con `mensaje` | Se queda con el `mensaje` | El aviso rojo con la regla, en español (por ejemplo, que pasaron más de 5 minutos) |
| `401` | Borra la sesión | Vuelve al inicio de sesión; si había sesión, «Su sesión expiró» |
| `403` | Se queda con el `mensaje` | «No tiene permiso para hacer esto» |
| `404` | Se queda con el `mensaje` | El aviso rojo, en español |
| `500` | Un mensaje genérico | «Ocurrió un error, intente de nuevo» |
| **Nada** (la API no responde) | `ok = false`, **sin código inventado** | «El servicio no está disponible» y la pantalla sigue en pie |

**La última fila es la que se equivoca casi siempre:** no responder no es
responder mal. Un 404 es la API funcionando y diciendo que algo no existe; que
no llegue nada es que no hay con quién hablar. Por eso el cliente de la API
distingue las dos situaciones, y por eso las vistas nunca muestran verbos HTTP,
rutas ni códigos.
