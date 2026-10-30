from flask import Flask, render_template, session, redirect, url_for, request, abort
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from auth.routes import auth_bp, oauth
from s3Service.s3service import s3_service
from destinations.routes import destinations_bp
from blog.routes import blog_bp
from models import db, Review, Destination, BlogPost
from dotenv import load_dotenv
from collections import Counter
from utils import get_is_admin
import os


load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

app.config["GOOGLE_CLIENT_ID"] = os.getenv("GOOGLE_CLIENT_ID")
app.config["GOOGLE_CLIENT_SECRET"] = os.getenv("GOOGLE_CLIENT_SECRET")
oauth.init_app(app)

database_url = os.getenv('DATABASE_URL', 'sqlite:///reviews.db')
# Render entrega URLs con el prefijo "postgres://" pero SQLAlchemy requiere "postgresql://"
if database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql://', 1)
app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

with app.app_context():
    db.create_all()
    # Seed automático si la base está vacía
    if Destination.query.count() == 0:
        from seed import run_seed
        run_seed()

login_manager = LoginManager(app)
login_manager.login_view = "auth.login"

app.register_blueprint(auth_bp)
app.register_blueprint(s3_service)
app.register_blueprint(destinations_bp)
app.register_blueprint(blog_bp)

class User(UserMixin):
    def __init__(self, id_, name, email, picture=""):
        self.id = id_
        self.name = name
        self.email = email
        self.picture = picture

@login_manager.user_loader
def load_user(user_id):
    user_data = session.get("user")
    if user_data and user_data["id"] == user_id:
        return User(user_data["id"], user_data["name"], user_data["email"], user_data.get("picture", ""))
    return None

@app.context_processor
def inject_globals():
    return {'is_admin': get_is_admin()}

@app.errorhandler(403)
def forbidden(_e):
    return render_template("403.html"), 403

_sentiment_analyzer = None

def get_sentiment_analyzer():
    global _sentiment_analyzer
    if _sentiment_analyzer is None:
        from pysentimiento import create_analyzer
        _sentiment_analyzer = create_analyzer(task="sentiment", lang="es")
    return _sentiment_analyzer

# ----------------------------------------
# RUTAS PRINCIPALES
# ----------------------------------------
@app.route("/")
def home():
    featured = Destination.query.order_by(Destination.created_at.desc()).limit(6).all()
    latest_posts = BlogPost.query.order_by(BlogPost.created_at.desc()).limit(3).all()
    total_destinations = Destination.query.count()
    total_reviews = Review.query.count()
    total_posts = BlogPost.query.count()
    return render_template("home.html",
                           featured=featured,
                           latest_posts=latest_posts,
                           total_destinations=total_destinations,
                           total_reviews=total_reviews,
                           total_posts=total_posts)

@app.route("/profile")
@login_required
def profile():
    user_reviews = Review.query.filter_by(user_id=current_user.id).all()
    sentiments = [r.sentiment for r in user_reviews]
    dominant_sentiment = Counter(sentiments).most_common(1)[0][0] if sentiments else None

    sentiment_category_map = {
        "POSITIVE": "aventura",
        "NEGATIVE": "relax",
        "Neutral": "cultura",
    }
    rec_category = sentiment_category_map.get(dominant_sentiment)
    if rec_category:
        recommended_destinations = Destination.query.filter_by(category=rec_category).limit(4).all()
    else:
        recommended_destinations = Destination.query.order_by(Destination.created_at.desc()).limit(4).all()

    all_destinations = Destination.query.order_by(Destination.name).all()
    return render_template("profile.html",
                           user=current_user,
                           reviews=user_reviews,
                           dominant_sentiment=dominant_sentiment,
                           recommended_destinations=recommended_destinations,
                           all_destinations=all_destinations)

@app.route("/reviews", methods=["POST"])
@login_required
def add_review():
    text = request.form.get("text")
    destination_id = request.form.get("destination_id") or None
    next_url = request.form.get("next") or url_for("profile")
    if text:
        result = get_sentiment_analyzer().predict(text)
        label = result.output
        if label == "POS":
            sentiment = "POSITIVE"
        elif label == "NEG":
            sentiment = "NEGATIVE"
        else:
            sentiment = "Neutral"

        review = Review(
            user_id=current_user.id,
            text=text,
            sentiment=sentiment,
            destination_id=int(destination_id) if destination_id else None,
        )
        db.session.add(review)
        db.session.commit()

    return redirect(next_url)

@app.route("/admin")
@login_required
def admin_dashboard():
    if not get_is_admin():
        abort(403)
    return render_template("admin/dashboard.html",
                           total_destinations=Destination.query.count(),
                           total_posts=BlogPost.query.count(),
                           total_reviews=Review.query.count(),
                           recent_destinations=Destination.query.order_by(Destination.created_at.desc()).limit(5).all(),
                           recent_posts=BlogPost.query.order_by(BlogPost.created_at.desc()).limit(5).all())

@app.route("/logout")
@login_required
def logout():
    logout_user()
    session.clear()
    return redirect(url_for("home"))

if __name__ == "__main__":
    app.run(debug=True)
