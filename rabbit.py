import pika
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests

# Configura la conexión SMTP para el correo electrónico
email_address = 'whitehokst@gmail.com'
password = 'pzjw txjm lvdg ivwj'
smtp_server = 'smtp.gmail.com'
smtp_port = 587

# URL de la API para obtener el stock de productos
api_url = 'http://192.168.22.24:5000/productos_stock'

def obtenerStockdeProductos():
    try:
        response = requests.get(api_url)
        if response.status_code == 200:
            stock_actual = int(response.json()['producto_stock'])
            return stock_actual
        else:
            print(f" [!] Error al obtener el stock: Código de respuesta {response.status_code}")
    except requests.RequestException as e:
        print(f" [!] Error al obtener el stock: {str(e)}")
    return None

def enviarCorreo(destinatario, asunto, mensaje):
    msg = MIMEMultipart()
    msg['From'] = email_address
    msg['To'] = destinatario
    msg['Subject'] = asunto

    body = MIMEText(mensaje, 'plain')
    msg.attach(body)

    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(email_address, password)
        server.sendmail(email_address, destinatario, msg.as_string())
        server.quit()
        print(f" [x] Correo enviado a {destinatario}: {mensaje}")
    except smtplib.SMTPAuthenticationError:
        print(" [!] Error: Autenticación SMTP fallida. Verifica la contraseña del correo.")
    except smtplib.SMTPException as e:
        print(f" [!] Error al enviar el correo: {str(e)}")

def callback(ch, method, properties, body):
    mensaje = body.decode('utf-8')
    productos_stock = obtenerStockdeProductos()
    if productos_stock is not None:
        if productos_stock <= 20:
            destinatario = '200300581@ucaribe.edu.mx'
            asunto = "Alerta: Stock de productos se agota"
            enviarCorreo(destinatario, asunto, mensaje)
            print(f" [x] Mensaje: {mensaje}, Stock de productos actual: {productos_stock}")
    else:
        print(" [!] No se pudo obtener el stock de productos. Verifica la conexión a la API.")

credencial = pika.PlainCredentials('RedTheMaster', 'Windfall80')
connection = pika.BlockingConnection(pika.ConnectionParameters(host='192.168.22.24',port='5672', credentials=credencial))
connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()
channel.queue_declare(queue='notificaciones', durable=True)
channel.basic_consume(queue='notificaciones', on_message_callback=callback, auto_ack=True)

print('Esperando notificaciones. Para salir, presiona CTRL+C')
channel.start_consuming()