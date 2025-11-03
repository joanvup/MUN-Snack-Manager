from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required, current_user
from app import db
from app.models.models import Participante, Registro, Configuracion
from datetime import datetime

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