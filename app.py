
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__, template_folder="templates")
app.secret_key = 'your-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///installments.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

ROLE_ADMIN = 'admin'
ROLE_CLIENT = 'client'

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150))
    email = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(200))
    role = db.Column(db.String(10))

class Sale(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    phone_model = db.Column(db.String(100))
    total_price_usd = db.Column(db.Float)
    total_price_uzs = db.Column(db.Integer)
    down_payment = db.Column(db.Float)
    months = db.Column(db.Integer)
    monthly_payment = db.Column(db.Float)
    start_date = db.Column(db.Date)

class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sale_id = db.Column(db.Integer, db.ForeignKey('sale.id'))
    due_date = db.Column(db.Date)
    amount = db.Column(db.Float)
    status = db.Column(db.String(10))

@app.route('/')
def home():
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        if user.role == ROLE_ADMIN:
            return redirect(url_for('admin_dashboard'))
        else:
            return redirect(url_for('client_dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            return redirect(url_for('home'))
        flash('Invalid credentials')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))

@app.route('/admin')
def admin_dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    if user.role != ROLE_ADMIN:
        return redirect(url_for('home'))
    sales = Sale.query.all()
    return render_template('admin.html', user=user, sales=sales)

@app.route('/admin/add_sale', methods=['GET', 'POST'])
def add_sale():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    if user.role != ROLE_ADMIN:
        return redirect(url_for('home'))

    if request.method == 'POST':
        client_email = request.form['email']
        client_name = request.form['name']
        phone_model = request.form['phone_model']
        price_usd = float(request.form['price_usd'])
        price_uzs = int(request.form['price_uzs'])
        down_payment = float(request.form['down_payment'])
        months = int(request.form['months'])
        start_date = datetime.strptime(request.form['start_date'], '%Y-%m-%d')

        existing_user = User.query.filter_by(email=client_email).first()
        if not existing_user:
            new_user = User(
                name=client_name,
                email=client_email,
                password=generate_password_hash('client123'),
                role=ROLE_CLIENT
            )
            db.session.add(new_user)
            db.session.commit()
            client_id = new_user.id
        else:
            client_id = existing_user.id

        monthly_payment = (price_usd - down_payment) / months
        sale = Sale(
            user_id=client_id,
            phone_model=phone_model,
            total_price_usd=price_usd,
            total_price_uzs=price_uzs,
            down_payment=down_payment,
            months=months,
            monthly_payment=monthly_payment,
            start_date=start_date
        )
        db.session.add(sale)
        db.session.commit()

        for i in range(months):
            due_date = start_date + timedelta(days=30 * i)
            payment = Payment(
                sale_id=sale.id,
                due_date=due_date,
                amount=monthly_payment,
                status='pending'
            )
            db.session.add(payment)

        db.session.commit()
        flash('Client and payment plan added successfully')
        return redirect(url_for('admin_dashboard'))

    return render_template('add_sale.html')

@app.route('/client')
def client_dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    sale = Sale.query.filter_by(user_id=user.id).first()
    payments = Payment.query.filter_by(sale_id=sale.id).all() if sale else []
    return render_template('client.html', user=user, sale=sale, payments=payments)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        # Optional: create admin user if missing
        from werkzeug.security import generate_password_hash
        if not User.query.filter_by(email='abdulvali6091@gmail.com').first():
            admin = User(
                name='Abdulvali',
                email='abdulvali6091@gmail.com',
                password=generate_password_hash('admin123'),
                role='admin'
            )
            db.session.add(admin)
            db.session.commit()
    app.run(debug=True)
