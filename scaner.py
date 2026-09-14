# escaner.py

"""
MÓDULO: Captura y Lectura de Código QR (HTML5 / WebCam)
    Proporciona la interfaz y lógica JavaScript para acceder a la cámara
    del dispositivo móvil o computadora. Captura el código QR en tiempo real,
    descodifica su contenido y envía la petición de validación a la API.

"""
def obtener_html_escaner():
    """Retorna la interfaz web del escáner QR móvil integrada con HTML5-QRCode."""
    return """
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Escáner Móvil QR - EventAccess</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <script src="https://unpkg.com/html5-qrcode" type="text/javascript"></script>
        <style>
            body { background-color: #f8f9fa; font-family: sans-serif; }
            #reader { width: 100%; max-width: 500px; margin: auto; border-radius: 10px; overflow: hidden; }
            .card-res { max-width: 500px; margin: 20px auto; display: none; }
        </style>
    </head>
    <body class="p-3 text-center">
        <div class="container">
            <h3 class="mb-3"> Escáner de Boletos QR</h3>
            <p class="text-muted">Apunta con la cámara trasera al código QR del boleto</p>

            <div id="reader"></div>

            <div id="card-resultado" class="card card-res shadow p-3">
                <h4 id="txt-resultado" class="fw-bold"></h4>
                <p id="txt-detalle" class="mb-2"></p>
                <button class="btn btn-primary mt-2" onclick="reiniciarEscaner()">Escanear otro boleto</button>
            </div>

            <div class="mt-4">
                <a href="/" class="btn btn-secondary">Volver al Módulo de Boletos</a>
            </div>
        </div>

        <script>
            let html5QrcodeScanner;

            function onScanSuccess(decodedText, decodedResult) {
                // Detener escáner temporalmente al leer un código
                html5QrcodeScanner.clear();

                // Enviar el QR leído al servidor en Render / Aiven
                fetch('/api/validar_qr', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({codigo: decodedText})
                })
                .then(res => res.json())
                .then(data => {
                    const card = document.getElementById('card-resultado');
                    const txtRes = document.getElementById('txt-resultado');
                    const txtDet = document.getElementById('txt-detalle');
                    card.style.display = 'block';

                    if (data.exito) {
                        txtRes.className = "text-success fw-bold display-6";
                        txtRes.innerText = "✓ ACCESO AUTORIZADO";
                        txtDet.innerText = `Boleto: ${decodedText} | Estado: ${data.mensaje}`;
                    } else {
                        txtRes.className = "text-danger fw-bold display-6";
                        txtRes.innerText = "✗ ACCESO DENEGADO";
                        txtDet.innerText = `Boleto: ${decodedText} | Razón: ${data.mensaje}`;
                    }
                })
                .catch(err => {
                    alert("Error al conectar con el servidor: " + err);
                });
            }

            function iniciarEscaner() {
                document.getElementById('card-resultado').style.display = 'none';
                html5QrcodeScanner = new Html5QrcodeScanner(
                    "reader", { fps: 10, qrbox: {width: 250, height: 250} }, /* verbose= */ false
                );
                html5QrcodeScanner.render(onScanSuccess);
            }

            function reiniciarEscaner() {
                iniciarEscaner();
            }

            // Iniciar la cámara al cargar la página
            window.onload = iniciarEscaner;
        </script>
    </body>
    </html>
    """