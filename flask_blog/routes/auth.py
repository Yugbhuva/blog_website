from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from urllib.parse import urlparse
from datetime import datetime
from bson.objectid import ObjectId

from flask_blog.models.user import MongoUser, create_user
from flask_blog.forms.login_form import LoginForm
from flask_blog.forms.register_form import RegisterForm
from flask_blog.forms.delete_account_form import DeleteAccountForm
from flask_blog.forms.edit_profile_form import EditProfileForm
from flask_blog.app import mongo

auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('blog.index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user_doc = mongo.db.users.find_one({'email': form.email.data})
        if not user_doc or not MongoUser(user_doc).check_password(form.password.data):
            flash('Invalid email or password', 'danger')
            return redirect(url_for('auth.login'))
        user = MongoUser(user_doc)
        login_user(user, remember=form.remember_me.data)
        mongo.db.users.update_one({'_id': user_doc['_id']}, {'$set': {'last_login': datetime.utcnow()}})
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
        # Check if username or email already exists
        if mongo.db.users.find_one({'username': form.username.data}):
            flash('Username already exists. Please choose a different one.', 'danger')
            return redirect(url_for('auth.register'))
        if mongo.db.users.find_one({'email': form.email.data}):
            flash('Email already registered. Please use a different one.', 'danger')
            return redirect(url_for('auth.register'))
        user = create_user(
            username=form.username.data,
            email=form.email.data,
            password=form.password.data,
            bio=form.bio.data
        )
        flash('Your account has been created! You can now login.', 'success')
        return redirect(url_for('auth.login'))
    return render_template('register.html', title='Register', form=form)

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('blog.index'))

@auth.route('/profile')
@login_required
def profile():
    form = DeleteAccountForm()
    return render_template('profile.html', title='My Profile', form=form)

@auth.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        current_user_doc = mongo.db.users.find_one({'_id': ObjectId(current_user.id)})
        user_model = MongoUser(current_user_doc)
        
        update_data = {
            'username': form.username.data,
            'email': form.email.data,
            'bio': form.bio.data
        }
        
        mongo.db.users.update_one({'_id': ObjectId(current_user.id)}, {'$set': update_data})
        
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
    if not current_user.is_authenticated:
        flash('You must be logged in to delete your account.', 'danger')
        return redirect(url_for('auth.login'))
    if form.validate_on_submit():
        user_doc = mongo.db.users.find_one({'_id': ObjectId(current_user.id)})
        if not user_doc or not MongoUser(user_doc).check_password(form.password.data):
            flash('Incorrect password. Account deletion cancelled.', 'danger')
            return redirect(url_for('auth.profile'))
        user_id = current_user.id
        logout_user()
        mongo.db.users.delete_one({'_id': ObjectId(user_id)})
        flash('Your account has been permanently deleted.', 'success')
        return redirect(url_for('blog.index'))
    flash('Account deletion failed. Please check your password.', 'danger')
    return redirect(url_for('auth.profile'))