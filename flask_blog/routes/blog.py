from flask import Blueprint, render_template, redirect, url_for, flash, request, abort, jsonify
from flask_login import login_required, current_user
from datetime import datetime
import re
from bson import ObjectId
import markdown

from flask_blog.forms.post_form import PostForm
from flask_blog.forms.comment_form import CommentForm
from flask_blog.app import mongo
from flask_blog.models.user import get_user_by_id

blog = Blueprint('blog', __name__)

@blog.route('/category/add', methods=['POST'])
@login_required
def add_category():
    data = request.get_json()
    if not data or not data.get('name'):
        return jsonify({'error': 'Name is required'}), 400
    
    name = data['name'].strip()
    if mongo.db.categories.find_one({'name': name}):
        return jsonify({'error': 'Category already exists'}), 409

    category = {'name': name}
    result = mongo.db.categories.insert_one(category)
    
    new_category = {
        'id': str(result.inserted_id),
        'name': name
    }
    return jsonify(new_category), 201

@blog.route('/tag/add', methods=['POST'])
@login_required
def add_tag():
    data = request.get_json()
    if not data or not data.get('name'):
        return jsonify({'error': 'Name is required'}), 400
    
    name = data['name'].strip()
    if mongo.db.tags.find_one({'name': name}):
        return jsonify({'error': 'Tag already exists'}), 409
        
    tag = {'name': name}
    result = mongo.db.tags.insert_one(tag)

    new_tag = {
        'id': str(result.inserted_id),
        'name': name
    }
    return jsonify(new_tag), 201

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
    category_id = request.args.get('category', None, type=str)
    tag_id = request.args.get('tag', None, type=str)
    search_query = request.args.get('q', None, type=str)
    query = {'published': True}
    if category_id:
        query['category_id'] = ObjectId(category_id)
    if tag_id:
        query['tags'] = ObjectId(tag_id)
    if search_query:
        query['$or'] = [
            {'title': {'$regex': search_query, '$options': 'i'}},
            {'content': {'$regex': search_query, '$options': 'i'}}
        ]
    posts_cursor = mongo.db.posts.find(query).sort('created_at', -1)
    total = posts_cursor.count() if hasattr(posts_cursor, 'count') else mongo.db.posts.count_documents(query)
    posts = list(posts_cursor.skip((page-1)*per_page).limit(per_page))
    categories = list(mongo.db.categories.find())
    for category in categories:
        category['post_count'] = mongo.db.posts.count_documents({'category_id': category['_id'], 'published': True})
    tags = list(mongo.db.tags.find())
    recent_posts = list(mongo.db.posts.find({'published': True}).sort('created_at', -1).limit(5))
    for post in posts:
        post['author'] = get_user_by_id(post['user_id'])
        if post.get('category_id'):
            post['category'] = mongo.db.categories.find_one({'_id': post['category_id']})
        else:
            post['category'] = None
        post['comment_count'] = mongo.db.comments.count_documents({'post_id': post['_id']})
        post['tags'] = [mongo.db.tags.find_one({'_id': tag_id}) for tag_id in post.get('tags',[])]
        post['content'] = markdown.markdown(post['content'])
    # Always pass a posts dict with 'items' key
    posts_dict = {'items': posts, 'total': total, 'page': page, 'pages': (total+per_page-1)//per_page}
    return render_template(
        'index.html',
        title='Home',
        posts=posts_dict,
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
    post['author'] = get_user_by_id(post['user_id'])
    if post.get('category_id'):
        post['category'] = mongo.db.categories.find_one({'_id': post['category_id']})
    else:
        post['category'] = None
    post['tags'] = [mongo.db.tags.find_one({'_id': tag_id}) for tag_id in post.get('tags',[])]
    post['content'] = markdown.markdown(post['content'])
    form = CommentForm()
    if form.validate_on_submit() and current_user.is_authenticated:
        comment = {
            'content': form.content.data,
            'user_id': ObjectId(current_user.id),
            'post_id': post['_id'],
            'parent_id': ObjectId(form.parent_id.data) if form.parent_id.data else None,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow(),
            'approved': True
        }
        mongo.db.comments.insert_one(comment)
        flash('Your comment has been posted!', 'success')
        return redirect(url_for('blog.view_post', slug=post['slug']))
    comments = list(mongo.db.comments.find({'post_id': post['_id'], 'parent_id': None}).sort('created_at', -1))
    for comment in comments:
        comment['author'] = get_user_by_id(comment['user_id'])
        comment['replies'] = list(mongo.db.comments.find({'parent_id': comment['_id']}))
        for reply in comment['replies']:
            reply['author'] = get_user_by_id(reply['user_id'])
    categories = list(mongo.db.categories.find())
    for category in categories:
        category['post_count'] = mongo.db.posts.count_documents({'category_id': category['_id'], 'published': True})
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
        category['post_count'] = mongo.db.posts.count_documents({'category_id': category['_id'], 'published': True})
    tags = list(mongo.db.tags.find())
    form.category_id.choices = [(str(c['_id']), c['name']) for c in categories]
    form.tags.choices = [(str(t['_id']), t['name']) for t in tags]
    if form.validate_on_submit():
        slug = slugify(form.title.data)
        post = {
            'title': form.title.data,
            'content': form.content.data,
            'slug': slug,
            'user_id': ObjectId(current_user.id),
            'category_id': ObjectId(form.category_id.data),
            'published': form.published.data,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow(),
            'tags': [ObjectId(tag_id) for tag_id in form.tags.data]
        }
        mongo.db.posts.insert_one(post)
        flash('Your post has been created!', 'success')
        return redirect(url_for('blog.view_post', slug=slug))
    return render_template('new_post.html', title='New Post', form=form, is_edit=False)

@blog.route('/post/<string:slug>/edit', methods=['GET', 'POST'])
@login_required
def edit_post(slug):
    post = mongo.db.posts.find_one({'slug': slug})
    if not post:
        abort(404)
    if str(post['user_id']) != str(current_user.id) and not getattr(current_user, 'is_admin', False):
        abort(403)
    form = PostForm()
    categories = list(mongo.db.categories.find())
    for category in categories:
        category['post_count'] = mongo.db.posts.count_documents({'category_id': category['_id'], 'published': True})
    tags = list(mongo.db.tags.find())
    form.category_id.choices = [(str(c['_id']), c['name']) for c in categories]
    form.tags.choices = [(str(t['_id']), t['name']) for t in tags]
    if form.validate_on_submit():
        update = {
            'title': form.title.data,
            'content': form.content.data,
            'category_id': ObjectId(form.category_id.data),
            'published': form.published.data,
            'updated_at': datetime.utcnow(),
            'tags': [ObjectId(tag_id) for tag_id in form.tags.data]
        }
        mongo.db.posts.update_one({'_id': post['_id']}, {'$set': update})
        flash('Your post has been updated!', 'success')
        return redirect(url_for('blog.view_post', slug=post['slug']))
    elif request.method == 'GET':
        form.title.data = post['title']
        form.content.data = post['content']
        form.category_id.data = str(post['category_id'])
        form.published.data = post['published']
        form.tags.data = [str(tag_id) for tag_id in post.get('tags',[])]
    return render_template('edit_post.html', title='Edit Post', form=form, post=post, is_edit=True)

@blog.route('/post/<string:slug>/delete', methods=['POST'])
@login_required
def delete_post(slug):
    post = mongo.db.posts.find_one({'slug': slug})
    if not post:
        abort(404)
    if str(post['user_id']) != str(current_user.id) and not getattr(current_user, 'is_admin', False):
        abort(403)
    mongo.db.posts.delete_one({'_id': post['_id']})
    mongo.db.comments.delete_many({'post_id': post['_id']})
    flash('Your post has been deleted!', 'success')
    # Redirect to dashboard if 'from_dashboard' is in the form, else to index
    if request.form.get('from_dashboard'):
        return redirect(url_for('blog.dashboard'))
    return redirect(url_for('blog.index'))

@blog.route('/comment/<string:comment_id>/delete', methods=['POST'])
@login_required
def delete_comment(comment_id):
    comment = mongo.db.comments.find_one({'_id': ObjectId(comment_id)})
    if not comment:
        abort(404)
    post = mongo.db.posts.find_one({'_id': comment['post_id']})
    if str(comment['user_id']) != str(current_user.id) and str(post['user_id']) != str(current_user.id) and not getattr(current_user, 'is_admin', False):
        abort(403)
    mongo.db.comments.delete_one({'_id': ObjectId(comment_id)})
    flash('Comment deleted successfully!', 'success')
    return redirect(url_for('blog.view_post', slug=post['slug']))

@blog.route('/dashboard')
@login_required
def dashboard():
    posts = list(mongo.db.posts.find({'user_id': ObjectId(current_user.id)}).sort('created_at', -1))
    for post in posts:
        post['author'] = get_user_by_id(post['user_id'])
        if post.get('category_id'):
            post['category'] = mongo.db.categories.find_one({'_id': post['category_id']})
        else:
            post['category'] = None
        post['comment_count'] = mongo.db.comments.count_documents({'post_id': post['_id']})
        post['tags'] = [mongo.db.tags.find_one({'_id': tag_id}) for tag_id in post.get('tags',[])]
    comments = list(mongo.db.comments.find({'user_id': ObjectId(current_user.id)}).sort('created_at', -1))
    for comment in comments:
        comment['author'] = get_user_by_id(comment['user_id'])
        comment['post'] = mongo.db.posts.find_one({'_id': comment['post_id']})
    return render_template('dashboard.html', title='Dashboard', posts=posts, comments=comments)

@blog.route('/category/<string:category_id>')
def category_posts(category_id):
    category = mongo.db.categories.find_one({'_id': ObjectId(category_id)})
    if not category:
        abort(404)
    page = request.args.get('page', 1, type=int)
    per_page = 5
    query = {'category_id': ObjectId(category_id), 'published': True}
    posts_cursor = mongo.db.posts.find(query).sort('created_at', -1)
    total = posts_cursor.count() if hasattr(posts_cursor, 'count') else mongo.db.posts.count_documents(query)
    posts = list(posts_cursor.skip((page-1)*per_page).limit(per_page))
    categories = list(mongo.db.categories.find())
    for cat in categories:  # <-- changed from 'category' to 'cat'
        cat['post_count'] = mongo.db.posts.count_documents({'category_id': cat['_id'], 'published': True})
    tags = list(mongo.db.tags.find())
    recent_posts = list(mongo.db.posts.find({'published': True}).sort('created_at', -1).limit(5))
    for post in posts:
        post['author'] = get_user_by_id(post['user_id'])
        if post.get('category_id'):
            post['category'] = mongo.db.categories.find_one({'_id': post['category_id']})
        else:
            post['category'] = None
        post['comment_count'] = mongo.db.comments.count_documents({'post_id': post['_id']})
        post['tags'] = [mongo.db.tags.find_one({'_id': tag_id}) for tag_id in post.get('tags',[])]
        post['content'] = markdown.markdown(post['content'])
    return render_template(
        'index.html',
        title=f'Category: {category["name"]}',
        posts={'items': posts, 'total': total, 'page': page, 'pages': (total+per_page-1)//per_page},
        categories=categories,
        tags=tags,
        recent_posts=recent_posts,
        current_category=category
    )

@blog.route('/tag/<string:tag_id>')
def tag_posts(tag_id):
    tag = mongo.db.tags.find_one({'_id': ObjectId(tag_id)})
    if not tag:
        abort(404)
    page = request.args.get('page', 1, type=int)
    per_page = 5
    query = {'tags': ObjectId(tag_id), 'published': True}
    posts_cursor = mongo.db.posts.find(query).sort('created_at', -1)
    total = posts_cursor.count() if hasattr(posts_cursor, 'count') else mongo.db.posts.count_documents(query)
    posts = list(posts_cursor.skip((page-1)*per_page).limit(per_page))
    categories = list(mongo.db.categories.find())
    for category in categories:
        category['post_count'] = mongo.db.posts.count_documents({'category_id': category['_id'], 'published': True})
    tags = list(mongo.db.tags.find())
    recent_posts = list(mongo.db.posts.find({'published': True}).sort('created_at', -1).limit(5))
    for post in posts:
        post['author'] = get_user_by_id(post['user_id'])
        if post.get('category_id'):
            post['category'] = mongo.db.categories.find_one({'_id': post['category_id']})
        else:
            post['category'] = None
        post['comment_count'] = mongo.db.comments.count_documents({'post_id': post['_id']})
        post['tags'] = [mongo.db.tags.find_one({'_id': tag_id}) for tag_id in post.get('tags',[])]
        post['content'] = markdown.markdown(post['content'])
    return render_template(
        'index.html',
        title=f'Tag: {tag['name']}',
        posts={'items': posts, 'total': total, 'page': page, 'pages': (total+per_page-1)//per_page},
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
