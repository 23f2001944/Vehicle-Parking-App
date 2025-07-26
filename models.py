from app import app
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy(app)

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(32), unique=True, nullable=False)
    name = db.Column(db.String(64), nullable=True)
    passhash = db.Column(db.String(256), nullable=False)
    is_admin = db.Column(db.Boolean, nullable=False, default=False)
    reservations = db.relationship('Reservation', backref='user', lazy=True)

class ParkingLot(db.Model):
    __tablename__ = 'parking_lots'
    id = db.Column(db.Integer, primary_key=True)
    prime_location_name = db.Column(db.String(256), nullable=False)
    address = db.Column(db.Text, nullable=False)
    pin_code = db.Column(db.String(6), nullable=False)
    price_per_hour = db.Column(db.Float, nullable=False)
    max_spots = db.Column(db.Integer, nullable=False)
    spots = db.relationship('ParkingSpot', backref='lot', lazy=True)

class ParkingSpot(db.Model):
    __tablename__ = 'parking_spots'
    id = db.Column(db.Integer, primary_key=True)
    lot_id = db.Column(db.Integer, db.ForeignKey('parking_lots.id'), nullable=False)
    status = db.Column(db.Boolean, nullable=False, default=True)
    reservations = db.relationship('Reservation', backref='spot', lazy=True)

class Reservation(db.Model):
    __tablename__ = 'reservations'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    spot_id = db.Column(db.Integer, db.ForeignKey('parking_spots.id'), nullable=False)
    vehicle_number = db.Column(db.String(20), nullable=False)
    parking_timestamp = db.Column(db.DateTime, default=datetime.now)
    leaving_timestamp = db.Column(db.DateTime, nullable=True)
    parking_cost = db.Column(db.Float, nullable=True)

with app.app_context():
    db.create_all()