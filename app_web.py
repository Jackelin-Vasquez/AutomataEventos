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

    codigo = request.form.get('codigo')
    asistente = request.form.get('asistente')
    id_evento = request.form.get('id_evento', 1)
    tipo = request.form.get('tipo', 'General')
    metodo = request.form.get('metodo', 'QR')
    area = request.form.get('area', 'Zona VIP')

    base_datos.registrar_o_actualizar_boleto(codigo, asistente, id_evento, tipo, metodo, area)

    nombre_pdf = f"Boleto_{codigo}.pdf"
    generador_pdf.crear_pdf_boleto(codigo, asistente, f"Evento #{id_evento}", tipo, nombre_pdf)

    return send_file(nombre_pdf, as_attachment=True)


@app.route('/api/eventos')
def api_eventos():
    eventos = base_datos.obtener_eventos()
    return jsonify(eventos)


@app.route('/api/boletos')
def api_boletos():
    boletos = base_datos.obtener_todos_los_boletos()
    return jsonify(boletos)


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