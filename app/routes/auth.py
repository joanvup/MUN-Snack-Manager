from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app import db, bcrypt
from app.models.models import User

auth_bp = Blueprint('auth', __name__)
# --- RUTA RAÍZ / ÍNDICE ---
@auth_bp.route('/')
@login_required
def index():
    """
    Redirige al usuario logueado a su página principal según su rol.
    El decorador @login_required se encarga de enviar a los usuarios
    no autenticados a la página de login.
    """
    if current_user.role == 'admin':
        return redirect(url_for('admin.dashboard'))
    else:
        return redirect(url_for('operador.escaner'))
    
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        if current_user.role == 'admin':
            return redirect(url_for('admin.dashboard'))
        else:
            return redirect(url_for('operador.escaner'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()

        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            flash('Inicio de sesión exitoso.', 'success')
            if user.role == 'admin':
                return redirect(url_for('admin.dashboard'))
            else:
                return redirect(url_for('operador.escaner'))
        else:
            flash('Credenciales incorrectas. Por favor, inténtelo de nuevo.', 'danger')

    return render_template('auth/login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Ha cerrado la sesión.', 'info')
    return redirect(url_for('auth.login'))