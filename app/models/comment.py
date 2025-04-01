# app/models/comment.py
from app import db

class Comment(db.Model):
    __tablename__ = 'comments'

    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), nullable=False) # Links to posts.id
    author = db.Column(db.Text, nullable=False, index=True)
    comment_date = db.Column(db.Text)
    comment_time = db.Column(db.Text)
    comment_number = db.Column(db.Text)
    content = db.Column(db.Text, nullable=False)

    # The 'post' backref is automatically created by the relationship in Post model

    def __repr__(self):
        return f'<Comment {self.id} by {self.author} on Post {self.post_id}>'