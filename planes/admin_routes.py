"""HU-19: el administrador crea, modifica, desactiva y elimina planes."""
from datetime import datetime

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user

from models import ROL_CLIENTE, Plan, Usuario, db

planes_admin_bp = Blueprint("planes_admin", __name__, url_prefix="/admin/planes")


@planes_admin_bp.before_request
def solo_admin():
    if not current_user.is_authenticated:
        return redirect(url_for("auth.login"))
    if not current_user.es_admin:
        abort(403)


def planes_disponibles():
    """Planes que se ofrecen a clientes nuevos (los desactivados no aparecen)."""
    return Plan.query.filter_by(activo=True).order_by(Plan.nombre).all()


def clientes_activos(plan):
    """Cuántos clientes activos tienen este plan."""
    return Usuario.query.filter_by(plan_id=plan.id, rol=ROL_CLIENTE, activo=True).count()


def _leer_formulario():
    """Devuelve (datos, error). Valida nombre, tiempo de respuesta y créditos."""
    nombre = request.form.get("nombre", "").strip()
    try:
        horas = int(request.form.get("tiempo_respuesta_horas", ""))
        creditos = int(request.form.get("creditos", ""))
    except ValueError:
        return None, "El tiempo de respuesta y los créditos tienen que ser números."
    if not nombre:
        return None, "Indicá el nombre del plan."
    if horas <= 0 or creditos < 0:
        return None, "El tiempo de respuesta debe ser mayor a 0 y los créditos no pueden ser negativos."
    return {"nombre": nombre[:100], "tiempo_respuesta_horas": horas, "creditos": creditos}, None


@planes_admin_bp.route("/")
def listar():
    planes = Plan.query.order_by(Plan.activo.desc(), Plan.nombre).all()
    clientes = {p.id: clientes_activos(p) for p in planes}
    return render_template("admin/planes.html", planes=planes, clientes=clientes)


# Criterio 1: crear un plan con nombre, tiempo de respuesta y créditos -> queda disponible
@planes_admin_bp.route("/nuevo", methods=["GET", "POST"])
def crear():
    if request.method == "POST":
        datos, error = _leer_formulario()
        if error:
            flash(error, "error")
            return render_template("admin/plan_form.html", plan=None, form=request.form)
        plan = Plan(**datos, activo=True)
        db.session.add(plan)
        db.session.commit()
        flash(f"Plan «{plan.nombre}» creado y disponible.", "success")
        return redirect(url_for(".listar"))
    return render_template("admin/plan_form.html", plan=None, form={})


# Criterio 2: editar un plan -> guarda los cambios y registra usuario y fecha
@planes_admin_bp.route("/<int:plan_id>/editar", methods=["GET", "POST"])
def editar(plan_id):
    plan = db.get_or_404(Plan, plan_id)
    if request.method == "POST":
        datos, error = _leer_formulario()
        if error:
            flash(error, "error")
            return render_template("admin/plan_form.html", plan=plan, form=request.form)
        for campo, valor in datos.items():
            setattr(plan, campo, valor)
        plan.modificado_por = current_user
        plan.fecha_modificacion = datetime.utcnow()
        db.session.commit()
        flash(f"Plan «{plan.nombre}» actualizado.", "success")
        return redirect(url_for(".listar"))
    form = {
        "nombre": plan.nombre,
        "tiempo_respuesta_horas": plan.tiempo_respuesta_horas,
        "creditos": plan.creditos_mensuales,
    }
    return render_template("admin/plan_form.html", plan=plan, form=form)


# Criterio 3: no se elimina un plan con clientes activos; se informa cuántos y se propone desactivar
@planes_admin_bp.route("/<int:plan_id>/eliminar", methods=["POST"])
def eliminar(plan_id):
    plan = db.get_or_404(Plan, plan_id)
    cantidad = clientes_activos(plan)
    if cantidad:
        flash(
            f"No se puede eliminar «{plan.nombre}»: lo usan {cantidad} cliente(s) activo(s). "
            "Podés desactivarlo para que no se ofrezca a clientes nuevos.",
            "error",
        )
        return redirect(url_for(".listar", proponer=plan.id))
    # Los clientes dados de baja que lo tenían quedan sin plan
    Usuario.query.filter_by(plan_id=plan.id).update({"plan_id": None})
    db.session.delete(plan)
    db.session.commit()
    flash(f"Plan «{plan.nombre}» eliminado.", "success")
    return redirect(url_for(".listar"))


# Criterio 4: desactivar -> deja de ofrecerse a clientes nuevos; los que lo tienen lo conservan
@planes_admin_bp.route("/<int:plan_id>/estado", methods=["POST"])
def cambiar_estado(plan_id):
    plan = db.get_or_404(Plan, plan_id)
    plan.activo = not plan.activo
    plan.modificado_por = current_user
    plan.fecha_modificacion = datetime.utcnow()
    db.session.commit()
    if plan.activo:
        flash(f"Plan «{plan.nombre}» activado: vuelve a ofrecerse.", "success")
    else:
        flash(f"Plan «{plan.nombre}» desactivado: ya no se ofrece a clientes nuevos. "
              "Los clientes que lo tienen lo conservan.", "success")
    return redirect(url_for(".listar"))