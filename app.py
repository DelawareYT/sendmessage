from flask import Flask, request, jsonify, render_template, redirect, url_for, session
import mysql.connector
from datetime import datetime
import json
import bcrypt 

app = Flask(__name__)
app.secret_key = 'clave'
# Configuración de la base de datos
db_config = {
    'host': 'localhost',
    'user': 'root',  
    'password': 'windows7718',  
    'database': 'gestion',
    'charset': 'utf8mb4',
    'collation': 'utf8mb4_general_ci',
    'use_unicode': True
}

def get_db_connection():
    try:
        conn = mysql.connector.connect(**db_config)
        conn.set_charset_collation('utf8mb4', 'utf8mb4_general_ci')
        return conn
    except mysql.connector.Error as err:
        print(f"Error de conexión a la base de datos: {err}")
        raise


#AUTENTIFICACION
# Middleware para proteger rutas
@app.before_request
def proteger_rutas():
    # Define las rutas que no necesitan autenticación
    rutas_publicas = ['/login', '/logout']  # Añade otras rutas públicas si es necesario
    
    # Permitir acceso a archivos estáticos
    if request.path.startswith('/static/'):
        return  # Permitir el acceso sin restricciones

    # Bloquear acceso a rutas privadas si no hay sesión activa
    if not session.get('logged_in') and request.path not in rutas_publicas:
        return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        conn = None
        cursor = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)

            # Verificar si el usuario existe
            cursor.execute("SELECT * FROM usuarios WHERE username = %s", (username,))
            user = cursor.fetchone()

            if user and bcrypt.checkpw(password.encode('utf-8'), user['password_hash'].encode('utf-8')):
                session['logged_in'] = True
                session['username'] = username
                return redirect(url_for('index'))
            else:
                # Renderizar la página de login con un mensaje de error
                return render_template('login.html', error="Credenciales incorrectas")

        except Exception as e:
            print(f"Error en login: {str(e)}")
            return render_template('login.html', error="Error interno del servidor")
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    # Si no es POST, solo renderizar el formulario de login
    return render_template('login.html')
@app.route('/logout')
def logout():
    # Elimina la sesión del usuario
    session.clear()
    # Redirige al formulario de login
    return redirect(url_for('login'))

@app.route('/')
def index():
    return render_template('index.html')
##Register
@app.route('/register/usuarionuevo', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if not username or not password or not confirm_password:
            return "Todos los campos son obligatorios", 400
        
        if password != confirm_password:
            return "Las contraseñas no coinciden", 400

        conn = None
        cursor = None
        try:
            # Encriptar la contraseña
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Insertar el nuevo usuario en la base de datos
            query = "INSERT INTO usuarios (username, password_hash) VALUES (%s, %s)"
            cursor.execute(query, (username, hashed_password.decode('utf-8')))
            conn.commit()

            return redirect(url_for('login'))
        except mysql.connector.IntegrityError:
            return "El nombre de usuario ya existe", 400
        except Exception as e:
            print(f"Error en register: {str(e)}")
            return "Error interno del servidor", 500
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    return render_template('register.html')


@app.route('/api/departamentos', methods=['GET'])
def get_departamentos():
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, nombre, codigo FROM departamentos WHERE activo = true")
        departamentos = cursor.fetchall()
        return jsonify(departamentos)
    except Exception as e:
        print(f"Error en get_departamentos: {str(e)}")
        return jsonify({'error': str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route('/api/templates', methods=['GET'])
def get_templates_by_idioma_departamento():
    idioma = request.args.get('idioma')
    departamento_id = request.args.get('departamento_id')

    if not idioma or not departamento_id:
        return jsonify({'error': 'Idioma y departamento son requeridos'}), 400

    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT 
                tm.template_id, 
                tm.nombre AS template_nombre, 
                tm.mensaje,
                d.nombre AS departamento,
                tm.activo,
                tm.campos_variables  -- Aquí obtenemos los campos variables
            FROM 
                template_mensajes tm
            JOIN 
                departamentos d ON tm.departamento_id = d.id
            WHERE 
                tm.lengua = %s 
                AND tm.departamento_id = %s 
                AND tm.activo = true
        """, (idioma, departamento_id))

        templates = cursor.fetchall()
        return jsonify(templates)
    except Exception as e:
        print(f"Error en get_templates_by_idioma_departamento: {str(e)}")
        return jsonify({'error': str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
            
@app.route('/api/send-message', methods=['POST'])
def send_message():
    conn = None
    cursor = None
    try:
        data = request.json

        # Validar que todos los campos necesarios estén presentes
        required_fields = ['idioma', 'departamento_id', 'template_id', 'phoneNumber', 'message']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'status': 'error',
                    'message': f'Campo faltante: {field}'
                }), 400

        ip_address = request.remote_addr

        # Obtener el usuario desde la sesión
        usuario = session.get('username')
        if not usuario:
            return jsonify({
                'status': 'error',
                'message': 'Usuario no autenticado'
            }), 401  # Error si no hay un usuario autenticado

        message_data = {
            'language': data['idioma'],
            'departamento_id': data['departamento_id'],
            'template_id': data['template_id'],
            'phoneNumber': data['phoneNumber'],
            'message': data['message'],
            'ip': ip_address,
            'timestamp': datetime.now().isoformat(),
            'campos': data.get('campos', {}),
            'usuario': usuario  # Incluir el usuario que envió el mensaje
        }

        print("Datos a guardar en la base de datos:", message_data)

        conn = get_db_connection()
        cursor = conn.cursor()

        query = '''
            INSERT INTO mensajes 
            (idioma, departamento_id, template_id, numero_destino, mensaje, ip_origen, fecha_envio, json_data, usuario)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        '''

        values = (
            message_data['language'],
            message_data['departamento_id'],
            message_data['template_id'],
            message_data['phoneNumber'],
            message_data['message'],
            ip_address,
            datetime.now(),
            json.dumps(message_data),
            message_data['usuario']  # Guardar el nombre de usuario en la base de datos
        )

        cursor.execute(query, values)
        conn.commit()

        return jsonify({
            'status': 'success',
            'message': 'Mensaje guardado exitosamente',
            'data': message_data
        }), 200

    except Exception as e:
        print(f"Error en send_message: {str(e)}")  # Imprimir el error para depuración
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route('/api/idiomas', methods=['GET'])
def get_idiomas():
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT codigo, nombre FROM idiomas WHERE activo = true")
        idiomas = cursor.fetchall()
        return jsonify(idiomas)
    except Exception as e:
        print(f"Error en get_idiomas: {str(e)}")
        return jsonify({'error': str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
@app.route('/api/historial-mensajes', methods=['GET'])
def get_historial_mensajes():
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Consulta modificada para incluir el 'usuario'
        query = '''
            SELECT 
                m.id, 
                m.idioma, 
                m.departamento_id, 
                m.template_id, 
                m.numero_destino, 
                m.mensaje, 
                m.ip_origen, 
                m.fecha_envio, 
                IFNULL(tm.nombre, 'Sin Template') AS template_nombre,
                m.usuario  -- Añadir la columna usuario
            FROM mensajes m
            LEFT JOIN template_mensajes tm ON m.template_id = tm.template_id
            ORDER BY m.fecha_envio DESC
            LIMIT 20
        '''
        
        cursor.execute(query)
        mensajes = cursor.fetchall()
        
        # Asegúrate de que los mensajes tienen la columna 'usuario'
       
        
        return jsonify(mensajes), 200
    except Exception as e:
        print(f"Error en get_historial_mensajes: {str(e)}")
        return jsonify({'error': str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
            
def init_db():
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Asegurarnos que la base de datos use la codificación correcta
        cursor.execute("SET NAMES utf8mb4")
        cursor.execute("SET CHARACTER SET utf8mb4")
        cursor.execute("SET character_set_connection=utf8mb4")
        
        # Crear tabla mensajes si no existe
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS mensajes (
                id INT AUTO_INCREMENT PRIMARY KEY,
                idioma VARCHAR(2) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci,
                departamento_id INT,
                template_id INT,
                numero_destino VARCHAR(15),
                mensaje TEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci,
                ip_origen VARCHAR(45),
                fecha_envio DATETIME,
                json_data JSON
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
        ''')
        
        # Crear tabla departamentos si no existe
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS departamentos (
                id INT AUTO_INCREMENT PRIMARY KEY,
                nombre VARCHAR(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
                codigo VARCHAR(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
                activo BOOLEAN DEFAULT true
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
        ''')
        
        # Crear tabla templates si no existe
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS templates (
                id INT AUTO_INCREMENT PRIMARY KEY,
                departamento_id INT NOT NULL,
                nombre VARCHAR(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
                codigo VARCHAR(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
                mensaje_es TEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
                mensaje_en TEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
                activo BOOLEAN DEFAULT true,
                FOREIGN KEY (departamento_id) REFERENCES departamentos(id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
        ''')
        
        conn.commit()
        
        # Insertar datos iniciales en departamentos si está vacía
        cursor.execute("SELECT COUNT(*) FROM departamentos")
        if cursor.fetchone()[0] == 0:
            cursor.execute('''
                INSERT INTO departamentos (nombre, codigo) VALUES 
                ('Contabilidad', 'CONT'),
                ('Tienda', 'STORE'),
                ('Call Center', 'CALL')
            ''')
            
            conn.commit()
            
        # Insertar datos iniciales en templates si está vacía
        cursor.execute("SELECT COUNT(*) FROM templates")
        if cursor.fetchone()[0] == 0:
            cursor.execute('''
                INSERT INTO templates (departamento_id, nombre, codigo, mensaje_es, mensaje_en) VALUES
                (1, 'Factura pendiente', 'INVOICE_DUE', 'Estimado cliente, tiene una factura pendiente.', 'Dear customer, you have a pending invoice.'),
                (1, 'Pago recibido', 'PAYMENT_RECEIVED', 'Confirmamos la recepción de su pago.', 'We confirm the reception of your payment.'),
                (2, 'Orden lista', 'ORDER_READY', 'Su pedido está listo para recoger.', 'Your order is ready for pickup.'),
                (2, 'Envío confirmado', 'SHIPPING_CONF', 'Su pedido ha sido enviado.', 'Your order has been shipped.'),
                (3, 'Ticket creado', 'TICKET_CREATED', 'Su ticket de soporte ha sido creado.', 'Your support ticket has been created.'),
                (3, 'Seguimiento', 'FOLLOWUP', 'Seguimiento a su caso anterior.', 'Following up on your previous case.')
            ''')
            
            conn.commit()
            
    except Exception as e:
        print(f"Error en init_db: {str(e)}")
        raise
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

if __name__ == '__main__':
    init_db()  
    app.run(debug=True, host="0.0.0.0", port=8000)
    
    


    
