from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, send_from_directory
from flask_login import login_required, current_user
from functools import wraps
from werkzeug.utils import secure_filename
import os
import pandas as pd
import pycountry

from app import db
from app.models.models import Participante, Committe, Pais, InstitucionEducativa, Configuracion, Registro, User

from app.utils import generate_qr_code_img
import io
import zipfile
from flask import send_file
from app import bcrypt

from datetime import datetime, time

# Creación del Blueprint para las rutas de administración
admin_bp = Blueprint('admin', __name__)

# --- Funciones Auxiliares (Decoradores y Utilidades) ---

def admin_required(f):
    """
    Decorador para asegurar que solo los usuarios con el rol 'admin' puedan acceder a una ruta.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('No tienes permiso para acceder a esta página.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

def save_file(file, subfolder):
    """
    Guarda un archivo en una subcarpeta específica dentro de la carpeta de uploads.
    Devuelve el nombre del archivo guardado o None si no hay archivo.
    """
    if not file or file.filename == '':
        return None
    
    filename = secure_filename(file.filename)
    upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], subfolder)
    
    # Asegura que el directorio de destino exista
    os.makedirs(upload_path, exist_ok=True)
    
    file.save(os.path.join(upload_path, filename))
    return filename

# --- Rutas del Panel de Administración ---

@admin_bp.route('/')
@login_required
# @admin_required
def dashboard():
    """Página principal del dashboard del administrador."""
    total_participantes = Participante.query.count()
    meriendas_entregadas = Registro.query.count()
    config = Configuracion.query.first()
    return render_template('admin/dashboard.html', total_participantes=total_participantes, meriendas_entregadas=meriendas_entregadas, config=config)

@admin_bp.route('/configuracion', methods=['GET', 'POST'])
@login_required
@admin_required
def configuracion():
    """Página para configurar los detalles del evento."""
    config = Configuracion.query.first()
    if request.method == 'POST':
        config.nombre_evento = request.form.get('nombre_evento')
        config.fechas_evento = request.form.get('fechas_evento')
        config.meriendas_totales = int(request.form.get('meriendas_totales'))
        config.cooldown_minutos = int(request.form.get('cooldown_minutos'))
        
        if 'logo_evento' in request.files:
            logo_file = request.files['logo_evento']
            if logo_file.filename != '':
                logo_filename = save_file(logo_file, 'logos_evento')
                config.logo_evento = logo_filename
                
        db.session.commit()
        flash('Configuración guardada con éxito.', 'success')
        return redirect(url_for('admin.configuracion'))
    return render_template('admin/configuracion.html', config=config)

# --- Rutas CRUD para Participantes ---

@admin_bp.route('/participantes')
@login_required
@admin_required
def participantes():
    """Muestra y gestiona los participantes."""
    lista_participantes = Participante.query.all()
    committes = Committe.query.all()
    paises = Pais.query.all()
    instituciones = InstitucionEducativa.query.all()
    config = Configuracion.query.first()
    return render_template('admin/participantes.html', participantes=lista_participantes, committes=committes, paises=paises, instituciones=instituciones, config=config)

@admin_bp.route('/participante/add', methods=['POST'])
@login_required
@admin_required
def add_participante():
    """Añade un nuevo participante a la base de datos."""
    nombre = request.form.get('nombre_participante')
    committe_id = request.form.get('committe_id')
    pais_id = request.form.get('pais_id')
    institucion_id = request.form.get('institucion_id')
    config = Configuracion.query.first()

    nuevo_participante = Participante(
        nombre_participante=nombre,
        committe_id=committe_id,
        pais_id=pais_id,
        institucion_id=institucion_id,
        saldo_merienda=config.meriendas_totales if config else 6
    )
    
    foto_file = request.files.get('foto_participante')
    if foto_file and foto_file.filename != '':
        # Guardar primero para obtener el ID
        db.session.add(nuevo_participante)
        db.session.flush()  # Asigna el ID sin hacer commit
        
        # Renombrar la foto con el ID del participante
        _, file_extension = os.path.splitext(secure_filename(foto_file.filename))
        new_filename = f"{nuevo_participante.id_participante}{file_extension}"
        
        upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'fotos')
        os.makedirs(upload_path, exist_ok=True)
        foto_file.save(os.path.join(upload_path, new_filename))
        
        nuevo_participante.foto_participante = new_filename
    else:
        db.session.add(nuevo_participante)
        
    db.session.commit()
    flash('Participante añadido con éxito.', 'success')
    return redirect(url_for('admin.participantes'))

@admin_bp.route('/participante/delete/<int:id>', methods=['POST'])
@login_required
@admin_required
def delete_participante(id):
    """Elimina un participante de la base de datos."""
    participante = Participante.query.get_or_404(id)
    # Opcional: eliminar también el archivo de foto del servidor
    if participante.foto_participante:
        try:
            os.remove(os.path.join(current_app.config['UPLOAD_FOLDER'], 'fotos', participante.foto_participante))
        except OSError as e:
            print(f"Error eliminando archivo de foto: {e}")

    db.session.delete(participante)
    db.session.commit()
    flash('Participante eliminado correctamente.', 'success')
    return redirect(url_for('admin.participantes'))

# --- Rutas CRUD para Committes ---

@admin_bp.route('/committes', methods=['GET', 'POST'])
@login_required
@admin_required
def committes():
    """Muestra y gestiona los comités."""
    if request.method == 'POST':
        nombre = request.form.get('nombre_committe')
        logo_file = request.files.get('logo_committe')
        
        nuevo_committe = Committe(nombre_committe=nombre)
        if logo_file:
            logo_filename = save_file(logo_file, 'logos_committe')
            if logo_filename:
                nuevo_committe.logo_committe = logo_filename
                
        db.session.add(nuevo_committe)
        db.session.commit()
        flash('Comité añadido con éxito.', 'success')
        return redirect(url_for('admin.committes'))

    lista_committes = Committe.query.all()
    config = Configuracion.query.first()
    return render_template('admin/committes.html', committes=lista_committes, config=config)

@admin_bp.route('/committe/delete/<int:id>', methods=['POST'])
@login_required
@admin_required
def delete_committe(id):
    """Elimina un comité."""
    committe = Committe.query.get_or_404(id)
    db.session.delete(committe)
    db.session.commit()
    flash('Comité eliminado.', 'success')
    return redirect(url_for('admin.committes'))

# --- Rutas CRUD para Paises ---

@admin_bp.route('/paises', methods=['GET', 'POST'])
@login_required
@admin_required
def paises():
    """Muestra y gestiona los países, generando el código de bandera automáticamente."""
    if request.method == 'POST':
        nombre = request.form.get('nombre_pais').strip()
        
        if not nombre:
            flash('El nombre del país no puede estar vacío.', 'danger')
            return redirect(url_for('admin.paises'))

        # Buscar el país usando pycountry
        try:
            country = pycountry.countries.get(name=nombre)
            if not country:
                # Intenta una búsqueda difusa si la exacta falla
                country = pycountry.countries.search_fuzzy(nombre)[0]

            country_code = country.alpha_2.lower()
            
            nuevo_pais = Pais(nombre_pais=nombre, country_code=country_code)
            db.session.add(nuevo_pais)
            db.session.commit()
            flash(f'País "{nombre}" añadido con éxito. Código: {country_code}', 'success')

        except (LookupError, AttributeError):
            flash(f'No se pudo encontrar un código de bandera para "{nombre}". Por favor, verifique el nombre (debe estar en inglés).', 'danger')
        
        return redirect(url_for('admin.paises'))

    lista_paises = Pais.query.all()
    config = Configuracion.query.first()
    return render_template('admin/paises.html', paises=lista_paises, config=config)

# La ruta de eliminar país no necesita cambios
@admin_bp.route('/pais/delete/<int:id>', methods=['POST'])
@login_required
@admin_required
def delete_pais(id):
    """Elimina un país."""
    pais = Pais.query.get_or_404(id)
    db.session.delete(pais)
    db.session.commit()
    flash('País eliminado.', 'success')
    return redirect(url_for('admin.paises'))

# --- Rutas CRUD para Instituciones ---

@admin_bp.route('/instituciones', methods=['GET', 'POST'])
@login_required
@admin_required
def instituciones():
    """Muestra y gestiona las instituciones."""
    if request.method == 'POST':
        nombre = request.form.get('nombre_institucion')
        logo_file = request.files.get('logo_institucion')

        nueva_institucion = InstitucionEducativa(nombre_institucion=nombre)
        if logo_file:
            logo_filename = save_file(logo_file, 'logos_institucion')
            if logo_filename:
                nueva_institucion.logo_institucion = logo_filename
        
        db.session.add(nueva_institucion)
        db.session.commit()
        flash('Institución añadida con éxito.', 'success')
        return redirect(url_for('admin.instituciones'))
    
    lista_instituciones = InstitucionEducativa.query.all()
    config = Configuracion.query.first()
    return render_template('admin/instituciones.html', instituciones=lista_instituciones, config=config)

@admin_bp.route('/institucion/delete/<int:id>', methods=['POST'])
@login_required
@admin_required
def delete_institucion(id):
    """Elimina una institución."""
    institucion = InstitucionEducativa.query.get_or_404(id)
    db.session.delete(institucion)
    db.session.commit()
    flash('Institución eliminada.', 'success')
    return redirect(url_for('admin.instituciones'))


# --- RUTA PARA EDITAR PARTICIPANTE ---
@admin_bp.route('/participante/edit/<int:id>', methods=['POST'])
@login_required
@admin_required
def edit_participante(id):
    participante = Participante.query.get_or_404(id)
    
    participante.nombre_participante = request.form.get('nombre_participante')
    participante.committe_id = request.form.get('committe_id')
    participante.pais_id = request.form.get('pais_id')
    participante.institucion_id = request.form.get('institucion_id')
    
    foto_file = request.files.get('foto_participante')
    if foto_file and foto_file.filename != '':
        # Si se sube una nueva foto, la guardamos/reemplazamos
        _, file_extension = os.path.splitext(secure_filename(foto_file.filename))
        new_filename = f"{participante.id_participante}{file_extension}"
        
        upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'fotos')
        foto_file.save(os.path.join(upload_path, new_filename))
        participante.foto_participante = new_filename

    db.session.commit()
    flash('Participante actualizado con éxito.', 'success')
    return redirect(url_for('admin.participantes'))


# --- RUTA PARA EDITAR COMMITTE ---
@admin_bp.route('/committe/edit/<int:id>', methods=['POST'])
@login_required
@admin_required
def edit_committe(id):
    committe = Committe.query.get_or_404(id)
    committe.nombre_committe = request.form.get('nombre_committe')

    logo_file = request.files.get('logo_committe')
    if logo_file:
        logo_filename = save_file(logo_file, 'logos_committe')
        if logo_filename:
            committe.logo_committe = logo_filename
    
    db.session.commit()
    flash('Comité actualizado con éxito.', 'success')
    return redirect(url_for('admin.committes'))


# --- RUTA PARA EDITAR INSTITUCION ---
@admin_bp.route('/institucion/edit/<int:id>', methods=['POST'])
@login_required
@admin_required
def edit_institucion(id):
    institucion = InstitucionEducativa.query.get_or_404(id)
    institucion.nombre_institucion = request.form.get('nombre_institucion')

    logo_file = request.files.get('logo_institucion')
    if logo_file:
        logo_filename = save_file(logo_file, 'logos_institucion')
        if logo_filename:
            institucion.logo_institucion = logo_filename
    
    db.session.commit()
    flash('Institución actualizada con éxito.', 'success')
    return redirect(url_for('admin.instituciones'))
# --- Rutas para Importación de Datos y Reportes ---

@admin_bp.route('/importar', methods=['GET', 'POST'])
@login_required
@admin_required
def importar_datos():
    config = Configuracion.query.first()
    if request.method == 'POST':
        file = request.files.get('file')
        if not file or not file.filename.endswith('.xlsx'):
            flash('Por favor, suba un archivo Excel (.xlsx) válido.', 'danger')
            return redirect(request.url)

        try:
            xls = pd.ExcelFile(file, engine='openpyxl')
            
            # Procesar Instituciones y Committes (sin cambios)
            df_instituciones = pd.read_excel(xls, 'Instituciones')
            for _, row in df_instituciones.iterrows():
                if not InstitucionEducativa.query.filter_by(nombre_institucion=row['nombre_institucion']).first():
                    db.session.add(InstitucionEducativa(nombre_institucion=row['nombre_institucion']))

            df_committes = pd.read_excel(xls, 'Committes')
            for _, row in df_committes.iterrows():
                if not Committe.query.filter_by(nombre_committe=row['nombre_committe']).first():
                    db.session.add(Committe(nombre_committe=row['nombre_committe']))

            # --- CORRECCIÓN AQUÍ: Procesar Países con pycountry ---
            df_paises = pd.read_excel(xls, 'Paises')
            for _, row in df_paises.iterrows():
                nombre_pais = row['nombre_pais'].strip()
                if not Pais.query.filter_by(nombre_pais=nombre_pais).first():
                    country_code = None
                    try:
                        # Intenta encontrar el código del país
                        country = pycountry.countries.search_fuzzy(nombre_pais)[0]
                        country_code = country.alpha_2.lower()
                    except (LookupError, AttributeError):
                        # Si no lo encuentra, el código quedará como None
                        print(f"Advertencia: No se encontró código de bandera para '{nombre_pais}' durante la importación.")
                    
                    nuevo_pais = Pais(nombre_pais=nombre_pais, country_code=country_code)
                    db.session.add(nuevo_pais)

            db.session.commit()

            # Procesar Estudiantes (sin cambios)
            df_estudiantes = pd.read_excel(xls, 'Estudiantes')
            # ... (el resto de la función sigue igual) ...
            for _, row in df_estudiantes.iterrows():
                institucion = InstitucionEducativa.query.filter_by(nombre_institucion=row['institucion_educativa']).first()
                pais = Pais.query.filter_by(nombre_pais=row['pais_representado']).first()
                committe = Committe.query.filter_by(nombre_committe=row['committe']).first()

                if institucion and pais and committe:
                    nuevo_participante = Participante(
                        nombre_participante=row['nombre_participante'],
                        institucion_id=institucion.id_institucion,
                        pais_id=pais.id_pais,
                        committe_id=committe.id_committe,
                        saldo_merienda=config.meriendas_totales if config else 6
                    )
                    db.session.add(nuevo_participante)

            db.session.commit()
            flash('Datos importados con éxito.', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error al importar el archivo: {e}', 'danger')
        
        return redirect(url_for('admin.importar_datos'))

    return render_template('admin/importar.html', config=config)

@admin_bp.route('/descargar_plantilla')
@login_required
@admin_required
def descargar_plantilla():
    """Proporciona el archivo de plantilla Excel para la descarga."""
    project_root = os.path.join(current_app.root_path, '..')
    return send_from_directory(directory=project_root, path='plantilla_importacion.xlsx', as_attachment=True)

@admin_bp.route('/reportes')
@login_required
# @admin_required
def reportes():
    """Muestra un reporte de meriendas con filtros y ordenación."""
    # --- 1. OBTENER PARÁMETROS DE LA URL ---
    fecha_str = request.args.get('fecha')
    participante_id = request.args.get('participante_id')
    committe_id = request.args.get('committe_id')
    institucion_id = request.args.get('institucion_id')
    sort_by = request.args.get('sort_by', 'fecha_hora') # Default: ordenar por fecha
    order = request.args.get('order', 'desc') # Default: descendente (más nuevos primero)

    # --- 2. CONSTRUIR LA CONSULTA BASE ---
    query = Registro.query.join(Participante).join(User).join(Committe).join(InstitucionEducativa)

    # --- 3. APLICAR FILTROS DINÁMICAMENTE ---
    if fecha_str:
        try:
            fecha_obj = datetime.strptime(fecha_str, '%Y-%m-%d').date()
            start_of_day = datetime.combine(fecha_obj, time.min)
            end_of_day = datetime.combine(fecha_obj, time.max)
            query = query.filter(Registro.fecha_hora.between(start_of_day, end_of_day))
        except ValueError:
            flash('Formato de fecha inválido.', 'danger')
    
    if participante_id:
        query = query.filter(Registro.id_participante == participante_id)
    
    if committe_id:
        query = query.filter(Participante.committe_id == committe_id)
        
    if institucion_id:
        query = query.filter(Participante.institucion_id == institucion_id)

    # --- 4. APLICAR ORDENACIÓN DINÁMICAMENTE ---
    sort_columns = {
        'fecha_hora': Registro.fecha_hora,
        'participante': Participante.nombre_participante,
        'committe': Committe.nombre_committe,
        'institucion': InstitucionEducativa.nombre_institucion,
        'operador': User.username
    }
    
    sort_column = sort_columns.get(sort_by, Registro.fecha_hora)
    
    if order == 'asc':
        query = query.order_by(sort_column.asc())
    else:
        query = query.order_by(sort_column.desc())

    # --- 5. EJECUTAR LA CONSULTA Y PREPARAR DATOS PARA LA PLANTILLA ---
    registros = query.all()
    
    # Obtener datos para los menús desplegables del filtro
    participantes = Participante.query.order_by(Participante.nombre_participante).all()
    committes = Committe.query.order_by(Committe.nombre_committe).all()
    instituciones = InstitucionEducativa.query.order_by(InstitucionEducativa.nombre_institucion).all()
    config = Configuracion.query.first()

    return render_template(
        'admin/reportes.html', 
        registros=registros, 
        config=config,
        # Pasar los datos para los filtros
        participantes=participantes,
        committes=committes,
        instituciones=instituciones,
        # Pasar los valores actuales de los filtros para mantener el estado del formulario
        fecha=fecha_str,
        participante_id=participante_id,
        committe_id=committe_id,
        institucion_id=institucion_id,
        # Pasar los valores de ordenación para construir los enlaces de las columnas
        sort_by=sort_by,
        order=order
    )

# --- RUTA PARA GENERACIÓN DE CÓDIGOS QR ---

@admin_bp.route('/participantes/generar_qrs')
@login_required
@admin_required
def generar_todos_los_qrs():
    """
    Genera los códigos QR de todos los participantes y los ofrece como descarga en un archivo ZIP.
    """
    participantes = Participante.query.all()
    if not participantes:
        flash('No hay participantes para generar códigos QR.', 'warning')
        return redirect(url_for('admin.participantes'))

    # Crear un archivo ZIP en memoria
    memory_file = io.BytesIO()
    with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
        for p in participantes:
            # Preparar los datos para el QR
            participante_data = {
                "id": p.id_participante,
                "nombre": p.nombre_participante,
                "committe": p.committe.nombre_committe,
                "pais": p.pais.nombre_pais,
                "institucion": p.institucion.nombre_institucion
            }
            
            # Generar la imagen del QR
            qr_img_buffer = generate_qr_code_img(participante_data)
            
            # Definir el nombre del archivo PNG
            file_name = f"{p.id_participante}.png"
            
            # Escribir la imagen en el archivo ZIP
            zf.writestr(file_name, qr_img_buffer.getvalue())

    # Rebobinar el archivo en memoria para prepararlo para la lectura
    memory_file.seek(0)

    # Enviar el archivo ZIP para su descarga
    return send_file(
        memory_file,
        download_name='codigos_qr_participantes.zip',
        as_attachment=True,
        mimetype='application/zip'
    )

# --- Rutas CRUD para Usuarios ---

@admin_bp.route('/usuarios', methods=['GET'])
@login_required
@admin_required
def usuarios():
    """Muestra la página de gestión de usuarios."""
    lista_usuarios = User.query.all()
    config = Configuracion.query.first()
    return render_template('admin/usuarios.html', users=lista_usuarios, config=config)

@admin_bp.route('/usuario/add', methods=['POST'])
@login_required
@admin_required
def add_user():
    """Añade un nuevo usuario."""
    username = request.form.get('username')
    password = request.form.get('password')
    confirm_password = request.form.get('confirm_password')
    role = request.form.get('role')

    if password != confirm_password:
        flash('Las contraseñas no coinciden.', 'danger')
        return redirect(url_for('admin.usuarios'))

    user_exists = User.query.filter_by(username=username).first()
    if user_exists:
        flash('El nombre de usuario ya existe.', 'danger')
        return redirect(url_for('admin.usuarios'))
    
    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
    new_user = User(username=username, password=hashed_password, role=role)
    db.session.add(new_user)
    db.session.commit()
    
    flash('Usuario creado con éxito.', 'success')
    return redirect(url_for('admin.usuarios'))

@admin_bp.route('/usuario/edit/<int:id>', methods=['POST'])
@login_required
@admin_required
def edit_user(id):
    """Edita el nombre de usuario y el rol."""
    user = User.query.get_or_404(id)
    new_username = request.form.get('username')
    new_role = request.form.get('role')

    # Verificar si el nuevo nombre de usuario ya está en uso por otro usuario
    if new_username != user.username and User.query.filter_by(username=new_username).first():
        flash('Ese nombre de usuario ya está en uso.', 'danger')
        return redirect(url_for('admin.usuarios'))

    user.username = new_username
    user.role = new_role
    db.session.commit()
    flash('Usuario actualizado correctamente.', 'success')
    return redirect(url_for('admin.usuarios'))

@admin_bp.route('/usuario/password/<int:id>', methods=['POST'])
@login_required
@admin_required
def change_user_password(id):
    """Cambia la contraseña de un usuario."""
    user = User.query.get_or_404(id)
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password_change')

    if not new_password or new_password != confirm_password:
        flash('Las contraseñas no coinciden o están vacías.', 'danger')
        return redirect(url_for('admin.usuarios'))
    
    user.password = bcrypt.generate_password_hash(new_password).decode('utf-8')
    db.session.commit()
    flash(f'La contraseña para el usuario "{user.username}" ha sido cambiada.', 'success')
    return redirect(url_for('admin.usuarios'))


@admin_bp.route('/usuario/delete/<int:id>', methods=['POST'])
@login_required
@admin_required
def delete_user(id):
    """Elimina un usuario."""
    if id == current_user.id:
        flash('No puedes eliminar tu propia cuenta de administrador.', 'danger')
        return redirect(url_for('admin.usuarios'))
    
    user_to_delete = User.query.get_or_404(id)
    db.session.delete(user_to_delete)
    db.session.commit()
    flash('Usuario eliminado con éxito.', 'success')
    return redirect(url_for('admin.usuarios'))