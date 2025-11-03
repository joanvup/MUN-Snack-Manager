import click
from flask.cli import with_appcontext
from . import db, bcrypt
from .models.models import User, Configuracion
import qrcode
from PIL import Image
import io
import json

@click.command(name='init-db')
@with_appcontext
def init_db_command():
    """Limpia los datos existentes y crea nuevas tablas y datos iniciales."""
    db.drop_all()
    db.create_all()

    # Crear usuario administrador por defecto
    hashed_password = bcrypt.generate_password_hash('admin123').decode('utf-8')
    admin_user = User(
        username='admin',
        password=hashed_password,
        role='admin'
    )
    db.session.add(admin_user)

    # Crear configuración inicial del evento
    default_config = Configuracion(
        nombre_evento="Mi Evento MUN",
        fechas_evento="Del 1 al 4 de Diciembre de 2025",
        meriendas_totales=6
    )
    db.session.add(default_config)

    db.session.commit()
    click.echo('Base de datos inicializada con usuario admin (pass: admin123) y configuración por defecto.')

# --- NUEVA FUNCIÓN PARA GENERAR QR ---
def generate_qr_code_img(data_dict: dict):
    """
    Genera una imagen de código QR a partir de un diccionario de datos.
    
    Args:
        data_dict (dict): Diccionario con la información del participante.

    Returns:
        io.BytesIO: Un objeto de bytes en memoria que contiene la imagen PNG del QR.
    """
    # --- MÉTODO 1: Incluir todos los datos (como solicitaste) ---
    # Convertimos el diccionario a una cadena de texto en formato JSON.
    qr_data = json.dumps(data_dict, ensure_ascii=False)
    
    # --- MÉTODO 2: Incluir solo el ID (Recomendado para la lógica de escaneo actual) ---
    # Si prefieres usar solo el ID, comenta la línea anterior y descomenta la siguiente:
    # qr_data = str(data_dict.get("id"))

    # Configuración del QR
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M, # Tolerancia a errores media
        box_size=10, # Tamaño de cada "caja" del QR
        border=1,    # Margen estrecho (1 caja de borde)
    )
    
    qr.add_data(qr_data)
    qr.make(fit=True)

    # Crear la imagen desde el objeto QR
    img = qr.make_image(fill_color="black", back_color="white")

    # --- Ajuste de tamaño a 4x4 cm (aprox. 472x472 píxeles a 300 DPI) ---
    # 1 pulgada = 2.54 cm. DPI = Puntos por Pulgada.
    # Pixeles = (cm / 2.54) * DPI
    # (4 cm / 2.54) * 300 DPI ≈ 472.44 pixeles
    target_size_px = 472
    img = img.resize((target_size_px, target_size_px), Image.Resampling.NEAREST)

    # Guardar la imagen en un buffer de memoria en lugar de un archivo físico
    img_buffer = io.BytesIO()
    img.save(img_buffer, format='PNG')
    img_buffer.seek(0) # Rebobinar el buffer para que pueda ser leído

    return img_buffer