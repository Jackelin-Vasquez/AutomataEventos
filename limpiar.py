from base_datos import db

def limpiar():
    print("Conectando a la base de datos de Aiven...")
    conexion = db.conectar()
    if conexion:
        cursor = conexion.cursor()
        # Desactivar temporalmente llaves foráneas para poder borrar en orden
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")
        cursor.execute("TRUNCATE TABLE boletos;")
        cursor.execute("TRUNCATE TABLE eventos;")
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")
        conexion.commit()
        cursor.close()
        conexion.close()
        print("¡Todos los datos de Aiven se han eliminado con éxito!")

if __name__ == "__main__":
    limpiar()