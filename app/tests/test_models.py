import unittest
import os
import json
from flask import Flask
from app.app import create_app, db
from app.models import Users, ShoppingList, ShoppingListItem, UserToken

class ModelsTestCase(unittest.TestCase):
	"""Models Test Case"""

	def setUp(self):
		self.app = create_app(config_name="testing")
		self.user = Users(username="John Doe", email="johndoe@sl.com", password="secret")
		with self.app.app_context():
			# create all tables
			db.create_all()

	def test_user_model(self):
		pass

	def tearDown(self):
	    """teardown all initialized variables."""
	    with self.app.app_context():
	        # drop all tables
	        db.session.remove()
	        db.drop_all()
