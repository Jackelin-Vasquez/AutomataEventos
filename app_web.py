"""
MÓDULO: Servidor Web Principal (API & Routing)
    Punto de entrada de la aplicación Flask. Administra el enrutamiento web,
    las vistas de usuario/administrador, los endpoints de la API REST para el
    escáner QR, la generación e integración de boletos y la comunicación con
    el simulador  del AFND.
"""

import os
from flask import Flask, render_template_string, request, send_file, jsonify
import base_datos
import generador_pdf

app = Flask(__name__)

# --- VISTA DE GESTIÓN Y EMISIÓN DE BOLETOS ---
HTML_BOLETOS = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Gestión de Boletos - EventAccess</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { background-color: #f4f6f9; }
        .card-custom { border-radius: 12px; border: none; }
    </style>
</head>
<body>
    <nav class="navbar navbar-dark bg-dark mb-4 shadow">
        <div class="container">
            <span class="navbar-brand mb-0 h1">🎟 EventAccess - Módulo de Boletos</span>
            <a href="/escanear" class="btn btn-outline-success"> Ir al Escáner QR</a>
        </div>
    </nav>

    <div class="container">
        <div class="row">
            <!-- FORMULARIO: CREAR NUEVO BOLETO Y GENERAR PDF -->
            <div class="col-md-5 mb-4">
                <div class="card card-custom shadow p-4 bg-white">
                    <h5 class="text-primary font-weight-bold mb-3">Registrar Nuevo Boleto</h5>
                    <form action="/generar_boleto" method="POST">
                        <div class="mb-3">
                            <label class="form-label">Código del Boleto</label>
                            <input type="text" name="codigo" class="form-control" placeholder="Ej. EVT101" required>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Nombre del Asistente</label>
                            <input type="text" name="asistente" class="form-control" placeholder="Ej. Maria Lopez" required>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Nombre del Evento</label>
                            <input type="text" name="evento" class="form-control" placeholder="Ej. Concierto de Gala" required>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Tipo de Boleto</label>
                            <select name="tipo" class="form-select">
                                <option value="General">General</option>
                                <option value="VIP">VIP</option>
                            </select>
                        </div>
                        <button type="submit" class="btn btn-primary w-100 font-weight-bold">
                             Guardar en BD y Descargar PDF
                        </button>
                    </form>
                </div>
            </div>

            <!-- TABLA: BOLETOS REGISTRADOS EN AIVEN MYSQL -->
            <div class="col-md-7">
                <div class="card card-custom shadow p-4 bg-white">
                    <h5 class="text-secondary font-weight-bold mb-3">Boletos Registrados en la Nube</h5>
                    <div class="table-responsive">
                        <table class="table table-hover align-middle">
                            <thead class="table-light">
                                <tr>
                                    <th>Código</th>
                                    <th>Asistente</th>
                                    <th>Tipo</th>
                                    <th>Estado</th>
                                </tr>
                            </thead>
                            <tbody id="tabla-boletos">
                                <tr><td colspan="4" class="text-center text-muted">Cargando registros de Aiven...</td></tr>
                            </tbody>
                        </table>
                    </div>
                    <button onclick="cargarBoletos()" class="btn btn-sm btn-outline-secondary mt-2"> Actualizar Tabla</button>
                </div>
            </div>
        </div>
    </div>

    <script>
        function cargarBoletos() {
            fetch('/api/boletos')
                .then(res => res.json())
                .then(data => {
                    const tbody = document.getElementById('tabla-boletos');
                    tbody.innerHTML = '';
                    if (data.length === 0) {
                        tbody.innerHTML = '<tr><td colspan="4" class="text-center">No hay boletos registrados.</td></tr>';
                        return;
                    }
                    data.forEach(b => {
                        const badgeClass = b.estado === 'valida' ? 'bg-success' : 'bg-danger';
                        tbody.innerHTML += `
                            <tr>
                                <td><b>${b.codigo}</b></td>
                                <td>${b.asistente || 'N/A'}</td>
                                <td>${b.tipo || 'General'}</td>
                                <td><span class="badge ${badgeClass}">${b.estado}</span></td>
                            </tr>
                        `;
                    });
                });
        }
        // Cargar boletos al iniciar la página
        cargarBoletos();
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_BOLETOS)

# ENDPOINT: Genera el boleto en BD (Aiven) y descarga el PDF inmediatamente
@app.route('/generar_boleto', methods=['POST'])
def generar_boleto():
    codigo = request.form.get('codigo')
    asistente = request.form.get('asistente')
    evento = request.form.get('evento')
    tipo = request.form.get('tipo')

    # 1. Insertar o actualizar en Aiven MySQL
    base_datos.registrar_o_actualizar_boleto(codigo, asistente, evento, tipo)

    # 2. Generar el PDF localmente
    nombre_pdf = f"Boleto_{codigo}.pdf"
    generador_pdf.crear_pdf_boleto(codigo, asistente, evento, tipo, nombre_pdf)

    # 3. Descargar el PDF al usuario
    return send_file(nombre_pdf, as_attachment=True)

# API: Obtener lista de boletos para la tabla web
@app.route('/api/boletos')
def api_boletos():
    boletos = base_datos.obtener_todos_los_boletos()
    return jsonify(boletos)

# VISTA: Escáner QR
@app.route('/escanear')
def escanear():
    import scaner
    return scaner.obtener_html_escaner()

# API: Validar QR desde el escáner
@app.route('/api/validar_qr', methods=['POST'])
def validar_qr():
    data = request.get_json()
    codigo = data.get('codigo')
    resultado = base_datos.validar_y_cambiar_estado(codigo)
    return jsonify(resultado)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)