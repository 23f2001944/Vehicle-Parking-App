# 🅿️ Smart Parking Management System

A web-based Parking Management System built using **Flask**, allowing **users** to reserve spots, **admins** to manage parking lots, and both to track parking activity. The project supports real-time booking, billing, analytics, and user authentication.

---

## 📁 Project Structure
│
├── static/
│ └── images/
│ ├── logo.png
│ ├── revenue_chart.png
│ └── spots_chart.png
│
├── templates/
│ ├── admin/
│ │ └── ...
│ ├── parkinglot/
│ │ └── ...
│ ├── user/
│ │ └── ...
│ ├── layout.html
│ ├── index.html
│ ├── navbar.html
│ └── ...
│
├── instance/           # SQLite DB
│
├── venv/               # Python virtual environment
│
├── .env
├── .gitignore
├── app.py              # Main application file
├── config.py           # Config settings
├── models.py           # SQLAlchemy ORM models
├── routes.py           # All app routes
├── requirements.txt    # Project documentation
├── report.pdf          # Project report
└── README.md           # Python dependencies


---

### 👤 Users
- Register and login
- Book a parking spot by entering vehicle number
- View current bookings
- Park out with automated cost calculation
- View full reservation history

### 🛠️ Admins
- Add, edit, and delete parking lots
- View all users and their details
- View all reservation history
- Summary dashboard with statistics and revenue graphs

---

## 📊 Admin Summary Dashboard

- 📈 Revenue from each parking lot (bar chart)
- 📊 Total vs Available spots (stacked bar chart)

Graphs are dynamically generated using `matplotlib` and saved in `static/images/`.

---

## 🛠️ Tech Stack

- **Backend:** Python, Flask
- **Frontend:** HTML, Bootstrap, Jinja2
- **Database:** SQLite (via SQLAlchemy)
- **Libraries:** 
  - `Flask`
  - `Flask_SQLAlchemy`
  - `Werkzeug` (for password hashing)
  - `matplotlib` (for graph generation)

---

## 📦 Setup Instructions

1. **Clone the repo**
   git clone https://github.com/23f2001944/Vehicle-Parking-App/mad1-parking.git
   cd mad1-parking

2. **Create and activate virtual environment**
    python -m venv venv
    ./venv/Scripts/activate

3. **Install Dependencies**
    pip install -r requirements.txt

4. **Set up a .env file using the reference of .env.example**

5. **Run the application**
    flask run

---

## 🧪 Default Admin Credentials
    username: admin
    password: admin@123