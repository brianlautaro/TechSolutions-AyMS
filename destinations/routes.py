from flask import Blueprint, render_template, request, redirect, url_for
from flask_login import current_user
from models import db, Destination, Review
from utils import admin_required

destinations_bp = Blueprint("destinations", __name__, url_prefix="/destinos")

@destinations_bp.route("/")
def index():
    categoria = request.args.get('categoria', 'todos')
    if categoria and categoria != 'todos':
        destinations = Destination.query.filter_by(category=categoria).order_by(Destination.created_at.desc()).all()
    else:
        destinations = Destination.query.order_by(Destination.created_at.desc()).all()
    return render_template("destinos/index.html", destinations=destinations, categoria=categoria)

@destinations_bp.route("/<int:dest_id>")
def detail(dest_id):
    dest = Destination.query.get_or_404(dest_id)
    reviews = Review.query.filter_by(destination_id=dest_id).all()
    related_posts = dest.blog_posts[:3]
    return render_template("destinos/detalle.html", dest=dest, reviews=reviews, related_posts=related_posts)

@destinations_bp.route("/admin/nuevo", methods=["GET", "POST"])
@admin_required
def create():
    if request.method == "POST":
        dest = Destination(
            name=request.form['name'],
            country=request.form['country'],
            description=request.form.get('description', ''),
            long_description=request.form.get('long_description', ''),
            image_url=request.form.get('image_url', ''),
            category=request.form.get('category', 'aventura'),
            emoji=request.form.get('emoji', '✈️'),
            price_range=request.form.get('price_range', '$$'),
        )
        db.session.add(dest)
        db.session.commit()
        return redirect(url_for('destinations.detail', dest_id=dest.id))
    return render_template("destinos/formulario.html", dest=None, action="Crear destino")

@destinations_bp.route("/admin/<int:dest_id>/editar", methods=["GET", "POST"])
@admin_required
def edit(dest_id):
    dest = Destination.query.get_or_404(dest_id)
    if request.method == "POST":
        dest.name = request.form['name']
        dest.country = request.form['country']
        dest.description = request.form.get('description', '')
        dest.long_description = request.form.get('long_description', '')
        dest.image_url = request.form.get('image_url', '')
        dest.category = request.form.get('category', 'aventura')
        dest.emoji = request.form.get('emoji', '✈️')
        dest.price_range = request.form.get('price_range', '$$')
        db.session.commit()
        return redirect(url_for('destinations.detail', dest_id=dest.id))
    return render_template("destinos/formulario.html", dest=dest, action="Editar destino")

@destinations_bp.route("/admin/<int:dest_id>/eliminar", methods=["POST"])
@admin_required
def delete(dest_id):
    dest = Destination.query.get_or_404(dest_id)
    db.session.delete(dest)
    db.session.commit()
    return redirect(url_for('destinations.index'))
