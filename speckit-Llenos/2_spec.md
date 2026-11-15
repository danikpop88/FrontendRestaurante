# Especificación — MVP de "La mesa de la abuela"

> Rige la constitución del proyecto: [1_constitution.md](1_constitution.md).
> Esta especificación dice **QUÉ** debe hacer el sistema y **PARA QUIÉN**.
> No dice con qué tecnología: eso va en `3_plan.md`.
>
> | Documento | Contenido |
> |---|---|
> | **2_spec.md** (este) | QUÉ construir en el MVP y sus criterios de aceptación |
> | [3_plan.md](3_plan.md) | CÓMO: stack, estructura y diseño de las capas |
> | [4_research.md](4_research.md) | Decisiones y alternativas |
> | [5_data_model.md](5_data_model.md) | Entidades, atributos, relaciones y estados |
> | [6_contracts.md](6_contracts.md) | Endpoints y formatos exactos de entrada y salida |
> | [7_quickstart.md](7_quickstart.md) | Cómo levantar y validar el proyecto |
> | [8_tasks.md](8_tasks.md) | Orden de construcción por fases verificables |
> | [9_checklist.md](9_checklist.md) | Revisión de calidad de la especificación |

---

## 1. Propósito del MVP

Hoy el restaurante gestiona sus pedidos en papel y libretas: el pedido a
domicilio se toma por llamada o mensaje y se anota a mano; el pedido en mesa se
escribe en una nota que viaja a cocina y luego a caja. Eso genera desorden,
pérdida de información y falta de coordinación entre quienes participan.

El MVP construye **el recorrido completo de un pedido**, de punta a punta:
se registra (por el cliente en domicilio o por el mesero en mesa), llega a
cocina, se prepara, se entrega y queda visible en las ventas del administrador.

Lo que importa es que el recorrido **funcione completo, con sus reglas de
negocio y sus flujos alternativos**, no que tenga muchas funciones.

## 2. Alcance

Cada requisito funcional tiene uno de tres estados en el MVP:

- **Implementado:** funciona de verdad.
- **Simulado:** el comportamiento existe, pero el servicio externo real se
  reemplaza por una versión de prueba (por ejemplo, el aviso se muestra en
  pantalla en lugar de enviarse como notificación push).
- **Proyectado:** se documenta, pero no se programa en el MVP.

El MVP incluye **pedidos en mesa, pedidos a domicilio y pago contra entrega**.

| RF | Qué permite | Rol | Estado en el MVP |
|---|---|---|---|
| RF-01 | Registrarse e iniciar sesión según el rol (el administrador crea las cuentas del personal) | Todos | Implementado |
| RF-02 | Ver el menú por categorías | Cliente | Implementado |
| RF-03 | Armar el carrito y calcular el total | Cliente | Implementado |
| RF-04 | Ver el resumen del pedido | Cliente | Implementado |
| RF-05 | Ver el estado del pedido y cancelarlo mientras aún se pueda | Cliente | Implementado |
| RF-06 | Registrar la dirección de entrega | Cliente | Implementado |
| RF-07 | Elegir pago contra entrega | Cliente | **Simulado** (sin pasarela de pago) |
| RF-08 | Reservar una mesa | Cliente | Proyectado |
| RF-09 | Calificar el servicio | Cliente | Proyectado |
| RF-10 | Ver ventas y pagos | Administrador | Implementado |
| RF-11 | Ver reservas vigentes | Administrador | Implementado (con datos de ejemplo) |
| RF-12 | Editar productos del menú | Administrador | Implementado |
| RF-13 | Crear productos nuevos | Administrador | Implementado |
| RF-14 | Marcar un producto como Agotado | Administrador | Implementado |
| RF-15 | Consultar inventario de cocina | Administrador | Proyectado |
| RF-16 | Tomar, ver, modificar y cancelar órdenes de mesa | Mesero | Implementado |
| RF-17 | Recibir aviso de plato listo | Mesero | **Simulado** (aviso en pantalla) |
| RF-18 | Ver cola de cocina (pedidos de mesa) | Chef | Implementado |
| RF-19 | Ver cola de cocina (pedidos a domicilio) | Chef | Implementado |
| RF-20 | Avisar que una orden está lista | Chef | Implementado |
| RF-21 | Cerrar la entrega y registrar el cobro | Domiciliario | Implementado |
| RF-22 | Comunicarse con el cliente | Domiciliario | Proyectado |
| RF-23 | Consultar contacto y dirección del cliente | Domiciliario | Implementado |
| RF-24 | Recibir aviso de pedido listo; el sistema le asigna el pedido | Domiciliario | **Simulado** (aviso en pantalla) |

> El MVP cubre los 24 requisitos del Entregable sin agregar ninguno: lo que
> salió de las clarificaciones (sección 8) quedó dentro de RF-01, RF-05, RF-16
> y RF-24.

**No incluye (deliberado):** pagos en línea con pasarela (solo pago contra
entrega), ruta optimizada para domiciliarios, comunicación entre domiciliario
y cliente, calificación del servicio, creación de reservas por el cliente e
inventario de insumos.

## 3. Requisitos funcionales

> Se conservan los identificadores del Entregable 1 (RF-xx, RN-xx) para que
> la trazabilidad no se pierda. Cada requisito dice qué ve y qué logra la
> persona; los **flujos alternativos** dicen qué pasa cuando algo sale mal.

### 3.A — Acceso (transversal)

#### RF-01 — Registrarse e iniciar sesión según el rol
Una persona nueva se registra como cliente y, para hacerlo, da su
consentimiento explícito al tratamiento de sus datos (RNF-14). El
administrador crea las cuentas del personal (meseros, chefs y domiciliarios).
Todo usuario ingresa con sus credenciales y accede únicamente a las funciones
de su rol (Cliente, Mesero, Chef, Domiciliario, Administrador).
- **Alternativo:** registro con datos incompletos, inválidos o ya registrados →
  se rechaza con los motivos.
- **Alternativo:** la persona no acepta el tratamiento de sus datos → no se
  crea la cuenta.
- **Alternativo (RN-09):** solo el rol Administrador puede crear cuentas del
  personal.
- **Alternativo:** clave con menos de 12 caracteres (RNF-01), sea de cliente o
  de personal → se rechaza.
- **Alternativo:** credenciales inválidas → se rechaza el acceso con un mensaje
  claro, sin revelar cuál dato falló.
- **Alternativo:** un usuario intenta usar una función de otro rol → se
  rechaza (RN-09, RN-10).
- **Alternativo:** sesión inactiva por 30 minutos → se cierra y pide ingresar
  de nuevo.

### 3.B — Gestión de pedidos

#### RF-02 — Consultar el menú
El cliente ve los productos con nombre, precio, imagen, descripción y
disponibilidad, y puede filtrar por categoría.
- **Alternativo (RN-05):** un producto "Agotado" se ve bloqueado y no se puede
  agregar al carrito.
- **Alternativo:** una categoría sin productos muestra un mensaje, no un error.

#### RF-03 — Armar el carrito
El cliente agrega productos, cambia cantidades, los elimina, y ve el total
antes de hacer el pedido.
- **Alternativo:** cantidad menor que 1 → se rechaza.
- **Alternativo:** carrito vacío → no se puede hacer el pedido.

#### RF-04 — Ver el resumen del pedido
Antes de confirmar, el cliente ve productos, cantidades y total.

#### RF-05 — Ver el estado del pedido
En cualquier momento, el cliente ve en qué estado va su pedido: Recibido, En
cocina, En camino o Entregado. Desde esa misma pantalla puede **cancelar** su
pedido solo si no está en cocina y no han pasado más de 5 minutos desde que lo
hizo.
- **Alternativo (RN-01):** pasados 5 minutos → se rechaza la cancelación.
- **Alternativo (RN-04):** pedido "En cocina" → se rechaza la cancelación.

#### RF-06 — Registrar la dirección de entrega
El cliente registra la dirección donde recibirá el pedido.
- **Alternativo (RN-07):** no se acepta un pedido a domicilio sin número de
  contacto del cliente.

#### RF-16 — Tomar, ver, modificar y cancelar órdenes de mesa (mesero)
El mesero registra una orden con el número de mesa y los platillos, la
consulta, la modifica y puede cancelarla.
- **Alternativo (RN-01):** pasados 5 minutos desde que se realizó la orden, ya
  no se puede modificar ni cancelar.
- **Alternativo (RN-04):** una orden que ya está "En cocina" no se modifica ni
  se cancela.
- **Alternativo (RN-05):** un producto "Agotado" no se puede seleccionar.

### 3.C — Pagos

#### RF-07 — Elegir pago contra entrega
El cliente elige pagar en efectivo cuando reciba su pedido. El pedido queda
confirmado con el pago pendiente de cobro. En el MVP el cobro se **simula**
sin pasarela de pago: no hay un cobro real en línea.
- **Alternativo:** pedido sin método de pago elegido → no se confirma.

### 3.D — Administración de cocina

#### RF-18 — Ver la cola de cocina de pedidos de mesa
El chef ve las órdenes del restaurante ordenadas por llegada, con mesa,
platos, bebidas y cantidades. Puede tomar una orden para empezar a prepararla:
desde ese momento pasa a "En cocina".

#### RF-19 — Ver la cola de cocina de pedidos a domicilio
El chef ve los pedidos a domicilio ordenados por llegada, con sus detalles y
una indicación clara de que son para enviar. Puede tomar un pedido para
empezar a prepararlo: desde ese momento pasa a "En cocina".

#### RF-20 — Avisar que una orden está lista
El chef marca una orden como lista y el sistema avisa a quien corresponde: al
mesero (con el número de mesa) o al domiciliario. La orden
pasa a "En camino".
- **Alternativo:** marcar como lista una orden que ya estaba lista → no se
  duplica el aviso.

#### RF-17 y RF-24 — Recibir aviso de pedido listo (simulado)
El mesero (RF-17) ve un aviso en su pantalla cuando una orden de mesa está
lista. El domiciliario (RF-24) recibe además el pedido: cuando el chef marca un
pedido a domicilio como listo, **el sistema lo asigna automáticamente** al
domiciliario con menos pedidos activos, y este ve el aviso en su pantalla. En el MVP el aviso es
**simulado**: se muestra en pantalla y no hay notificación push real.
- **Alternativo (RN-08):** un pedido que ya está "En camino" no se reasigna a
  otro domiciliario.
- **Alternativo:** no hay domiciliarios disponibles → el pedido queda pendiente
  de asignar hasta que haya uno.

### 3.E — Domicilios

#### RF-23 — Consultar contacto y dirección del cliente
El domiciliario ve el teléfono y la dirección del cliente de sus pedidos
asignados.

#### RF-21 — Cerrar la entrega y registrar el cobro
El domiciliario marca cada pedido asignado como "Entregado" o "Devuelto". Al
marcarlo "Entregado" registra el cobro del pago contra entrega.
- **Alternativo:** un pedido "Devuelto" no genera cobro ni cuenta como venta.

### 3.F — Administración del menú

#### RF-12, RF-13, RF-14 — Editar, crear y marcar como Agotado
El administrador edita nombre, descripción, categoría y precio de un producto,
crea productos nuevos (nombre, categoría, precio y foto) y marca un producto
como "Agotado".
- **Alternativo (RN-09):** solo el rol Administrador puede hacerlo.
- **Alternativo:** nombre vacío, precio negativo o categoría inexistente → se
  rechaza con los motivos.

### 3.G — Ventas y reservas

#### RF-10 — Ver ventas y pagos
El administrador ve las ventas con su fecha y los pagos. **Un pedido cuenta
como venta cuando fue entregado y su cobro quedó registrado.**
- **Alternativo (RN-10):** solo el rol Administrador puede verlas.
- **Alternativo:** no hay ventas en el periodo → se muestra un mensaje, no un
  error.

#### RF-11 — Ver reservas vigentes
El administrador ve las reservas con nombre de quien reservó, fecha y horario.
En el MVP las reservas son **datos de ejemplo cargados de antemano en la base
de datos**, porque la creación de reservas está proyectada.

## 4. Requisitos no funcionales

Estado de cada RNF en el MVP (los de la matriz de trazabilidad se conservan;
el resto se definió en las clarificaciones):

| RNF | Qué exige | Estado en el MVP |
|---|---|---|
| RNF-10 | Cobertura de pruebas mayor al 70 % | Implementado |
| RNF-11 | Separar lógica de negocio e interfaz con capas | Implementado |
| RNF-12 | Funcionar en las dos últimas versiones de Chrome y Firefox | Implementado |
| RNF-15 | Ejecución modular y portable, sin depender solo de contenedores | Implementado |
| RNF-02 | HTTPS con TLS 1.3 | Proyectado (en local no se usa TLS) |
| RNF-06 | Disponibilidad del 98,5 % | Proyectado (no medible en el MVP) |
| RNF-07 | Respaldos automáticos diarios | Proyectado |
| RNF-01 | Clave de mínimo 12 caracteres | Implementado (se aplica también a los clientes) |
| RNF-03 | La sesión expira a los 30 minutos de inactividad | Implementado |
| RNF-04 | Menú en menos de 800 ms con 50 usuarios simultáneos | Implementado (se verifica con una prueba básica de carga) |
| RNF-05 | Reporte de ventas en menos de 3 s | Implementado (se verifica con una consulta de prueba) |
| RNF-08 | Accesibilidad WCAG 2.1 nivel A | Implementado en el front existente |
| RNF-09 | Retroalimentación visual en formularios | Implementado |
| RNF-14 | Consentimiento explícito al registrarse | Implementado |
| RNF-13 | Notificaciones push en Android 10+ | Proyectado (el aviso es simulado en pantalla) |

## 5. Criterios de aceptación

> Cada criterio es una prueba verificable: **Dado** una situación inicial,
> **cuando** ocurre algo, **entonces** pasa tal cosa. Si un criterio no se
> puede comprobar, está mal escrito.

1. **Acceso por rol.** Dado un usuario con rol Mesero, cuando intenta ver los
   reportes de ventas, entonces el sistema se lo impide (RN-10).
2. **Credenciales inválidas.** Dado un usuario registrado, cuando ingresa una
   clave incorrecta, entonces no accede y ve un mensaje claro.
3. **Sesión expirada.** Dado un usuario con sesión iniciada, cuando pasan 30
   minutos sin actividad, entonces debe iniciar sesión de nuevo.
4. **Registro del cliente.** Dada una persona nueva, cuando se registra con
   datos válidos, una clave de 12 caracteres o más y acepta el tratamiento de
   sus datos, entonces puede iniciar sesión; con datos inválidos, ya
   registrados o una clave más corta, se rechaza con los motivos.
5. **Cuentas del personal.** Dado un administrador, cuando crea la cuenta de un
   mesero con una clave de 12 caracteres o más, entonces ese mesero puede
   iniciar sesión; con una clave más corta, o si quien intenta crearla no es
   administrador, se rechaza.
6. **Menú.** Dado un menú con un producto "Agotado", cuando el cliente lo
   consulta, entonces ve el producto bloqueado y no puede agregarlo al carrito
   (RN-05).
7. **Carrito.** Dado un carrito con productos, cuando el cliente cambia una
   cantidad, entonces el total se recalcula; y con el carrito vacío no puede
   hacer el pedido.
8. **Pedido a domicilio sin contacto.** Dado un pedido a domicilio sin teléfono
   del cliente, cuando intenta confirmarlo, entonces se rechaza (RN-07).
9. **Pago contra entrega.** Dado un pedido con dirección, cuando el cliente
   elige pago contra entrega, entonces el pedido queda confirmado con pago
   pendiente.
10. **Orden de mesa.** Dado un mesero con sesión, cuando registra una orden con
    mesa y platillos, entonces aparece en la cola de cocina.
11. **Modificar o cancelar dentro del plazo.** Dado un pedido recién creado y
    que no está en cocina, cuando se modifica o se cancela antes de 5 minutos,
    entonces la acción se realiza (cancelar elimina el pedido); pasados 5
    minutos, se rechaza (RN-01).
12. **Cancelar en cocina.** Dada una orden "En cocina", cuando alguien intenta
    cancelarla, entonces se rechaza (RN-04).
13. **Cola de cocina.** Dadas varias órdenes, cuando el chef abre la cola,
    entonces las ve por orden de llegada y distingue las de domicilio; cuando toma
    una, esta pasa a "En cocina".
14. **Aviso de plato listo.** Dada una orden de mesa en preparación, cuando el
    chef la marca lista, entonces el mesero ve el aviso en su pantalla con el
    número de mesa.
15. **Asignación automática.** Dado un pedido a domicilio en cocina, cuando el
    chef lo marca como listo, entonces el sistema lo asigna al domiciliario con
    menos pedidos activos, que ve el aviso, el teléfono y la dirección del cliente.
16. **Reasignación.** Dado un pedido "En camino", cuando se intenta asignar a
    otro domiciliario, entonces se rechaza (RN-08).
17. **Entrega y cobro.** Dado un pedido asignado, cuando el domiciliario lo
    marca "Entregado", entonces queda registrado el cobro y el cliente ve el
    nuevo estado; si lo marca "Devuelto", no hay cobro.
18. **Menú del administrador.** Dado un administrador, cuando edita un producto
    con datos válidos, entonces el menú se actualiza; con datos inválidos, se
    rechaza con los motivos (RN-09).
19. **Ventas.** Dado un administrador, cuando abre las ventas, entonces ve solo
    los pedidos entregados con cobro registrado; los devueltos no aparecen.
20. **Reservas de ejemplo.** Dado un administrador, cuando abre el listado de
    reservas, entonces ve las reservas de ejemplo con nombre, fecha y horario.
21. **Recorrido completo.** Un pedido a domicilio recorre: cliente lo hace →
    chef lo ve → chef lo marca listo → el sistema lo asigna → domiciliario lo
    entrega y registra el cobro → aparece en las ventas del administrador, sin
    pasos manuales fuera del sistema.

## 6. Glosario mínimo

| Término | Significado |
|---|---|
| **Pedido** | Solicitud de productos, de mesa o a domicilio, con su estado y total |
| **Comanda / orden de mesa** | Pedido que el mesero toma en una mesa |
| **Pedido a domicilio** | Pedido que el cliente hace desde la aplicación para recibir en su dirección |
| **Estado del pedido** | Etapa en la que va: Recibido, En cocina, En camino o Entregado. Cancelar elimina el pedido; una entrega devuelta se registra en el domicilio |
| **Simulado** | Funciona, pero con un reemplazo de prueba del servicio externo real |
| **Proyectado** | Documentado y diseñado, pero no programado en el MVP |
| **Venta** | Pedido entregado cuyo cobro quedó registrado |
| **Criterio de aceptación** | Prueba verificable que decide si algo está terminado |

## 7. Definición de TERMINADO

Los 21 criterios pasan, incluidos los flujos alternativos → demostración
funcional estable → cada integrante con sus commits → recién entonces se
pasa a `3_plan.md`.

## 8. Clarificaciones

> Registro de ambigüedades detectadas **antes** de planear, con la respuesta
> acordada y su razón. Mientras quede un **[NECESITA ACLARACIÓN]**, no se pasa
> a `3_plan.md`. **Todas las dudas están cerradas: se puede pasar a la
> planeación.**

| # | La pregunta | La respuesta acordada, con su razón | Dónde quedó |
|---|---|---|---|
| C1 | El alcance del MVP (F1–F8) no menciona domicilios ni pagos, pero la matriz y los diagramas sí. ¿Cuál manda? | **El MVP incluye domicilios y pago contra entrega.** Sin ellos el pedido no cierra su recorrido y las épicas de los diagramas quedarían sin respaldo. | §2 Alcance · Constitución Art. 10 |
| C2 | RN-01: a los 5 minutos, ¿el pedido pasa solo a cocina o solo deja de poder cambiarse? | **No pasa solo a cocina: pasados 5 minutos la orden no se puede modificar ni cancelar.** | RF-05 · RF-16 · criterio 11 |
| C3 | ¿Quién asigna el pedido a un domiciliario? | **El propio sistema, automáticamente.** Evita una tarea manual más y mantiene el recorrido completo dentro del sistema. | RF-24 · criterio 15 |
| C4 | Las reservas no se pueden crear en el MVP, pero el administrador las ve. ¿De dónde salen? | **Son datos de ejemplo cargados de antemano en la base de datos.** La creación de reservas está proyectada. | RF-11 · criterio 20 |
| C5 | ¿Quién crea las cuentas? | **El cliente se registra solo; el administrador crea las cuentas del personal.** | RF-01 · criterios 4 y 5 |
| C6 | ¿Cómo se simula un aviso (RF-17, RF-24)? | **Se muestra en la pantalla del rol que lo recibe.** No hay notificación push real. | RF-17 · RF-24 · criterios 14 y 15 |
| C7 | ¿Cuándo cuenta un pedido como venta? | **Cuando fue entregado y se registró el cobro.** Un pedido devuelto o cancelado no es venta. | RF-10 · RF-21 · criterio 19 |
| C8 | ¿Qué pedidos se pueden cancelar? | **Los que no están en cocina y no han pasado más de 5 minutos desde que se realizaron.** | RF-05 · RF-16 · criterios 11 y 12 |
| C9 | ¿Con qué criterio el sistema elige al domiciliario, y en qué momento lo asigna? | **Al domiciliario con menos pedidos activos, en el momento en que el chef marca el pedido como listo.** Reparte la carga sin reglas complejas y evita elegir a mano. Si no hay domiciliarios disponibles, el pedido queda pendiente de asignar. | RF-24 · criterio 15 |
| C10 | ¿Qué regla de clave tiene el cliente? RNF-01 solo cubría al personal. | **La misma: 12 caracteres como mínimo, para clientes y personal.** Una sola regla es más simple de explicar y validar, y los datos del cliente también se protegen. | RF-01 · criterio 4 |
| C11 | ¿Cuándo pasa un pedido de "Recibido" a "En cocina"? La máquina de estados lo deja en `enviarACocina()` sin decir quién lo dispara. | **Cuando el chef toma el pedido de su cola.** No pasa solo a los 5 minutos. Así la ventana de 5 minutos para modificar o cancelar tiene sentido, y RN-04 bloquea cambios desde que el pedido está en cocina. | RF-18 · RF-19 · criterio 13 |
| C12 | Con los cuatro estados del nivel 4 (Recibido, En cocina, En camino, Entregado), ¿cómo se representan "listo", "cancelado" y "devuelto"? | **Marcar listo avanza el pedido de En cocina a En camino y notifica; cancelar elimina el pedido; la devolución se registra en el domicilio (`estadoEntrega` y `motivoDevolucion`) y el pedido sigue En camino.** El equipo decidió no agregar estados al nivel 4. | RF-05 · RF-16 · RF-20 · RF-21 · criterios 11, 14, 17 y 19 |

**Cómo se escribe una entrada nueva:** la pregunta tal como se hizo, la
respuesta acordada **con su razón**, y el documento donde quedó plasmada. Si la
respuesta cambia un requisito, se corrige el requisito arriba: esta sección lo
registra, no lo reemplaza.
