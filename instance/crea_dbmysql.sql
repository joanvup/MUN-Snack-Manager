-- 1. Crea una nueva base de datos para la aplicación.
-- Usamos utf8mb4 para un soporte completo de caracteres y emojis.
CREATE DATABASE mun_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 2. Crea un nuevo usuario para que tu aplicación lo use.
-- Reemplaza 'tu_contraseña_segura' con una contraseña fuerte y real.
CREATE USER 'mun_user'@'localhost' IDENTIFIED BY 'S0portefcbv@1';

-- 3. Otorga todos los privilegios necesarios al nuevo usuario sobre la nueva base de datos.
GRANT ALL PRIVILEGES ON mun_db.* TO 'mun_user'@'localhost';

-- 4. Refresca los privilegios para que los cambios surtan efecto.
FLUSH PRIVILEGES;