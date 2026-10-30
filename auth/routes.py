from flask import Blueprint, redirect, url_for, session
from authlib.integrations.flask_client import OAuth
from flask_login import login_user
from dotenv import load_dotenv
import os

load_dotenv()

auth_bp = Blueprint("auth", __name__)
oauth = OAuth()

google = oauth.register(
    name="google",
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)

@auth_bp.route("/login")
def login():
    redirect_uri = url_for("auth.authorize", _external=True)
    return google.authorize_redirect(redirect_uri)

@auth_bp.route("/authorize")
def authorize():
    token = google.authorize_access_token()
    user_info = google.userinfo()

    session["user"] = {
        "id": user_info["sub"],
        "name": user_info["name"],
        "email": user_info["email"],
        "picture": user_info.get("picture", ""),
    }

    from app import User
    user = User(user_info["sub"], user_info["name"], user_info["email"], user_info.get("picture", ""))
    login_user(user)

    # Crear o actualizar perfil en la base de datos
    from models import db, UserProfile
    admin_email = os.getenv("ADMIN_EMAIL", "")
    is_admin = bool(admin_email and user_info["email"] == admin_email)
    profile = UserProfile.query.filter_by(google_id=user_info["sub"]).first()
    if not profile:
        profile = UserProfile(
            google_id=user_info["sub"],
            email=user_info["email"],
            name=user_info["name"],
            is_admin=is_admin,
        )
        db.session.add(profile)
    else:
        profile.is_admin = is_admin
    db.session.commit()

    return redirect(url_for("profile"))
