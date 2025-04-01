# app/models/user_stats.py
from app import db

class UserStats(db.Model):
    __tablename__ = 'user_stats'

    username = db.Column(db.Text, primary_key=True)
    total_comments = db.Column(db.Integer, default=0)
    threads_participated = db.Column(db.Integer, default=0)
    first_comment_date = db.Column(db.Text)
    last_comment_date = db.Column(db.Text)

    def __repr__(self):
        return f'<UserStats for {self.username}>'