from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class UserProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    google_id = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(200), nullable=False)
    name = db.Column(db.String(200))
    is_admin = db.Column(db.Boolean, default=False)

class Destination(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    country = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(500))
    long_description = db.Column(db.Text)
    image_url = db.Column(db.String(500))
    category = db.Column(db.String(50), default='aventura')  # aventura / relax / cultura
    emoji = db.Column(db.String(10), default='✈️')
    price_range = db.Column(db.String(10), default='$$')     # $ / $$ / $$$
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class BlogPost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(300), nullable=False)
    content = db.Column(db.Text, nullable=False)
    image_url = db.Column(db.String(500))
    author_name = db.Column(db.String(200))
    destination_id = db.Column(db.Integer, db.ForeignKey('destination.id'), nullable=True)
    destination = db.relationship('Destination', backref='blog_posts')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(100))
    text = db.Column(db.String(500))
    sentiment = db.Column(db.String(20))
    destination_id = db.Column(db.Integer, db.ForeignKey('destination.id'), nullable=True)
    destination = db.relationship('Destination', backref='reviews')

class Image(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(500), nullable=False)
    description = db.Column(db.String(250))
    section = db.Column(db.String(50), nullable=False)
