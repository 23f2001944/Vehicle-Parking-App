from app import app
from flask import render_template, redirect, request, url_for, flash
from models import db, User, ParkingLot, ParkingSpot, Reservation
from werkzeug.security import generate_password_hash, check_password_hash

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login_post():
    username = request.form.get('username')
    password = request.form.get('password')

    if not username or not password:
        flash("Please fill out all the necessary fields!")
        return redirect(url_for('login'))
    
    user = User.query.filter_by(username=username).first()  #check for preexisting users with the same username

    if not user:
        flash("User does not exist!")
        return redirect(url_for('login'))
    
    if not check_password_hash(user.passhash, password):
        flash("Incorrect Password!")
        return redirect(url_for('login'))

    return redirect(url_for('index'))


@app.route('/register')
def register():
    return render_template('register.html')

@app.route('/register', methods=['POST'])
def register_post():
    username = request.form.get('username')
    name = request.form.get('name')
    password = request.form.get('password')
    confirm_password = request.form.get('confirm_password')
    password_hash = generate_password_hash(password)    #generate a hash of the password
    
    if not username or not password or not confirm_password:
        flash("Please fill out all the necessary fields!")
        return redirect(url_for('register'))
    
    if password != confirm_password:
        flash("The passwords do not match!")
        return redirect(url_for('register'))
    
    user = User.query.filter_by(username=username).first()

    if user:
        flash("Username already taken!")
        return redirect(url_for('register'))
    
    new_user = User(username=username, name=name, passhash=password_hash)
    db.session.add(new_user)
    db.session.commit()

    return redirect(url_for('login'))