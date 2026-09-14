# escaner.py

"""
MÓDULO: Captura y Lectura de Código QR (HTML5 / WebCam)
    Proporciona la interfaz y lógica JavaScript para acceder a la cámara
    del dispositivo móvil o computadora. Captura el código QR en tiempo real,
    descodifica su contenido y envía la petición de validación a la API.

"""
def obtener_html_escaner():
    return """
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Control de Puerta - EventAccess</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <script src="https://unpkg.com/html5-qrcode" type="text/javascript"></script>
        <style>
            body { background-color: #f8f9fa; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
            #reader { width: 100%; max-width: 450px; margin: auto; border-radius: 12px; overflow: hidden; }
            .card-res { max-width: 500px; margin: 20px auto; display: none; }
            .nav-pills .nav-link.active { background-color: #198754; }
        </style>
    </head>
    <body class="p-3">
        <div class="container text-center" style="max-width: 600px;">
            <div class="d-flex justify-content-between align-items-center mb-3">
                <h4 class="fw-bold m-0">Control de Puerta</h4>
                <a href="/" class="btn btn-sm btn-outline-secondary">← Volver al Dashboard</a>
            </div>

            <p class="text-muted small">Selecciona el método para validar la entrada al evento</p>

            <ul class="nav nav-pills nav-justified mb-3" id="pills-tab" role="tablist">
                <li class="nav-item">
                    <button class="nav-link active fw-bold" id="tab-qr" data-bs-toggle="pill" data-bs-target="#pills-qr" type="button" onclick="iniciarEscaner()">Escáner QR</button>
                </li>
                <li class="nav-item">
                    <button class="nav-link fw-bold" id="tab-manual" data-bs-toggle="pill" data-bs-target="#pills-manual" type="button" onclick="detenerEscaner()">Ingreso Manual</button>
                </li>
            </ul>

            <div class="tab-content" id="pills-tabContent">
                <div class="tab-pane fade show active" id="pills-qr" role="tabpanel">
                    <div id="reader" class="shadow-sm border"></div>
                </div>

                <div class="tab-pane fade" id="pills-manual" role="tabpanel">
                    <div class="card p-4 shadow-sm border-0 bg-white">
                        <h6 class="fw-bold text-dark mb-2">Validar Código de Entrada</h6>
                        <form onsubmit="validarManual(event)" class="d-flex gap-2">
                            <input type="text" id="input-codigo-manual" class="form-control" placeholder="Ej. EVT-A1B2C3" required>
                            <button type="submit" class="btn btn-success fw-bold text-nowrap">Validar</button>
                        </form>
                    </div>
                </div>
            </div>

            <div id="card-resultado" class="card card-res shadow p-4 border-0">
                <h3 id="txt-resultado" class="fw-bold mb-2"></h3>
                <p id="txt-detalle" class="mb-3 text-secondary"></p>
                <div id="txt-cadena" class="mb-3"></div>
                <button class="btn btn-dark w-100 fw-bold py-2" onclick="reiniciarEscaner()">Siguiente boleto</button>
            </div>
        </div>

        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
        <script>
            let html5QrcodeScanner = null;

            function procesarValidacion(codigo) {
                detenerEscaner();

                fetch('/api/validar_qr', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({codigo: codigo})
                })
                .then(res => res.json())
                .then(data => {
                    const card = document.getElementById('card-resultado');
                    const txtRes = document.getElementById('txt-resultado');
                    const txtDet = document.getElementById('txt-detalle');
                    const txtCad = document.getElementById('txt-cadena');
                    card.style.display = 'block';

                    if (data.exito) {
                        txtRes.className = "text-success fw-bold";
                        txtRes.innerText = "ACCESO AUTORIZADO";
                        txtDet.innerText = data.mensaje;
                        txtCad.innerHTML = `<span class="badge bg-light text-dark border">Cadena AFND: <code>${data.cadena}</code></span>`;
                    } else {
                        txtRes.className = "text-danger fw-bold";
                        txtRes.innerText = "ACCESO DENEGADO";
                        txtDet.innerText = data.mensaje;
                        txtCad.innerHTML = `<span class="badge bg-danger">Cadena AFND: <code>${data.cadena}</code></span>`;
                    }
                })
                .catch(err => alert("Error al conectar con el servidor: " + err));
            }

            function onScanSuccess(decodedText) {
                procesarValidacion(decodedText);
            }

            function validarManual(e) {
                e.preventDefault();
                const codigo = document.getElementById('input-codigo-manual').value.trim();
                if (codigo) {
                    procesarValidacion(codigo);
                    document.getElementById('input-codigo-manual').value = '';
                }
            }

            function iniciarEscaner() {
                document.getElementById('card-resultado').style.display = 'none';
                if (!html5QrcodeScanner) {
                    html5QrcodeScanner = new Html5QrcodeScanner(
                        "reader", { fps: 10, qrbox: {width: 250, height: 250} }, false
                    );
                    html5QrcodeScanner.render(onScanSuccess);
                }
            }

            function detenerEscaner() {
                if (html5QrcodeScanner) {
                    html5QrcodeScanner.clear().catch(err => console.error(err));
                    html5QrcodeScanner = null;
                }
            }

            function reiniciarEscaner() {
                document.getElementById('card-resultado').style.display = 'none';
                const tabQrActive = document.getElementById('tab-qr').classList.contains('active');
                if (tabQrActive) {
                    iniciarEscaner();
                }
            }

            window.onload = iniciarEscaner;
        </script>
    </body>
    </html>
    """