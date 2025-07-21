from datetime import datetime
from flask_blog.app import mongo
from bson.objectid import ObjectId

class Comment:
    @staticmethod
    def create(data):
        data['created_at'] = datetime.utcnow()
        data['updated_at'] = datetime.utcnow()
        data['approved'] = data.get('approved', True)
        result = mongo.db.comments.insert_one(data)
        return str(result.inserted_id)

    @staticmethod
    def get_by_id(comment_id):
        return mongo.db.comments.find_one({'_id': ObjectId(comment_id)})

    @staticmethod
    def find_by_post(post_id):
        return list(mongo.db.comments.find({'post_id': post_id, 'parent_id': None}).sort('created_at', -1))

    @staticmethod
    def find_replies(parent_id):
        return list(mongo.db.comments.find({'parent_id': parent_id}).sort('created_at', -1))

    @staticmethod
    def update(comment_id, data):
        data['updated_at'] = datetime.utcnow()
        mongo.db.comments.update_one({'_id': ObjectId(comment_id)}, {'$set': data})

    @staticmethod
    def delete(comment_id):
        mongo.db.comments.delete_one({'_id': ObjectId(comment_id)})
