import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from dotenv import load_dotenv
from datetime import datetime
import pytz # <-- Importar pytz

load_dotenv()  # <-- Cargar las variables del archivo .env

db = SQLAlchemy()
bcrypt = Bcrypt()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = "Por favor, inicie sesión para acceder a esta página."
login_manager.login_message_category = "info"

# --- INICIO: FILTRO DE ZONA HORARIA PERSONALIZADO ---
def format_to_local_time(utc_dt):
    """Filtro de Jinja2 para convertir una fecha UTC a la hora local de Bogotá."""
    if not utc_dt:
        return ""
    # Define las zonas horarias
    utc_zone = pytz.timezone('UTC')
    local_zone = pytz.timezone('America/Bogota')
    
    # Convierte la fecha naive de la DB a una fecha "aware" en UTC
    aware_utc_dt = utc_zone.localize(utc_dt)
    
    # Convierte a la zona horaria local
    local_dt = aware_utc_dt.astimezone(local_zone)
    
    # Formatea la fecha para mostrarla
    return local_dt.strftime('%Y-%m-%d %I:%M:%S %p') # Formato 12 horas con AM/PM
# --- FIN: FILTRO ---


def create_app():
    app = Flask(__name__)
    # --- CONFIGURACIÓN ACTUALIZADA ---
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'a_very_secret_key_that_should_be_changed')
    
    # Construir la URI de la base de datos desde las variables de entorno
    db_user = os.environ.get('DB_USER')
    db_password = os.environ.get('DB_PASSWORD')
    db_host = os.environ.get('DB_HOST')
    db_name = os.environ.get('DB_NAME')

    # Cadena de conexión para MySQL con PyMySQL
    # El formato es: 'mysql+pymysql://<user>:<password>@<host>/<dbname>?charset=utf8mb4'
    app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+pymysql://{db_user}:{db_password}@{db_host}/{db_name}?charset=utf8mb4"
    
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    # Configuración de carpetas de subida
    base_upload_path = os.path.join(app.root_path, 'static/uploads')
    app.config['UPLOAD_FOLDER'] = base_upload_path
    app.config['PHOTOS_FOLDER'] = os.path.join(base_upload_path, 'fotos')
    app.config['COMMITTE_LOGOS_FOLDER'] = os.path.join(base_upload_path, 'logos_committe')
    app.config['PAIS_LOGOS_FOLDER'] = os.path.join(base_upload_path, 'iconos_bandera')
    app.config['INSTITUCION_LOGOS_FOLDER'] = os.path.join(base_upload_path, 'logos_institucion')
    app.config['EVENTO_LOGO_FOLDER'] = os.path.join(base_upload_path, 'logos_evento')
    # Crear carpetas si no existen
    for folder in ['fotos', 'logos_committe', 'iconos_bandera', 'logos_institucion', 'logos_evento']:
        os.makedirs(os.path.join(base_upload_path, folder), exist_ok=True)


    # Configuración de carpetas
    app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static/uploads')
    app.config['PHOTOS_FOLDER'] = os.path.join(app.config['UPLOAD_FOLDER'], 'fotos')

     # --- REGISTRAR EL FILTRO EN LA APP ---
    app.jinja_env.filters['to_local_time'] = format_to_local_time

    # Crear carpetas si no existen
    for folder in ['uploads', 'fotos', 'logos_committe', 'logos_institucion', 'logos_evento', 'iconos_bandera']:
        os.makedirs(os.path.join(app.root_path, 'static/uploads', folder), exist_ok=True)

    # Inicializar extensiones
    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)

    # Registrar Blueprints (rutas)
    from .routes.auth import auth_bp
    from .routes.admin import admin_bp
    from .routes.operador import operador_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(operador_bp, url_prefix='/operador')

    # Registrar comando para inicializar la BD
    from .utils import init_db_command
    app.cli.add_command(init_db_command)

    # Contexto para que el modelo User esté disponible
    from .models.models import User
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    return app