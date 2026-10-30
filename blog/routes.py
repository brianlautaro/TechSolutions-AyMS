from flask import Blueprint, render_template, request, redirect, url_for
from flask_login import current_user
from models import db, BlogPost, Destination
from utils import admin_required

blog_bp = Blueprint("blog", __name__, url_prefix="/blog")

@blog_bp.route("/")
def index():
    posts = BlogPost.query.order_by(BlogPost.created_at.desc()).all()
    return render_template("blog/index.html", posts=posts)

@blog_bp.route("/<int:post_id>")
def detail(post_id):
    post = BlogPost.query.get_or_404(post_id)
    other_posts = BlogPost.query.filter(BlogPost.id != post_id).order_by(BlogPost.created_at.desc()).limit(3).all()
    return render_template("blog/detalle.html", post=post, other_posts=other_posts)

@blog_bp.route("/admin/nuevo", methods=["GET", "POST"])
@admin_required
def create():
    if request.method == "POST":
        dest_id = request.form.get('destination_id') or None
        post = BlogPost(
            title=request.form['title'],
            content=request.form['content'],
            image_url=request.form.get('image_url', ''),
            author_name=current_user.name,
            destination_id=int(dest_id) if dest_id else None,
        )
        db.session.add(post)
        db.session.commit()
        return redirect(url_for('blog.detail', post_id=post.id))
    destinations = Destination.query.order_by(Destination.name).all()
    return render_template("blog/formulario.html", post=None, destinations=destinations, action="Crear articulo")

@blog_bp.route("/admin/<int:post_id>/editar", methods=["GET", "POST"])
@admin_required
def edit(post_id):
    post = BlogPost.query.get_or_404(post_id)
    if request.method == "POST":
        dest_id = request.form.get('destination_id') or None
        post.title = request.form['title']
        post.content = request.form['content']
        post.image_url = request.form.get('image_url', '')
        post.destination_id = int(dest_id) if dest_id else None
        db.session.commit()
        return redirect(url_for('blog.detail', post_id=post.id))
    destinations = Destination.query.order_by(Destination.name).all()
    return render_template("blog/formulario.html", post=post, destinations=destinations, action="Editar articulo")

@blog_bp.route("/admin/<int:post_id>/eliminar", methods=["POST"])
@admin_required
def delete(post_id):
    post = BlogPost.query.get_or_404(post_id)
    db.session.delete(post)
    db.session.commit()
    return redirect(url_for('blog.index'))
