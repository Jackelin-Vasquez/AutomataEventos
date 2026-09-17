"""
MÓDULO: Servidor Web Principal (API & Routing)
DESCRIPCIÓN:
    Administra rutas web, login, API REST de boletos y eventos,
    integrando envío de correos vía SendGrid y control de capacidad máxima.
"""

import os
import base64
import requests
from flask import Flask, render_template, request, send_file, jsonify, redirect, url_for, session
import base_datos
import generador_pdf

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "eventaccess_secret_key_2026")

USUARIOS = {
    "control": {"password": "123", "rol": "control", "nombre": "Personal de Control"},
    "admin": {"password": "admin", "rol": "admin", "nombre": "Administrador AFND"}
}


def enviar_boleto_por_correo(destinatario_correo, nombre_asistente, codigo_boleto, nombre_evento, ruta_pdf):
    """Envía el boleto PDF mediante la API HTTP de SendGrid usando Single Sender Verification."""
    api_key = os.getenv("SENDGRID_API_KEY")
    remitente = os.getenv("MAIL_USER")

    if not api_key or not remitente:
        print("[MAIL ERROR]: Falta configurar SENDGRID_API_KEY o MAIL_USER en las variables de entorno.")
        return False

    try:
        with open(ruta_pdf, "rb") as archivo:
            archivo_pdf = archivo.read()
        archivo_base64 = base64.b64encode(archivo_pdf).decode("utf-8")

        datos = {
            "personalizations": [
                {
                    "to": [{"email": destinatario_correo}],
                    "subject": f"¡Tu boleto para {nombre_evento} está listo! ({codigo_boleto})"
                }
            ],
            "from": {
                "email": remitente,
                "name": "EventAccess System"
            },
            "content": [
                {
                    "type": "text/html",
                    "value": f"""
                        <div style="font-family: Arial, sans-serif; color: #333; padding: 20px; border: 1px solid #e2e8f0; border-radius: 8px;">
                            <h2 style="color: #2563eb;">¡Hola {nombre_asistente}!</h2>
                            <p>Gracias por registrarte en <strong>EventAccess</strong>.</p>
                            <p>Tu pase digital para el evento <strong>{nombre_evento}</strong> se ha generado con éxito.</p>
                            <p style="background: #f8fafc; padding: 10px; border-radius: 5px;">
                                <strong>Código de boleto:</strong> {codigo_boleto}
                            </p>
                            <p>Encontrarás tu boleto oficial adjunto a este correo en formato PDF.</p>
                            <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 20px 0;">
                            <p style="font-size: 12px; color: #64748b;">Sistema automatizado de control de eventos.</p>
                        </div>
                    """
                }
            ],
            "attachments": [
                {
                    "content": archivo_base64,
                    "filename": f"Boleto_{codigo_boleto}.pdf",
                    "type": "application/pdf",
                    "disposition": "attachment"
                }
            ]
        }

        respuesta = requests.post(
            "https://api.sendgrid.com/v3/mail/send",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json=datos,
            timeout=15
        )

        if respuesta.status_code == 202 or respuesta.ok:
            print(f"[MAIL SUCCESS]: Boleto enviado exitosamente a {destinatario_correo} vía SendGrid")
            return True
        else:
            print(f"[MAIL ERROR]: SendGrid respondió con error {respuesta.status_code}: {respuesta.text}")
            return False

    except Exception as e:
        print(f"[MAIL ERROR]: No se pudo conectar con SendGrid: {e}")
        return False


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

        try:
            capacidad = int(request.form.get('capacidad', 100))
        except ValueError:
            capacidad = 100

        if nombre_evento:
            base_datos.crear_evento(nombre_evento, tipos_entrada, areas_acceso, capacidad)

    return redirect(url_for('index'))


@app.route('/generar_boleto', methods=['POST'])
def generar_boleto():
    if 'usuario' not in session:
        return redirect(url_for('login'))

    id_evento_raw = request.form.get('id_evento', '1')
    try:
        id_evento = int(''.join(filter(str.isdigit, str(id_evento_raw))))
        if id_evento == 0:
            id_evento = 1
    except ValueError:
        id_evento = 1

    tipo = request.form.get('tipo', 'General')

    # 1. Validar capacidad global del evento
    if not base_datos.verificar_capacidad_evento(id_evento):
        return "Error: Este evento ha alcanzado su capacidad máxima global de boletos.", 400

    # 2. Validar capacidad específica de la categoría (VIP / General)
    if not base_datos.verificar_capacidad_categoria(id_evento, tipo):
        return f"Error: Se han agotado los boletos para la categoría '{tipo}' en este evento.", 400

    codigo = base_datos.obtener_siguiente_codigo()
    asistente = request.form.get('asistente', 'Invitado')
    correo_asistente = request.form.get('correo', '')
    metodo = request.form.get('metodo', 'QR')
    area = request.form.get('area', 'Zona General')

    # Guardar en base de datos
    base_datos.registrar_o_actualizar_boleto(codigo, asistente, id_evento, tipo, metodo, area)

    # Obtener nombre del evento
    conexion = base_datos.db.conectar()
    if conexion:
        cursor = conexion.cursor(dictionary=True)
        cursor.execute("SELECT nombre_evento FROM eventos WHERE id_evento = %s", (id_evento,))
        evento_info = cursor.fetchone()
        cursor.close()
        conexion.close()
        nombre_evento_real = evento_info['nombre_evento'] if evento_info and evento_info.get('nombre_evento') else "Evento Principal"
    else:
        nombre_evento_real = "Evento Principal"

    # Generar PDF en /tmp
    ruta_pdf = os.path.join('/tmp', f"Boleto_{codigo}.pdf")
    generador_pdf.crear_pdf_boleto(codigo, asistente, nombre_evento_real, tipo, ruta_pdf)

    # Enviar correo mediante SendGrid SOLAMENTE si el campo de correo no está vacío
    if correo_asistente and correo_asistente.strip() != "":
        enviar_boleto_por_correo(correo_asistente, asistente, codigo, nombre_evento_real, ruta_pdf)

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