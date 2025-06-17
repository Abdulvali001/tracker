
from app import db, User, app
from werkzeug.security import generate_password_hash

with app.app_context():
    db.create_all()

    if not User.query.filter_by(email='abdulvali6091@gmail.com').first():
        admin = User(
            name='Abdulvali',
            email='abdulvali6091@gmail.com',
            password=generate_password_hash('admin123'),
            role='admin'
        )
        db.session.add(admin)
        db.session.commit()

    print("Database initialized and admin user created.")
