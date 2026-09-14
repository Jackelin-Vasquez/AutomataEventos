"""
MÓDULO: Generador de Tickets de Acceso (ReportLab PDF)
    Encargado de la creación dinámica de archivos PDF en formato ticket (A6).
    Renderiza la información relevante del asistente, tipo de entrada, evento
    y dibuja vectorialmente el código QR único para su posterior escaneo.
"""

from reportlab.lib.pagesizes import A6, landscape
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.barcode import qr


def crear_pdf_boleto(codigo="EVT123", asistente="invitado", evento="Concierto Principal 2026", tipo="VIP", archivo_salida="Boleto_EVT123.pdf"):
    """Genera un boleto PDF en formato ticket con código QR."""
    ancho, alto = landscape(A6)
    c = canvas.Canvas(archivo_salida, pagesize=landscape(A6))

    # Encabezado
    c.setFillColor(colors.HexColor("#1A252C"))
    c.rect(0, alto - 45, ancho, 45, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(15, alto - 28, "🎟 EventAccess - TICKET OFICIAL")

    # Detalles del boleto
    c.setFillColor(colors.HexColor("#2C3E50"))
    c.setFont("Helvetica-Bold", 12)
    c.drawString(15, alto - 65, f"Evento: {evento}")

    c.setFont("Helvetica", 10)
    c.setFillColor(colors.HexColor("#333333"))
    c.drawString(15, alto - 85, f"Asistente: {asistente}")
    c.drawString(15, alto - 100, f"Tipo de Entrada: {tipo} | Área: Zona {tipo}")
    c.drawString(15, alto - 115, f"Código de Boleto: {codigo}")

    c.setFont("Helvetica-Oblique", 8)
    c.setFillColor(colors.HexColor("#7F8C8D"))
    c.drawString(15, 20, "Presente este código QR en su celular el día del evento.")

    # Código QR
    qr_code = qr.QrCodeWidget(codigo)
    bounds = qr_code.getBounds()
    width = bounds[2] - bounds[0]
    height = bounds[3] - bounds[1]

    d = Drawing(105, 105, transform=[105.0 / width, 0, 0, 105.0 / height, 0, 0])
    d.add(qr_code)
    d.drawOn(c, ancho - 120, 25)

    c.save()
    print(f"Boleto generado exitosamente: '{archivo_salida}'")


if __name__ == "__main__":
    crear_pdf_boleto()