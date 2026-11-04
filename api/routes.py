"""HU-22: API de solo lectura para que sistemas externos consulten los clientes."""
from flask import Blueprint, jsonify, request

from models import ROL_CLIENTE, TokenAPI, Usuario, db

api_bp = Blueprint("api", __name__, url_prefix="/api")


def _token_del_encabezado():
    """Lee 'Authorization: Bearer <token>'. Devuelve None si no viene o tiene otro formato."""
    encabezado = request.headers.get("Authorization", "")
    tipo, _, token = encabezado.partition(" ")
    if tipo.lower() != "bearer" or not token.strip():
        return None
    return token.strip()


def _error(codigo, mensaje):
    respuesta = jsonify({"error": mensaje})
    respuesta.status_code = codigo
    return respuesta


def _cliente_a_dict(u):
    # Solo datos de cliente: nunca contraseña, google_id ni datos de seguridad
    return {
        "id": u.id,
        "nombre": u.nombre,
        "apellido": u.apellido,
        "email": u.email,
        "telefono": u.telefono,
        "plan": u.plan.nombre if u.plan else None,
        "activo": u.activo,
        "fecha_alta": u.fecha_alta.isoformat() if u.fecha_alta else None,
    }


@api_bp.route("/clientes", methods=["GET"])
def listar_clientes():
    token = _token_del_encabezado()
    if not token:
        respuesta = _error(401, "Falta el encabezado Authorization: Bearer <token>.")
        respuesta.headers["WWW-Authenticate"] = "Bearer"
        return respuesta

    registro = TokenAPI.buscar_valido(token)
    if not registro:
        respuesta = _error(401, "Token inválido, vencido o revocado.")
        respuesta.headers["WWW-Authenticate"] = 'Bearer error="invalid_token"'
        return respuesta

    permitido = registro.registrar_consulta()
    db.session.commit()  # guarda el contador y el último uso (solo del token)
    if not permitido:
        respuesta = _error(429, "Superaste el límite de 100 consultas por hora.")
        respuesta.headers["Retry-After"] = "3600"
        return respuesta

    clientes = Usuario.query.filter_by(rol=ROL_CLIENTE).order_by(Usuario.id).all()
    return jsonify({
        "cantidad": len(clientes),
        "clientes": [_cliente_a_dict(u) for u in clientes],
    }), 200