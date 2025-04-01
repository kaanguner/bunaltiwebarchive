# app/models/post.py
from app import db # Import the db instance created in app/__init__.py

class Post(db.Model):
    __tablename__ = 'posts'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.Text, nullable=False)
    wayback_url = db.Column(db.Text)
    original_url = db.Column(db.Text)

    # Define the relationship to Comment
    # Note: We refer to the Class name 'Comment' here
    comments = db.relationship('Comment', backref='post', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Post {self.id}: {self.title[:50]}>'