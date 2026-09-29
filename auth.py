from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from database import get_user_by_email, insert_user, User

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
        
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        
        if not all([name, email, password]):
            flash("All fields are required.", "error")
            return render_template('register.html')
            
        existing_user = get_user_by_email(email)
        if existing_user:
            flash("Email already registered.", "error")
            return render_template('register.html')
            
        hashed_password = generate_password_hash(password)
        insert_user(name, email, hashed_password)
        
        flash("Registration successful. Please log in.", "success")
        return redirect(url_for('auth.login'))
        
    return render_template('register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
        
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        if not all([email, password]):
            flash("All fields are required.", "error")
            return render_template('login.html')
            
        user_data = get_user_by_email(email)
        if user_data and check_password_hash(user_data['password_hash'], password):
            user = User(user_data['id'], user_data['name'], user_data['email'])
            login_user(user)
            return redirect(url_for('home'))
        else:
            flash("Invalid email or password.", "error")
            
    return render_template('login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

@auth_bp.route('/block/<int:user_id>', methods=['POST'])
@login_required
def block(user_id):
    from database import block_user
    if user_id != current_user.id:
        block_user(current_user.id, user_id)
        flash("User has been blocked. You will no longer receive messages from them.", "success")
    return redirect(request.referrer or url_for('home'))
