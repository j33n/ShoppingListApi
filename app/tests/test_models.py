import unittest
import os
import json
from flask import Flask
from app.app import create_app, db
from app.models import Users, ShoppingList, ShoppingListItem, UserToken

class ModelsTestCase(unittest.TestCase):
	"""Models Test Case"""

	def setUp(self):
		pass

	def test_user_model(self):
		pass
