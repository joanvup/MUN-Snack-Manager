from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required, current_user
from app import db
from app.models.models import Participante, Registro, Configuracion
from datetime import datetime, timedelta

operador_bp = Blueprint('operador', __name__)

@operador_bp.route('/escaner')
@login_required
def escaner():
    config = Configuracion.query.first()
    return render_template('operador/escaner.html', config=config)

@operador_bp.route('/validar_qr', methods=['POST'])
@login_required
def validar_qr():
    data = request.get_json()
    if not data or 'id_participante' not in data:
        return jsonify({'success': False, 'message': 'ID de participante no proporcionado.'}), 400

    try:
        participante_id = int(data['id_participante'])
    except ValueError:
        return jsonify({'success': False, 'message': 'ID inválido. Debe ser un número.'}), 400
    
    participante = Participante.query.get(participante_id)

    if not participante:
        return jsonify({'success': False, 'message': 'Participante no encontrado.'}), 404
    
    # --- INICIO: LÓGICA DE COOLDOWN ---
    config = Configuracion.query.first()
    cooldown_period = timedelta(minutes=config.cooldown_minutos if config else 60)
    
    # Buscar el último registro para este participante
    ultimo_registro = Registro.query.filter_by(id_participante=participante.id_participante).order_by(Registro.fecha_hora.desc()).first()

    if ultimo_registro:
        tiempo_desde_ultimo_registro = datetime.utcnow() - ultimo_registro.fecha_hora
        if tiempo_desde_ultimo_registro < cooldown_period:
            tiempo_restante = cooldown_period - tiempo_desde_ultimo_registro
            minutos_restantes = round(tiempo_restante.total_seconds() / 60)
            return jsonify({
                'success': False,
                'message': f'Este participante ya fue registrado hace poco. Inténtelo de nuevo en {minutos_restantes} minutos.'
            })
    # --- FIN: LÓGICA DE COOLDOWN ---

    if participante.saldo_merienda > 0:
        participante.saldo_merienda -= 1
        nuevo_registro = Registro(
            id_participante=participante.id_participante,
            operador_responsable_id=current_user.id,
            fecha_hora=datetime.utcnow()
        )
        db.session.add(nuevo_registro)
        db.session.commit()
        return jsonify({
            'success': True,
            'message': f'Merienda registrada para {participante.nombre_participante}.',
            'saldo_restante': participante.saldo_merienda
        })
    else:
        return jsonify({
            'success': False,
            'message': f'{participante.nombre_participante} no tiene meriendas disponibles.',
            'saldo_restante': 0
        })