from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from datetime import datetime
from sqlalchemy import desc, func
import re

from flask_blog.models.post import Post, Category, Tag
from flask_blog.models.comment import Comment
from flask_blog.models.user import User
from flask_blog.forms.post_form import PostForm
from flask_blog.forms.comment_form import CommentForm
from flask_blog.app import db

blog = Blueprint('blog', __name__)

def slugify(title):
    """
    Create a URL-friendly slug from a title.
    """
    # Convert to lowercase and replace spaces with hyphens
    slug = title.lower().strip().replace(' ', '-')
    # Remove special characters
    slug = re.sub(r'[^a-z0-9-]', '', slug)
    # Remove multiple hyphens
    slug = re.sub(r'[-]+', '-', slug)
    # Add timestamp to ensure uniqueness
    slug = f"{slug}-{int(datetime.utcnow().timestamp())}"
    return slug

@blog.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    per_page = 5
    
    # Get filter parameters
    category_id = request.args.get('category', None, type=int)
    tag_id = request.args.get('tag', None, type=int)
    search_query = request.args.get('q', None, type=str)
    
    # Base query - only published posts
    query = Post.query.filter_by(published=True)
    
    # Apply filters if provided
    if category_id:
        query = query.filter_by(category_id=category_id)
    
    if tag_id:
        query = query.join(Post.tags).filter(Tag.id == tag_id)
    
    if search_query:
        search = f"%{search_query}%"
        query = query.filter(Post.title.ilike(search) | Post.content.ilike(search))
    
    # Order by most recent
    posts = query.order_by(Post.created_at.desc()).paginate(page=page, per_page=per_page)
    
    # Get categories and tags for sidebar
    categories = Category.query.all()
    tags = Tag.query.all()
    
    # Get recent posts for sidebar
    recent_posts = Post.query.filter_by(published=True).order_by(Post.created_at.desc()).limit(5).all()
    
    return render_template(
        'index.html', 
        title='Home', 
        posts=posts,
        categories=categories,
        tags=tags,
        recent_posts=recent_posts,
        search_query=search_query
    )

@blog.route('/post/<string:slug>', methods=['GET', 'POST'])
def view_post(slug):
    post = Post.query.filter_by(slug=slug).first_or_404()
    
    # Comment form
    form = CommentForm()
    if form.validate_on_submit() and current_user.is_authenticated:
        comment = Comment(
            content=form.content.data,
            user_id=current_user.id,
            post_id=post.id,
            parent_id=form.parent_id.data if form.parent_id.data else None
        )
        db.session.add(comment)
        db.session.commit()
        flash('Your comment has been posted!', 'success')
        return redirect(url_for('blog.view_post', slug=post.slug))
    
    # Get all comments
    comments = Comment.query.filter_by(post_id=post.id, parent_id=None).order_by(Comment.created_at.desc()).all()
    
    # Get categories and tags for sidebar
    categories = Category.query.all()
    tags = Tag.query.all()
    
    # Get recent posts for sidebar
    recent_posts = Post.query.filter_by(published=True).order_by(Post.created_at.desc()).limit(5).all()
    
    return render_template(
        'post.html', 
        title=post.title,
        post=post,
        form=form,
        comments=comments,
        categories=categories,
        tags=tags,
        recent_posts=recent_posts
    )

@blog.route('/post/new', methods=['GET', 'POST'])
@login_required
def new_post():
    form = PostForm()
    
    # Get categories and tags for the form
    form.category_id.choices = [(c.id, c.name) for c in Category.query.order_by('name')]
    form.tags.choices = [(t.id, t.name) for t in Tag.query.order_by('name')]
    
    if form.validate_on_submit():
        # Create slug from title
        slug = slugify(form.title.data)
        
        # Create new post
        post = Post(
            title=form.title.data,
            content=form.content.data,
            slug=slug,
            user_id=current_user.id,
            category_id=form.category_id.data,
            published=form.published.data
        )
        
        # Add selected tags
        for tag_id in form.tags.data:
            tag = Tag.query.get(tag_id)
            if tag:
                post.tags.append(tag)
        
        db.session.add(post)
        db.session.commit()
        
        flash('Your post has been created!', 'success')
        return redirect(url_for('blog.view_post', slug=post.slug))
    
    return render_template('new_post.html', title='New Post', form=form, is_edit=False)

@blog.route('/post/<string:slug>/edit', methods=['GET', 'POST'])
@login_required
def edit_post(slug):
    post = Post.query.filter_by(slug=slug).first_or_404()
    
    # Check if the current user is the author
    if post.user_id != current_user.id and not current_user.is_admin:
        abort(403)
    
    form = PostForm()
    
    # Get categories and tags for the form
    form.category_id.choices = [(c.id, c.name) for c in Category.query.order_by('name')]
    form.tags.choices = [(t.id, t.name) for t in Tag.query.order_by('name')]
    
    if form.validate_on_submit():
        post.title = form.title.data
        post.content = form.content.data
        post.category_id = form.category_id.data
        post.published = form.published.data
        post.updated_at = datetime.utcnow()
        
        # Update tags
        post.tags = []
        for tag_id in form.tags.data:
            tag = Tag.query.get(tag_id)
            if tag:
                post.tags.append(tag)
        
        db.session.commit()
        
        flash('Your post has been updated!', 'success')
        return redirect(url_for('blog.view_post', slug=post.slug))
    
    elif request.method == 'GET':
        # Populate form with existing data
        form.title.data = post.title
        form.content.data = post.content
        form.category_id.data = post.category_id
        form.published.data = post.published
        form.tags.data = [tag.id for tag in post.tags]
    
    return render_template('edit_post.html', title='Edit Post', form=form, post=post, is_edit=True)

@blog.route('/post/<string:slug>/delete', methods=['POST'])
@login_required
def delete_post(slug):
    post = Post.query.filter_by(slug=slug).first_or_404()
    
    # Check if the current user is the author
    if post.user_id != current_user.id and not current_user.is_admin:
        abort(403)
    
    db.session.delete(post)
    db.session.commit()
    
    flash('Your post has been deleted!', 'success')
    return redirect(url_for('blog.index'))

@blog.route('/comment/<int:comment_id>/delete', methods=['POST'])
@login_required
def delete_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    
    # Check if the current user is the author of the comment or post
    post = Post.query.get(comment.post_id)
    if comment.user_id != current_user.id and post.user_id != current_user.id and not current_user.is_admin:
        abort(403)
    
    db.session.delete(comment)
    db.session.commit()
    
    flash('Comment deleted successfully!', 'success')
    return redirect(url_for('blog.view_post', slug=post.slug))

@blog.route('/dashboard')
@login_required
def dashboard():
    # Get user's posts
    posts = Post.query.filter_by(user_id=current_user.id).order_by(Post.created_at.desc()).all()
    
    # Get user's comments
    comments = Comment.query.filter_by(user_id=current_user.id).order_by(Comment.created_at.desc()).all()
    
    return render_template('dashboard.html', title='Dashboard', posts=posts, comments=comments)

@blog.route('/category/<int:category_id>')
def category_posts(category_id):
    category = Category.query.get_or_404(category_id)
    page = request.args.get('page', 1, type=int)
    per_page = 5
    
    posts = Post.query.filter_by(category_id=category_id, published=True).order_by(
        Post.created_at.desc()
    ).paginate(page=page, per_page=per_page)
    
    # Get categories and tags for sidebar
    categories = Category.query.all()
    tags = Tag.query.all()
    
    # Get recent posts for sidebar
    recent_posts = Post.query.filter_by(published=True).order_by(Post.created_at.desc()).limit(5).all()
    
    return render_template(
        'index.html',
        title=f'Category: {category.name}',
        posts=posts,
        categories=categories,
        tags=tags,
        recent_posts=recent_posts,
        current_category=category
    )

@blog.route('/tag/<int:tag_id>')
def tag_posts(tag_id):
    tag = Tag.query.get_or_404(tag_id)
    page = request.args.get('page', 1, type=int)
    per_page = 5
    
    posts = Post.query.filter(Post.tags.any(id=tag_id), Post.published==True).order_by(
        Post.created_at.desc()
    ).paginate(page=page, per_page=per_page)
    
    # Get categories and tags for sidebar
    categories = Category.query.all()
    tags = Tag.query.all()
    
    # Get recent posts for sidebar
    recent_posts = Post.query.filter_by(published=True).order_by(Post.created_at.desc()).limit(5).all()
    
    return render_template(
        'index.html',
        title=f'Tag: {tag.name}',
        posts=posts,
        categories=categories,
        tags=tags,
        recent_posts=recent_posts,
        current_tag=tag
    )

@blog.app_errorhandler(404)
def not_found_error(error):
    return render_template('error.html', title='Page Not Found', error_code=404, error_message='Page not found'), 404

@blog.app_errorhandler(403)
def forbidden_error(error):
    return render_template('error.html', title='Forbidden', error_code=403, error_message='You do not have permission to access this resource'), 403

@blog.app_errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('error.html', title='Server Error', error_code=500, error_message='Internal server error'), 500
