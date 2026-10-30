from functools import wraps
from flask import redirect, url_for, abort
from flask_login import current_user

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        from models import UserProfile
        profile = UserProfile.query.filter_by(google_id=current_user.id).first()
        if not profile or not profile.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated

def get_is_admin():
    if not current_user.is_authenticated:
        return False
    from models import UserProfile
    profile = UserProfile.query.filter_by(google_id=current_user.id).first()
    return bool(profile and profile.is_admin)
