"""
MÓDULO: Servidor Web Principal (API & Routing)
DESCRIPCIÓN:
    Administra rutas web, login, API REST de boletos y eventos.
"""

import os
from flask import Flask, render_template, request, send_file, jsonify, redirect, url_for, session
import base_datos
import generador_pdf

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "eventaccess_secret_key_2026")

USUARIOS = {
    "control": {"password": "123", "rol": "control", "nombre": "Personal de Control"},
    "admin": {"password": "admin", "rol": "admin", "nombre": "Administrador AFND"}
}


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario = request.form.get('usuario')
        password = request.form.get('password')

        if usuario in USUARIOS and USUARIOS[usuario]['password'] == password:
            session['usuario'] = usuario
            session['rol'] = USUARIOS[usuario]['rol']
            session['nombre'] = USUARIOS[usuario]['nombre']
            return redirect(url_for('index'))
        return render_template('login.html', error="Usuario o contraseña incorrectos")

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


@app.route('/')
def index():
    if 'usuario' not in session:
        return redirect(url_for('login'))
    return render_template('index.html')


@app.route('/simulador')
def simulador():
    if 'usuario' not in session:
        return redirect(url_for('login'))
    if session.get('rol') != 'admin':
        return "Acceso Denegado: Vista reservada exclusivamente para Administradores.", 403
    return render_template('simulador.html')


@app.route('/escanear')
def escanear():
    if 'usuario' not in session:
        return redirect(url_for('login'))
    try:
        import scaner
        return scaner.obtener_html_escaner()
    except ImportError:
        return render_template('escanear.html')


# --- ENDPOINTS API ---

@app.route('/crear_evento', methods=['POST'])
def crear_evento():
    if session.get('rol') == 'admin':
        nombre_evento = request.form.get('nombre_evento')
        tipos_entrada = request.form.get('tipos_entrada', 'VIP,General')
        areas_acceso = request.form.get('areas_acceso', 'Zona VIP,Zona General')

        if nombre_evento:
            base_datos.crear_evento(nombre_evento, tipos_entrada, areas_acceso)
    return redirect(url_for('index'))


@app.route('/generar_boleto', methods=['POST'])
def generar_boleto():
    if 'usuario' not in session:
        return redirect(url_for('login'))

    codigo = base_datos.obtener_siguiente_codigo()
    asistente = request.form.get('asistente', 'Invitado')
    id_evento_raw = request.form.get('id_evento', '1')
    tipo = request.form.get('tipo', 'General')
    metodo = request.form.get('metodo', 'QR')
    area = request.form.get('area', 'Zona General')

    # Limpiar y extraer de forma segura el ID numérico del evento
    try:
        id_evento = int(''.join(filter(str.isdigit, str(id_evento_raw))))
        if id_evento == 0:
            id_evento = 1
    except ValueError:
        id_evento = 1

    # Guardar en base de datos incluyendo el asistente y el ID limpio
    base_datos.registrar_o_actualizar_boleto(codigo, asistente, id_evento, tipo, metodo, area)

    # Obtener el nombre real y exacto del evento desde la BD para el PDF
    conexion = base_datos.db.conectar()
    cursor = conexion.cursor(dictionary=True)
    cursor.execute("SELECT nombre_evento FROM eventos WHERE id_evento = %s", (id_evento,))
    evento_info = cursor.fetchone()
    cursor.close()
    conexion.close()

    nombre_evento_real = evento_info['nombre_evento'] if evento_info and evento_info.get('nombre_evento') else "Evento Principal"

    # Guardar el PDF temporalmente en /tmp para compatibilidad total con Render
    ruta_pdf = os.path.join('/tmp', f"Boleto_{codigo}.pdf")
    generador_pdf.crear_pdf_boleto(codigo, asistente, nombre_evento_real, tipo, ruta_pdf)

    return send_file(ruta_pdf, as_attachment=True)


@app.route('/api/eventos')
def api_eventos():
    eventos = base_datos.obtener_eventos()
    return jsonify(eventos)


@app.route('/api/boletos')
def api_boletos():
    boletos = base_datos.obtener_todos_los_boletos()
    return jsonify(boletos)


@app.route('/api/siguiente_codigo')
def api_siguiente_codigo():
    codigo = base_datos.obtener_siguiente_codigo()
    return jsonify({"codigo": codigo})


@app.route('/api/validar_qr', methods=['POST'])
def validar_qr():
    data = request.get_json() or {}
    codigo = data.get('codigo', '')
    resultado = base_datos.validar_y_cambiar_estado(codigo)
    return jsonify(resultado)


if __name__ == '__main__':
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    app.jinja_env.auto_reload = True

    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)