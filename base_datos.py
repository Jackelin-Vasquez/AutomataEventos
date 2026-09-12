import mysql.connector
from mysql.connector import Error


class GestorBaseDatosMySQL:
    """
    Maneja el código, tipo de entrada, método, evento, área de acceso y estado.
    """

    def __init__(self, host="localhost", user="root", password=".", database="evento_concierto",
                 port=3306):
        self.config = {
            'host': host,
            'user': user,
            'password': password,
            'database': database,
            'port': port
        }

    def conectar(self):
        """Abre y retorna una conexión activa con MySQL Workbench."""
        try:
            return mysql.connector.connect(**self.config)
        except Error as e:
            print(f"Error de conexión con MySQL: {e}")
            return None

    def obtener_boletos_para_combo(self):
        """Retorna la lista de códigos de entradas para el menú de la interfaz."""
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
        1. Lectura e identificación de tipo, método, evento y área.
        2. Validación de formato y estado (valida / usada).
        3. Conversión de los datos ingresados en la cadena de símbolos para el AFND.
        """
        conexion = self.conectar()
        if not conexion:
            return "qqe", "ERROR: Sin conexión a MySQL Workbench"

        cursor = conexion.cursor(dictionary=True)
        query = """
            SELECT b.codigo, b.tipo_entrada, b.metodo_validacion, e.nombre_evento, b.area_acceso, b.estado
            FROM boletos b
            JOIN eventos e ON b.id_evento = e.id_evento
            WHERE b.codigo = %s
        """
        cursor.execute(query, (codigo_entrada,))
        resultado = cursor.fetchone()

        cursor.close()
        conexion.close()

        # Caso: El código no existe en la base de datos
        if not resultado:
            return "qqe", f"DENEGADO: El código de entrada '{codigo_entrada}' no existe en el sistema"

        tipo = resultado['tipo_entrada'].lower()  # 'vip' o 'general'
        metodo = resultado['metodo_validacion'].lower()  # 'qr' o 'codigo'
        estado = resultado['estado'].lower()  # 'valida' o 'usada'

        # Mapeo de caracteres para el alfabeto del AFND:
        # Método: QR -> 'q', Código Impreso -> 'c'
        simbolo_metodo = 'q' if 'qr' in metodo else 'c'
        # Tipo: VIP -> 'v', General -> 'g'
        simbolo_tipo = 'v' if 'vip' in tipo else 'g'

        # Verificación del Estado
        if estado == 'usada':
            # Estado inválido/usado genera el símbolo de error 'e'
            cadena_afnd = f"{simbolo_metodo}{simbolo_metodo}{simbolo_tipo}e"
            mensaje = f"ENTRADA USADA: '{codigo_entrada}' ({resultado['tipo_entrada']}) - Estado: USADA"
        elif estado == 'valida':
            # Estado válido genera el símbolo de autorización 'a'
            cadena_afnd = f"{simbolo_metodo}{simbolo_metodo}{simbolo_tipo}{simbolo_tipo}a"
            mensaje = f"ENTRADA VÁLIDA: '{codigo_entrada}' para evento '{resultado['nombre_evento']}' - Área: {resultado['area_acceso']}"
        else:
            cadena_afnd = f"{simbolo_metodo}{simbolo_metodo}{simbolo_tipo}e"
            mensaje = f"ESTADO INVÁLIDO: '{codigo_entrada}' no está autorizada."

        return cadena_afnd, mensaje

    def marcar_como_usada(self, codigo_entrada):
        """Inactiva la entrada cambiando su estado a 'usada' tras la aprobación del AFND."""
        conexion = self.conectar()
        if not conexion:
            return False

        try:
            cursor = conexion.cursor()
            cursor.execute("UPDATE boletos SET estado = 'usada' WHERE codigo = %s", (codigo_entrada,))
            conexion.commit()
            cursor.close()
            conexion.close()
            print(f"[MySQL]: La entrada '{codigo_entrada}' cambió su estado a 'usada'.")
            return True
        except Error as e:
            print(f"Error al actualizar en MySQL: {e}")
            return False

    def procesar_lectura_qr(self, texto_qr_escaneado):
        """
        Recibe directamente el texto desencriptado o leído por la cámara/escáner QR
        y ejecuta la consulta en MySQL.
        """
        # Limpia espacios o saltos de línea que pueda enviar el lector de QR
        codigo_limpio = texto_qr_escaneado.strip()

        # Llama a la función existente para mapear a la cadena del AFND
        return self.consultar_y_generar_cadena(codigo_limpio)


# =============================================================================
# PRUEBA
# =============================================================================
if __name__ == "__main__":
    print("--- Probando Módulo MySQL con Requerimientos del Documento ---")

    #Recuerda colocar tu contraseña de MySQL
    db = GestorBaseDatosMySQL(password=".")

    # 1. Probar consulta de entrada VIP Válida
    print("\n1. Probando entrada VIP por QR ('EVT123'):")
    cadena1, msg1 = db.consultar_y_generar_cadena("EVT123")
    print(f"   Mensaje: {msg1}")
    print(f"   Cadena para el AFND: '{cadena1}'")

    # 2. Probar consulta de entrada General Usada
    print("\n2. Probando entrada Usada ('EVT125'):")
    cadena2, msg2 = db.consultar_y_generar_cadena("EVT125")
    print(f"   Mensaje: {msg2}")
    print(f"   Cadena para el AFND: '{cadena2}'")