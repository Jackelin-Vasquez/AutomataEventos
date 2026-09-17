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
        """Crea la base de datos, sus tablas y migra columnas faltantes si ya existen."""
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
                        areas_acceso VARCHAR(255) DEFAULT 'Zona VIP,Zona General',
                        capacidad INT DEFAULT 100
                    )
                """)

                # Migraciones seguras para tablas preexistentes
                for col_query in [
                    "ALTER TABLE eventos ADD COLUMN tipos_entrada VARCHAR(255) DEFAULT 'VIP,General'",
                    "ALTER TABLE eventos ADD COLUMN areas_acceso VARCHAR(255) DEFAULT 'Zona VIP,Zona General'",
                    "ALTER TABLE eventos ADD COLUMN capacidad INT DEFAULT 100"
                ]:
                    try:
                        cursor.execute(col_query)
                    except Error:
                        pass

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

                try:
                    cursor.execute("ALTER TABLE boletos ADD COLUMN asistente VARCHAR(100) DEFAULT 'Invitado General'")
                    conexion.commit()
                except Error:
                    pass

                cursor.execute("SELECT COUNT(*) FROM eventos")
                if cursor.fetchone()[0] == 0:
                    cursor.execute("""
                        INSERT INTO eventos (id_evento, nombre_evento, tipos_entrada, areas_acceso, capacidad) 
                        VALUES (1, 'Concierto Principal 2026', 'VIP,General', 'Zona VIP,Zona General', 100)
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
        """Abre y retorna una conexión activa con el servidor MySQL."""
        try:
            return mysql.connector.connect(**self.config)
        except Error as e:
            print(f"Error de conexión con MySQL: {e}")
            return None

    def crear_evento(self, nombre_evento, tipos_entrada="VIP,General", areas_acceso="Zona VIP,Zona General", capacidad=100):
        """Permite al Administrador registrar un nuevo evento con su capacidad máxima."""
        conexion = self.conectar()
        if not conexion:
            return False

        try:
            cursor = conexion.cursor()
            query = """
                INSERT INTO eventos (nombre_evento, tipos_entrada, areas_acceso, capacidad)
                VALUES (%s, %s, %s, %s)
            """
            cursor.execute(query, (nombre_evento, tipos_entrada, areas_acceso, int(capacidad)))
            conexion.commit()
            cursor.close()
            conexion.close()
            print(f"[MySQL]: Nuevo evento '{nombre_evento}' registrado con capacidad {capacidad}.")
            return True
        except Error as e:
            print(f"Error al crear evento: {e}")
            return False

    def verificar_capacidad_evento(self, id_evento):
        """Devuelve True si aún hay espacio disponible, o False si se alcanzó el límite."""
        conexion = self.conectar()
        if not conexion:
            return False

        cursor = conexion.cursor(dictionary=True)
        cursor.execute("SELECT capacidad FROM eventos WHERE id_evento = %s", (id_evento,))
        evento = cursor.fetchone()

        if not evento:
            cursor.close()
            conexion.close()
            return False

        capacidad_maxima = evento['capacidad']

        cursor.execute("SELECT COUNT(*) as total FROM boletos WHERE id_evento = %s", (id_evento,))
        resultado = cursor.fetchone()
        total_emitidos = resultado['total'] if resultado else 0

        cursor.close()
        conexion.close()

        return total_emitidos < capacidad_maxima

    def verificar_capacidad_categoria(self, id_evento, tipo_entrada, limite_por_defecto=50):
        """Verifica si aún hay cupo disponible para una categoría específica leyendo los límites del evento."""
        conexion = self.conectar()
        if not conexion:
            return False

        cursor = conexion.cursor(dictionary=True)

        # Obtener la cadena de tipos y límites guardada en el evento (Ej: "VIP:30,General:100")
        cursor.execute("SELECT tipos_entrada FROM eventos WHERE id_evento = %s", (id_evento,))
        evento = cursor.fetchone()

        limite_maximo = limite_por_defecto
        if evento and evento['tipos_entrada']:
            # Analizar la cadena para extraer el límite específico de esta categoría
            partes = evento['tipos_entrada'].split(',')
            for parte in partes:
                if ':' in parte:
                    cat, limite = parte.split(':')
                    if cat.strip().lower() == tipo_entrada.strip().lower():
                        limite_maximo = int(limite)
                        break

        # 2. Contar cuántos boletos de este tipo exacto ya se han emitido para el evento
        cursor.execute(
            "SELECT COUNT(*) as total FROM boletos WHERE id_evento = %s AND tipo_entrada = %s",
            (id_evento, tipo_entrada)
        )
        resultado = cursor.fetchone()
        total_emitidos = resultado['total'] if resultado else 0

        cursor.close()
        conexion.close()

        # 3. Comparar lo emitido contra el límite dinámico configurado
        return total_emitidos < limite_maximo

    def obtener_eventos(self):
        """Retorna la lista de eventos disponibles con su capacidad."""
        conexion = self.conectar()
        if not conexion:
            return []

        cursor = conexion.cursor(dictionary=True)
        cursor.execute("SELECT id_evento, nombre_evento, tipos_entrada, areas_acceso, capacidad FROM eventos")
        eventos = cursor.fetchall()
        cursor.close()
        conexion.close()
        return eventos

    def obtener_boletos_activos(self):
        conexion = self.conectar()
        if not conexion:
            return []

        cursor = conexion.cursor()
        cursor.execute("SELECT codigo FROM boletos")
        filas = cursor.fetchall()
        cursor.close()
        conexion.close()
        return [f[0] for f in filas]

    def obtener_siguiente_codigo(self):
        """Genera el siguiente código secuencial para un nuevo boleto."""
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

    def consultar_desde_qr(self, texto_raw_qr):
        if not texto_raw_qr:
            return "qqe", "Error: Lectura QR vacía."
        return self.consultar_y_generar_cadena(str(texto_raw_qr).strip())

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
            print(f"Error al actualizar estado en MySQL: {e}")
            return False

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

    def validar_y_cambiar_estado(self, codigo):
        cadena_afnd, mensaje = self.consultar_y_generar_cadena(codigo)
        exito = "AUTORIZADO" in mensaje
        if exito:
            self.marcar_como_usada(codigo)
        return {"exito": exito, "mensaje": mensaje, "cadena": cadena_afnd}

    def reiniciar_boletos_prueba(self):
        conexion = self.conectar()
        if not conexion:
            return
        cursor = conexion.cursor()
        cursor.execute("UPDATE boletos SET estado = 'valida'")
        conexion.commit()
        cursor.close()
        conexion.close()


# --- INSTANCIA GLOBAL Y EXPOSICIÓN DE FUNCIONES ---
db = GestorBaseDatosMySQL()

crear_evento = db.crear_evento
verificar_capacidad_evento = db.verificar_capacidad_evento
obtener_eventos = db.obtener_eventos
obtener_todos_los_boletos = db.obtener_todos_los_boletos
validar_y_cambiar_estado = db.validar_y_cambiar_estado
registrar_o_actualizar_boleto = db.registrar_o_actualizar_boleto
consultar_y_generar_cadena = db.consultar_y_generar_cadena
marcar_como_usada = db.marcar_como_usada
reiniciar_boletos_prueba = db.reiniciar_boletos_prueba
obtener_siguiente_codigo = db.obtener_siguiente_codigo


if __name__ == "__main__":
    print("Base de datos inicializada correctamente.")