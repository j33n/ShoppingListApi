"""This module contains all the test bases needed by our tests"""
import json
import unittest

from api import create_app, db

class TestBase(unittest.TestCase):
    """Base class which other test suite will inherit from"""

    def setUp(self):
        """Initialise app and define test variables"""
        self.app = create_app(config_name="testing")
        self.client = self.app.test_client
        self.user = {
            'username': 'Stallion',
            'email': 'rocky@test.com',
            'password': 'secret',
            'confirm_password': 'secret',
            'question': 'What is your favorite pet name?',
            'answer': 'Monster'
        }
        self.shoppinglist = {
            'title': "My favorite meal",
            'description': 'Items to cook my favorite meal'
        }
        self.shoppinglistitem = {
            'item_title': "Vegetables",
            'item_description': 'Carrots and Cabbages'
        }

        with self.app.app_context():
            # create all tables
            db.create_all()

    def register_user(self):
        """Helper to register a user"""
        return self.client().post('/api/v1/auth/register', data=self.user)

    def login_user(self, email="rocky@test.com", password="secret"):
        """Helper to login a user"""
        user_data = {
            'email': email,
            'password': password
        }
        return self.client().post('/api/v1/auth/login', data=user_data)

    def access_token(self):
        """Helper to login a user and return a token"""
        res = self.login_user()
        loaded_token = json.loads(res.data.decode())
        bearer_token = "Bearer {}".format(loaded_token['token'])
        return bearer_token

    def create_shoppinglist(self):
        """Helper to create a shoppinglist"""
        access_token = self.access_token()
        return self.client().post(
            '/api/v1/shoppinglists',
            headers=dict(Authorization=access_token),
            data=self.shoppinglist
        )

    def create_item(self):
        """Helper to create an item on a shoppinglist"""
        access_token = self.access_token()
        self.create_shoppinglist()
        return self.client().post(
            '/api/v1/shoppinglists/1/items',
            headers=dict(Authorization=access_token),
            data=self.shoppinglistitem
        )

    def logout_user(self):
        """Helper to logout a user on"""
        return self.client().post(
            '/api/v1/auth/logout',
            headers=dict(Authorization=self.access_token())
        )

    def tearDown(self):
        """teardown all initialized variables."""
        with self.app.app_context():
            # drop all tables
            db.session.remove()
            db.drop_all()
