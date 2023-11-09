from flask import Flask, jsonify, make_response
from flask_socketio import SocketIO
import pika
from flask_cors import CORS, cross_origin
import json
stock_actual = 100

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'mysecretkey'
    return app

app = create_app()
socketio = SocketIO(app, cors_allowed_origins="http://localhost:3000")
CORS(app, resources={r"/productos_stock": {"origins": "http://localhost:3000"}})

# Configurar encabezados para deshabilitar el almacenamiento en caché
@app.after_request
def add_header(response):
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

# Configura la conexión a RabbitMQ para publicar mensajes
rabbit_connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
rabbit_channel = rabbit_connection.channel()
rabbit_channel.queue_declare(queue='notificaciones', durable=True)

@app.route('/productos_stock', methods=['GET'])
@cross_origin(origin="http://localhost:3000")
def obtenerProductos():
    stock_actual = obtenerStockdeProductos() 
    if stock_actual is not None:
        if stock_actual <= 20:
            # Publica un mensaje en la cola si el stock es igual o menor a 20
            mensaje = {'mensaje': f"Alerta: Stock de productos es bajo ({stock_actual})"}
            rabbit_channel.basic_publish(exchange='', routing_key='notificaciones', body=json.dumps(mensaje))
            socketio.emit('message',mensaje)
        response = jsonify({'producto_stock': stock_actual})
        return make_response(response)
    else:
        return 'No se pudo obtener el stock de productos', 500

def obtenerStockdeProductos():
    global stock_actual
    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
        channel = connection.channel()
        channel.queue_declare(queue='producto', durable=True)

        # Consumir los mensajes de la cola y actualizar el stock
        method_frame, header_frame, body = channel.basic_get(queue='producto')
        while method_frame:
            mensaje = int(body.decode('utf-8'))
            stock_actual = mensaje
            method_frame, header_frame, body = channel.basic_get(queue='producto')
            #print(f"Stock actualizado: {stock_actual}")
        return stock_actual
    except Exception as e:
        print(f"Error al obtener el stock: {str(e)}")
        return None 
    
@socketio.on('message')
def handle_message(message):
    print(f'Mensaje de Socket.IO: {message}')

@app.route('/actualizar_stock', methods=['POST'])
@cross_origin(origin="http://localhost:3000")
def actualizar_stock():
    nuevo_stock = obtenerStockdeProductos()
    notificacion = obtenerProductos()
    if notificacion:
        notificacion = notificacion.json  # Convierte el objeto Response a un diccionario
    #print(notificacion)
    return jsonify({'success': True, 'nuevo_stock': nuevo_stock, 'notificacion': notificacion})
    

if __name__ == '__main__':
    socketio.run(app,host='192.168.213.87', port=5000,  allow_unsafe_werkzeug=True)