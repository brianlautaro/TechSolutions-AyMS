from flask import Blueprint, render_template, request, redirect, url_for
import boto3
import time
from config import Config
from models import db, Image

s3_service = Blueprint("s3_service", __name__, url_prefix="/s3")

# -------------------------------
# Funciones de S3
# -------------------------------
def s3_client():
    return boto3.client(
        's3',
        region_name=Config.S3_REGION,
        aws_access_key_id=Config.AWS_ACCESS_KEY,
        aws_secret_access_key=Config.AWS_SECRET_KEY
    )

def upload_file_to_s3(file, filename):
    s3 = s3_client()
    try:
        s3.upload_fileobj(file, Config.S3_BUCKET, filename)
        url = f"https://{Config.S3_BUCKET}.s3.{Config.S3_REGION}.amazonaws.com/{filename}"
        print(f"Imagen subida: {url}")
        return url
    except Exception as e:
        print("Error subiendo archivo:", e)
        return None

# -------------------------------
# Función para traer imágenes de la BDD
# -------------------------------
def list_s3_files():
    print("Cargando imágenes desde la BDD...")
    images_db = Image.query.all()
    sections = {}
    for img in images_db:
        sections.setdefault(img.section, []).append({
            "url": img.url,
            "description": img.description
        })

    for default_section in ["banners", "cards", "carrousel", "contacto", "uploads", "otros"]:
        sections.setdefault(default_section, [])

    return sections

# -------------------------------
# Rutas del blueprint
# -------------------------------
@s3_service.route("/gallery")
def index():
    images = list_s3_files()
    return render_template("gallery.html", images=images)

@s3_service.route("/upload", methods=["POST"])
def upload():
    file = request.files.get("image")
    folder = request.form.get("folder", "uploads")
    description = request.form.get("description", "")
    if file:
        filename = f"img/{folder}/{int(time.time())}_{file.filename}"
        uploaded_url = upload_file_to_s3(file, filename)
        if uploaded_url:
            new_image = Image(url=uploaded_url, description=description, section=folder)
            db.session.add(new_image)
            db.session.commit()
            print("Imagen y descripción guardadas en la BDD")
    return redirect(url_for("s3_service.index"))
