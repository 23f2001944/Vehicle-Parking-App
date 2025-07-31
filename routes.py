from app import app
from flask import render_template, redirect, request, url_for, flash, session
from models import db, User, ParkingLot, ParkingSpot, Reservation
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime
import matplotlib.pyplot as plt
import os
import re
    
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
    session['is_admin'] = user.is_admin
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
    
    if not all([username, password, confirm_password]):
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
            flash("Login to access that page.", category="info")
            return redirect(url_for('login'))
    return inner

def admin_required(func):
    @wraps(func)
    def inner(*args, **kwargs):
        if 'user_id' not in session:
            flash("Login to access that page.", category="info")
            return redirect(url_for('login'))
        user = User.query.get(session['user_id'])
        if not user.is_admin:
            flash("Admin access only.", category="info")
            return redirect(url_for('index'))
        return func(*args, **kwargs)
    return inner

@app.route('/')
@auth_required
def index():
    user = User.query.get(session['user_id'])
    if user.is_admin:
        return redirect(url_for('admin'))
    parking_lots = ParkingLot.query.all()
    availability = {}
    for lot in parking_lots:
        available = ParkingSpot.query.filter_by(lot_id=lot.id, status=True).count()
        availability[lot.id] = available
    return render_template('index.html', parking_lots=parking_lots, availability=availability)

@app.route('/book/<int:lot_id>', methods=['POST'])
@auth_required
def book_spot_post(lot_id):
    user_id = session.get('user_id')
    vehicle_number = request.form.get('vehicle_number')

    #Check vehicle number format
    pattern = r"^[A-Z]{2}\d{2}[A-Z]{0,2}\d{4}$"
    if not re.match(pattern, vehicle_number.upper()):
        flash("Invalid vehicle number format. Example: MH12AB1234", category="danger")
        return redirect(url_for('index'))

    available_spot = ParkingSpot.query.filter_by(lot_id=lot_id, status=True).first()
    if not available_spot:
        flash("No available spots.", category="danger")
        return redirect(url_for('index'))

    # Create reservation
    new_reservation = Reservation(
        spot_id=available_spot.id,
        user_id=user_id,
        vehicle_number=vehicle_number,
        parking_timestamp=datetime.now()
    )
    available_spot.status = False  # Mark as occupied
    db.session.add(new_reservation)
    db.session.commit()
    
    flash("Spot booked successfully!", category="success")
    return redirect(url_for('index'))

@app.route('/bookings')
@auth_required
def show_bookings():
    reservations = Reservation.query.filter_by(user_id=session['user_id'], leaving_timestamp=None).all()
    return render_template('user/bookings.html', reservations=reservations)

@app.route('/booking/<int:booking_id>', methods=['POST'])
@auth_required
def show_booking_post(booking_id):
    reservation = Reservation.query.filter_by(id=booking_id, user_id=session['user_id']).first()
    if not reservation:
        flash("Booking not found or unauthorized.", category="danger")
        return redirect(url_for('show_bookings'))

    if reservation.leaving_timestamp is not None:
        flash("This booking has already been completed.", category="info")
        return redirect(url_for('show_bookings'))

    reservation.leaving_timestamp = datetime.now()    # Set leaving time

    # Calculate cost
    parked_duration = (reservation.leaving_timestamp - reservation.parking_timestamp).total_seconds() / 3600
    parked_hours = round(parked_duration, 2)
    rate = reservation.spot.lot.price_per_hour
    reservation.parking_cost = round(parked_hours * rate, 2)

    # Mark the spot as available again (True -> Available)
    reservation.spot.status = True

    db.session.commit()
    flash(f"Parked out successfully! ₹{reservation.parking_cost} has been charged.", category="success")
    return redirect(url_for('index'))

@app.route('/history')
@auth_required
def history():
    reservations = Reservation.query.filter_by(user_id=session['user_id']).order_by(Reservation.parking_timestamp.desc()).all()
    money_spent = sum(r.parking_cost for r in reservations if r.parking_cost is not None)
    return render_template('user/history.html', reservations=reservations, money_spent=money_spent)
    
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

    if not username or not current_password:
        flash("Please fill out all the necessary fields!", category="danger")
        return redirect(url_for('profile'))
    
    if username != user.username:
        old_user = User.query.filter_by(username=username).first()
        if old_user:
            flash("User by this name already exist!", category="danger")
            return redirect(url_for('profile'))
    
    user.username=username
    user.name=name

    if new_password:
        user.passhash = generate_password_hash(new_password)

    db.session.commit()
    flash("Your profile is updated succesfully!", category="info")
    return redirect(url_for('profile'))

@app.route('/logout')
@auth_required
def logout():
    session.pop('user_id')
    return redirect(url_for('login')) 

#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
#---------------ADMIN PAGES---------------
#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@

@app.route('/admin')
@admin_required
def admin():
    parking_lots = ParkingLot.query.all()
    return render_template('admin.html', parking_lots=parking_lots)
    
@app.route('/parkinglot/add')
@admin_required
def add_parkinglot():
    return render_template('parkinglot/add.html')

@app.route('/parkinglot/add', methods=['POST'])
@admin_required
def add_parkinglot_post():
    prime_location_name = request.form.get('prime_location_name')
    address = request.form.get('address')
    pin_code = request.form.get('pin_code')
    price_per_hour = request.form.get('price_per_hour')
    max_spots = request.form.get('max_spots')

    if not all([prime_location_name, address, pin_code, price_per_hour, max_spots]):
        flash("All fields are required!", category="danger")
        return redirect(url_for('add_parkinglot'))

    if not pin_code.isdigit() or len(pin_code) != 6:
        flash("Pin code must be a 6-digit number.", category="danger")
        return redirect(url_for('add_parkinglot'))

    if float(price_per_hour) < 0 or int(max_spots) < 1:
        flash("Price cannot be negative and there must be at least 1 spot.", category="danger")
        return redirect(url_for('add_parkinglot'))
    
    parking_lot = ParkingLot(prime_location_name=prime_location_name, address=address, pin_code=pin_code, price_per_hour=price_per_hour,max_spots=max_spots)
    db.session.add(parking_lot)
    db.session.commit()

    for _ in range(int(max_spots)):
        spot = ParkingSpot(lot_id=parking_lot.id)
        db.session.add(spot)

    db.session.commit()

    flash('Parking lot and its spots created successfully!', category='success')
    return redirect(url_for('admin'))


@app.route('/parkinglot/<int:lot_id>/')
@admin_required
def show_parkingspot(lot_id):
    parking_lot = ParkingLot.query.get(lot_id)
    if not parking_lot:
        flash("This parking lot does not exist.", category='danger')
        return redirect(url_for('admin'))
    spots = ParkingSpot.query.filter_by(lot_id=lot_id).all()
    all_spots = ParkingSpot.query.filter_by(lot_id=lot_id).count()
    available = ParkingSpot.query.filter_by(lot_id=lot_id, status=True).count()
    return render_template('parkinglot/show_spots.html', parking_lot=parking_lot, spots=spots, all_spots=all_spots, available=available)

@app.route('/parkinglot/<int:lot_id>/edit')
@admin_required
def edit_parkinglot(lot_id):
    parking_lot = ParkingLot.query.get(lot_id)
    if not parking_lot:                         #if the user manually tries to visit a parking lot which does not exist
        flash("This parking lot does not exist.", category='danger')
        return redirect(url_for('admin'))
    return render_template('parkinglot/edit.html', parking_lot=parking_lot)

@app.route('/parkinglot/<int:lot_id>/edit', methods=['POST'])
@admin_required
def edit_parkinglot_post(lot_id):
    parking_lot = ParkingLot.query.get(lot_id)
    if not parking_lot:
        flash("This parking lot does not exist.", category='danger')
        return redirect(url_for('admin'))
    
    #=====collects info from the frontend======
    prime_location_name = request.form.get('prime_location_name')
    address = request.form.get('address')
    pin_code = request.form.get('pin_code')
    price_per_hour = request.form.get('price_per_hour')
    new_spots = request.form.get('max_spots')

    #===========validation checks============
    if not all([prime_location_name, address, pin_code, price_per_hour, new_spots]):
        flash("All fields are required!", category="danger")
        return redirect(url_for('edit_parkinglot', lot_id=lot_id))
    
    try:
        price_per_hour = float(price_per_hour)
        new_spots = int(new_spots)
    except ValueError:
        flash("Invalid number format.", category="danger")
        return redirect(url_for('edit_parkinglot', lot_id=lot_id))

    if not pin_code.isdigit() or len(pin_code) != 6:
        flash("Pin code must be a 6-digit number.", category="danger")
        return redirect(url_for('edit_parkinglot', lot_id=lot_id))

    if price_per_hour < 0 or new_spots < 1:
        flash("Price cannot be negative and there must be at least 1 spot.", category="danger")
        return redirect(url_for('edit_parkinglot', lot_id=lot_id))

    current_spots = ParkingSpot.query.filter_by(lot_id=lot_id).count()
    
    if new_spots > current_spots:
        to_add = new_spots - current_spots
        for _ in range(to_add):
            new_spot = ParkingSpot(lot_id=lot_id, status=True)
            db.session.add(new_spot)

    elif new_spots < current_spots:
        available_spots = ParkingSpot.query.filter_by(lot_id=lot_id, status=True).all()
        to_delete = current_spots - new_spots
        if len(available_spots) < to_delete:
            flash(f"Cannot reduce to {new_spots}. Not enough available spots to delete.", category="danger")
            return redirect(url_for('edit_parkinglot', lot_id=lot_id))
        for spot in available_spots[:to_delete]:
            db.session.delete(spot)

    #===========update the values============
    parking_lot.prime_location_name = prime_location_name
    parking_lot.address = address
    parking_lot.pin_code = pin_code
    parking_lot.price_per_hour = price_per_hour
    parking_lot.max_spots = new_spots

    db.session.commit()
    flash('The parking lot information is updated successfully.', category='success')
    return redirect(url_for('admin'))

@app.route('/parkinglot/<int:lot_id>/delete')
@admin_required
def delete_parkinglot(lot_id):
    parking_lot = ParkingLot.query.get(lot_id)
    if not parking_lot:
        flash("This parking lot does not exist.", category='danger')
        return redirect(url_for('admin'))
    return render_template('parkinglot/delete.html', parking_lot=parking_lot)

@app.route('/parkinglot/<int:lot_id>/delete', methods=['POST'])
@admin_required
def delete_parkinglot_post(lot_id):
    parking_lot = ParkingLot.query.get(lot_id)
    if not parking_lot:
        flash("This parking lot does not exist.", category='danger')
        return redirect(url_for('admin'))

    # Check for occupied spots in this lot (True -> Available, False -> Occupied)
    occupied_spots = ParkingSpot.query.filter_by(lot_id=lot_id, status=False).first()
    if occupied_spots:
        flash("Cannot delete this parking lot. Some spots are currently occupied.", category="danger")
        return redirect(url_for('admin'))

    db.session.delete(parking_lot)
    db.session.commit()

    flash('Parking lot deleted successfully.', category='info')
    return redirect(url_for('admin'))

@app.route('/spot/<int:spot_id>/')
@admin_required
def show_spotdetails(spot_id):
    parking_spot = ParkingSpot.query.get(spot_id)
    if not parking_spot:
        flash("This parking spot does not exist.", category='danger')
        return redirect(url_for('admin'))

    if parking_spot.status:  # True -> available
        flash("This spot is currently available. No reservation details to show.", category="info")
        return redirect(url_for('admin'))

    # Fetch active reservation (not parked out yet)
    reservation = Reservation.query.filter_by(spot_id=spot_id, leaving_timestamp=None).first()
    if not reservation:
        flash("No active reservation found for this spot.", category="warning")
        return redirect(url_for('admin'))
    
    user = User.query.get(reservation.user_id)

    return render_template('parkinglot/spotdetails.html', spot=parking_spot, reservation=reservation, user=user)


@app.route('/userdetails')
@admin_required
def user_details():
    users = User.query.all()
    return render_template('admin/users.html', users=users)

@app.route('/reservations')
@admin_required
def reservation_history():
    reservations = Reservation.query.order_by(Reservation.parking_timestamp.desc()).all()
    total_revenue = sum(r.parking_cost for r in reservations if r.parking_cost is not None)
    return render_template('admin/reservations.html', reservations=reservations, total_revenue=total_revenue)

@app.route('/summary')
@admin_required
def admin_summary(): 
    parking_lots = ParkingLot.query.all()
    lot_names, revenues, total_spots, available_spots = [], [], [], []

    for lot in parking_lots:
        lot_names.append(f"Lot {lot.id}")
        lot_revenue = sum(
            res.parking_cost or 0
            for spot in lot.spots
            for res in spot.reservations
        )
        revenues.append(lot_revenue)
        total_spots.append(len(lot.spots))
        available_spots.append(sum(1 for spot in lot.spots if spot.status))

    # Generate charts
    if not os.path.exists('static/images'):
        os.makedirs('static/images')

    plt.figure(figsize=(8, 5))
    plt.bar(lot_names, revenues, color='skyblue')
    plt.title('Revenue from Each Parking Lot')
    plt.xlabel('Parking Lot')
    plt.ylabel('Revenue (₹)')
    plt.tight_layout()
    plt.savefig('static/images/revenue_chart.png')
    plt.close()

    plt.figure(figsize=(8, 5))
    x = range(len(lot_names))
    plt.bar(x, total_spots, label='Total Spots', color='lightgray')
    plt.bar(x, available_spots, label='Available Spots', color='green')
    plt.xticks(x, lot_names)
    plt.title('Total vs Available Spots')
    plt.xlabel('Parking Lot')
    plt.ylabel('Number of Spots')
    plt.legend()
    plt.tight_layout()
    plt.savefig('static/images/spots_chart.png')
    plt.close()

    return render_template("admin/summary.html", total_revenue=sum(revenues))