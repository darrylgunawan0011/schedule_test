# Integration of Frontend into Flask Routes

from flask import Flask, render_template, request, redirect, url_for, session, send_file
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import pandas as pd
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///attendance.db'
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)

class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    type = db.Column(db.String(10), nullable=False)

@app.route('/')
def home():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            return redirect(url_for('dashboard'))
        return 'Invalid credentials'
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Check if the username already exists
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            return 'Username already exists'
        
        # Hash the password before saving it
        hashed_password = generate_password_hash(password)
        
        # Create a new user record
        new_user = User(username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for('login'))  # Redirect to login page after registration

    return render_template('register.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html')

@app.route('/clock', methods=['POST'])
def clock():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    photo = request.files['photo']
    if photo:
        photo_path = f'static/photos/{session["user_id"]}_{datetime.utcnow().isoformat()}.jpg'
        photo.save(photo_path)
        clock_type = request.form['type']
        new_record = Attendance(user_id=session['user_id'], type=clock_type)
        db.session.add(new_record)
        db.session.commit()
        return redirect(url_for('dashboard'))
    return 'Photo capture required for clock-in/out'

@app.route('/export')
def export():
    records = Attendance.query.all()
    df = pd.DataFrame([(r.user_id, r.timestamp, r.type) for r in records],
                      columns=['User ID', 'Timestamp', 'Type'])
    csv_path = 'attendance_records.csv'
    df.to_csv(csv_path, index=False)
    return send_file(csv_path, as_attachment=True)

if __name__ == '__main__':
    os.makedirs('static/photos', exist_ok=True)
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=8200)
