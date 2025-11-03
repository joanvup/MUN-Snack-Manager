from app import db
from flask_login import UserMixin
from datetime import datetime

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='operador') # roles: 'admin', 'operador'

class Participante(db.Model):
    id_participante = db.Column(db.Integer, primary_key=True)
    nombre_participante = db.Column(db.String(150), nullable=False)
    saldo_merienda = db.Column(db.Integer, nullable=False)
    foto_participante = db.Column(db.String(100), nullable=True)

    committe_id = db.Column(db.Integer, db.ForeignKey('committe.id_committe'), nullable=False)
    pais_id = db.Column(db.Integer, db.ForeignKey('pais.id_pais'), nullable=False)
    institucion_id = db.Column(db.Integer, db.ForeignKey('institucion_educativa.id_institucion'), nullable=False)

    committe = db.relationship('Committe', backref=db.backref('participantes', lazy=True))
    pais = db.relationship('Pais', backref=db.backref('participantes', lazy=True))
    institucion = db.relationship('InstitucionEducativa', backref=db.backref('participantes', lazy=True))

class Committe(db.Model):
    id_committe = db.Column(db.Integer, primary_key=True)
    nombre_committe = db.Column(db.String(100), unique=True, nullable=False)
    logo_committe = db.Column(db.String(100), nullable=True)

class Pais(db.Model):
    id_pais = db.Column(db.Integer, primary_key=True)
    nombre_pais = db.Column(db.String(100), unique=True, nullable=False)
    # CAMBIO: Almacenaremos el código ISO de 2 letras (ej: "co", "us")
    country_code = db.Column(db.String(10), nullable=True) 

class InstitucionEducativa(db.Model):
    id_institucion = db.Column(db.Integer, primary_key=True)
    nombre_institucion = db.Column(db.String(150), unique=True, nullable=False)
    logo_institucion = db.Column(db.String(100), nullable=True)

class Configuracion(db.Model):
    id_config = db.Column(db.Integer, primary_key=True)
    nombre_evento = db.Column(db.String(150), nullable=False)
    logo_evento = db.Column(db.String(100), nullable=True)
    fechas_evento = db.Column(db.String(150), nullable=False)
    meriendas_totales = db.Column(db.Integer, default=6, nullable=False)
    cooldown_minutos = db.Column(db.Integer, default=60, nullable=False)

class Registro(db.Model):
    id_registro = db.Column(db.Integer, primary_key=True)
    fecha_hora = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    id_participante = db.Column(db.Integer, db.ForeignKey('participante.id_participante'), nullable=False)
    operador_responsable_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    participante = db.relationship('Participante', backref=db.backref('registros', lazy=True))
    operador = db.relationship('User', backref=db.backref('registros_realizados', lazy=True))