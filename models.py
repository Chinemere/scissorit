import random, string
from random import randint
from datetime import datetime, timedelta
from sqlalchemy import DateTime, Column
from utils import db
from flask_login import  UserMixin



class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer(), primary_key=True)
    username = db.Column(db.String(), nullable= False, unique=True)
    email= db.Column(db.String(), nullable= False, unique=True)
    passwordHash= db.Column(db.Text(), nullable= False)
    url= db.relationship('Url', backref='url_generator', lazy=True)
    is_active = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f'<User {self.username}>'

    def save(self):
        db.session.add(self)
        db.session.commit()
    

    def delete(self):
        db.session.delete(self)
        db.session.commit()
    
    @staticmethod
    def get_user_id(id):
        return User.query.get_or_404(id)
    
    def get_id(self):
        return self.id

    
   



class Url(db.Model):
    __tablename__ = 'urls'
    id = db.Column(db.Integer(), primary_key=True)
    url_source= db.Column(db.String(1200), nullable=False)
    scissored_url = db.Column(db.String(10), unique=True, nullable=False)
    clicks = db.Column(db.Integer(), nullable=False, default= 0)
    user = db.Column(db.Integer(), db.ForeignKey('users.id') )
    created_at = Column(DateTime, default=datetime.utcnow)

    
    def __repr__(self):
        return f'<Url {self.scissored_url}  {self.clicks}>'
    
    def save(self):
        db.session.add(self)
        db.session.commit()
    

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    
    @classmethod
    def get_url_id(cls, id):
        return cls.query.get_or_404(id)
    
    

    #function to generate short urls
    @classmethod
    def create_short_url( cls, length):
        letters = string.ascii_letters+ string.digits
        random_string = ''.join(random.choice(letters) for i in range(length))
        if not cls.query.filter_by(scissored_url=random_string).first():
            return random_string
    
    @classmethod
    def create_custom_url( cls, custom_name):
        letters = custom_name
        random_string = ''.join(letters)
        if not cls.query.filter_by(scissored_url=random_string).first():
            return letters
    
    @classmethod
    def getTime(cls, dt):
        now = datetime.utcnow()
        timeDifference= now - dt

        if timeDifference < timedelta(minutes=1):
            return ' Just now'
        elif timeDifference < timedelta(hours=1):
            minutes = int(timeDifference.total_seconds()/60)
            return f"{minutes}  minutes ago "
        elif timeDifference < timedelta(days=1):
            hours = int(timeDifference.total_seconds()/3600)
            return f" {hours} hours ago"
        elif timeDifference < timedelta(weeks=1):
            days = timeDifference.days
            return f"{days} days ago"
        else:
            years = now.year-dt.year
            return f"{years} years ago"
        




    
    




    