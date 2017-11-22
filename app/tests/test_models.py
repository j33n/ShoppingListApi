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
		self.user = Users(
			username="John Doe",
			email="johndoe@sl.com",
			password="secret",
			question="What is the name of your pet?",
			answer="Beast"
		)
		self.shoppinglist = ShoppingList(owner_id="1", title="Yellow Bananas", description="johndoe@sl.com")
		self.shoppinglistitem = ShoppingListItem(owner_id="1", shoppinglist_id="1", item_title="Yellow Bananas with green", item_description="And maracuja")
		self.usertoken = UserToken(token="a_certain_token")
		with self.app.app_context():
			# create all tables
			db.create_all()

	def test_user_model(self):	
		user = self.user
		# Test User model presentation
		self.assertEquals(str(user), "<username John Doe")

	def test_shoppinglist_model(self):
		shoppinglist = self.shoppinglist
		# Test Shopping list model presentation
		self.assertEquals(str(shoppinglist), "<title Yellow Bananas")

	def test_shoppinglistitem_model(self):
		shoppinglistitem = self.shoppinglistitem
		# Test Shopping list item model presentation
		self.assertEquals(str(shoppinglistitem), "<item_title Yellow Bananas with green")

	def test_user_token_model(self):
		usertoken = self.usertoken
		# Test Shopping list item model presentation
		self.assertEquals(str(usertoken), "<token: a_certain_token")


	def tearDown(self):
	    """teardown all initialized variables."""
	    with self.app.app_context():
	        # drop all tables
	        db.session.remove()
	        db.drop_all()
