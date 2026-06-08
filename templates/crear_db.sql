-- Crear tabla de usuarios
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    rol TEXT NOT NULL
);

-- Crear tabla de inventario
CREATE TABLE IF NOT EXISTS inventario (
    serial TEXT PRIMARY KEY,
    nombre TEXT NOT NULL,
    modelo TEXT,
    departamento TEXT,
    status TEXT DEFAULT 'Operativo'
);

-- Crear tabla de casos con fecha_creacion automática
CREATE TABLE IF NOT EXISTS casos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    titulo TEXT NOT NULL,
    reporte_por TEXT,
    piso TEXT,
    departamento TEXT,
    serial TEXT,
    tecnico_asignado TEXT,
    archivo_adjunto TEXT,
    estatus TEXT DEFAULT 'Abierto',
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(serial) REFERENCES inventario(serial)
);

-- Insertar un usuario admin por defecto (opcional)
INSERT OR IGNORE INTO usuarios (username, password, rol) VALUES ('admin', 'admin123', 'Administrador');