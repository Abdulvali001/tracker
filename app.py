from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
app.secret_key = 'your-secret-key'

# Configure the database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tracker.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(200))
    role = db.Column(db.String(10))  

# Payment model
class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    model = db.Column(db.String(100))
    amount = db.Column(db.Float)

# Home route
@app.route('/')
def home():
    return redirect(url_for('login'))

# Register route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])
        role = request.form['role']

        new_user = User(name=name, email=email, password=password, role=role)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))

    return render_template('register.html')

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['role'] = user.role

            if user.role == 'admin':
                return redirect(url_for('admin_dashboard'))
            elif user.role == 'client':
                return redirect(url_for('client_dashboard'))

        return 'Invalid credentials'

    return render_template('login.html')

# Admin dashboard
@app.route('/admin_dashboard')
def admin_dashboard():
    if 'user_id' in session and session.get('role') == 'admin':
        users = User.query.all()
        return render_template('admin_dashboard.html', users=users)
    return redirect(url_for('login'))

# Client dashboard
@app.route('/client_dashboard')
def client_dashboard():
    if 'user_id' in session and session.get('role') == 'client':
        payments = Payment.query.filter_by(client_id=session['user_id']).all()
        return render_template('client_dashboard.html', payments=payments)
    return redirect(url_for('login'))

# Logout route
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# Add payment (admin only)
@app.route('/add_payment', methods=['GET', 'POST'])
def add_payment():
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))

    if request.method == 'POST':
        client_id = request.form['client_id']
        model = request.form['model']
        amount = float(request.form['amount'])

        new_payment = Payment(client_id=client_id, model=model, amount=amount)
        db.session.add(new_payment)
        db.session.commit()
        return redirect(url_for('admin_dashboard'))

    clients = User.query.filter_by(role='client').all()
    return render_template('add_payment.html', clients=clients)

# Run app
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
