import os
import io
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_mysqldb import MySQL
import MySQLdb.cursors
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from flask import send_file
import xlsxwriter

app = Flask(__name__)

# Clave secreta para las sesiones
app.secret_key = 'clave_secreta'

# Configuración de MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'sa'
app.config['MYSQL_PASSWORD'] = '12345678'
app.config['MYSQL_DB'] = 'crud_python'

# Configuración para la carga de archivos (imagenes)
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['ALLOWED_EXTENSIONS'] = {'jpg', 'jpeg', 'png'}

mysql = MySQL(app)

# Función para verificar si la extensión del archivo es permitida
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# Ruta principal (Home)
@app.route('/')
def home():
    if 'loggedin' in session:
        return render_template('dashboard.html', username=session['name_surname'])
    return redirect(url_for('login'))

# Ruta para la página de inicio de sesión
@app.route('/login', methods=['GET', 'POST'])
def login():
    msg = ''
    if request.method == 'POST' and 'email_user' in request.form and 'pass_user' in request.form:
        email_user = request.form['email_user']
        pass_user = request.form['pass_user']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM users WHERE email_user = %s AND pass_user = %s', (email_user, pass_user,))
        account = cursor.fetchone()
        if account:
            session['loggedin'] = True
            session['id'] = account['id']
            session['name_surname'] = account['name_surname']
            flash('¡Felicitaciones, la sesión fue correcta!', 'success')  # Mensaje de felicitaciones
            return redirect(url_for('home'))
        else:
            msg = '¡Correo o contraseña incorrectos!'
    return render_template('login.html', msg=msg)


# Ruta para registrar nuevos usuarios
@app.route('/register', methods=['GET', 'POST'])
def register():
    msg = ''
    success = False  # Variable para controlar si fue un registro exitoso
    if request.method == 'POST':
        if 'name_surname' in request.form and 'email_user' in request.form and 'pass_user' in request.form:
            name_surname = request.form['name_surname']
            email_user = request.form['email_user']
            pass_user = request.form['pass_user']
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

            # Verificar si el usuario ya existe
            cursor.execute('SELECT * FROM users WHERE email_user = %s', (email_user,))
            account = cursor.fetchone()

            if account:
                msg = '¡El correo ya está registrado!'
            else:
                cursor.execute('INSERT INTO users (name_surname, email_user, pass_user) VALUES (%s, %s, %s)', (name_surname, email_user, pass_user))
                mysql.connection.commit()
                msg = '¡Registro exitoso! Serás redirigido a la página de inicio de sesión en unos segundos.'
                success = True  # Indica que fue exitoso
        else:
            msg = 'Por favor, llena todos los campos.'

    return render_template('register.html', msg=msg, success=success)

# Ruta para registrar un nuevo empleado
@app.route('/registrar_empleado', methods=['GET', 'POST'])
def registrar_empleado():
    if request.method == 'POST':
        try:
            # Obtener datos del formulario
            nombre_empleado = request.form.get('nombre_empleado', '').strip()
            apellido_empleado = request.form.get('apellido_empleado', '').strip()
            sexo_empleado = request.form.get('sexo_empleado', '').strip()
            telefono_empleado = request.form.get('telefono_empleado', '').strip()
            email_empleado = request.form.get('email_empleado', '').strip()
            profesion_empleado = request.form.get('profesion_empleado', '').strip()
            salario_empleado = request.form.get('salario_empleado', '').strip()
            foto_empleado = request.files.get('foto_empleado')

            # Validación básica de datos
            if not nombre_empleado or not apellido_empleado or not email_empleado:
                flash('Por favor, completa todos los campos obligatorios.', 'error')
                return redirect(request.url)

            # Guardar imagen en carpeta estática (si se selecciona)
            foto_path = None
            if foto_empleado and foto_empleado.filename:
                if allowed_file(foto_empleado.filename):
                    # Asegurar un nombre seguro para el archivo
                    filename = secure_filename(foto_empleado.filename)
                    # Construir la ruta completa donde se guardará el archivo
                    save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    # Guardar el archivo en la carpeta correspondiente
                    foto_empleado.save(save_path)
                    # Guardar solo el nombre del archivo para la base de datos
                    foto_path = filename
                else:
                    flash('¡Archivo no válido! Solo se permiten imágenes JPG, JPEG y PNG.', 'error')
                    return redirect(request.url)


            # Insertar los datos del empleado en la base de datos
            cursor = mysql.connection.cursor()
            cursor.execute(''' 
                INSERT INTO tbl_empleados (nombre_empleado, apellido_empleado, sexo_empleado, telefono_empleado, 
                email_empleado, profesion_empleado, salario_empleado, foto_empleado)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ''', (nombre_empleado, apellido_empleado, sexo_empleado, telefono_empleado, email_empleado,
                  profesion_empleado, salario_empleado, foto_path))

            mysql.connection.commit()

            flash('¡Empleado registrado con éxito!', 'success')
            return redirect(url_for('registrar_empleado'))
        except Exception as e:
            flash(f'Ocurrió un error al registrar el empleado: {e}', 'error')
            return redirect(request.url)

    return render_template('registrar_empleado.html')

# Ruta para la lista de empleados
@app.route('/lista_empleados', methods=['GET', 'POST'])
def lista_empleados():
    try:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

        # Obtener término de búsqueda desde el formulario
        search_term = request.form.get('search_term', '').strip() if request.method == 'POST' else ''

        if search_term:
            # Consulta para buscar empleados
            query = '''
                SELECT * FROM tbl_empleados
                WHERE nombre_empleado LIKE %s OR apellido_empleado LIKE %s OR email_empleado LIKE %s
            '''
            params = ('%' + search_term + '%', '%' + search_term + '%', '%' + search_term + '%')
            cursor.execute(query, params)
        else:
            # Mostrar todos los empleados si no hay búsqueda
            cursor.execute('SELECT * FROM tbl_empleados')

        empleados = cursor.fetchall()

        # Reemplazar valores nulos con 'N/A'
        empleados_limpios = [
            {key: (value if value is not None else 'N/A') for key, value in empleado.items()}
            for empleado in empleados
        ]

        return render_template('lista_empleados.html', empleados=empleados_limpios, search_term=search_term)
    except Exception as e:
        flash(f'Ocurrió un error al cargar la lista de empleados: {e}', 'error')
        return redirect(url_for('home'))

# Ruta para ver detalle de empleado
@app.route('/detalle_empleado/<int:id_empleado>', methods=['GET'])
def detalle_empleado(id_empleado):
    try:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM tbl_empleados WHERE id_empleado = %s', (id_empleado,))
        empleado = cursor.fetchone()

        if not empleado:
            flash('Empleado no encontrado.', 'error')
            return redirect(url_for('lista_empleados'))

        return render_template('detalle_empleado.html', empleado=empleado)
    except Exception as e:
        flash(f'Ocurrió un error al cargar los detalles del empleado: {e}', 'error')
        return redirect(url_for('lista_empleados'))

    
# Ruta para actualizar los detalles del empleado
@app.route('/actualizar_empleado/<int:id_empleado>', methods=['GET', 'POST'])
def actualizar_empleado(id_empleado):
    try:
        # Obtener los detalles actuales del empleado
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM tbl_empleados WHERE id_empleado = %s', (id_empleado,))
        empleado = cursor.fetchone()

        if not empleado:
            flash('Empleado no encontrado.', 'error')
            return redirect(url_for('lista_empleados'))

        if request.method == 'POST':
            # Obtener los nuevos datos del formulario
            nombre_empleado = request.form.get('nombre_empleado', '').strip()
            apellido_empleado = request.form.get('apellido_empleado', '').strip()
            foto_empleado = request.files.get('foto_empleado')

            # Validación básica de datos
            if not nombre_empleado or not apellido_empleado:
                flash('Por favor, completa todos los campos obligatorios.', 'error')
                return redirect(request.url)

            # Manejo de la foto: si se carga una nueva, actualizarla
            foto_path = empleado['foto_empleado']  # Mantener la foto actual si no se carga una nueva
            if foto_empleado and foto_empleado.filename:
                if allowed_file(foto_empleado.filename):
                    # Asegurar un nombre seguro para el archivo
                    filename = secure_filename(foto_empleado.filename)
                    # Construir la ruta completa donde se guardará el archivo
                    save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    # Guardar el archivo en la carpeta correspondiente
                    foto_empleado.save(save_path)
                    # Actualizar el nombre del archivo para la base de datos
                    foto_path = filename
                else:
                    flash('¡Archivo no válido! Solo se permiten imágenes JPG, JPEG y PNG.', 'error')
                    return redirect(request.url)

            # Actualizar los datos del empleado en la base de datos
            cursor.execute(''' 
                UPDATE tbl_empleados 
                SET nombre_empleado = %s, apellido_empleado = %s, foto_empleado = %s
                WHERE id_empleado = %s
            ''', (nombre_empleado, apellido_empleado, foto_path, id_empleado))

            mysql.connection.commit()

            flash('¡Empleado actualizado con éxito!', 'success')
            return redirect(url_for('detalle_empleado', id_empleado=id_empleado))

        return render_template('actualizar_empleado.html', empleado=empleado)

    except Exception as e:
        flash(f'Ocurrió un error al actualizar el empleado: {e}', 'error')
        return redirect(url_for('lista_empleados'))


# Ruta para eliminar empleado
@app.route('/eliminar_empleado/<int:id_empleado>', methods=['POST'])
def eliminar_empleado(id_empleado):
    try:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        
        # Obtener la información del empleado, incluyendo la foto
        cursor.execute('SELECT foto_empleado FROM tbl_empleados WHERE id_empleado = %s', (id_empleado,))
        empleado = cursor.fetchone()

        if empleado:
            # Verificar si existe una foto asociada y eliminarla si está en el sistema de archivos
            foto_path = empleado['foto_empleado']
            if foto_path:
                full_path = os.path.join(app.config['UPLOAD_FOLDER'], foto_path)
                if os.path.exists(full_path):
                    os.remove(full_path)  # Eliminar archivo del sistema

            # Eliminar al empleado de la base de datos
            cursor.execute('DELETE FROM tbl_empleados WHERE id_empleado = %s', (id_empleado,))
            mysql.connection.commit()

            flash('¡Empleado eliminado con éxito!', 'success')
        else:
            flash('Empleado no encontrado.', 'error')

    except FileNotFoundError as fnfe:
        flash(f'Error al intentar eliminar el archivo de la foto: {fnfe}', 'error')
    except Exception as e:
        flash(f'Ocurrió un error al eliminar el empleado: {e}', 'error')
    
    return redirect(url_for('lista_empleados'))

# Ruta generar reporte en excel
@app.route('/generar_reporte', methods=['GET'])
def generar_reporte():
    try:
        # Obtener los datos de empleados desde la base de datos
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM tbl_empleados')
        empleados = cursor.fetchall()

        # Crear un archivo Excel en memoria
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('Empleados')

        # Agregar encabezados
        headers = ['ID', 'Nombre', 'Apellido', 'Sexo', 'Teléfono', 'Email', 'Profesión', 'Salario', 'Foto', 'Fecha de Ingreso']
        for col_num, header in enumerate(headers):
            worksheet.write(0, col_num, header)

        # Agregar datos de los empleados
        for row_num, empleado in enumerate(empleados, start=1):
            worksheet.write(row_num, 0, empleado['id_empleado'])
            worksheet.write(row_num, 1, empleado['nombre_empleado'])
            worksheet.write(row_num, 2, empleado['apellido_empleado'])

            # Convertir valor de sexo
            sexo_empleado = empleado.get('sexo_empleado')

            # Asegurarse de manejar tanto cadenas como enteros
            if str(sexo_empleado) == "1":
                sexo = "Hombre"
            elif str(sexo_empleado) == "2":
                sexo = "Mujer"
            else:
                sexo = "N/A"

            worksheet.write(row_num, 3, sexo)

            worksheet.write(row_num, 4, empleado['telefono_empleado'])
            worksheet.write(row_num, 5, empleado['email_empleado'])
            worksheet.write(row_num, 6, empleado['profesion_empleado'])
            worksheet.write(row_num, 7, empleado['salario_empleado'])
            worksheet.write(row_num, 8, empleado['foto_empleado'] if empleado['foto_empleado'] else 'N/A')

            # Agregar la fecha de ingreso, convirtiéndola a string
            fecha_registro = str(empleado.get('fecha_registro')) if empleado.get('fecha_registro') else "N/A"
            worksheet.write(row_num, 9, fecha_registro)

        # Cerrar el libro de Excel
        workbook.close()

        # Establecer el puntero al principio del archivo
        output.seek(0)

        # Enviar el archivo como respuesta para su descarga
        return send_file(
            output,
            as_attachment=True,
            download_name='reporte_empleados.xlsx',
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    except Exception as e:
        flash(f'Ocurrió un error al generar el reporte: {e}', 'error')
        return redirect(url_for('lista_empleados'))

# Ruta para mostrar lista de usuarios
@app.route('/lista_usuarios', methods=['GET', 'POST'])
def lista_usuarios():
    try:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

        # Obtener término de búsqueda desde los parámetros GET o POST
        search_term = request.args.get('search_term', '').strip() if request.method == 'GET' else request.form.get('search_term', '').strip()

        # Si hay un término de búsqueda, realizar la consulta de búsqueda
        if search_term:
            query = '''
                SELECT id, name_surname, email_user, created_user FROM users
                WHERE name_surname LIKE %s OR email_user LIKE %s
            '''
            params = ('%' + search_term + '%', '%' + search_term + '%')
            cursor.execute(query, params)
        else:
            # Si no hay término de búsqueda, mostrar todos los usuarios
            cursor.execute('SELECT id, name_surname, email_user, created_user FROM users')

        usuarios = cursor.fetchall()

        # Reemplazar valores nulos con 'N/A' en los resultados
        usuarios_limpios = [
            {key: (value if value is not None else 'N/A') for key, value in usuario.items()}
            for usuario in usuarios
        ]

        # Pasar los usuarios limpios al template
        return render_template('lista_usuarios.html', usuarios=usuarios_limpios, search_term=search_term)
    
    except Exception as e:
        flash(f'Ocurrió un error al cargar la lista de usuarios: {e}', 'error')
        return redirect(url_for('home'))

# Ruta eliminar usuarios
@app.route('/eliminar_usuario/<int:user_id>', methods=['POST'])
def eliminar_usuario(user_id):
    try:
        # Establecer conexión a la base de datos
        cursor = mysql.connection.cursor()

        # Eliminar el usuario de la base de datos por ID
        query = "DELETE FROM users WHERE id = %s"
        cursor.execute(query, (user_id,))

        # Confirmar la eliminación
        mysql.connection.commit()

        # Flash message de éxito
        flash('Usuario eliminado correctamente.', 'success')

        return redirect(url_for('lista_usuarios'))

    except Exception as e:
        # Si ocurre un error, mostrar un mensaje de error
        flash(f'Ocurrió un error al eliminar el usuario: {e}', 'error')
        return redirect(url_for('lista_usuarios'))

# Ruta para ver el perfil y cambiar la contraseña
@app.route('/perfil', methods=['GET', 'POST'])
def perfil():
    if 'id' not in session:
        flash('Por favor, inicia sesión para acceder a tu perfil.', 'warning')
        return redirect(url_for('login'))

    try:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM users WHERE id = %s', (session['id'],))
        user = cursor.fetchone()

        if not user:
            flash('Usuario no encontrado.', 'danger')
            return redirect(url_for('logout'))

        if request.method == 'POST':
            name_surname = request.form.get('name_surname', '').strip()
            current_password = request.form.get('clave_actual', '').strip()
            new_password = request.form.get('nueva_clave', '').strip()
            confirm_password = request.form.get('repetir_clave', '').strip()

            # Imprimir por consola la contraseña actual ingresada y la almacenada (texto plano)
            print(f"Contraseña almacenada (texto plano): {user['pass_user']}")
            print(f"Contraseña actual ingresada: {current_password}")

            # Verificamos que los campos requeridos estén completos
            if not name_surname or not current_password:
                flash('El nombre y la contraseña actual son obligatorios.', 'danger')
                return redirect(url_for('perfil'))

            # Comparar las contraseñas como texto plano (no recomendado para producción)
            if user['pass_user'] != current_password:
                flash('La contraseña actual es incorrecta.', 'danger')
                return redirect(url_for('perfil'))

            # Si no se proporcionan nuevas contraseñas, solo actualizamos el nombre
            if not new_password and not confirm_password:
                cursor.execute(
                    '''
                    UPDATE users
                    SET name_surname = %s
                    WHERE id = %s
                    ''',
                    (name_surname, session['id']),
                )
                mysql.connection.commit()
                flash('Tu nombre ha sido actualizado exitosamente.', 'success')
                return redirect(url_for('perfil'))

            # Verificamos que las nuevas contraseñas coincidan
            if new_password != confirm_password:
                flash('Las contraseñas nuevas no coinciden.', 'danger')
                return redirect(url_for('perfil'))

            # Actualizamos la contraseña en texto plano (esto no es seguro)
            cursor.execute(
                '''
                UPDATE users
                SET name_surname = %s, pass_user = %s
                WHERE id = %s
                ''',
                (name_surname, new_password, session['id']),
            )
            mysql.connection.commit()

            flash('Tu perfil ha sido actualizado exitosamente.', 'success')
            return redirect(url_for('perfil'))

        return render_template('perfil_usuario.html', info_perfil_session=user)

    except Exception as e:
        flash(f'Ocurrió un error: {e}', 'danger')
        return redirect(url_for('perfil'))


# Ruta para cerrar sesión
@app.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('name_surname', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
