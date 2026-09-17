"""
MÓDULO: Gestor de Persistencia y Datos (Aiven MySQL / Local)
DESCRIPCIÓN:
    Maneja la conexión segura con la base de datos MySQL.
    Gestiona la creación de eventos (incluyendo tipos de entrada y áreas)
    y la emisión/validación de boletos para el AFND.
"""

import os
import mysql.connector
from mysql.connector import Error


class GestorBaseDatosMySQL:
    def __init__(self, host=None, user=None, password=None, database=None, port=None):
        self.host = host or os.getenv("MYSQL_HOST", "localhost")
        self.user = user or os.getenv("MYSQL_USER", "root")
        self.password = password or os.getenv("MYSQL_PASSWORD", "Wilson07.")
        self.database = database or os.getenv("MYSQL_DATABASE", "evento_concierto")
        self.port = int(port or os.getenv("MYSQL_PORT", 3306))

        self.config = {
            'host': self.host,
            'user': self.user,
            'password': self.password,
            'database': self.database,
            'port': self.port
        }

        self.inicializar_base_datos()

    def inicializar_base_datos(self):
        try:
            conn = mysql.connector.connect(
                host=self.host, user=self.user, password=self.password, port=self.port
            )
            cursor = conn.cursor()
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {self.database}")
            cursor.close()
            conn.close()

            conexion = self.conectar()
            if conexion:
                cursor = conexion.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS eventos (
                        id_evento INT AUTO_INCREMENT PRIMARY KEY,
                        nombre_evento VARCHAR(100) NOT NULL,
                        tipos_entrada VARCHAR(255) DEFAULT 'VIP,General',
                        areas_acceso VARCHAR(255) DEFAULT 'Zona VIP,Zona General'
                    )
                """)

                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS boletos (
                        codigo VARCHAR(25) PRIMARY KEY,
                        asistente VARCHAR(100) DEFAULT 'Invitado General',
                        tipo_entrada VARCHAR(50) NOT NULL,
                        metodo_validacion VARCHAR(20) NOT NULL,
                        id_evento INT NOT NULL,
                        area_acceso VARCHAR(50) NOT NULL,
                        estado VARCHAR(20) DEFAULT 'valida',
                        FOREIGN KEY (id_evento) REFERENCES eventos(id_evento) ON DELETE CASCADE
                    )
                """)
                conexion.commit()

                # Migración de seguridad por si la tabla ya existía sin la columna asistente
                try:
                    cursor.execute("ALTER TABLE boletos ADD COLUMN asistente VARCHAR(100) DEFAULT 'Invitado General'")
                    conexion.commit()
                except Error:
                    pass

                cursor.execute("SELECT COUNT(*) FROM eventos")
                if cursor.fetchone()[0] == 0:
                    cursor.execute("""
                        INSERT INTO eventos (id_evento, nombre_evento, tipos_entrada, areas_acceso) 
                        VALUES (1, 'Concierto Principal 2026', 'VIP,General', 'Zona VIP,Zona General')
                    """)
                    cursor.execute("""
                        INSERT INTO boletos (codigo, asistente, tipo_entrada, metodo_validacion, id_evento, area_acceso, estado) VALUES
                        ('EVT123', 'Juan Pérez', 'VIP', 'QR', 1, 'Zona VIP', 'valida'),
                        ('EVT124', 'María Gómez', 'General', 'QR', 1, 'Zona General', 'valida'),
                        ('EVT125', 'Carlos Ruiz', 'VIP', 'QR', 1, 'Zona VIP', 'usada')
                    """)
                    conexion.commit()

                cursor.close()
                conexion.close()
        except Error as e:
            print(f"Error al inicializar esquema en MySQL: {e}")

    def conectar(self):
        try:
            return mysql.connector.connect(**self.config)
        except Error as e:
            print(f"Error de conexión con MySQL: {e}")
            return None

    def obtener_siguiente_codigo(self):
        conexion = self.conectar()
        if not conexion:
            return "EVT126"

        try:
            cursor = conexion.cursor()
            cursor.execute("SELECT codigo FROM boletos WHERE codigo REGEXP '^EVT[0-9]+$' ORDER BY LENGTH(codigo) DESC, codigo DESC LIMIT 1")
            resultado = cursor.fetchone()
            cursor.close()
            conexion.close()

            if not resultado:
                return "EVT126"

            ultimo_codigo = resultado[0]
            solo_numeros = int(''.join(filter(str.isdigit, ultimo_codigo)))
            return f"EVT{solo_numeros + 1}"
        except Exception as e:
            print(f"Error generando código secuencial: {e}")
            return "EVT126"

    def registrar_o_actualizar_boleto(self, codigo, asistente, id_evento, tipo, metodo="QR", area="Zona VIP"):
        conexion = self.conectar()
        if not conexion:
            return False
        try:
            cursor = conexion.cursor()
            if isinstance(id_evento, str) and "#" in id_evento:
                id_evento = int(id_evento.split("#")[-1])

            query = """
                INSERT INTO boletos (codigo, asistente, tipo_entrada, metodo_validacion, id_evento, area_acceso, estado)
                VALUES (%s, %s, %s, %s, %s, %s, 'valida')
                ON DUPLICATE KEY UPDATE 
                    asistente=%s, tipo_entrada=%s, metodo_validacion=%s, id_evento=%s, area_acceso=%s, estado='valida'
            """
            cursor.execute(query, (codigo, asistente, tipo, metodo, int(id_evento), area, asistente, tipo, metodo, int(id_evento), area))
            conexion.commit()
            cursor.close()
            conexion.close()
            return True
        except Error as e:
            print(f"Error al registrar/actualizar boleto: {e}")
            return False

    def consultar_y_generar_cadena(self, codigo_entrada):
        conexion = self.conectar()
        if not conexion:
            return "qqe", "ERROR: Sin conexión a MySQL"

        codigo_limpio = codigo_entrada.strip()
        cursor = conexion.cursor(dictionary=True)
        query = """
            SELECT b.codigo, b.asistente, b.tipo_entrada, b.metodo_validacion, e.nombre_evento, b.area_acceso, b.estado
            FROM boletos b
            JOIN eventos e ON b.id_evento = e.id_evento
            WHERE b.codigo = %s
        """
        cursor.execute(query, (codigo_limpio,))
        resultado = cursor.fetchone()
        cursor.close()
        conexion.close()

        if not resultado:
            return "qqe", f"DENEGADO: El código '{codigo_limpio}' no existe en el sistema."

        tipo = resultado['tipo_entrada'].lower()
        metodo = resultado['metodo_validacion'].lower()
        estado = resultado['estado'].lower()

        simbolo_metodo = 'q' if 'qr' in metodo else 'c'
        simbolo_tipo = 'v' if 'vip' in tipo else 'g'

        if estado == 'usada':
            cadena_afnd = f"{simbolo_metodo}{simbolo_metodo}{simbolo_tipo}e"
            mensaje = f"ALERTA DE FRAUDE: Entrada de '{resultado['asistente']}' ya fue UTILIZADA previamente."
        elif estado == 'valida':
            cadena_afnd = f"{simbolo_metodo}{simbolo_metodo}{simbolo_tipo}{simbolo_tipo}a"
            mensaje = f"AUTORIZADO: Boleto de '{resultado['asistente']}' válido para {resultado['nombre_evento']} ({resultado['area_acceso']})."
        else:
            cadena_afnd = f"{simbolo_metodo}{simbolo_metodo}{simbolo_tipo}e"
            mensaje = f"DENEGADO: Estado '{estado}' no reconocido."

        return cadena_afnd, mensaje

    def marcar_como_usada(self, codigo_entrada):
        conexion = self.conectar()
        if not conexion:
            return False
        try:
            cursor = conexion.cursor()
            cursor.execute("UPDATE boletos SET estado = 'usada' WHERE codigo = %s", (codigo_entrada.strip(),))
            conexion.commit()
            cursor.close()
            conexion.close()
            return True
        except Error as e:
            print(f"Error al actualizar estado: {e}")
            return False

    def validar_y_cambiar_estado(self, codigo):
        cadena_afnd, mensaje = self.consultar_y_generar_cadena(codigo)
        exito = "AUTORIZADO" in mensaje
        if exito:
            self.marcar_como_usada(codigo)
        return {"exito": exito, "mensaje": mensaje, "cadena": cadena_afnd}

    def obtener_eventos(self):
        conexion = self.conectar()
        if not conexion:
            return []
        cursor = conexion.cursor(dictionary=True)
        cursor.execute("SELECT id_evento, nombre_evento, tipos_entrada, areas_acceso FROM eventos")
        eventos = cursor.fetchall()
        cursor.close()
        conexion.close()
        return eventos

    def obtener_todos_los_boletos(self):
        conexion = self.conectar()
        if not conexion:
            return []
        cursor = conexion.cursor(dictionary=True)
        query = """
            SELECT b.codigo, b.asistente, b.tipo_entrada AS tipo, b.metodo_validacion, 
                   e.nombre_evento AS evento, b.area_acceso, b.estado
            FROM boletos b
            JOIN eventos e ON b.id_evento = e.id_evento
        """
        cursor.execute(query)
        boletos = cursor.fetchall()
        cursor.close()
        conexion.close()
        return boletos

db = GestorBaseDatosMySQL()
crear_evento = db.crear_evento
obtener_eventos = db.obtener_eventos
obtener_todos_los_boletos = db.obtener_todos_los_boletos
validar_y_cambiar_estado = db.validar_y_cambiar_estado
registrar_o_actualizar_boleto = db.registrar_o_actualizar_boleto
consultar_y_generar_cadena = db.consultar_y_generar_cadena
marcar_como_usada = db.marcar_como_usada
obtener_siguiente_codigo = db.obtener_siguiente_codigo