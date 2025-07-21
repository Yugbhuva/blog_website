from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from datetime import datetime
import re
from bson.objectid import ObjectId
from flask_blog.app import mongo

from flask_blog.models.post import Post, Category, Tag
from flask_blog.models.comment import Comment
from flask_blog.models.user import User
from flask_blog.forms.post_form import PostForm
from flask_blog.forms.comment_form import CommentForm

blog = Blueprint('blog', __name__)

def get_paginated_posts(query, page, per_page=5):
    """
    Helper function to paginate posts from MongoDB.
    """
    total_posts = mongo.db.posts.count_documents(query)
    skip = (page - 1) * per_page
    
    posts_cursor = mongo.db.posts.find(query).sort('created_at', -1).skip(skip).limit(per_page)

    items = []
    for post in posts_cursor:
        post['author'] = User.get_by_id(post['user_id'])
        post['comment_count'] = mongo.db.comments.count_documents({'post_id': str(post['_id'])})
        if post.get('category_id'):
            post['category'] = Category.get_by_id(post['category_id'])
        else:
            post['category'] = None
        items.append(post)

    total_pages = (total_posts + per_page - 1) // per_page if per_page > 0 else 0

    # Directly calculate the list of page numbers
    last = 0
    page_numbers = []
    left_edge = 1
    right_edge = 1
    left_current = 2
    right_current = 2
    for num in range(1, total_pages + 1):
        if num <= left_edge or \
           (page - left_current - 1 < num < page + right_current) or \
           num > total_pages - right_edge:
            if last + 1 != num:
                page_numbers.append(None)
            page_numbers.append(num)
            last = num

    pagination = {
        'items': items,
        'total': total_posts,
        'page': page,
        'pages': total_pages,
        'has_prev': page > 1,
        'prev_num': page - 1,
        'has_next': page < total_pages,
        'next_num': page + 1,
        'page_numbers': page_numbers
    }
    return pagination


def slugify(title):
    slug = title.lower().strip().replace(' ', '-')
    slug = re.sub(r'[^a-z0-9-]', '', slug)
    slug = re.sub(r'[-]+', '-', slug)
    slug = f"{slug}-{int(datetime.utcnow().timestamp())}"
    return slug

@blog.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    per_page = 5
    
    # Get filter parameters
    category_id = request.args.get('category', None, type=str)
    tag_id = request.args.get('tag', None, type=str)
    search_query = request.args.get('q', None, type=str)
    
    query = {'published': True}
    if category_id:
        query['category_id'] = category_id
    if tag_id:
        query['tags'] = {'$in': [tag_id]}
    if search_query:
        query['$or'] = [
            {'title': {'$regex': search_query, '$options': 'i'}},
            {'content': {'$regex': search_query, '$options': 'i'}}
        ]

    posts_pagination = get_paginated_posts(query, page, per_page)
    
    # Get categories and tags for sidebar
    categories = list(mongo.db.categories.find())
    for category in categories:
        category['post_count'] = mongo.db.posts.count_documents({'category_id': str(category['_id']), 'published': True})
    tags = list(mongo.db.tags.find())
    
    # Get recent posts for sidebar
    recent_posts = list(mongo.db.posts.find({'published': True}).sort('created_at', -1).limit(5))
    
    return render_template(
        'index.html', 
        title='Home', 
        posts=posts_pagination,
        categories=categories,
        tags=tags,
        recent_posts=recent_posts,
        search_query=search_query
    )

@blog.route('/post/<string:slug>', methods=['GET', 'POST'])
def view_post(slug):
    post = mongo.db.posts.find_one({'slug': slug})
    if not post:
        abort(404)
    post['author'] = User.get_by_id(post['user_id'])
    if post.get('category_id'):
        post['category'] = Category.get_by_id(post['category_id'])
    else:
        post['category'] = None
    form = CommentForm()
    if form.validate_on_submit() and current_user.is_authenticated:
        comment_data = {
            'content': form.content.data,
            'user_id': str(current_user.id),
            'post_id': str(post['_id']),
            'parent_id': form.parent_id.data if form.parent_id.data else None
        }
        Comment.create(comment_data)
        flash('Your comment has been posted!', 'success')
        return redirect(url_for('blog.view_post', slug=post['slug']))
    comments = Comment.find_by_post(str(post['_id']))
    for comment in comments:
        comment['author'] = User.get_by_id(comment['user_id'])
        if comment.get('replies'):
            for reply in comment['replies']:
                reply['author'] = User.get_by_id(reply['user_id'])

    categories = list(mongo.db.categories.find())
    for category in categories:
        category['post_count'] = mongo.db.posts.count_documents({'category_id': str(category['_id']), 'published': True})
    tags = list(mongo.db.tags.find())
    recent_posts = list(mongo.db.posts.find({'published': True}).sort('created_at', -1).limit(5))
    return render_template(
        'post.html',
        title=post['title'],
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
    categories = list(mongo.db.categories.find())
    for category in categories:
        category['post_count'] = mongo.db.posts.count_documents({'category_id': str(category['_id']), 'published': True})
    tags = list(mongo.db.tags.find())
    form.category_id.choices = [(str(c['_id']), c['name']) for c in categories]
    form.tags.choices = [(str(t['_id']), t['name']) for t in tags]
    if form.validate_on_submit():
        slug = slugify(form.title.data)
        post_data = {
            'title': form.title.data,
            'content': form.content.data,
            'slug': slug,
            'user_id': str(current_user.id),
            'category_id': form.category_id.data,
            'published': form.published.data,
            'tags': form.tags.data
        }
        Post.create(post_data)
        flash('Your post has been created!', 'success')
        return redirect(url_for('blog.view_post', slug=slug))
    return render_template('new_post.html', title='New Post', form=form, is_edit=False)

@blog.route('/post/<string:slug>/edit', methods=['GET', 'POST'])
@login_required
def edit_post(slug):
    post = mongo.db.posts.find_one({'slug': slug})
    if not post:
        abort(404)
    if post['user_id'] != str(current_user.id) and not getattr(current_user, 'is_admin', False):
        abort(403)
    form = PostForm()
    categories = list(mongo.db.categories.find())
    for category in categories:
        category['post_count'] = mongo.db.posts.count_documents({'category_id': str(category['_id']), 'published': True})
    tags = list(mongo.db.tags.find())
    form.category_id.choices = [(str(c['_id']), c['name']) for c in categories]
    form.tags.choices = [(str(t['_id']), t['name']) for t in tags]
    if form.validate_on_submit():
        update_data = {
            'title': form.title.data,
            'content': form.content.data,
            'category_id': form.category_id.data,
            'published': form.published.data,
            'tags': form.tags.data
        }
        Post.update(str(post['_id']), update_data)
        flash('Your post has been updated!', 'success')
        return redirect(url_for('blog.view_post', slug=slug))
    elif request.method == 'GET':
        form.title.data = post['title']
        form.content.data = post['content']
        form.category_id.data = post['category_id']
        form.published.data = post['published']
        form.tags.data = post.get('tags', [])
    return render_template('edit_post.html', title='Edit Post', form=form, post=post, is_edit=True)

@blog.route('/post/<string:slug>/delete', methods=['POST'])
@login_required
def delete_post(slug):
    post = mongo.db.posts.find_one({'slug': slug})
    if not post:
        abort(404)
    if post['user_id'] != str(current_user.id) and not getattr(current_user, 'is_admin', False):
        abort(403)
    Post.delete(str(post['_id']))
    flash('Your post has been deleted!', 'success')
    return redirect(url_for('blog.index'))

@blog.route('/comment/<string:comment_id>/delete', methods=['POST'])
@login_required
def delete_comment(comment_id):
    comment = Comment.get_by_id(comment_id)
    if not comment:
        abort(404)
    post = Post.get_by_id(comment['post_id'])
    if comment['user_id'] != str(current_user.id) and post['user_id'] != str(current_user.id) and not getattr(current_user, 'is_admin', False):
        abort(403)
    Comment.delete(comment_id)
    flash('Comment deleted successfully!', 'success')
    return redirect(url_for('blog.view_post', slug=post['slug']))

@blog.route('/dashboard')
@login_required
def dashboard():
    posts = list(mongo.db.posts.find({'user_id': str(current_user.id)}).sort('created_at', -1))
    for post in posts:
        post['author'] = User.get_by_id(post['user_id'])
        if post.get('category_id'):
            post['category'] = Category.get_by_id(post['category_id'])
        else:
            post['category'] = None
        post['comment_count'] = mongo.db.comments.count_documents({'post_id': str(post['_id'])})
    
    comments = list(mongo.db.comments.find({'user_id': str(current_user.id)}).sort('created_at', -1))
    for comment in comments:
        comment['author'] = User.get_by_id(comment['user_id'])
        comment['post'] = Post.get_by_id(comment['post_id'])
        
    return render_template('dashboard.html', title='Dashboard', posts=posts, comments=comments)

@blog.route('/category/<string:category_id>')
def category_posts(category_id):
    category = Category.get_by_id(category_id)
    if not category:
        abort(404)
    page = request.args.get('page', 1, type=int)
    per_page = 5
    
    query = {'category_id': category_id, 'published': True}
    posts_pagination = get_paginated_posts(query, page, per_page)
    
    # Get categories and tags for sidebar
    categories = list(mongo.db.categories.find())
    for cat in categories:
        cat['post_count'] = mongo.db.posts.count_documents({'category_id': str(cat['_id']), 'published': True})
    tags = list(mongo.db.tags.find())
    
    # Get recent posts for sidebar
    recent_posts = list(mongo.db.posts.find({'published': True}).sort('created_at', -1).limit(5))
    
    return render_template(
        'index.html',
        title=f'Category: {category["name"]}',
        posts=posts_pagination,
        categories=categories,
        tags=tags,
        recent_posts=recent_posts,
        current_category=category,
        search_query=None
    )

@blog.route('/tag/<string:tag_id>')
def tag_posts(tag_id):
    tag = Tag.get_by_id(tag_id)
    if not tag:
        abort(404)
    page = request.args.get('page', 1, type=int)
    per_page = 5
    
    query = {'tags': {'$in': [tag_id]}, 'published': True}
    posts_pagination = get_paginated_posts(query, page, per_page)
    
    # Get categories and tags for sidebar
    categories = list(mongo.db.categories.find())
    for category in categories:
        category['post_count'] = mongo.db.posts.count_documents({'category_id': str(category['_id']), 'published': True})
    tags = list(mongo.db.tags.find())
    
    # Get recent posts for sidebar
    recent_posts = list(mongo.db.posts.find({'published': True}).sort('created_at', -1).limit(5))
    
    return render_template(
        'index.html',
        title=f'Tag: {tag["name"]}',
        posts=posts_pagination,
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
    return render_template('error.html', title='Server Error', error_code=500, error_message='Internal server error'), 500
