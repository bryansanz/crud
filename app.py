import os, sqlite3, pandas as pd
from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file, jsonify
from werkzeug.utils import secure_filename
from functools import wraps
import io

app = Flask(__name__)
app.secret_key = 'clave_secreta_osti_pro'
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def get_db():
    conn = sqlite3.connect('osti_database.db')
    conn.row_factory = sqlite3.Row
    return conn

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('rol') != 'Administrador':
            flash("Acceso denegado: Solo administradores", "danger")
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

# --- Rutas de Autenticación y Dashboard ---
@app.route('/')
def index(): return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        db = get_db()
        user = db.execute("SELECT * FROM usuarios WHERE username=? AND password=?", 
                          (request.form['username'], request.form['password'])).fetchone()
        db.close()
        if user:
            session.update({'user': user['username'], 'rol': user['rol']})
            return redirect(url_for('dashboard'))
        flash("Credenciales incorrectas", "danger")
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user' not in session: return redirect(url_for('login'))
    db = get_db()
    user_filter = "" if session['rol'] in ['Administrador', 'Coordinador'] else f"WHERE tecnico_asignado LIKE '%{session['user']}%'"
    abiertos = db.execute(f"SELECT count(*) FROM casos {user_filter} {'AND' if user_filter else 'WHERE'} estatus='Abierto'").fetchone()[0] or 0
    cerrados = db.execute(f"SELECT count(*) FROM casos {user_filter} {'AND' if user_filter else 'WHERE'} estatus='Cerrado'").fetchone()[0] or 0
    en_revision = db.execute(f"SELECT count(*) FROM casos {user_filter} {'AND' if user_filter else 'WHERE'} estatus='En Revisión'").fetchone()[0] or 0
    total_equipos = db.execute("SELECT count(*) FROM inventario").fetchone()[0] or 0
# Nueva consulta para inventario por piso
    inventario_piso = db.execute("SELECT piso, COUNT(*) as total FROM inventario GROUP BY piso").fetchall()
    data_piso = {row['piso']: row['total'] for row in inventario_piso}


    db.close()
    return render_template('dashboard.html', 
                           abiertos=abiertos, cerrados=cerrados, 
                           en_revision=en_revision, total_equipos=total_equipos,
                           data_piso=data_piso)

# --- Inventario con Filtros ---
@app.route('/inventario', methods=['GET', 'POST'])
def inventario():
    if 'user' not in session: return redirect(url_for('login'))
    db = get_db()
    if request.method == 'POST':
        db.execute("INSERT INTO inventario (serial, nombre, modelo, bien_nacional, piso, departamento, ram, disco, ip, mac) VALUES (?,?,?,?,?,?,?,?,?,?)",
                   (request.form.get('serial'), request.form.get('nombre'), request.form.get('modelo', ''), 
                    request.form.get('bien_nacional', ''), request.form.get('piso', ''), request.form.get('departamento', ''), 
                    request.form.get('ram', ''), request.form.get('disco', ''), request.form.get('ip', ''), request.form.get('mac', '')))
        db.commit()
        return redirect(url_for('inventario'))
    
    piso = request.args.get('piso')
    depto = request.args.get('departamento')
    query = "SELECT * FROM inventario WHERE 1=1"
    params = []
    if piso: query += " AND piso = ?"; params.append(piso)
    if depto: query += " AND departamento = ?"; params.append(depto)

    data = [dict(row) for row in db.execute(query, params).fetchall()]
    db.close()
    return render_template('inventario.html', inventario=data)

@app.route('/exportar_inventario')
@admin_required
def exportar_inventario():
    piso, depto = request.args.get('piso'), request.args.get('departamento')
    query = "SELECT * FROM inventario WHERE 1=1"
    params = []
    if piso: query += " AND piso = ?"; params.append(piso)
    if depto: query += " AND departamento = ?"; params.append(depto)
    db = get_db()
    df = pd.read_sql_query(query, db, params=params)
    db.close()
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name='Inventario', index=False)
    output.seek(0)
    return send_file(output, download_name="Inventario_OSTI.xlsx", as_attachment=True)

# --- Casos ---
@app.route('/detalle_caso/<int:id>')
def detalle_caso(id):
    if 'user' not in session: return jsonify({"error": "No autorizado"}), 403
    db = get_db()
    caso = db.execute("SELECT * FROM casos WHERE id=?", (id,)).fetchone()
    db.close()
    return jsonify(dict(caso)) if caso else jsonify({"error": "No encontrado"}), 404

@app.route('/casos', methods=['GET', 'POST'])
def casos():
    if 'user' not in session: return redirect(url_for('login'))
    db = get_db()
    if request.method == 'POST':
        if 'reasignar_id' in request.form and session['rol'] in ['Administrador', 'Coordinador']:
            db.execute("UPDATE casos SET tecnico_asignado=? WHERE id=?", (request.form['nuevo_tecnico'], request.form['reasignar_id']))
            db.commit()
        elif 'caso_id' in request.form:
            f = request.files.get('archivo_adjunto')
            estatus = request.form['estatus']
            filename = secure_filename(f.filename) if f and f.filename else None
            if filename: f.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            if filename:
                db.execute("UPDATE casos SET estatus=?, archivo_adjunto=? WHERE id=?", (estatus, filename, request.form['caso_id']))
            else:
                db.execute("UPDATE casos SET estatus=? WHERE id=?", (estatus, request.form['caso_id']))
            db.commit()
        elif session['rol'] == 'Administrador' and 'titulo' in request.form:
            tecnicos_str = ", ".join(request.form.getlist('tecnicos'))
            db.execute("INSERT INTO casos (titulo, reporte_por, usuario_reporta, serial, piso, departamento, tecnico_asignado, estatus) VALUES (?,?,?,?,?,?,?,?)",
                       (request.form['titulo'], request.form['reporte_por'], request.form['usuario_reporta'], request.form['serial'], request.form['piso'], request.form['departamento'], tecnicos_str, 'Abierto'))
            db.commit()
    
    if session['rol'] in ['Administrador', 'Coordinador']:
        lista_casos = [dict(row) for row in db.execute("SELECT * FROM casos").fetchall()]
    else:
        lista_casos = [dict(row) for row in db.execute("SELECT * FROM casos WHERE tecnico_asignado LIKE ?", ('%' + session['user'] + '%',)).fetchall()]
    
    lista_inventario = [dict(row) for row in db.execute("SELECT * FROM inventario").fetchall()]
    tecnicos = [dict(row) for row in db.execute("SELECT username FROM usuarios WHERE rol='Técnico'").fetchall()]
    db.close()
    return render_template('casos.html', casos=lista_casos, tecnicos=tecnicos, inventario=lista_inventario)

# --- Gestión y Reportes ---
@app.route('/gestion_usuarios', methods=['GET', 'POST'])
@admin_required
def gestion_usuarios():
    db = get_db()
    if request.method == 'POST':
        accion = request.form.get('accion')
        if accion == 'nuevo_usuario':
            try:
                db.execute("INSERT INTO usuarios (username, password, rol) VALUES (?,?,?)", 
                           (request.form['usuario'], request.form['clave'], request.form['rol']))
                db.commit()
            except sqlite3.IntegrityError: flash("Error: El usuario ya existe.", "danger")
        elif accion == 'cambiar_rol':
            db.execute("UPDATE usuarios SET rol=? WHERE id=?", (request.form['nuevo_rol'], request.form['id_usuario']))
            db.commit()
        elif accion == 'eliminar_usuario':
            db.execute("DELETE FROM usuarios WHERE id=?", (request.form['id_usuario'],))
            db.commit()
    usuarios = [dict(row) for row in db.execute("SELECT * FROM usuarios").fetchall()]
    db.close()
    return render_template('usuarios.html', usuarios=usuarios)

@app.route('/reportes', methods=['GET'])
@admin_required
def reportes():
    db = get_db()
    mes_filtro, anio_filtro = request.args.get('mes'), request.args.get('anio')
    where_clause, params = "", []
    if mes_filtro and anio_filtro:
        where_clause = "WHERE strftime('%m', fecha_creacion) = ? AND strftime('%Y', fecha_creacion) = ?"
        params = [mes_filtro.zfill(2), anio_filtro]
    elif anio_filtro:
        where_clause = "WHERE strftime('%Y', fecha_creacion) = ?"
        params = [anio_filtro]

    reporte_tiempo = db.execute(f'''SELECT strftime('%Y', fecha_creacion) as anio, strftime('%m', fecha_creacion) as mes, 
        COUNT(*) as total, SUM(CASE WHEN estatus='Cerrado' THEN 1 ELSE 0 END) as cerrados 
        FROM casos {where_clause} GROUP BY anio, mes ORDER BY anio DESC, mes DESC''', params).fetchall()
    
    reporte_soporte = db.execute(f'''SELECT tecnico_asignado, COUNT(*) as total, 
        SUM(CASE WHEN estatus='Cerrado' THEN 1 ELSE 0 END) as cerrados 
        FROM casos {where_clause} {'AND' if where_clause else 'WHERE'} tecnico_asignado IS NOT NULL GROUP BY tecnico_asignado''', params).fetchall()
    
    meses = {'01': 'Enero', '02': 'Febrero', '03': 'Marzo', '04': 'Abril', '05': 'Mayo', '06': 'Junio', 
             '07': 'Julio', '08': 'Agosto', '09': 'Septiembre', '10': 'Octubre', '11': 'Noviembre', '12': 'Diciembre'}
    db.close()
    return render_template('reportes.html', reporte_tiempo=reporte_tiempo, reporte_soporte=reporte_soporte, meses=meses, mes_sel=mes_filtro, anio_sel=anio_filtro)

@app.route('/exportar_reportes')
@admin_required
def exportar_reportes():
    db = get_db()
    df_tiempo = pd.read_sql_query("SELECT strftime('%Y', fecha_creacion) as anio, strftime('%m', fecha_creacion) as mes, COUNT(*) as total FROM casos GROUP BY anio, mes", db)
    df_soporte = pd.read_sql_query("SELECT tecnico_asignado, COUNT(*) as total FROM casos WHERE tecnico_asignado IS NOT NULL GROUP BY tecnico_asignado", db)
    db.close()
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_tiempo.to_excel(writer, sheet_name='Por_Tiempo', index=False)
        df_soporte.to_excel(writer, sheet_name='Por_Tecnico', index=False)
    output.seek(0)
    return send_file(output, download_name="Reporte_OSTI.xlsx", as_attachment=True)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    if not os.path.exists(UPLOAD_FOLDER): os.makedirs(UPLOAD_FOLDER)
    app.run(debug=True)