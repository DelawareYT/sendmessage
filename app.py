from flask import Flask, request, jsonify, render_template
import mysql.connector
from datetime import datetime
import json

app = Flask(__name__)

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

@app.route('/')
def index():
    return render_template('index.html')

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
            SELECT tm.template_id AS id, tm.mensaje AS mensaje, d.nombre AS departamento
            FROM template_mensajes tm
            JOIN departamentos d ON tm.departamento_id = d.id
            WHERE tm.lengua = %s AND tm.departamento_id = %s AND tm.activo = true
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
@app.route('/api/templates/<int:departamento_id>', methods=['GET'])
def get_templates(departamento_id):
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT id, nombre, codigo, mensaje_es, mensaje_en 
            FROM templates 
            WHERE departamento_id = %s AND activo = true
        """, (departamento_id,))
        templates = cursor.fetchall()
        return jsonify(templates)
    except Exception as e:
        print(f"Error en get_templates: {str(e)}")
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
        ip_address = request.remote_addr
        
        message_data = {
            'language': data['language'],
            'departamento_id': data['departamento_id'],  # Agregar departamento_id
            'template_id': data['template_id'],
            'phoneNumber': data['phoneNumber'],
            'message': data['message'],
            'ip': ip_address,
            'timestamp': datetime.now().isoformat()
        }
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = '''
            INSERT INTO mensajes 
            (idioma, departamento_id, template_id, numero_destino, mensaje, ip_origen, fecha_envio, json_data)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        '''
        
        values = (
            data['language'],
            data['departamento_id'],  # Usar data['departamento_id']
            data['template_id'],
            data['phoneNumber'],
            data['message'],
            ip_address,
            datetime.now(),
            json.dumps(message_data)
        )
        
        cursor.execute(query, values)
        conn.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Mensaje guardado exitosamente',
            'data': message_data
        }), 200
        
    except Exception as e:
        print(f"Error en send_message: {str(e)}")
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

    


    
