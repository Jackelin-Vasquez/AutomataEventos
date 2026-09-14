import os
import mysql.connector
from mysql.connector import Error


class GestorBaseDatosMySQL:
    """
    Módulo de Lógica de Datos para EventAccess.
    Maneja la persistencia en MySQL, la validación de boletos,
    la creación de eventos y la traducción a cadenas para el AFND.
    """

    def __init__(self, host=None, user=None, password=None, database=None, port=None):
        # Lee variables de entorno de Render/Aiven; si no existen, usa credenciales locales
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

        # Garantizar que el esquema y las tablas existan al instanciar
        self.inicializar_base_datos()

    def inicializar_base_datos(self):
        """Crea la base de datos, sus tablas y datos base si no existen."""
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
                        nombre_evento VARCHAR(100) NOT NULL
                    )
                """)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS boletos (
                        codigo VARCHAR(25) PRIMARY KEY,
                        tipo_entrada VARCHAR(20) NOT NULL,
                        metodo_validacion VARCHAR(20) NOT NULL,
                        id_evento INT NOT NULL,
                        area_acceso VARCHAR(30) NOT NULL,
                        estado VARCHAR(20) DEFAULT 'valida',
                        FOREIGN KEY (id_evento) REFERENCES eventos(id_evento) ON DELETE CASCADE
                    )
                """)
                conexion.commit()

                cursor.execute("SELECT COUNT(*) FROM eventos")
                if cursor.fetchone()[0] == 0:
                    cursor.execute(
                        "INSERT INTO eventos (id_evento, nombre_evento) VALUES (1, 'Concierto Principal 2026')")
                    cursor.execute("""
                        INSERT INTO boletos (codigo, tipo_entrada, metodo_validacion, id_evento, area_acceso, estado) VALUES
                        ('EVT123', 'VIP', 'QR', 1, 'Zona VIP', 'valida'),
                        ('EVT124', 'General', 'QR', 1, 'Zona General', 'valida'),
                        ('EVT125', 'VIP', 'QR', 1, 'Zona VIP', 'usada')
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

    def obtener_boletos_activos(self):
        """Retorna la lista de códigos de boletos registrados."""
        conexion = self.conectar()
        if not conexion:
            return []

        cursor = conexion.cursor()
        cursor.execute("SELECT codigo FROM boletos")
        filas = cursor.fetchall()
        cursor.close()
        conexion.close()
        return [f[0] for f in filas]

    def consultar_y_generar_cadena(self, codigo_entrada):
        """
        1. Consulta la BD usando el código escaneado.
        2. Verifica el estado ('valida' vs 'usada').
        3. Traduce los atributos del boleto a la cadena de símbolos para el AFND.
        """
        conexion = self.conectar()
        if not conexion:
            return "qqe", "ERROR: Sin conexión a MySQL"

        codigo_limpio = codigo_entrada.strip()

        cursor = conexion.cursor(dictionary=True)
        query = """
            SELECT b.codigo, b.tipo_entrada, b.metodo_validacion, e.nombre_evento, b.area_acceso, b.estado
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
            mensaje = f"ALERTA DE FRAUDE: Entrada '{codigo_limpio}' ya fue UTILIZADA previamente."
        elif estado == 'valida':
            cadena_afnd = f"{simbolo_metodo}{simbolo_metodo}{simbolo_tipo}{simbolo_tipo}a"
            mensaje = f"AUTORIZADO: Boleto '{codigo_limpio}' válido para {resultado['nombre_evento']} ({resultado['area_acceso']})."
        else:
            cadena_afnd = f"{simbolo_metodo}{simbolo_metodo}{simbolo_tipo}e"
            mensaje = f"DENEGADO: Estado '{estado}' no reconocido."

        return cadena_afnd, mensaje

    def consultar_desde_qr(self, texto_raw_qr):
        """Punto de entrada directo para el escáner OpenCV."""
        if not texto_raw_qr:
            return "qqe", "Error: Lectura QR vacía."
        return self.consultar_y_generar_cadena(str(texto_raw_qr).strip())

    def marcar_como_usada(self, codigo_entrada):
        """Inactiva la entrada actualizando estado = 'usada' en MySQL."""
        conexion = self.conectar()
        if not conexion:
            return False

        try:
            cursor = conexion.cursor()
            cursor.execute("UPDATE boletos SET estado = 'usada' WHERE codigo = %s", (codigo_entrada.strip(),))
            conexion.commit()
            cursor.close()
            conexion.close()
            print(f"[MySQL]: La entrada '{codigo_entrada}' se actualizó a estado = 'usada'.")
            return True
        except Error as e:
            print(f"Error al actualizar estado en MySQL: {e}")
            return False

    def crear_evento(self, nombre_evento):
        """Permite al Administrador registrar un nuevo evento."""
        conexion = self.conectar()
        if not conexion:
            return False

        try:
            cursor = conexion.cursor()
            cursor.execute("INSERT INTO eventos (nombre_evento) VALUES (%s)", (nombre_evento,))
            conexion.commit()
            cursor.close()
            conexion.close()
            print(f"➕ [MySQL]: Nuevo evento '{nombre_evento}' registrado.")
            return True
        except Error as e:
            print(f"Error al crear evento: {e}")
            return False

    def obtener_eventos(self):
        """Retorna la lista de eventos disponibles."""
        conexion = self.conectar()
        if not conexion:
            return []

        cursor = conexion.cursor(dictionary=True)
        cursor.execute("SELECT id_evento, nombre_evento FROM eventos")
        eventos = cursor.fetchall()
        cursor.close()
        conexion.close()
        return eventos

    def registrar_boleto(self, codigo, tipo_entrada, metodo_validacion, id_evento, area_acceso):
        """Permite al Administrador dar de alta un nuevo boleto."""
        conexion = self.conectar()
        if not conexion:
            return False

        try:
            cursor = conexion.cursor()
            query = """
                INSERT INTO boletos (codigo, tipo_entrada, metodo_validacion, id_evento, area_acceso, estado)
                VALUES (%s, %s, %s, %s, %s, 'valida')
            """
            cursor.execute(query, (codigo, tipo_entrada, metodo_validacion, id_evento, area_acceso))
            conexion.commit()
            cursor.close()
            conexion.close()
            print(f"➕ [MySQL]: Boleto '{codigo}' registrado exitosamente.")
            return True
        except Error as e:
            print(f"Error al registrar boleto: {e}")
            return False

    def reiniciar_boletos_prueba(self):
        """Restaura todos los boletos a estado = 'valida'."""
        conexion = self.conectar()
        if not conexion:
            return

        cursor = conexion.cursor()
        cursor.execute("UPDATE boletos SET estado = 'valida'")
        conexion.commit()
        cursor.close()
        conexion.close()
        print("🔄 [MySQL]: Todos los boletos han sido restaurados a 'valida'.")


if __name__ == "__main__":
    db = GestorBaseDatosMySQL()
    print("Base de datos inicializada correctamente.")