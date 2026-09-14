import cv2
from base_datos import GestorBaseDatosMySQL

db = GestorBaseDatosMySQL()
detector = cv2.QRCodeDetector()
cap = cv2.VideoCapture(0)

print("\n📷 Escáner iniciado. Presiona 'q' para salir...\n")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    data, bbox, _ = detector.detectAndDecode(frame)

    if data:
        codigo = data.strip()
        print(f"\n🎯 QR DETECTADO: '{codigo}'")

        cadena_afnd, mensaje = db.consultar_y_generar_cadena(codigo)
        print(f"💬 Estado BD: {mensaje}")
        print(f"⚙️ Cadena AFND: '{cadena_afnd}'")

        if "AUTORIZADO" in mensaje:
            db.marcar_como_usada(codigo)

        cv2.imshow("Escáner EventAccess", frame)
        cv2.waitKey(2000)
        break

    cv2.imshow("Escáner EventAccess", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()