-- =====================================================================
-- db/datos_ejemplo.sql
-- Datos de ejemplo del MVP de "La mesa de la abuela".
-- Se carga DESPUÉS de crear_tablas.sql, en mesa_abuela y mesa_abuela_test.
--
-- Contiene SOLO 4 tablas (lo que pide 8_tasks.md, Fase 0):
--   producto (menú con categorías), mesa, usuario (uno por rol del
--   personal) y reserva (ejemplos de RF-11).
-- Las otras 5 tablas (pedido, detalle_pedido, domicilio, pago, aviso)
-- las llena el propio sistema cuando se usa: precargarlas alteraría el
-- smoke test (asignación al domiciliario con menos pedidos, ventas, etc.).
--
-- Las categorías válidas del menú son las que aparecen en producto.categoria
-- (la capa de negocio rechaza una categoría que no exista). "Todas" no es
-- una categoría: es el filtro de la pantalla para no filtrar.
-- =====================================================================

-- ---------------------------------------------------------------------
-- 1. PRODUCTOS DEL MENÚ
--    ATENCIÓN: los precios son PROVISIONALES; reemplácelos por los reales.
--    descripcion e imagen quedan vacías.
-- ---------------------------------------------------------------------
INSERT INTO producto (nombre, precio, disponible, categoria) VALUES
    ('Arepa paisa rellena',          12000.00, TRUE, 'Entradas'),
    ('Patacón con pollo',            24000.00, TRUE, 'Platos Fuertes'),
    ('Picada de la abuela',          38000.00, TRUE, 'Platos Fuertes'),
    ('Arroz con leche de la abuela',  8000.00, TRUE, 'Postres'),
    ('Copa tres leches',             12000.00, TRUE, 'Postres'),
    ('Limonada de panela',            6000.00, TRUE, 'Bebidas');

-- ---------------------------------------------------------------------
-- 2. MESAS (inventadas para poder probar: números 1 a 6)
-- ---------------------------------------------------------------------
INSERT INTO mesa (numero_mesa, capacidad_personas, disponibilidad) VALUES
    (1, 2, TRUE),
    (2, 2, TRUE),
    (3, 4, TRUE),
    (4, 4, TRUE),
    (5, 6, TRUE),
    (6, 8, TRUE);

-- ---------------------------------------------------------------------
-- 3. USUARIOS DE PRUEBA: uno por rol del personal.
--    - contrasena: 'PENDIENTE_FASE_2' es solo un marcador. En la Fase 2
--      se genera el hash scrypt real con seguridad.py y se reemplaza aquí.
--    - id_empleado: se asigna al crear la cuenta del empleado.
--    - Hay DOS domiciliarios para comprobar la asignación automática
--      al que tenga menos pedidos activos (criterio 15).
--    - No se precarga ningún cliente: el cliente se registra solo por la API.
-- ---------------------------------------------------------------------
INSERT INTO usuario (nombre, telefono, email, contrasena, id_empleado, tipo_cargo, estado) VALUES
    ('Administrador Prueba', '3000000001', 'admin@mesaabuela.com',         'PENDIENTE_FASE_2', 1, 'Administrador', TRUE),
    ('Chef Prueba',          '3000000002', 'chef@mesaabuela.com',          'PENDIENTE_FASE_2', 2, 'Chef',          TRUE),
    ('Mesero Prueba',        '3000000003', 'mesero@mesaabuela.com',        'PENDIENTE_FASE_2', 3, 'Mesero',        TRUE),
    ('Domiciliario Uno',     '3000000004', 'domiciliario1@mesaabuela.com', 'PENDIENTE_FASE_2', 4, 'Domiciliario',  TRUE),
    ('Domiciliario Dos',     '3000000005', 'domiciliario2@mesaabuela.com', 'PENDIENTE_FASE_2', 5, 'Domiciliario',  TRUE);

-- ---------------------------------------------------------------------
-- 4. RESERVAS DE EJEMPLO (RF-11). Una reserva es "vigente" si su fecha
--    es hoy o posterior; por eso las fechas se calculan desde la fecha
--    actual y no se vencen con el tiempo. Se enlazan a la mesa por su
--    numero_mesa. id_cliente queda vacío en las reservas de ejemplo.
-- ---------------------------------------------------------------------
INSERT INTO reserva (id_mesa, nombre_titular, telefono_titular, hora_reserva, fecha_reserva) VALUES
    ((SELECT id_mesa FROM mesa WHERE numero_mesa = 5), 'Carlos Ruiz',   '3109876543', '19:30', CURRENT_DATE + 5),
    ((SELECT id_mesa FROM mesa WHERE numero_mesa = 3), 'Marta Ospina',  '3151234567', '13:00', CURRENT_DATE + 7);