# Quickstart — MVP de "La mesa de la abuela"

> Validación rápida del MVP ya construido. Si aún no hay nada, empiece por
> [8_tasks.md](8_tasks.md). Los criterios que se mencionan son los 21 de
> [2_spec.md](2_spec.md) §5, y las rutas, las de [6_contracts.md](6_contracts.md).

---

## 1. Arrancar TODO

Por RNF-15 no se depende de contenedores: se usan comandos estándar. Hace falta
**Python 3.11+** y **PostgreSQL** (puerto 5432). Los comandos son de PowerShell;
en Linux y macOS cambia solo la activación del entorno virtual.

### 1.1 La base de datos

```powershell
# desde la raíz del proyecto
psql -U <usuario> -c "CREATE DATABASE mesa_abuela;"
psql -U <usuario> -d mesa_abuela -f db/crear_tablas.sql
psql -U <usuario> -d mesa_abuela -f db/datos_ejemplo.sql

# para las pruebas automáticas (sección 3):
psql -U <usuario> -c "CREATE DATABASE mesa_abuela_test;"
psql -U <usuario> -d mesa_abuela_test -f db/crear_tablas.sql
psql -U <usuario> -d mesa_abuela_test -f db/datos_ejemplo.sql
```

Verificación: `psql -U <usuario> -d mesa_abuela -c "\dt"` debe listar **9 tablas**,
y `producto`, `mesa`, `reserva` y `usuario` deben traer los datos de ejemplo. Si
no tiene `psql`, cargue los dos scripts desde el cliente SQL que use (por ejemplo
pgAdmin).

### 1.2 La API

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1          # Linux/macOS:  source .venv/bin/activate
pip install -r requirements.txt

# variables de entorno que lee config.py
$env:DB_HOST = "localhost"
$env:DB_PUERTO = "5432"
$env:DB_NOMBRE = "mesa_abuela"
$env:DB_USUARIO = "<usuario>"
$env:DB_CLAVE = "<clave>"
$env:ORIGEN_FRONT = "http://localhost:5500"

uvicorn app.main:app --port 8000
```

### 1.3 La pantalla

En **otra terminal**:

```powershell
cd frontend
python -m http.server 5500
```

Eso deja corriendo tres cosas:

| | Dónde | Qué es |
|---|---|---|
| **La pantalla** | <http://localhost:5500> | Por donde se usa el sistema |
| La API | <http://localhost:8000> | JSON; el front habla con ella |
| Documentación de la API | <http://localhost:8000/docs> | La que genera FastAPI, para comparar con [6_contracts.md](6_contracts.md) |
| PostgreSQL | `localhost:5432` | Para mirar la base por dentro |

Empiece por el 5500, que es como lo va a ver alguien que no programó esto.

## 2. Smoke test de la API (criterios 1 a 21)

Primero se preparan dos ayudantes y un token por cada rol. Los usuarios son los
de prueba que carga `db/datos_ejemplo.sql`.

```powershell
$api = "http://localhost:8000"

# Entrar: devuelve el token de la sesión
function Entrar($email, $clave) {
  (Invoke-RestMethod -Method Post -Uri "$api/api/autenticacion/sesion" -ContentType "application/json" `
     -Body (@{ email = $email; contrasena = $clave } | ConvertTo-Json)).token
}
# Pedir: devuelve el objeto de la respuesta (solo sirve cuando sale bien; para guardar ids)
function Pedir($verbo, $ruta, $cuerpo = $null, $token = $null) {
  $h = @{}; if ($token) { $h.Authorization = "Bearer $token" }
  $p = @{ Method = $verbo; Uri = "$api$ruta"; Headers = $h; ContentType = "application/json" }
  if ($cuerpo) { $p.Body = ($cuerpo | ConvertTo-Json -Depth 5) }
  Invoke-RestMethod @p
}
# Llamar: muestra el código HTTP y el cuerpo, salga bien o mal (para ver los errores)
function Llamar($verbo, $ruta, $cuerpo = $null, $token = $null) {
  $a = @("-s", "-i", "-X", $verbo, "$api$ruta", "-H", "Content-Type: application/json")
  if ($token) { $a += @("-H", "Authorization: Bearer $token") }
  if ($cuerpo) { $cuerpo | ConvertTo-Json -Depth 5 | curl.exe @a --data-binary "@-" } else { curl.exe @a }
}

$ta  = Entrar "<email_administrador>" "<clave>"
$tch = Entrar "<email_chef>" "<clave>"
$tm  = Entrar "<email_mesero>" "<clave>"
$td  = Entrar "<email_domiciliario>" "<clave>"
```

### 2.1 Acceso (criterios 1 a 5)

```powershell
# 4. Registro del cliente
Llamar POST /api/autenticacion/registro @{ nombre="Cliente Prueba"; telefono="3001112233"; email="prueba@correo.com"; contrasena="una-clave-larga-123"; acepta_tratamiento_datos=$true }   # 201
Llamar POST /api/autenticacion/registro @{ nombre="Otro"; telefono="3001112244"; email="otro@correo.com"; contrasena="corta"; acepta_tratamiento_datos=$true }                       # 422: clave de menos de 12 caracteres
Llamar POST /api/autenticacion/registro @{ nombre="Otro"; telefono="3001112244"; email="otro@correo.com"; contrasena="una-clave-larga-123"; acepta_tratamiento_datos=$false }       # 422: no acepta el tratamiento de datos
Llamar POST /api/autenticacion/registro @{ nombre="Cliente Prueba"; telefono="3001112233"; email="prueba@correo.com"; contrasena="una-clave-larga-123"; acepta_tratamiento_datos=$true } # 409: email ya registrado

# 2. Credenciales inválidas, y sin sesión
Llamar POST /api/autenticacion/sesion @{ email="prueba@correo.com"; contrasena="clave-equivocada" }   # 401, sin decir cuál dato falló
Llamar GET /api/menu/productos                                                                          # 401: falta el token

$tc = Entrar "prueba@correo.com" "una-clave-larga-123"

# 1. Acceso por rol
Llamar GET "/api/ventas-pagos?desde=2026-01-01&hasta=2026-12-31" $null $tm   # 403: un Mesero no ve las ventas (RN-10)

# 5. Cuentas del personal
Llamar POST /api/autenticacion/empleados @{ nombre="Mesero Nuevo"; telefono="3001234000"; email="mesero.nuevo@correo.com"; contrasena="una-clave-larga-123"; tipo_cargo="Mesero" } $ta   # 201
Llamar POST /api/autenticacion/empleados @{ nombre="X"; telefono="1"; email="x@correo.com"; contrasena="una-clave-larga-123"; tipo_cargo="Mesero" } $tc                                   # 403: no es Administrador
```

**3. Sesión expirada:** inicie sesión, no haga nada durante 30 minutos y repita
cualquier petición con ese token: debe responder **401**. Si no quiere esperar,
la prueba automática adelanta el reloj: `pytest pruebas -k sesion`.

### 2.2 Menú y carrito (criterios 6 y 7)

```powershell
$menu = Pedir GET /api/menu/productos $null $tc
$menu.datos | Select-Object -First 3                         # los productos, con categoría y disponibilidad
Llamar GET "/api/menu/productos?categoria=<una_categoria>" $null $tc   # solo esa categoría

$prod = $menu.datos[0].id_producto

# 6. Un producto agotado no se puede pedir (RN-05)
Llamar PATCH "/api/menu/productos/$prod/disponibilidad" @{ disponible=$false } $ta   # 200
Llamar POST /api/pedidos/resumen @{ tipo_pedido="DOMICILIO"; direccion="Calle 1 # 2-3"; metodo_pago="CONTRA_ENTREGA"; items=@(@{ id_producto=$prod; cantidad=1 }) } $tc   # 409
Llamar PATCH "/api/menu/productos/$prod/disponibilidad" @{ disponible=$true } $ta    # lo deja disponible otra vez

# 7. Carrito: el total se recalcula (con IVA del 19 %); vacío o cantidad < 1 no se acepta
Llamar POST /api/pedidos/resumen @{ tipo_pedido="DOMICILIO"; direccion="Calle 1 # 2-3"; metodo_pago="CONTRA_ENTREGA"; items=@(@{ id_producto=$prod; cantidad=2 }) } $tc   # 200 con el total
Llamar POST /api/pedidos/resumen @{ tipo_pedido="DOMICILIO"; direccion="Calle 1 # 2-3"; metodo_pago="CONTRA_ENTREGA"; items=@() } $tc                                   # 422: carrito vacío
Llamar POST /api/pedidos/resumen @{ tipo_pedido="DOMICILIO"; direccion="Calle 1 # 2-3"; metodo_pago="CONTRA_ENTREGA"; items=@(@{ id_producto=$prod; cantidad=0 }) } $tc   # 422

# 18. Menú del administrador: datos válidos, y datos inválidos con los motivos
Llamar PUT "/api/menu/productos/$prod" @{ nombre="Nombre editado"; categoria="<una_categoria>"; precio=-5; descripcion="x" } $ta   # 422: precio negativo
```

### 2.3 Pedidos, pago y cocina (criterios 8 a 15)

```powershell
# 9. Pedido a domicilio con pago contra entrega: nace Recibido y con pago pendiente
Llamar POST /api/pedidos @{ tipo_pedido="DOMICILIO"; direccion="Calle 1 # 2-3"; items=@(@{ id_producto=$prod; cantidad=2 }) } $tc   # 422: falta el método de pago
$dom = Pedir POST /api/pedidos @{ tipo_pedido="DOMICILIO"; direccion="Calle 1 # 2-3"; metodo_pago="CONTRA_ENTREGA"; items=@(@{ id_producto=$prod; cantidad=2 }) } $tc
$dom.estado_pedido                                                       # Recibido

# 10. Orden de mesa por el mesero (usa un numero_mesa de los datos de ejemplo)
$mesa = Pedir POST /api/pedidos @{ tipo_pedido="EN_RESTAURANTE"; numero_mesa=<numero_mesa>; items=@(@{ id_producto=$prod; cantidad=1 }) } $tm
Llamar POST /api/pedidos @{ tipo_pedido="EN_RESTAURANTE"; numero_mesa=<numero_mesa>; items=@(@{ id_producto=$prod; cantidad=1 }) } $tc   # 403: un Cliente solo crea pedidos a domicilio

# 11. Dentro de los 5 minutos se puede modificar y cancelar
Llamar PUT "/api/pedidos/$($mesa.id_pedido)" @{ items=@(@{ id_producto=$prod; cantidad=3 }) } $tm       # 200
$otro = Pedir POST /api/pedidos @{ tipo_pedido="DOMICILIO"; direccion="Calle 1 # 2-3"; metodo_pago="CONTRA_ENTREGA"; items=@(@{ id_producto=$prod; cantidad=1 }) } $tc
Llamar DELETE "/api/pedidos/$($otro.id_pedido)" $null $tc                                             # 200: cancelar elimina el pedido
Llamar GET "/api/pedidos/$($otro.id_pedido)" $null $tc                                                # 404: ya no existe

# 13. La cola de cocina: por orden de llegada, y se pueden filtrar los domicilios
Llamar GET /api/cocina/pedidos $null $tch
Llamar GET "/api/cocina/pedidos?tipo_pedido=DOMICILIO" $null $tch

# 12. En cocina ya no se modifica ni se cancela (RN-04)
Llamar POST "/api/cocina/pedidos/$($mesa.id_pedido)/tomar" $null $tch                                 # 200: pasa a EnCocina
Llamar DELETE "/api/pedidos/$($mesa.id_pedido)" $null $tm                                             # 409
Llamar PUT "/api/pedidos/$($mesa.id_pedido)" @{ items=@(@{ id_producto=$prod; cantidad=1 }) } $tm     # 409

# 14. Aviso de plato listo para el mesero
Llamar POST "/api/cocina/pedidos/$($mesa.id_pedido)/marcar-listo" $null $tch                          # 200: pasa a EnCamino
Llamar POST "/api/cocina/pedidos/$($mesa.id_pedido)/marcar-listo" $null $tch                          # 409: no se duplica el aviso
Llamar GET "/api/notificaciones?leido=false" $null $tm                                                # el aviso, con el número de mesa

# 15. Asignación automática del domiciliario
Llamar POST "/api/cocina/pedidos/$($dom.id_pedido)/tomar" $null $tch
Llamar POST "/api/cocina/pedidos/$($dom.id_pedido)/marcar-listo" $null $tch
Llamar GET /api/domicilios $null $td                                                                  # el pedido, con teléfono y dirección del cliente
Llamar GET "/api/notificaciones?leido=false" $null $td                                                # el aviso del domiciliario
```

La ventana de los 5 minutos del **criterio 11** se comprueba también con el
reloj real: cree un pedido, espere **más de 5 minutos** y repita `PUT` o
`DELETE`; debe responder **409** (RN-01).

### 2.4 Entrega, ventas y reservas (criterios 16 a 21)

```powershell
# 17. Entrega y cobro
$dm = (Pedir GET /api/domicilios $null $td).datos[0].id_domicilio
Llamar PATCH "/api/domicilios/$dm/estado-entrega" @{ estado_entrega="Entregado" } $td                # 200: queda cobrado
Llamar PATCH "/api/domicilios/$dm/estado-entrega" @{ estado_entrega="Entregado" } $td                # 409: la entrega ya se cerró

# 19. Ventas: solo los pedidos entregados con cobro registrado
Llamar GET "/api/ventas-pagos?desde=2026-01-01&hasta=2026-12-31" $null $ta                            # el pedido entregado, con su pago Cobrado
Llamar GET "/api/ventas-pagos?desde=2026-12-31&hasta=2026-01-01" $null $ta                            # 422: desde posterior a hasta

# 17 (variante): un pedido devuelto exige motivo, no genera cobro y no aparece en las ventas
#   (haga otro pedido a domicilio, llévelo hasta marcar-listo y cierre con "Devuelto")
Llamar PATCH "/api/domicilios/<id_domicilio>/estado-entrega" @{ estado_entrega="Devuelto" } $td        # 422: falta motivo_devolucion
Llamar PATCH "/api/domicilios/<id_domicilio>/estado-entrega" @{ estado_entrega="Devuelto"; motivo_devolucion="El cliente no estaba" } $td   # 200

# 20. Reservas de ejemplo
Llamar GET /api/reservas $null $ta                                                                    # nombre, fecha, hora y mesa
Llamar GET /api/reservas $null $tc                                                                    # 403
```

**21. Recorrido completo:** lo que acaba de hacer en 2.3 y 2.4 con `$dom` es el
recorrido: el cliente lo hace → el chef lo toma y lo marca listo → el sistema lo
asigna → el domiciliario lo entrega y cobra → aparece en las ventas del
administrador, sin pasos fuera del sistema.

**Tres criterios que la API no puede mostrar a mano:**

- **8** (domicilio sin teléfono): el registro exige teléfono, así que desde la API
  no se puede crear un cliente sin él. Lo comprueba `pytest pruebas -k telefono`.
- **16** (reasignar un pedido "En camino"): la asignación es automática y no hay
  una ruta para reasignar. Lo comprueba `pytest pruebas -k reasignacion`.
- **3** (sesión de 30 minutos): se espera, o se usa `pytest pruebas -k sesion`.

## 3. Pruebas automáticas, las capas y los cinco patrones

```powershell
cd backend
pytest --cov=app                          # usa la base mesa_abuela_test
pytest --cov=app --cov-fail-under=70      # falla si la cobertura baja del 70 % (RNF-10)
```

Los tests de cada patrón llevan el nombre del patrón, para poder correrlos por
separado con `-k`.

### 3.1 Prueba de capas (sin PostgreSQL)

Las pruebas de las reglas de negocio usan el gestor con un **repositorio falso en
memoria** (que implementa `IRepositorioPedidos`) y un **reloj falso**
(`IReloj`). Si funcionan con PostgreSQL apagado, las capas quedaron bien cortadas
(Artículos 2 y 5 de la constitución):

```powershell
# apague PostgreSQL, y entonces:
pytest pruebas -k "reglas or capas"
```

### 3.2 Los cinco patrones

| Patrón | Qué debe pasar | A mano (sección 2) | Prueba automática |
|---|---|---|---|
| **State** | `IPedido` delega en su `IEstadoPedido`: `EstadoRecibido` deja modificar y cancelar solo en los primeros 5 minutos; `EstadoEnCocina` no deja; las transiciones inválidas se rechazan | Criterios 11 y 12: `PUT` y `DELETE` dentro y fuera del plazo, y con el pedido en cocina | `pytest pruebas -k state` (con el reloj falso adelantado 5 minutos) |
| **Factory Method** | `GestorPedidos` elige el creador según `TipoPedido`: la orden de mesa pide `numero_mesa`; el domicilio pide `direccion` y `metodo_pago` | Criterios 9 y 10: el mismo `POST /api/pedidos` produce un pedido distinto según el `tipo_pedido`, y falla distinto | `pytest pruebas -k factory` |
| **Observer** | Al marcar listo, el pedido notifica solo a quien corresponde: `Mesero` en un pedido de mesa, `Domiciliario` en uno a domicilio | Criterios 14 y 15: cada uno ve **su** aviso en `GET /api/notificaciones`, y el otro no | `pytest pruebas -k observer` |
| **Proxy** | El cobro pasa por `ServicioPagoProxy`: valida el pedido con `esValido()` y registra la transacción antes de delegar en `ServicioPagoReal`; `GestorPedidos` solo conoce `IServicioPago` | Criterio 17: el pago está `Pendiente de Cobro` al crear el pedido y pasa a `Cobrado` solo al cerrar la entrega | `pytest pruebas -k proxy` (un pedido inválido no llega al servicio real) |
| **Command** | `ComandoMarcarListo` y `ComandoCancelarPedido` guardan el `pedido`, quién lo ejecutó (`ejecutadoPor`) y cuándo (`fechaHora`); el `Chef` solo invoca comandos | Criterios 12 a 14: marcar listo y cancelar funcionan, y marcar listo dos veces no duplica el aviso | `pytest pruebas -k comando` (el comando conserva el usuario y la hora) |

Si un patrón no se puede demostrar con su fila, ese patrón no está bien
implementado: no basta con que las clases existan.

## 4. La pantalla (criterios 1 a 21, vistos por una persona)

Abra <http://localhost:5500> y haga esto **leyendo lo que dice la pantalla**. Lo
que se juzga aquí no es si funciona (eso ya lo dijo la API) sino si se entiende y
si nadie ve jerga técnica:

1. **Registro e inicio de sesión.** Cree una cuenta de cliente (con una clave
   corta debe decir el motivo, en español) y entre. Cada rol llega solo a sus
   pantallas.
2. **Cliente.** Vea el menú por categoría (los agotados, bloqueados), arme el
   carrito, vea el total, confirme con dirección y pago contra entrega, y mire
   «Mis pedidos». Cancele un pedido recién hecho; pasados 5 minutos el botón
   debe explicar, en español, que ya no se puede.
3. **Mesero.** Registre una orden de mesa, mírela en sus órdenes y espere el aviso
   de plato listo (aparece unos segundos después de que el chef la marque).
4. **Chef.** Vea la cola por llegada, tome un pedido y márquelo listo. Pruebe
   cancelar uno en cocina: debe negarse con un mensaje claro.
5. **Domiciliario.** Vea el aviso, el teléfono y la dirección del cliente, y cierre
   la entrega como «Entregado» o como «Devuelto» (pide el motivo).
6. **Administrador.** Cree una cuenta del personal, edite un producto y márquelo
   agotado, y mire las ventas por fechas y las reservas de ejemplo.
7. **La prueba de los dos procesos.** Con PostgreSQL encendido, apague solo la
   API (`Ctrl+C` en la terminal de `uvicorn`) y refresque cualquier pantalla. La
   pantalla **sigue en pie**, con su menú, y con un aviso de que el servicio no
   está disponible, **y sin un solo dato**. Los datos siguen ahí, en PostgreSQL:
   si aparecieran, sería porque el front llegó a la base por su cuenta. No
   aparecen. Vuelva a arrancar la API y, al refrescar, los datos regresan sin
   tocar nada.

## 5. Si algo falla

| Síntoma | Causa probable |
|---|---|
| `ModuleNotFoundError` al arrancar | El entorno virtual no está activado o falta `pip install -r requirements.txt` |
| 500 en todas las rutas, o error de conexión | PostgreSQL apagado, o las variables de entorno apuntan mal (servidor `localhost`, puerto `5432`, base `mesa_abuela`) |
| La pantalla dice «El servicio no está disponible» | La API está caída, o el cliente de la API apunta a una dirección distinta de `http://localhost:8000` |
| El navegador bloquea las llamadas (error de CORS) | `ORIGEN_FRONT` debe ser exactamente `http://localhost:5500`: la API solo permite el origen del front |
| `localhost:5500` abre una lista de archivos o un 404 | El servidor del front se arrancó en la carpeta equivocada: debe abrirse dentro de `frontend/` |
| 401 en todas las rutas | Falta la cabecera `Authorization`, o la sesión expiró (30 minutos sin actividad): inicie sesión de nuevo |
| 409 al modificar o cancelar un pedido recién creado | Pasaron más de 5 minutos, o el chef ya lo tomó (RN-01 y RN-04) |
| 422 al crear un pedido | Carrito vacío, cantidad menor que 1, o falta la dirección, la mesa o el método de pago |
| Un aviso no aparece | Solo reciben avisos el Mesero y el Domiciliario; el front los pide cada pocos segundos, espere un momento |
| Los datos de ejemplo no están o quedaron sucios | Elimine la base `mesa_abuela`, créela de nuevo y vuelva a cargar los dos scripts de `db/` |
| `pytest` falla al conectarse | Falta crear `mesa_abuela_test` o cargarle los scripts (sección 1.1) |
| La cobertura sale por debajo del 70 % | Faltan pruebas de alguna regla o patrón (sección 3): RNF-10 exige más del 70 % |
| Puerto 8000, 5500 o 5432 ocupado | Hay otro programa usándolo: ciérrelo, o apague el otro proyecto que corra en ese puerto |
