import os
import sqlite3
from datetime import datetime
from flask import Flask, render_template, request, redirect, session

app = Flask(__name__)
app.secret_key = 'clave_secreta_consultorio_dental'

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'consultorio.db')

def obtener_conexion():
    conexion = sqlite3.connect(DB_PATH)
    conexion.row_factory = sqlite3.Row
    return conexion

def inicializar_bd():
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS citas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            paciente TEXT,
            telefono TEXT,
            servicio TEXT,
            fecha_registro TEXT,
            estado TEXT DEFAULT 'Pendiente'
        )
    ''')
    conexion.commit()

    try:
        cursor.execute("ALTER TABLE citas ADD COLUMN fecha_registro TEXT")
        conexion.commit()
    except sqlite3.OperationalError:
        pass

    conexion.close()

inicializar_bd()

@app.route('/')
def inicio():
    exito = request.args.get('exito')
    paciente = request.args.get('paciente', '')
    return render_template('index.html', exito=exito, paciente=paciente)

@app.route('/agendar', methods=['POST'])
def agendar():
    nombre = request.form.get('paciente', '').strip() or 'Paciente'
    telefono = request.form.get('telefono', '').strip() or 'Sin Teléfono'
    servicio = request.form.get('servicio', '').strip() or 'Valoración General'
    
    ahora = datetime.now()
    fecha_registro = ahora.strftime("%d/%m/%Y %I:%M %p")

    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute(
        "INSERT INTO citas (paciente, telefono, servicio, fecha_registro, estado) VALUES (?, ?, ?, ?, 'Pendiente')",
        (nombre, telefono, servicio, fecha_registro)
    )
    conexion.commit()
    conexion.close()

    return redirect(f'/?exito=1&paciente={nombre}#formulario')

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        password = request.form.get('password')
        if password in ['1234', '12345', 'admin']:
            session['logueado'] = True
            return redirect('/admin')
        else:
            error = "Contraseña incorrecta."
    return render_template('login.html', error=error)

@app.route('/admin')
def admin():
    if not session.get('logueado'):
        return redirect('/login')

    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("SELECT * FROM citas ORDER BY id DESC")
    filas = cursor.fetchall()
    conexion.close()

    return render_template('admin.html', solicitudes=filas)

# RUTA PARA CAMBIAR ESTADO (Pendiente <-> Atendido)
@app.route('/cambiar_estado/<int:id>')
def cambiar_estado(id):
    if not session.get('logueado'):
        return redirect('/login')
    
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("SELECT estado FROM citas WHERE id = ?", (id,))
    cita = cursor.fetchone()
    
    if cita:
        nuevo_estado = 'Atendido' if cita['estado'] == 'Pendiente' else 'Pendiente'
        cursor.execute("UPDATE citas SET estado = ? WHERE id = ?", (nuevo_estado, id))
        conexion.commit()
        
    conexion.close()
    return redirect('/admin')

# RUTA PARA ELIMINAR / DESCARTAR PACIENTE
@app.route('/eliminar_cita/<int:id>')
def eliminar_cita(id):
    if not session.get('logueado'):
        return redirect('/login')
        
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("DELETE FROM citas WHERE id = ?", (id,))
    conexion.commit()
    conexion.close()
    
    return redirect('/admin')

@app.route('/logout')
def logout():
    session.pop('logueado', None)
    return redirect('/login')

if __name__ == '__main__':
    app.run(debug=True)
