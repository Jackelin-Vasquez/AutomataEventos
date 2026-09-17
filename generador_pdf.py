"""
MÓDULO: Generador de Tickets de Acceso (ReportLab PDF)
DESCRIPCIÓN:
    Diseño moderno tipo pase de abordar (horizontal) con código QR integrado
    para los boletos de EventAccess.
"""

import os
import qrcode
from reportlab.lib.pagesizes import letter, landscape
from reportlab.pdfgen import canvas
from reportlab.lib import colors


def crear_pdf_boleto(codigo, asistente, nombre_evento, tipo_entrada, ruta_salida):
    """Genera un archivo PDF con un diseño moderno de boleto horizontal (tipo pase de abordar)."""
    ruta_qr_temp = f"temp_qr_{codigo}.png"
    try:
        # 1. Generar la imagen del QR temporal
        qr_img = qrcode.make(codigo)
        qr_img.save(ruta_qr_temp)

        # 2. Configurar lienzo en formato Horizontal (Landscape) sobre tamaño Letter
        c = canvas.Canvas(ruta_salida, pagesize=landscape(letter))
        ancho, alto = landscape(letter)

        # Dimensiones de la tarjeta del boleto principal
        ticket_x = 50
        ticket_y = alto - 260
        ticket_w = 680
        ticket_h = 200

        # Fondo blanco de la tarjeta con esquinas y bordes limpios
        c.setFillColor(colors.white)
        c.setStrokeColor(colors.HexColor("#cbd5e1")) # Borde gris claro
        c.setLineWidth(1)
        c.roundRect(ticket_x, ticket_y, ticket_w, ticket_h, 12, fill=True, stroke=True)

        # Línea divisoria vertical interna del ticket (punteada con setDash correcto)
        c.setStrokeColor(colors.HexColor("#e2e8f0"))
        c.setLineWidth(1)
        c.setDash([4, 4])
        c.line(ticket_x + 210, ticket_y + 20, ticket_x + 210, ticket_y + ticket_h - 20)
        c.setDash() # Restaurar a línea sólida

        # --- SECCIÓN IZQUIERDA: Marca y Código QR ---
        c.setFillColor(colors.HexColor("#0f172a"))
        c.setFont("Helvetica-Bold", 18)
        c.drawString(ticket_x + 25, ticket_y + ticket_h - 35, "EventAccess")

        c.setFont("Helvetica", 9)
        c.setFillColor(colors.HexColor("#64748b"))
        c.drawString(ticket_x + 25, ticket_y + ticket_h - 50, "PASS OFICIAL AFND")

        # Incrustar el Código QR
        c.drawImage(ruta_qr_temp, ticket_x + 35, ticket_y + 25, width=110, height=110)

        c.setFont("Helvetica", 8)
        c.setFillColor(colors.HexColor("#94a3b8"))
        c.drawString(ticket_x + 30, ticket_y + 12, "Escanee en puerta")

        # --- SECCIÓN CENTRAL: Datos del Evento y Asistente ---
        start_text_x = ticket_x + 235

        # Número de Boleto / Código
        c.setFont("Helvetica-Bold", 12)
        c.setFillColor(colors.HexColor("#2563eb"))
        c.drawString(start_text_x, ticket_y + ticket_h - 35, f"N° {codigo}")

        # Nombre del Evento (Dinamico)
        c.setFont("Helvetica-Bold", 14)
        c.setFillColor(colors.HexColor("#1e293b"))
        c.drawString(start_text_x, ticket_y + ticket_h - 65, f"Evento: {nombre_evento}")

        # Titular / Asistente (Dinamico)
        c.setFont("Helvetica", 11)
        c.setFillColor(colors.HexColor("#475569"))
        c.drawString(start_text_x, ticket_y + ticket_h - 95, f"Titular: {asistente}")

        # Tipo de Entrada y Estado
        c.setFont("Helvetica-Bold", 10)
        c.setFillColor(colors.HexColor("#059669"))
        c.drawString(start_text_x, ticket_y + ticket_h - 125, f"Clase / Acceso: {tipo_entrada}")

        c.setFont("Helvetica", 10)
        c.setFillColor(colors.HexColor("#64748b"))
        c.drawString(start_text_x + 180, ticket_y + ticket_h - 125, "Estado: VÁLIDA")

        # Pie del boleto interno
        c.setFont("Helvetica-Oblique", 9)
        c.setFillColor(colors.HexColor("#94a3b8"))
        c.drawString(start_text_x, ticket_y + 25, "Presente este pase al ingresar al recinto. Válido por 1 acceso.")

        c.save()

    except Exception as e:
        print(f"Error generando PDF: {e}")

    finally:
        if os.path.exists(ruta_qr_temp):
            try:
                os.remove(ruta_qr_temp)
            except:
                pass