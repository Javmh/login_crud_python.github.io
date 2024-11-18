import MySQLdb

# Conexión a la base de datos
conn = MySQLdb.connect(host='localhost', user='sa', passwd='12345678', db='crud_python')
cursor = conn.cursor()

# ID del usuario que quieres consultar
user_id = 27

# Consulta SQL
cursor.execute("SELECT pass_user FROM users WHERE id = %s", (user_id,))

# Obtener y mostrar el resultado
result = cursor.fetchone()
if result:
    print(f"Contraseña (hash) del usuario con ID {user_id}: {result[0]}")
else:
    print(f"No se encontró un usuario con el ID {user_id}")

# Cerrar conexión
cursor.close()
conn.close()
