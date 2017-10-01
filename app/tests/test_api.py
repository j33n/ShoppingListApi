import unittest
import os
import json
from flask import Flask
from app.app import create_app, db

class ApiTestCase(unittest.TestCase):
	"""User test case"""

	def setUp(self):
		"""Initialise app and define test variables"""
		self.app = create_app(config_name="testing")
		self.client = self.app.test_client
		self.user = {
			'username': 'Stallion',
			'email': 'rocky@test.com',
			'password': 'secret',
			'confirm_password': 'secret'
		}
		self.shoppinglist = {
		'owner_id': '1',
		'title': 'My favorite meal',
		'description': 'Items to cook my favorite meal'
		}

		with self.app.app_context():
			# create all tables
			db.create_all()

	def register_user(self):
		return self.client().post('/auth/register', data=self.user)

	def login_user(self, email="rocky@test.com", password="secret"):
		user_data = {
            'email': email,
            'password': password
        }
		return self.client().post('/auth/login', data=user_data)

	def test_user_creation(self):
		"""Ensure we can create a user"""
		response = self.register_user()
		self.assertEqual(response.status_code, 201)
		self.assertIn("User account created successfuly", str(response.data))

	def test_user_login(self):
		"""Test user can login"""
		self.register_user()
		response = self.login_user()
		self.assertEqual(response.status_code, 200)
		self.assertIn("token", str(response.data))

	def test_create_shoppinglist(self):
		"""Test user can create a shoppinglist"""
		self.register_user()
		res = self.login_user()
		access_token = json.loads(res.data.decode())
		response = self.client().post(
			'/shoppinglists',
			headers=dict(Authorization="Bearer " + access_token['token']),
			data=self.shoppinglist
		)
		self.assertTrue('My favorite meal' in str(response.data))
		self.assertEqual(201, response.status_code)

	def test_create_duplicate_list(self):
		"""Test user can't create two similar shoppinglists"""
		self.register_user()
		res = self.login_user()
		access_token = json.loads(res.data.decode())
		self.client().post(
			'/shoppinglists',
			headers=dict(Authorization="Bearer " + access_token['token']),
			data=self.shoppinglist
		)
		response = self.client().post(
			'/shoppinglists',
			headers=dict(Authorization="Bearer " + access_token['token']),
			data=self.shoppinglist
		)
		self.assertIn(b'Shopping List My favorite meal already exists', response.data)
		self.assertEqual(response.status_code, 202)
		
	def test_valid_shoppinglist_data(self):
		"""Test user is entering valid shopping lists"""
		pass

	# def test:


	def tearDown(self):
	    """teardown all initialized variables."""
	    with self.app.app_context():
	        # drop all tables
	        db.session.remove()
	        db.drop_all()

# Make the tests conveniently executable
if __name__ == "__main__":
    unittest.main()

