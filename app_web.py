import os
from flask import Flask, render_template_string, request, jsonify
from base_datos import GestorBaseDatosMySQL

app = Flask(__name__)
db = GestorBaseDatosMySQL()

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>EventAccess - Escáner Móvil</title>
    <script src="https://unpkg.com/html5-qrcode"></script>
    <style>
        body { font-family: system-ui, sans-serif; text-align: center; background: #0f172a; color: white; padding: 20px; }
        #reader { width: 100%; max-width: 350px; margin: auto; border-radius: 12px; overflow: hidden; }
        .card { background: #1e293b; padding: 15px; border-radius: 10px; margin-top: 20px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.3); }
        code { background: #334155; padding: 2px 6px; border-radius: 4px; color: #38bdf8; }
    </style>
</head>
<body>
    <h2>🎟 Control de Acceso</h2>
    <div id="reader"></div>
    <div class="card">
        <div id="resultado">Apunta la cámara al código QR del boleto...</div>
    </div>

    <script>
        function onScanSuccess(decodedText) {
            fetch('/validar', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({codigo: decodedText})
            })
            .then(res => res.json())
            .then(data => {
                document.getElementById('resultado').innerHTML = 
                    `<p style="color:${data.color}; font-size:18px; font-weight:bold;">${data.mensaje}</p>
                     <p>Cadena AFND: <code>${data.cadena}</code></p>`;
            });
        }
        let html5QrcodeScanner = new Html5QrcodeScanner("reader", { fps: 10, qrbox: 250 });
        html5QrcodeScanner.render(onScanSuccess);
    </script>
</body>
</html>
"""


@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)


@app.route('/validar', methods=['POST'])
def validar():
    data = request.get_json() or {}
    codigo = data.get('codigo', '')
    cadena, mensaje = db.consultar_y_generar_cadena(codigo)

    if "AUTORIZADO" in mensaje:
        db.marcar_como_usada(codigo)
        color = "#4ade80"  # Verde
    else:
        color = "#f87171"  # Rojo

    return jsonify({'cadena': cadena, 'mensaje': mensaje, 'color': color})


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)