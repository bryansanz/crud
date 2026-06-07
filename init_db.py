import sqlite3
import os

def init_db():
    db_path = 'osti_database.db'
    
    # --- Borrar base vieja para evitar conflictos ---
    if os.path.exists(db_path):
        os.remove(db_path)
        print("Base de datos antigua eliminada. Creando una nueva...")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # 1. Tabla de Usuarios
        cursor.execute('''CREATE TABLE usuarios (
                            id INTEGER PRIMARY KEY AUTOINCREMENT, 
                            username TEXT UNIQUE, 
                            password TEXT, 
                            rol TEXT)''')

        # 2. Tabla de Inventario
        cursor.execute('''CREATE TABLE inventario (
                            serial TEXT PRIMARY KEY, 
                            nombre TEXT, 
                            modelo TEXT, 
                            bien_nacional TEXT, 
                            piso TEXT, 
                            departamento TEXT, 
                            procesador TEXT, 
                            ram TEXT, 
                            disco TEXT,
                            ip TEXT, 
                            mac TEXT)''')

        # 3. Tabla de Casos
        # AJUSTE: Usamos DATETIME('now', 'localtime') para asegurar que las 
        # funciones strftime de los reportes reciban un formato completo.
        cursor.execute('''CREATE TABLE casos (
                            id INTEGER PRIMARY KEY AUTOINCREMENT, 
                            titulo TEXT, 
                            reporte_por TEXT, 
                            usuario_reporta TEXT,
                            serial TEXT, 
                            bien_nacional TEXT,
                            piso TEXT, 
                            departamento TEXT, 
                            tecnico_asignado TEXT,
                            estatus TEXT DEFAULT 'Abierto', 
                            archivo_adjunto TEXT,
                            fecha_creacion TIMESTAMP DEFAULT (DATETIME('now', 'localtime')))''')

        # --- Inserción de usuarios por defecto ---
        usuarios_iniciales = [
            ('admin', '1234', 'Administrador'),
            ('coordinador', '1234', 'Coordinador'),
            ('tecnico1', '1234', 'Técnico')
        ]
        
        cursor.executemany("INSERT INTO usuarios (username, password, rol) VALUES (?, ?, ?)", usuarios_iniciales)

        conn.commit()
        print("Base de datos inicializada correctamente.")
        
    except Exception as e:
        print(f"Error al inicializar la base de datos: {e}")
    finally:
        conn.close()

if __name__ == '__main__':
    init_db()