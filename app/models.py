import datetime
import jwt
from flask import current_app
from app.app import db
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Users(db.Model):

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String, nullable=False, unique=True)
    password = db.Column(db.String, nullable=False)
    question = db.Column(db.String(255), nullable=False)
    answer = db.Column(db.String(255), nullable=False)
    date_created = db.Column(db.DateTime, default=db.func.current_timestamp())

    def __init__(self, username, email, password, question, answer):
        """Initialize with username, email and password"""
        self.username = username
        self.email = email
        self.password = password
        self.question = question
        self.answer = answer

    def save_user(self):
        db.session.add(self)
        db.session.commit()

    def encode_token(self, user_id):
        """Generates the Auth Token"""
        payload = {
            'exp': datetime.datetime.utcnow() + datetime.timedelta(days=0, seconds=5),
            'iat': datetime.datetime.utcnow(),
            'sub': user_id
        }
        return jwt.encode(
            payload,
            current_app.config.get('SECRET_KEY'),
            algorithm='HS256'
        )

    @staticmethod
    def decode_token(user_id):
        """Validates the auth token"""
        try:
            payload = jwt.decode(user_id, current_app.config.get('SECRET_KEY'))
            is_created_token = UserToken.check_token(user_id)
            if is_created_token:
                return 'Token created. Please log in again.'
            else:
                return payload['sub']
        except jwt.ExpiredSignatureError:
            return 'Signature expired. Please log in again.'
        except jwt.InvalidTokenError:
            return 'Invalid token. Please log in again.'

    def __repr__(self):
        return '<username {}'.format(self.username)

class UserToken(db.Model):
    """
    User Token Model for storing JWT tokens
    """
    __tablename__ = 'user_token'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    token = db.Column(db.String(500), unique=True, nullable=False)
    created_on = db.Column(db.DateTime, nullable=False)

    def __init__(self, token):
        self.token = token
        self.created_on = datetime.datetime.now()    

    @staticmethod
    def check_token(auth_token):
        # check whether auth token has been created
        res = UserToken.query.filter_by(token=str(auth_token)).first()
        if res:
            return True
        else:
            return False

    def __repr__(self):
        return '<token: {}'.format(self.token)

class ShoppingList(db.Model):
    """Model for Shopping Lists"""
    __tablename__ = 'shoppinglists'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    owner_id = db.Column(db.Integer, nullable=False)
    title = db.Column(db.String(255), nullable=False, unique=True)
    description = db.Column(db.String(500), nullable=False)
    date_created = db.Column(db.DateTime, default=db.func.current_timestamp())
    date_modified = db.Column(
        db.DateTime, default=db.func.current_timestamp(),
        onupdate=db.func.current_timestamp())

    def __init__(self, owner_id, title, description):
        self.owner_id = owner_id
        self.title = title
        self.description = description

    def save_shoppinglist(self):
        db.session.add(self)
        db.session.commit()

    def delete_shoppinglist(self):
        db.session.delete(self)
        db.session.commit()

    def __repr__(self):
        return '<title {}'.format(self.title)

class ShoppingListItem(db.Model):
    """Model for Shopping Lists"""
    __tablename__ = 'shoppinglistitems'

    item_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    owner_id = db.Column(db.Integer, nullable=False)
    shoppinglist_id = db.Column(db.Integer, nullable=False)
    item_title = db.Column(db.String(255), nullable=False, unique=True)
    item_description = db.Column(db.String(500), nullable=False)
    date_created = db.Column(db.DateTime, default=db.func.current_timestamp())
    date_modified = db.Column(
        db.DateTime, default=db.func.current_timestamp(),
        onupdate=db.func.current_timestamp())

    def __init__(self, owner_id, shoppinglist_id, item_title, item_description):
        self.owner_id = owner_id
        self.shoppinglist_id = shoppinglist_id
        self.item_title = item_title
        self.item_description = item_description

    def save_shoppinglistitem(self):
        db.session.add(self)
        db.session.commit()

    def delete_shoppinglistitem(self):
        db.session.delete(self)
        db.session.commit()

    def __repr__(self):
        return '<item_title {}'.format(self.item_title)