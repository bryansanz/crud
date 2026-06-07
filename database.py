import sqlite3
import os

def inicializar_base_datos():
    # Nombre del archivo de la base de datos
    db_name = 'database.db'
    
    print("🛡️ [OSTI] Iniciando validación y construcción de la Base de Datos...")
    
    # Establecemos conexión con la base de datos local
    conn = sqlite3.connect(db_name, timeout=20)
    cursor = conn.cursor()
    
    # 1. TABLA DE USUARIOS (Roles y credenciales del sistema)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT UNIQUE NOT NULL,
            clave TEXT NOT NULL,
            role TEXT NOT NULL
        )
    """)
    
    # 2. TABLA DE PISOS / DIVISIONES
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pisos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre_piso TEXT UNIQUE NOT NULL
        )
    """)
    
    # 3. TABLA DE DEPARTAMENTOS (Asociados estrictamente a un piso)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS departamentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre_depto TEXT NOT NULL,
            piso_pertenece TEXT NOT NULL,
            FOREIGN KEY (piso_pertenece) REFERENCES pisos (nombre_piso)
        )
    """)
    
    # 4. TABLA DE INVENTARIO (Control de Hardware e IP)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS inventario (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_name TEXT NOT NULL,
            codigo TEXT UNIQUE NOT NULL,
            cantidad INTEGER NOT NULL,
            piso TEXT,
            departamento TEXT,
            estado TEXT DEFAULT 'En Stock',
            procesador TEXT DEFAULT 'N/A',
            ram TEXT DEFAULT 'N/A',
            ip TEXT DEFAULT 'Dinámica'
        )
    """)
    
    # 5. TABLA DE CASOS (Mesa de Incidentes con soporte para documentos adjuntos)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS casos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo TEXT NOT NULL,
            descripcion TEXT NOT NULL,
            prioridad TEXT NOT NULL,
            estado TEXT DEFAULT 'Abierto',
            solicitante TEXT NOT NULL,
            fecha TEXT NOT NULL,
            adjunto TEXT
        )
    """)
    
    # =====================================================================
    #  INYECCIÓN DE DATOS POR DEFECTO (Para pruebas iniciales)
    # =====================================================================
    
    # Crear usuario Administrador inicial por defecto (si no existe)
    # Nota: En producción puedes cambiar 'admin123' por la clave que uses.
    try:
        cursor.execute("""
            INSERT INTO usuarios (usuario, clave, role) 
            VALUES (?, ?, ?)
        """, ('admin', 'admin123', 'Administrador'))
        print("👤 Usuario 'admin' base creado con éxito. Clave: admin123")
    except sqlite3.IntegrityError:
        # El usuario ya existía, no pasa nada
        pass
# Asegurar existencia de la tabla usuarios
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT UNIQUE NOT NULL,
            clave TEXT NOT NULL,
            role TEXT NOT NULL
        )
    """)
    # Guardar cambios y cerrar conexión
    conn.commit()
    conn.close()
    print("✅ [OSTI] Estructura de tablas verificada e indexada correctamente.")

if __name__ == "__main__":
    inicializar_base_datos()