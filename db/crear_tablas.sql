-- =====================================================================
-- db/crear_tablas.sql
-- Crea las 9 tablas del MVP de "La mesa de la abuela" (PostgreSQL).
--
-- PAPEL EN LA ARQUITECTURA: este script es la CAPA 3 (persistencia).
-- La base NO tiene lógica: ni triggers ni procedimientos almacenados.
-- Las reglas de negocio (RN-01 a RN-10) viven en la capa de negocio de
-- la API (Artículo 3 de la constitución). Aquí solo se guardan los datos
-- y se garantiza su integridad (llaves, UNIQUE y catálogos con CHECK).
--
-- Orden: primero las tablas que no dependen de nadie (usuario, producto,
-- mesa) y después las que las referencian con llaves foráneas.
-- Se carga igual en mesa_abuela y en mesa_abuela_test.
-- =====================================================================

-- ---------------------------------------------------------------------
-- 1. USUARIO: toda la jerarquía (Cliente y empleados) en UNA sola tabla.
--    Cliente  -> id_empleado, tipo_cargo y estado quedan vacíos (NULL).
--    Empleado -> las tres columnas vienen llenas; tipo_cargo dice si es
--                Chef, Mesero, Domiciliario o Administrador.
--    contrasena guarda el HASH scrypt con sal, nunca el texto plano.
-- ---------------------------------------------------------------------
CREATE TABLE usuario (
    id_usuario   INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nombre       VARCHAR(100) NOT NULL,
    telefono     VARCHAR(20)  NOT NULL,
    email        VARCHAR(100) NOT NULL UNIQUE,
    contrasena   VARCHAR(255) NOT NULL,
    direccion    VARCHAR(200),                       -- solo clientes
    id_empleado  INTEGER UNIQUE,                     -- solo empleados
    tipo_cargo   VARCHAR(20)
                 CHECK (tipo_cargo IN ('Chef', 'Mesero', 'Domiciliario', 'Administrador')),
    estado       BOOLEAN                             -- solo empleados; falso = no activo
);

-- ---------------------------------------------------------------------
-- 2. PRODUCTO: los platos del menú. disponible = FALSE significa
--    "Agotado" (RN-05). Los productos no se eliminan: se editan o se
--    marcan como agotados.
-- ---------------------------------------------------------------------
CREATE TABLE producto (
    id_producto  INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nombre       VARCHAR(100)  NOT NULL,
    descripcion  VARCHAR(300),
    precio       NUMERIC(12,2) NOT NULL,
    disponible   BOOLEAN       NOT NULL DEFAULT TRUE,
    categoria    VARCHAR(50)   NOT NULL,
    imagen       VARCHAR(200)                        -- ruta de la foto
);

-- ---------------------------------------------------------------------
-- 3. MESA: las mesas del restaurante. numero_mesa es UNIQUE porque
--    la tabla pedido la referencia por ese número.
-- ---------------------------------------------------------------------
CREATE TABLE mesa (
    id_mesa             INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    numero_mesa         INTEGER NOT NULL UNIQUE,
    capacidad_personas  INTEGER NOT NULL,
    disponibilidad      BOOLEAN NOT NULL DEFAULT TRUE
);

-- ---------------------------------------------------------------------
-- 4. PEDIDO: los pedidos de mesa y de domicilio en UNA sola tabla.
--    tipo_pedido distingue el tipo. Los estados son las cuatro clases
--    del nivel 4 del C4 (patrón State). Cancelar NO es un estado:
--    elimina el pedido. Devuelto tampoco: se registra en domicilio.
-- ---------------------------------------------------------------------
CREATE TABLE pedido (
    id_pedido      INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    tipo_pedido    VARCHAR(20) NOT NULL
                   CHECK (tipo_pedido IN ('EN_RESTAURANTE', 'DOMICILIO')),
    estado_pedido  VARCHAR(20) NOT NULL
                   CHECK (estado_pedido IN ('Recibido', 'EnCocina', 'EnCamino', 'Entregado')),
    fecha          TIMESTAMP     NOT NULL,           -- hora exacta: RN-01 mide minutos
    total          NUMERIC(12,2) NOT NULL,           -- incluye el IVA del 19 %
    id_cliente     INTEGER REFERENCES usuario (id_usuario),   -- vacío en pedidos de mesa
    numero_mesa    INTEGER REFERENCES mesa (numero_mesa),     -- vacío en pedidos a domicilio
    id_chef        INTEGER REFERENCES usuario (id_usuario)    -- se llena cuando el chef lo toma
);

-- ---------------------------------------------------------------------
-- 5. DETALLE_PEDIDO: las líneas de cada pedido. La llave primaria es
--    compuesta (pedido + producto). El subtotal es un atributo derivado
--    (cantidad x precio_unitario) y por eso NO tiene columna.
-- ---------------------------------------------------------------------
CREATE TABLE detalle_pedido (
    id_pedido                 INTEGER       NOT NULL REFERENCES pedido (id_pedido),
    id_producto               INTEGER       NOT NULL REFERENCES producto (id_producto),
    cantidad                  INTEGER       NOT NULL,
    precio_unitario           NUMERIC(12,2) NOT NULL,
    observaciones_especiales  VARCHAR(300),
    PRIMARY KEY (id_pedido, id_producto)
);

-- ---------------------------------------------------------------------
-- 6. DOMICILIO: la entrega de un pedido a domicilio (relación 1 a 1).
--    id_domiciliario queda vacío mientras el pedido está pendiente de
--    asignar. estado_entrega queda vacío mientras la entrega está en curso.
-- ---------------------------------------------------------------------
CREATE TABLE domicilio (
    id_domicilio       INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_pedido          INTEGER      NOT NULL UNIQUE REFERENCES pedido (id_pedido),
    id_domiciliario    INTEGER      REFERENCES usuario (id_usuario),
    direccion          VARCHAR(200) NOT NULL,
    estado_entrega     VARCHAR(20)
                       CHECK (estado_entrega IN ('Entregado', 'Devuelto')),
    fecha_entrega      DATE,
    motivo_devolucion  VARCHAR(300)                  -- se exige si es "Devuelto"
);

-- ---------------------------------------------------------------------
-- 7. PAGO: el pago contra entrega. Nace en "Pendiente de Cobro" y pasa
--    a "Cobrado" solo al cerrar la entrega. id_cliente queda vacío en
--    los pagos de pedidos de mesa.
-- ---------------------------------------------------------------------
CREATE TABLE pago (
    id_pago      INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_pedido    INTEGER       NOT NULL UNIQUE REFERENCES pedido (id_pedido),
    id_cliente   INTEGER       REFERENCES usuario (id_usuario),
    estado_pago  VARCHAR(30)   NOT NULL
                 CHECK (estado_pago IN ('Pendiente de Cobro', 'Cobrado')),
    fecha        DATE          NOT NULL,
    monto        NUMERIC(12,2) NOT NULL
);

-- ---------------------------------------------------------------------
-- 8. RESERVA: en el MVP son datos de ejemplo (RF-11); crear reservas
--    desde la aplicación es un requisito proyectado.
--    telefono_titular es texto porque un teléfono no cabe en un entero
--    de 32 bits.
-- ---------------------------------------------------------------------
CREATE TABLE reserva (
    id_reserva        INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_mesa           INTEGER      NOT NULL REFERENCES mesa (id_mesa),
    id_cliente        INTEGER      REFERENCES usuario (id_usuario),  -- vacío en las de ejemplo
    nombre_titular    VARCHAR(100) NOT NULL,
    telefono_titular  VARCHAR(20)  NOT NULL,
    hora_reserva      TIME         NOT NULL,
    fecha_reserva     DATE         NOT NULL
);

-- ---------------------------------------------------------------------
-- 9. AVISO: los avisos simulados de "pedido listo" (fuera del C4; los
--    agrega el plan). El front los pide cada pocos segundos y los
--    muestra en la pantalla del mesero o del domiciliario.
-- ---------------------------------------------------------------------
CREATE TABLE aviso (
    id_aviso    INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_usuario  INTEGER      NOT NULL REFERENCES usuario (id_usuario),
    mensaje     VARCHAR(300) NOT NULL,
    fecha       TIMESTAMP    NOT NULL,
    leido       BOOLEAN      NOT NULL DEFAULT FALSE
);