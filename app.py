from flask import Flask, request, jsonify, render_template, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import date
import os
import uuid

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'  # Change this to a secure key in production
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///site.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['FREE_MONTHLY_LIMIT'] = 100
app.config['PREMIUM_MONTHLY_LIMIT'] = 1000

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

VALID_MODELS = ['deepseek-r1', 'gpt-4o', 'claude']

# User model for the database
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(150), nullable=False)
    api_key = db.Column(db.String(36), unique=True, nullable=False)
    user_type = db.Column(db.String(10), default='free')  # 'free' or 'premium'
    monthly_requests = db.Column(db.Integer, default=0)
    last_reset_date = db.Column(db.Date, default=date.today)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Home page
@app.route('/')
def home():
    return render_template('home.html')

# Registration route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if User.query.filter_by(username=username).first():
            flash('Username already exists')
            return redirect(url_for('register'))
        user = User(
            username=username,
            api_key=str(uuid.uuid4()),
            user_type='free',
            monthly_requests=0,
            last_reset_date=date.today().replace(day=1)
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        flash('Registration successful! Please log in.')
        return redirect(url_for('login'))
    return render_template('register.html')

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('dashboard'))
        flash('Invalid username or password')
        return redirect(url_for('login'))
    return render_template('login.html')

# Logout route
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

# Dashboard route
@app.route('/dashboard')
@login_required
def dashboard():
    limit = app.config['FREE_MONTHLY_LIMIT'] if current_user.user_type == 'free' else app.config['PREMIUM_MONTHLY_LIMIT']
    return render_template('dashboard.html', user=current_user, limit=limit)

# Generate new API key route
@app.route('/generate-key', methods=['GET', 'POST'])
@login_required
def generate_key():
    if request.method == 'POST':
        current_user.api_key = str(uuid.uuid4())
        db.session.commit()
        flash('New API key generated. Your old key is now invalid.')
        return redirect(url_for('dashboard'))
    return render_template('confirm_generate.html')

# Upgrade to premium route
@app.route('/upgrade', methods=['POST'])
@login_required
def upgrade():
    current_user.user_type = 'premium'
    db.session.commit()
    flash('Upgraded to Premium! You now have 1,000 requests per month.')
    return redirect(url_for('dashboard'))

# API endpoint for answering requests
@app.route('/api/answer', methods=['POST'])
def answer():
    user_api_key = request.headers.get('X-API-Key')
    if not user_api_key:
        return jsonify({'error': 'Missing API key'}), 401
    user = User.query.filter_by(api_key=user_api_key).first()
    if not user:
        return jsonify({'error': 'Invalid API key'}), 401

    # Check and reset monthly limit if needed
    today = date.today()
    current_month_start = today.replace(day=1)
    if user.last_reset_date < current_month_start:
        user.monthly_requests = 0
        user.last_reset_date = current_month_start
        db.session.commit()

    # Determine user limit
    limit = app.config['FREE_MONTHLY_LIMIT'] if user.user_type == 'free' else app.config['PREMIUM_MONTHLY_LIMIT']
    if user.monthly_requests >= limit:
        return jsonify({'error': 'Monthly limit exceeded'}), 429

    # Process the request
    data = request.get_json()
    prompt = data.get('prompt', '')
    model = data.get('model', 'deepseek-r1')
    if not prompt:
        return jsonify({'error': 'Prompt required'}), 400
    if model not in VALID_MODELS:
        return jsonify({'error': f'Model {model} not supported. Use: {VALID_MODELS}'}), 400

    # Increment request count and return mock response
    user.monthly_requests += 1
    db.session.commit()
    return jsonify({'answer': f'Sample response from {model}'})

# Initialize database and run app
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
