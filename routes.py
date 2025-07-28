from app import app
from flask import render_template, redirect, request, url_for, flash, session
from models import db, User, ParkingLot, ParkingSpot, Reservation
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
    
@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login_post():
    username = request.form.get('username')
    password = request.form.get('password')

    if not username or not password:
        flash("Please fill out all the necessary fields!", category="danger")
        return redirect(url_for('login'))
    
    user = User.query.filter_by(username=username).first()  #check for preexisting users with the same username

    if not user:
        flash("User does not exist!", category="danger")
        return redirect(url_for('login'))
    
    if not check_password_hash(user.passhash, password):
        flash("Incorrect Password!", category="danger")
        return redirect(url_for('login'))

    session['user_id'] = user.id
    flash("Login successful!", category="success")
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
    
    if not username or not password or not confirm_password:
        flash("Please fill out all the necessary fields!", category="danger")
        return redirect(url_for('register'))
    
    if password != confirm_password:
        flash("The passwords do not match!", category="danger")
        return redirect(url_for('register'))
    
    #checks if there exists another user with the same username
    old_user = User.query.filter_by(username=username).first()

    if old_user:
        flash("User by this name already exists!", category="danger")
        return redirect(url_for('register'))
    
    password_hash = generate_password_hash(password)
    user = User(username=username, name=name, passhash=password_hash)
    db.session.add(user)
    db.session.commit()

    flash("Account created successfully!", category="success")
    return redirect(url_for('login'))


#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
#-------DECORATOR FOR AUTH_REQUIRED-------
#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@

def auth_required(func):
    @wraps(func)
    def inner(*args, **kwargs):
        if 'user_id' in session:
            return func(*args, **kwargs)
        else:
            flash("You do not have permission to view that page.", category="info")
            return redirect(url_for('login'))
    return inner

@app.route('/')
@auth_required
def index():
    return render_template('index.html')
    
@app.route('/profile')
@auth_required
def profile():
    user = User.query.get(session['user_id'])
    return render_template('profile.html', user=user)

@app.route('/profile', methods=['POST'])
@auth_required
def profile_post():
    username = request.form.get('username')
    name = request.form.get('name')
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')

    user = User.query.get(session['user_id'])

    if not username or not current_password or not new_password:
        flash("Please fill out all the necessary fields!", category="danger")
        return redirect(url_for('profile'))
    
    if not check_password_hash(user.passhash, current_password):
        flash("Incorrect Password!", category="danger")
        return redirect(url_for('profile'))
    
    if username != user.username:
        old_user = User.query.filter_by(username=username).first()
        if old_user:
            flash("User by this name already exist!", category="danger")
            return redirect(url_for('profile'))
    
    new_password_hash = generate_password_hash(new_password)
    user.username=username
    user.name=name
    user.passhash=new_password_hash
    db.session.commit()
    flash("Your profile is updated succesfully!", category="info")
    return redirect(url_for('profile'))

@app.route('/logout')
@auth_required
def logout():
    session.pop('user_id')
    return redirect(url_for('login')) 