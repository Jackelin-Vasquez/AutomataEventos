"""
MÓDULO: Generador de Tickets de Acceso (ReportLab PDF)
    Encargado de la creación dinámica de archivos PDF en formato ticket (A6).
    Renderiza la información relevante del asistente, tipo de entrada, evento
    y dibuja vectorialmente el código QR único para su posterior escaneo.
"""

import os
import qrcode
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors


def crear_pdf_boleto(codigo, asistente, nombre_evento, tipo_entrada, ruta_salida):
    """Genera un archivo PDF con formato de boleto y su código QR."""
    # 1. Generar la imagen del QR temporal
    qr_img = qrcode.make(codigo)
    ruta_qr_temp = f"temp_qr_{codigo}.png"
    qr_img.save(ruta_qr_temp)

    # 2. Configurar el lienzo del PDF
    c = canvas.Canvas(ruta_salida, pagesize=letter)
    ancho, alto = letter

    # Encabezado
    c.setFillColor(colors.HexColor("#0d6efd"))
    c.rect(0, alto - 100, ancho, 100, fill=True, stroke=False)

    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 24)
    c.drawString(50, alto - 55, "TICKET DE ACCESO OFICIAL")
    c.setFont("Helvetica", 12)
    c.drawString(50, alto - 80, "EventAccess System - Control de Acceso Automático")

    # Información del Boleto
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, alto - 150, f"Evento: {nombre_evento}")

    c.setFont("Helvetica", 12)
    c.drawString(50, alto - 180, f"Código Único: {codigo}")
    c.drawString(50, alto - 200, f"Comprador: {asistente}")
    c.drawString(50, alto - 220, f"Tipo de Entrada: {tipo_entrada}")
    c.drawString(50, alto - 240, f"Estado Inicial: VÁLIDA")

    # Incrustar Imagen del Código QR
    c.drawImage(ruta_qr_temp, 350, alto - 280, width=180, height=180)

    # Nota de pie de página
    c.setFont("Helvetica-Oblique", 10)
    c.setFillColor(colors.gray)
    c.drawString(50, alto - 310, "Presente este código QR en la puerta de acceso.")

    c.save()

    # Limpiar la imagen QR temporal
    if os.path.exists(ruta_qr_temp):
        os.remove(ruta_qr_temp)