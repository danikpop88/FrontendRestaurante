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
--    - contrasena: hash scrypt (con sal) de la clave de prueba
--      'una-clave-larga-123'. Es solo para desarrollo y demostración:
--      nunca usar una clave real en este script.
--    - id_empleado: se asigna al crear la cuenta del empleado.
--    - Hay DOS domiciliarios para comprobar la asignación automática
--      al que tenga menos pedidos activos (criterio 15).
--    - No se precarga ningún cliente: el cliente se registra solo por la API.
-- ---------------------------------------------------------------------
INSERT INTO usuario (nombre, telefono, email, contrasena, id_empleado, tipo_cargo, estado) VALUES
    ('Administrador Prueba', '3000000001', 'admin@mesaabuela.com',         '022b05ee1f0085629c4aea3e3df399b3$2c4350df667bcbb79d921395f73261ed1acd60a416bd2933962aedb913dd424ea8a56bf52f54094bd57534d6f911b36a07db0b0d9ea9712a244627ed210de285', 1, 'Administrador', TRUE),
    ('Chef Prueba',          '3000000002', 'chef@mesaabuela.com',          '8361c5d190ba070886ca2ac243f0242d$7ed6cd65c5ab1714f058d5799e7f8ade79e2393e4e00e62216d037e6aa72c565c782999d15da1501960dea7068a5444e2757662f9673ce97030be968ae5bda89', 2, 'Chef',          TRUE),
    ('Mesero Prueba',        '3000000003', 'mesero@mesaabuela.com',        'b774cc7e9740c8a634bb70391a81add5$b09032b1bcc5e34c2c88f3308d0e00ceda4f12d721c355a24cd347a2d6d8e144cca460607bb8af6212a24bab40163bc61e4247fed0d0e82ebca6cdfdd7bbacac', 3, 'Mesero',        TRUE),
    ('Domiciliario Uno',     '3000000004', 'domiciliario1@mesaabuela.com', '663fb659465f4ef2ed7129d8b7f61fd6$db73b78764d9a29c6abf5a926162e534358d565e532d99394859ba9f3bbac841a758174c18a9f852df70fbab79dbbbb8e972cc67d77884dcb7e9956ad652edcd', 4, 'Domiciliario',  TRUE),
    ('Domiciliario Dos',     '3000000005', 'domiciliario2@mesaabuela.com', '47475703db88828817a84170c38a4520$4e3d25390392dce3dbcd3274a100e624234284ae72f7c56a015e6c383647c18576eef43d630b0625c9032989c34d9c22fe85a4420d9cade1db665b6f5ae4abcf', 5, 'Domiciliario',  TRUE);
-- ---------------------------------------------------------------------
-- 4. RESERVAS DE EJEMPLO (RF-11). Una reserva es "vigente" si su fecha
--    es hoy o posterior; por eso las fechas se calculan desde la fecha
--    actual y no se vencen con el tiempo. Se enlazan a la mesa por su
--    numero_mesa. id_cliente queda vacío en las reservas de ejemplo.
-- ---------------------------------------------------------------------
INSERT INTO reserva (id_mesa, nombre_titular, telefono_titular, hora_reserva, fecha_reserva) VALUES
    ((SELECT id_mesa FROM mesa WHERE numero_mesa = 5), 'Carlos Ruiz',   '3109876543', '19:30', CURRENT_DATE + 5),
    ((SELECT id_mesa FROM mesa WHERE numero_mesa = 3), 'Marta Ospina',  '3151234567', '13:00', CURRENT_DATE + 7);