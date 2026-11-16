# Investigación y decisiones — MVP de "La mesa de la abuela"

> **Lectura opcional**: el porqué de las decisiones del plan, con las
> alternativas que se evaluaron y descartaron. Complementa a
> [3_plan.md](3_plan.md); el orden de trabajo está en [8_tasks.md](8_tasks.md).
>
> Las alternativas salen de lo que el equipo ya documentó: las fichas de
> análisis de patrones, el análisis SOLID y el alcance del MVP del Entregable,
> las clarificaciones del [2_spec.md](2_spec.md) y las decisiones del equipo.

---

## D1 — Tres contenedores y capas dentro de cada componente de la API

**Alternativa descartada:** que la Aplicación web acceda a la base de datos o a
los servicios externos por su cuenta.
**Decisión:** el C4 nivel 2 con tres contenedores (Aplicación web, API Backend
y Base de Datos Relacional). Solo la API Backend se comunica con la base de
datos y con los servicios externos. Dentro de la API hay un módulo por
componente del nivel 3, y cada módulo se organiza en tres capas: ruta →
servicio → repositorio.
**Por qué:** RNF-11 exige separar la lógica de negocio de la interfaz mediante
un patrón de capas. Un módulo por componente C4 hace que los nombres del código
sean los de los diagramas, que es lo que pide el Artículo 1 de la constitución.
**Precio asumido:** el nivel 4 del C4 dibuja solo dominio y patrones, así que
las rutas, los gestores y los repositorios son capa que el código agrega
alrededor. El equipo decidió **no modificar los diagramas**; por eso esa capa
queda descrita en el plan y no en el C4.

## D2 — FastAPI como framework de la API

**Alternativas descartadas:** Flask y Django.
**Decisión:** Python con FastAPI y uvicorn.
**Por qué:** valida las entradas con tipos (RNF-09), genera la documentación de
la API sola (útil para `6_contracts`) y su sistema de dependencias deja ver la
inyección de dependencias de SOLID. Flask es más simple, pero la validación
habría que escribirla a mano. Django impone su propia estructura y su ORM
esconde el SQL, lo que choca con las capas y con los componentes del C4.
**Precio asumido:** FastAPI tiene una curva corta si nadie del equipo lo ha
usado.

## D3 — psycopg con SQL parametrizado, sin ORM

**Alternativa descartada:** SQLAlchemy.
**Decisión:** psycopg 3 con consultas parametrizadas, dentro de la capa de
repositorio.
**Por qué:** el SQL queda visible y escrito por el equipo (Artículo 2 de la
constitución) y deja clarísima la capa de datos. Los valores van siempre como
parámetros, nunca concatenados, que es la defensa contra inyección SQL
(Artículo 6).
**Precio asumido:** SQLAlchemy habría permitido avanzar más rápido y
parametriza solo; con psycopg se escribe cada consulta.

## D4 — Clases abstractas con `ABC` y prefijo `I`

**Alternativa descartada:** `Protocol`.
**Decisión:** las clases abstractas e interfaces del diagrama (`<<abstract>>` e
`<<Interfaz>>`) se escriben con `abc.ABC` y llevan el prefijo `I` en el código:
`IEstadoPedido`, `IServicioPago`, `IPedido`.
**Por qué:** `ABC` es explícito, Python no deja crear un objeto si falta
implementar un método abstracto, y se ve claro en UML como clase abstracta o
interfaz. `Protocol` es más sutil de explicar en una sustentación. El prefijo
`I` es la convención de nombres que el equipo eligió para el código.
**Precio asumido:** el nombre en el código lleva una letra más que en el
diagrama; la correspondencia es mecánica y está escrita en el plan.

## D5 — State para el ciclo de vida del pedido

**Alternativas descartadas:** Strategy y Command.
**Decisión:** `IPedido` guarda un `IEstadoPedido`; cada estado concreto decide
qué acciones permite y a qué estado puede pasar.
**Por qué:** el comportamiento del pedido cambia según su estado: uno
"Recibido" se puede modificar o cancelar y uno "En cocina" ya no (RN-01, RN-04
y RN-06). Sin un patrón habría condicionales if-else anidados. Strategy sirve
para variar algoritmos (por ejemplo calcular una ruta) y no para gestionar
transiciones entre estados; Command encapsula una petición como objeto, y State
el comportamiento propio de un estado. Ayuda a cumplir el principio
abierto/cerrado y el de responsabilidad única.

## D6 — Proxy delante del servicio de pago

**Alternativas descartadas:** Decorator y Adapter.
**Decisión:** `ServicioPagoProxy` se pone delante de `ServicioPagoReal`: valida
el pedido con `esValido()` y registra la transacción antes de delegar el cobro.
`GestorPedidos` declara su dependencia como `IServicioPago`, no como
`ServicioPagoProxy`.
**Por qué:** el sistema trabaja con servicios externos y datos sensibles del
cliente (dirección, teléfono); acceder a ellos directamente genera acoplamiento
y dificulta añadir logs o validaciones. Decorator añade responsabilidades
dinámicamente, y aquí se necesita **control de acceso**; Adapter convierte
interfaces incompatibles, y aquí la interfaz ya es compatible. El análisis
SOLID pidió depender de la abstracción y no del Proxy concreto, para cumplir la
inversión de dependencias.

## D7 — Factory Method para crear pedidos

**Alternativas descartadas:** Abstract Factory y Builder.
**Decisión:** `ICreadorPedidos` con `CreadorPedidoMesa` y
`CreadorPedidoDomicilio`. `GestorPedidos` recibe un mapa `TipoPedido →
creador` inyectado, en lugar de usar `new` o un `if`.
**Por qué:** el pedido de mesa exige número de mesa y el de domicilio exige
dirección, con reglas distintas; centralizar su creación en una sola clase la
volvería compleja y difícil de extender. Abstract Factory crea familias de
objetos relacionados y aquí solo se crea un tipo de objeto (pedido); Builder
construye objetos paso a paso y aquí la creación es más directa. El mapa
inyectado resuelve el hallazgo del análisis SOLID: si el gestor eligiera con
`new` o `if`, la dependencia concreta reaparecería.

## D8 — Observer para avisar que un pedido está listo

**Alternativas descartadas:** Mediator y Command.
**Decisión:** `IPedido` mantiene una lista de `IObservadorPedido`; cuando el chef
marca el pedido como listo (pasa de `EnCocina` a `EnCamino`) llama
`notificarObservadores()`. Los observadores concretos son
`Mesero` y `Domiciliario`, como en el nivel 4.
**Por qué:** cuando el chef marca un pedido listo, varios actores deben
enterarse (mesero y domiciliario). Si el chef los llamara uno por uno habría
acoplamiento y sería difícil sumar observadores. Mediator centraliza la
comunicación, y aquí se quiere que varios actores reaccionen a un evento;
Command encapsula una petición, y Observer notifica un cambio. El pedido
depende de una interfaz y no de clases concretas.

## D9 — Command para las acciones de cocina

**Alternativas descartadas:** Strategy y Observer.
**Decisión:** `IComandoCocina` con `ComandoMarcarListo` y
`ComandoCancelarPedido`. Cada comando guarda el pedido, quién lo ejecutó y la
fecha y hora. El `Chef` solo invoca comandos y consulta la cola.
**Por qué:** las acciones de cocina deben poder auditarse y encolarse; si el
chef llamara directo a métodos del pedido se perdería la trazabilidad y la
pantalla quedaría acoplada a la lógica de negocio. Strategy varía algoritmos;
Observer notifica cambios y Command ejecuta acciones. El análisis SOLID pidió
registrar usuario y hora en cada comando, y que `Chef` no actualice estados
directamente.

## D10 — Patrones que se descartaron por sobreingeniería

**Alternativas descartadas:** Flyweight y Strategy.
**Decisión:** el MVP usa exactamente cinco patrones (State, Proxy, Factory
Method, Observer y Command), sin repetirlos.
**Por qué:** el MVP exige cinco patrones, que no se repitan, que cada uno
responda a una necesidad real y que se evite la sobreingeniería. Flyweight
(compartir platos del menú para ahorrar memoria) no aporta valor al MVP y su
complejidad es alta; Strategy (variar el cálculo de rutas) pertenece a la ruta
optimizada, que está fuera del MVP.

## D11 — Las reglas de negocio viven en la capa de negocio

**Alternativa descartada:** que el `Chef` actualice el estado del pedido
directamente desde su pantalla.
**Decisión:** las reglas RN-01 a RN-10 se aplican en la capa de negocio (el
gestor y las clases de dominio, como los estados). Nunca en la ruta, el
repositorio ni el front.
**Por qué:** el análisis SOLID encontró que, si el chef actualiza el estado por
su cuenta, la regla queda duplicada entre la pantalla de cocina y los comandos.
El pedido delega en su estado las transiciones y cancelaciones, así que los
comandos no repiten RN-01 ni RN-04. Y el front se puede saltar; el backend no.

## D12 — Las transiciones viven dentro de cada estado

**Alternativa considerada:** una tabla "estado → siguiente estado", que
recomendó el análisis SOLID.
**Decisión:** cada estado concreto contiene su propia transición
(`siguiente()`), como lo muestran la máquina de estados y el nivel 4.
**Por qué:** es lo que el diseño documentado define: cada estado es una clase
que encapsula su comportamiento y decide a qué estado puede pasar.
**Precio asumido:** el mismo análisis SOLID lo reconoce como cumplimiento
parcial del principio abierto/cerrado: insertar un estado intermedio
obliga a modificar la transición del estado anterior. Se compensa
probando cada estado con transiciones válidas e inválidas.

## D13 — La hora entra por un `IReloj`

**Alternativa descartada:** que los estados lean la hora del sistema
directamente.
**Decisión:** los estados reciben un `IReloj`. En producción es `RelojSistema`;
en las pruebas, un reloj falso al que se le adelanta la hora.
**Por qué:** RN-01 depende de un plazo de 5 minutos. Con la hora del sistema
dentro del estado, probar la regla obligaría a esperar 5 minutos reales; con el
reloj inyectado se prueba al instante, y cada regla necesita su prueba
(RNF-10).

## D14 — El pedido pasa a "En cocina" cuando el chef lo toma

**Alternativas descartadas:** (a) pasar a cocina al crear el pedido, como
muestra el mensaje 4 del diagrama de secuencia de cocina; (b) pasar solo a
los 5 minutos.
**Decisión:** `Recibido → EnCocina` ocurre cuando el chef toma el pedido de su
cola (evento `enviarACocina()` de la máquina de estados).
**Por qué:** si pasara a cocina al crearse, la ventana de 5 minutos para
modificar o cancelar nunca existiría. La opción (b) fue descartada por el
equipo en la clarificación C2: pasados 5 minutos el pedido no se modifica ni se
cancela, pero no pasa solo a cocina. Con esta decisión, RN-01 tiene sentido y
RN-04 bloquea cambios desde que el pedido está en cocina (clarificación C11).
**Precio asumido:** el diagrama de secuencia de cocina muestra el paso a "En
cocina" justo después de crear el pedido, y el equipo decidió no modificar los
diagramas. Es una diferencia conocida entre el plan y ese diagrama.

## D15 — Servicios externos simulados en el MVP

**Alternativas descartadas:** pasarela de pago en línea, notificaciones push
reales y telefonía enmascarada.
**Decisión:** el pago contra entrega se simula con el Proxy de pago, los avisos
de pedido listo se muestran en la pantalla del rol que los recibe, y la
telefonía enmascarada no se crea.
**Por qué:** el alcance del MVP deja fuera los pagos en línea con pasarela (solo
pago contra entrega) y la comunicación enmascarada para domiciliarios. Los
avisos se simulan en pantalla por decisión del equipo (clarificación C6); las
notificaciones push de Android (RNF-13) quedan proyectadas.
**Precio asumido:** el aviso solo se ve dentro de la aplicación; no llega al
celular.

## D16 — El sistema asigna al domiciliario automáticamente

**Alternativa descartada:** que una persona asigne cada pedido a mano.
**Decisión:** el sistema asigna el pedido al domiciliario con menos pedidos
activos, en el momento en que el chef lo marca como listo. Si no hay
domiciliarios disponibles, el pedido queda pendiente de asignar. Un pedido "En
camino" no se reasigna (RN-08).
**Por qué:** evita una tarea manual más, mantiene el recorrido completo dentro
del sistema y reparte la carga sin reglas complejas (clarificaciones C3 y C9).

## D17 — Reservas con datos de ejemplo

**Alternativa descartada:** que el cliente cree reservas desde el MVP.
**Decisión:** el administrador consulta reservas que se cargan de antemano en
la base de datos (`datos_ejemplo.sql`).
**Por qué:** la reserva de mesas (RF-08) es un requisito proyectado, pero el
administrador igual debe poder consultar reservas vigentes (RF-11). Los datos
de ejemplo cubren esa consulta sin construir la creación (clarificación C4).

## D18 — Ejecución sin contenedores obligatorios

**Alternativa descartada:** Docker Compose como única forma de ejecutar el
proyecto.
**Decisión:** instalación y ejecución con comandos estándar en Linux, macOS y
Windows, explicadas en el `README.md`. Docker, si el equipo lo agrega, es una
alternativa y no parte del MVP.
**Por qué:** RNF-15 exige que backend, frontend y base de datos se empaqueten
por separado y que el proyecto no dependa exclusivamente de contenedores.

## D19 — Un solo Cliente de la API en el front, y el front existente se conserva

**Alternativas descartadas:** que cada vista llame a la API por su cuenta, y
rehacer el front.
**Decisión:** `cliente_api.js` es la única pieza del front que usa `fetch`:
arma la petición, añade el token de sesión y traduce los errores a mensajes en
español. Las vistas HTML/CSS/JavaScript ya hechas se conservan.
**Por qué:** el C4 nivel 3 define el Cliente de la API como el "único punto de
comunicación con el backend". Si el formato de una respuesta cambia, se corrige
en un solo archivo y no en cada vista.

## D20 — Los cuatro estados del nivel 4

**Alternativa descartada:** agregar `Listo`, `Devuelto` y `Cancelado` como estados
del pedido, como aparecen en la máquina de estados del Entregado.
**Decisión:** el pedido tiene solo las cuatro clases de estado del C4 nivel 4:
`EstadoRecibido`, `EstadoEnCocina`, `EstadoEnCamino` y `EstadoEntregado`. Lo que
la máquina de estados llama "Listo" es la transición de `EnCocina` a `EnCamino`,
que dispara el aviso; la devolución se registra en el `Domicilio`
(`estadoEntrega` y `motivoDevolucion`), y cancelar elimina el pedido.
**Por qué:** el equipo decidió no modificar los diagramas y seguir siempre la
notación del C4. El nivel 3 ya asigna al componente Domicilios la gestión de si
una entrega se entrega o se devuelve, y `Pedido.cancelar()` no devuelve ningún
estado (clarificación C12).
**Precio asumido:** no queda historial de pedidos cancelados en la base, y un
pedido devuelto queda en "En camino" con su entrega marcada como "Devuelto".
Además, en un pedido de mesa "En camino" significa que el plato sale hacia la
mesa.
