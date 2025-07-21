from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from urllib.parse import urlparse
from datetime import datetime
from flask_blog.app import mongo
from flask_blog.models.user import User
from flask_blog.forms.login_form import LoginForm
from flask_blog.forms.register_form import RegisterForm
from flask_blog.forms.delete_account_form import DeleteAccountForm
from flask_blog.forms.edit_profile_form import EditProfileForm

auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('blog.index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.find_by_email(form.email.data)
        if user is None or not user.check_password(form.password.data):
            flash('Invalid email or password', 'danger')
            return redirect(url_for('auth.login'))
        login_user(user, remember=form.remember_me.data)
        user.last_login = datetime.utcnow()
        # Update last_login in MongoDB
        User.update_last_login(user.get_id())
        next_page = request.args.get('next')
        if not next_page or urlparse(next_page).netloc != '':
            next_page = url_for('blog.index')
        flash('You have been logged in successfully!', 'success')
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)

@auth.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('blog.index'))
    form = RegisterForm()
    if form.validate_on_submit():
        if User.find_by_email(form.email.data):
            flash('Email already registered. Please use a different one.', 'danger')
            return redirect(url_for('auth.register'))
        if User.find_by_username(form.username.data):
            flash('Username already exists. Please choose a different one.', 'danger')
            return redirect(url_for('auth.register'))
        user_data = {
            'username': form.username.data,
            'email': form.email.data,
            'password': form.password.data,
            'bio': form.bio.data
        }
        User.create(user_data)
        flash('Your account has been created! You can now login.', 'success')
        return redirect(url_for('auth.login'))
    return render_template('register.html', title='Register', form=form)

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('blog.index'))

@auth.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = DeleteAccountForm()
    posts = list(mongo.db.posts.find({'user_id': str(current_user.id)}).sort('created_at', -1))
    comments = list(mongo.db.comments.find({'user_id': str(current_user.id)}).sort('created_at', -1))
    return render_template('profile.html', title='My Profile', form=form, posts=posts, comments=comments)

@auth.route('/edit-profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.email = form.email.data
        current_user.bio = form.bio.data
        User.update(current_user.get_id(), {'username': current_user.username, 'email': current_user.email, 'bio': current_user.bio})
        flash('Your profile has been updated!', 'success')
        return redirect(url_for('auth.profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
        form.bio.data = current_user.bio
    return render_template('edit_profile.html', title='Edit Profile', form=form)

@auth.route('/delete-account', methods=['POST'])
@login_required
def delete_account():
    form = DeleteAccountForm()
    if form.validate_on_submit():
        if not current_user.check_password(form.password.data):
            flash('Incorrect password. Account deletion cancelled.', 'danger')
            return redirect(url_for('auth.profile'))
        user_id = current_user.get_id()
        logout_user()
        User.delete(user_id)
        flash('Your account has been permanently deleted.', 'success')
        return redirect(url_for('blog.index'))
    flash('Account deletion failed. Please check your password.', 'danger')
    return redirect(url_for('auth.profile'))