import unittest
import os
import json
import time
from flask import Flask
from app.app import create_app, db
from app.models import Users

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
			'confirm_password': 'secret',
			'question': 'What is your favorite pet name?',
			'answer': 'Tiger'
		}
		self.shoppinglist = {
		'owner_id': '1',
		'title': "My favorite meal",
		'description': 'Items to cook my favorite meal'
		}
		self.shoppinglistitem = {
		'owner_id': '1',
		'shoppinglist_id': '1',
		'item_title': "Vegetables",
		'item_description': 'Carrots and Cabbages'
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
	def access_token(self):
		res = self.login_user()
		access_token = json.loads(res.data.decode())
		token = "Bearer " + access_token['token']
		return token

	def test_user_creation(self):
		"""Test we can create a user"""
		response = self.register_user()
		self.assertEqual(response.status_code, 200)
		self.assertIn("User account created successfuly", str(response.data))
		# Test a user can't be created when a question is not set
		check_security_question = self.client().post('/auth/register', data={
			'username': 'Stallion',
			'email': 'rocky@test.com',
			'password': 'secret',
			'confirm_password': 'secret'
		})
		self.assertEqual(check_security_question.status_code, 202)
		self.assertIn("Please provide a security question!!", str(check_security_question.data))

	def test_password_mismatch(self):
		"""Test user creates an account when he confirms password"""
		response = self.client().post('/auth/register', data={
			'username': 'Stallion',
			'email': 'rocky@test.com',
			'password': 'secret',
			'confirm_password': 'secreto'
		})
		self.assertEqual(response.status_code, 202)
		self.assertIn("Password does not match", str(response.data))

	def test_missing_registration_data(self):
		"""Test a user is not missing out a password"""
		response = self.client().post('/auth/register', data={
			'username': 'Stallion',
			'email': 'rocky@test.com'
		})
		self.assertEqual(response.status_code, 500)
		self.assertIn("Password must be non-empty.", str(response.data))

	def test_account_duplicate(self):
		"""Test users can't create similar accounts"""
		response = self.register_user()
		self.assertEqual(response.status_code, 200)
		self.assertIn("User account created successfuly", str(response.data))
		response1 = self.register_user()
		self.assertEqual(response1.status_code, 202)
		self.assertIn("User account already exists.", str(response1.data))

	def test_empty_values(self):
		"""Test a user is not missing out an email or password"""
		response = self.client().post('/auth/register', data={
			'username': 'Stallion',
			'email': '',
			'password': 'secret',
			'confirm_password': 'secret',
			'question': 'What is your pet name?',
			'answer': 'Tiger'
		})
		self.assertEqual(response.status_code, 500)
		self.assertIn(b"Email or Username can\'t be empty.", response.data)


	def test_user_login(self):
		"""Test user can login"""
		self.register_user()
		response = self.login_user()
		self.assertEqual(response.status_code, 200)
		self.assertIn("token", str(response.data))
		# Test invalid credentials
		wrong_cred_login = self.client().post('/auth/login', data={
			'email': 'Stallion',
			'password': 'secret'
		})
		self.assertEqual(wrong_cred_login.status_code, 202)
		self.assertIn("Invalid credentials", str(wrong_cred_login.data))

	def test_middleware(self):
		"""Test a our middleware can't be broken"""
		self.register_user()
		mess_up_token = self.access_token() + "Mess up token"
		response1 = self.client().get('/shoppinglists',
			headers=dict(Authorization=mess_up_token))
		self.assertEqual(response1.status_code, 403)
		self.assertIn(b"Invalid token. Please log in again.", response1.data)
		response2 = self.client().get('/shoppinglists',
			headers=dict(Authorization=""))
		self.assertEqual(response2.status_code, 500)
		self.assertIn(b"Authorization is not provided", response2.data)

	def test_create_shoppinglist(self):
		"""Test user can create a shoppinglist"""
		self.register_user()
		# Test empty shoppinglists
		response1 = self.client().get(
			'/shoppinglists',
			headers=dict(Authorization=self.access_token())
		)
		self.assertTrue("You don't have any shoppinglists for now.", response1.data)
		self.assertEqual(200, response1.status_code)
		# Test shoppinglists without authorization
		response2 = self.client().post(
			'/shoppinglists',
			headers=dict(Authorization=self.access_token() + '_'),
			data=self.shoppinglist
		)
		self.assertTrue('fail' in str(response2.data))
		self.assertEqual(403, response2.status_code)

		response3 = self.client().post(
			'/shoppinglists',
			headers=dict(Authorization=self.access_token()),
			data=self.shoppinglist
		)
		self.assertTrue('My favorite meal' in str(response3.data))
		self.assertEqual(201, response3.status_code)

	def test_invalid_shoppinglists(self):
		"""Test user can't create mal formatted shoppinglists"""
		self.register_user()
		response1 = self.client().post(
			'/shoppinglists',
			headers=dict(Authorization=self.access_token()),
			data={
			'owner_id': '1',
			'title': 666666,
			'description': 'Items to cook my favorite meal'
			}
		)
		response2 = self.client().post(
			'/shoppinglists',
			headers=dict(Authorization=self.access_token()),
			data={
			'owner_id': '1',
			'title': "Nyamameat",
			'description': 'Items to cook my favorite meal'
			}
		)
		response3 = self.client().post(
			'/shoppinglists',
			headers=dict(Authorization=self.access_token()),
			data={
			'owner_id': '1',
			'title': "",
			'description': 'Items to cook my favorite meal'
			}
		)
		self.assertIn(b'Value can\'t be numbers', response1.data)
		self.assertEqual(202, response1.status_code)
		self.assertIn(b'Value should be more than 10 characters', response2.data)
		self.assertEqual(202, response2.status_code)
		self.assertIn(b'Value can\'t be empty', response3.data)
		self.assertEqual(202, response3.status_code)

	def test_duplicate_shoppinglist(self):
		"""Test user can't create two similar shoppinglists"""
		self.register_user()
		access_token = self.access_token()
		self.client().post(
			'/shoppinglists',
			headers=dict(Authorization=access_token),
			data=self.shoppinglist
		)
		response = self.client().post(
			'/shoppinglists',
			headers=dict(Authorization=access_token),
			data=self.shoppinglist
		)
		self.assertIn(b'Shopping List My favorite meal already exists', response.data)
		self.assertEqual(response.status_code, 202)
		
	def test_fetch_all_shoppinglists(self):
		"""Test user is able to display all shopping lists"""
		self.register_user()
		access_token = self.access_token()
		response1 = self.client().post(
			'/shoppinglists',
			headers=dict(Authorization=access_token),
			data=self.shoppinglist
		)
		self.assertEqual(response1.status_code, 201)
		response = self.client().get(
			'/shoppinglists',
			headers=dict(Authorization=access_token)
		)
		self.assertEqual(response.status_code, 202)
		self.assertIn('My favorite meal', str(response.data))

	def test_fetch_single_shoppinglist(self):
		"""Test user is able to display a single shopping lists"""
		self.register_user()
		access_token = self.access_token()
		response = self.client().post(
			'/shoppinglists',
			headers=dict(Authorization=access_token),
			data=self.shoppinglist
		)
		self.assertEqual(response.status_code, 201)
		results = json.loads(response.data.decode())
		get_single_sl = self.client().get(
			'/shoppinglist/{0}'.format(results['id']),
			headers=dict(Authorization=access_token)
		)
		self.assertIn(b"My favorite meal", get_single_sl.data)
		self.assertEqual(get_single_sl.status_code, 201)

	def test_non_existent_shoppinglist(self):
		"""Test user can't access non existent shoppinglist"""
		self.register_user()
		access_token = self.access_token()
		response = self.client().get(
			'/shoppinglist/1',
			headers=dict(Authorization=access_token)
		)
		self.assertIn(b"Requested value '1' was not found", response.data)
		self.assertEqual(response.status_code, 202)

	def test_update_shoppinglist(self):
		"""Test a user can update a shopping list"""
		self.register_user()
		access_token = self.access_token()
		response = self.client().post(
			'/shoppinglists',
			headers=dict(Authorization=access_token),
			data=self.shoppinglist
		)
		self.assertEqual(201, response.status_code)
		results = json.loads(response.data.decode())
		update_resp = self.client().put(
			'/shoppinglist/{0}'.format(results['id']),
			headers=dict(Authorization=access_token),
			data={
				'owner_id': '1',
				'title': "My favorite shoes",
				'description': 'Converse and Jordan 2015'
			}
		)
		self.assertTrue(b"Converse and Jordan 2015" in update_resp.data)
		self.assertTrue(b"Shopping List updated successfuly" in update_resp.data)
		self.assertEqual(update_resp.status_code, 200)
		# Test shoppinglist can't take an existing name on POST
		response1 = self.client().post(
			'/shoppinglists',
			headers=dict(Authorization=access_token),
			data={
				'owner_id': '1',
				'title': "My favorite shoes",
				'description': 'Converse and Jordan 2016'
			}
		)
		self.assertTrue(b"Shopping List My favorite shoes already exists" in response1.data)
		self.assertEqual(202, response1.status_code)
		# Test shoppinglist can't take an existing name on PUT
		check_update = self.client().put(
			'/shoppinglist/1',
			headers=dict(Authorization=access_token),
			data={
				'title': "My favorite shoes",
				'description': 'Converse and Jordan 2016'
			}
		)
		self.assertTrue(b"Shopping List My favorite shoes already exists" in check_update.data)
		self.assertEqual(202, check_update.status_code)
		# Test invalid use of data on PUT
		check_wrong_update_1 = self.client().put(
			'/shoppinglist/1',
			headers=dict(Authorization=access_token),
			data={
				'title': "666",
				'description': 'Converse and Jordan 2016'
			}
		)
		check_wrong_update_2 = self.client().put(
			'/shoppinglist/1',
			headers=dict(Authorization=access_token),
			data={
				'title': 'Fish',
				'description': 'Converse and Jordan 2016'
			}
		)
		check_wrong_update_3 = self.client().put(
			'/shoppinglist/1',
			headers=dict(Authorization=access_token),
			data={
				'title': '56',
				'description': 'aaaa'
			}
		)
		check_wrong_update_4 = self.client().put(
			'/shoppinglist/1',
			headers=dict(Authorization=access_token),
			data={
				'title': 'Converse and Jordan 2016',
				'description': 'Shoe'
			}
		)

		self.assertIn(b"Value can\'t be numbers", check_wrong_update_1.data)
		self.assertEqual(202, check_wrong_update_1.status_code)
		self.assertIn(b"Value should be more than 10 characters", check_wrong_update_2.data)
		self.assertEqual(202, check_wrong_update_2.status_code)
		self.assertIn(b"Value should be more than 10 characters", check_wrong_update_3.data)
		self.assertIn(b"Value can\'t be numbers", check_wrong_update_3.data)
		self.assertEqual(202, check_wrong_update_3.status_code)
		self.assertIn(b"Value should be more than 10 characters", check_wrong_update_4.data)
		self.assertEqual(202, check_wrong_update_4.status_code)


	def test_invalid_data_update(self):
		"""Test user can't update with invalid format title or description"""
		self.register_user()
		response = self.client().post(
			'/shoppinglists',
			headers=dict(Authorization=self.access_token()),
			data=self.shoppinglist
		)
		self.assertTrue(response.status_code, 201)
		response1 = self.client().put(
			'/shoppinglist/1',
			headers=dict(Authorization=self.access_token()),
			data={
			'owner_id': '1',
			'title': 666666,
			'description': 'Items to cook my favorite meal'
			}
		)
		response2 = self.client().put(
			'/shoppinglist/1',
			headers=dict(Authorization=self.access_token()),
			data={
			'owner_id': '1',
			'title': "Nyamameat",
			'description': 'Items to cook my favorite meal'
			}
		)
		response3 = self.client().put(
			'/shoppinglist/1',
			headers=dict(Authorization=self.access_token()),
			data={
			'owner_id': '1',
			'title': "",
			'description': 'Items to cook my favorite meal'
			}
		)
		response4 = self.client().put(
			'/shoppinglist/1',
			headers=dict(Authorization=self.access_token()),
			data={
			'owner_id': True,
			'title': "Nyamameat",
			'description': 'Items to cook my favorite meal'
			}
		)
		response5 = self.client().put(
			'/shoppinglist/1',
			headers=dict(Authorization=self.access_token()),
			data={
			'owner_id': "",
			'title': "",
			'description': 'Items to cook my favorite meal'
			}
		)
		self.assertIn(b'Value can\'t be numbers', response1.data)
		self.assertEqual(202, response1.status_code)
		self.assertIn(b'Value should be more than 10 characters', response2.data)
		self.assertEqual(202, response2.status_code)
		self.assertIn(b'Value can\'t be empty', response3.data)
		self.assertEqual(202, response3.status_code)
		self.assertIn(b'fail', response4.data)
		self.assertEqual(202, response4.status_code)
		self.assertIn(b'fail', response5.data)
		self.assertEqual(202, response5.status_code)


	def test_delete_shoppinglist(self):
		"""Test a user can delete a shopping list"""
		self.register_user()
		access_token = self.access_token()
		response = self.client().post(
			'/shoppinglists',
			headers=dict(Authorization=access_token),
			data=self.shoppinglist
		)
		self.assertEqual(201, response.status_code)
		results = json.loads(response.data.decode())
		update_resp = self.client().delete(
			'/shoppinglist/{0}'.format(results['id']),
			headers=dict(Authorization=access_token)
		)
		# Test delete non existing value
		invalid_deletion = self.client().delete(
			'/shoppinglist/2'.format(results['id']),
			headers=dict(Authorization=access_token)
		)
		self.assertIn(b"Requested value \'2\' was not found", invalid_deletion.data)
		self.assertEqual(202, invalid_deletion.status_code)
		self.assertFalse(b"Items to cook my favorite meal" in update_resp.data)
		self.assertIn(b"Shopping List \'My favorite meal\' deleted successfuly", update_resp.data)
		self.assertEqual(update_resp.status_code, 201)

	def test_add_shoppinglistitem(self):
		"""Test a user can add an item to shoppinglist"""
		self.register_user()
		access_token = self.access_token()
		response = self.client().post(
			'/shoppinglists',
			headers=dict(Authorization=access_token),
			data=self.shoppinglist
		)
		self.assertEqual(response.status_code, 201)
		results = json.loads(response.data.decode())

		"""Test our shopping list is empty"""
		check_emptyness = self.client().get(
			'/shoppinglist/1/items',
			headers=dict(Authorization=access_token)
		)
		self.assertTrue(b"You don\'t have any items for now" in check_emptyness.data)
		self.assertEqual(202, check_emptyness.status_code)

		# Test invalid values are not saved
		create_invalid_item = self.client().post(
			'/shoppinglist/{0}/items'.format(results['id']),
			headers=dict(Authorization=access_token),
			data={
				'owner_id': '1',
				'shoppinglist_id': '1',
				'item_title': "",
				'item_description': 'Carrots and Cabbages'
				}
			)
		self.assertIn(b'Value can\'t be empty', create_invalid_item.data)
		self.assertEqual(202, create_invalid_item.status_code)

		create_invalid_item_2 = self.client().post(
			'/shoppinglist/{0}/items'.format(results['id']),
			headers=dict(Authorization=access_token),
			data={
				'owner_id': '1',
				'shoppinglist_id': '1',
				'item_title': "Carrots and Cabbages",
				'item_description': '66666'
				}
			)
		self.assertIn(b'Value can\'t be numbers', create_invalid_item_2.data)
		self.assertEqual(202, create_invalid_item_2.status_code)
		
		create_item = self.client().post(
			'/shoppinglist/{0}/items'.format(results['id']),
			headers=dict(Authorization=access_token),
			data=self.shoppinglistitem
		)
		self.assertIn(b'Vegetables', create_item.data)
		self.assertEqual(201, create_item.status_code)

		create_invalid_item_2 = self.client().post(
			'/shoppinglist/{0}/items'.format(results['id']),
			headers=dict(Authorization=access_token),
			data={
				'owner_id': '1',
				'shoppinglist_id': '1',
				'item_title': "Carrots",
				'item_description': '66666'
				}
		)
		self.assertIn(b'Value should be more than 10 characters', create_invalid_item_2.data)
		self.assertIn(b'Value can\'t be numbers', create_invalid_item_2.data)
		self.assertEqual(202, create_invalid_item_2.status_code)

	def test_invalid_item_value(self):
		"""Test user can't update with invalid format title or description"""
		self.register_user()
		response = self.client().post(
			'/shoppinglists',
			headers=dict(Authorization=self.access_token()),
			data=self.shoppinglist
		)
		self.assertTrue(response.status_code, 201)
		results = json.loads(response.data.decode())
		response1 = self.client().post(
			'/shoppinglist/{0}/items'.format(results['id']),
			headers=dict(Authorization=self.access_token()),
			data={
			'owner_id': '1',
			'shoppinglist_id': results['id'],
			'item_title': 666666,
			'item_description': 'Carrots and Tomatoes'
			}
		)
		response2 = self.client().post(
			'/shoppinglist/{0}/items'.format(results['id']),
			headers=dict(Authorization=self.access_token()),
			data={
			'owner_id': '1',
			'shoppinglist_id': results['id'],
			'item_title': "Meat",
			'item_description': 'Carrots and Tomatoes'
			}
		)
		response3 = self.client().post(
			'/shoppinglist/{0}/items'.format(results['id']),
			headers=dict(Authorization=self.access_token()),
			data={
			'owner_id': '1',
			'shoppinglist_id': results['id'],
			'item_title': "",
			'item_description': 'Carrots and Tomatoes'
			}
		)
		self.assertIn(b'Value can\'t be numbers', response1.data)
		self.assertEqual(202, response1.status_code)
		self.assertIn(b'Value should be more than 10 characters', response2.data)
		self.assertEqual(202, response2.status_code)
		self.assertIn(b'Value can\'t be empty', response3.data)
		self.assertEqual(202, response3.status_code)

	def test_get_all_shoppinglist_items(self):
		"""Test that a user can get all items on a shoppiglist"""
		self.register_user()
		access_token = self.access_token()
		response = self.client().post(
			'/shoppinglists',
			headers=dict(Authorization=access_token),
			data=self.shoppinglist
		)
		self.assertEqual(response.status_code, 201)
		results = json.loads(response.data.decode())
		create_item = self.client().post(
			'/shoppinglist/{0}/items'.format(results['id']),
			headers=dict(Authorization=access_token),
			data=self.shoppinglistitem)
		self.assertEqual(201, create_item.status_code)
		get_items = self.client().get(
			'/shoppinglist/{0}/items'.format(results['id']),
			headers=dict(Authorization=access_token)
		)
		self.assertEqual(get_items.status_code, 202)
		self.assertIn('Carrots and Cabbages', str(get_items.data))

	def test_fetch_shoppinglist_item(self):
		"""Test user can get a single item on the shoppiglist"""
		self.register_user()
		access_token = self.access_token()
		response = self.client().post(
			'/shoppinglists',
			headers=dict(Authorization=access_token),
			data=self.shoppinglist
		)
		self.assertEqual(response.status_code, 201)
		results = json.loads(response.data.decode())
		create_item = self.client().post(
			'/shoppinglist/{0}/items'.format(results['id']),
			headers=dict(Authorization=access_token),
			data=self.shoppinglistitem)
		self.assertEqual(201, create_item.status_code)
		results1 = json.loads(create_item.data.decode())
		# Test one can be fetched
		get_single_item = self.client().get(
			'/shoppinglist/{0}/item/{1}'.format(results['id'], results1['item_id']),
			headers=dict(Authorization=access_token)
		)
		self.assertEqual(get_single_item.status_code, 201)
		self.assertIn('Carrots and Cabbages', str(get_single_item.data))
		# Test item title can't be duplicated
		create_duplicate_item = self.client().post(
			'/shoppinglist/{0}/items'.format(results['id']),
			headers=dict(Authorization=access_token),
			data=self.shoppinglistitem)
		self.assertEqual(create_duplicate_item.status_code, 202)
		self.assertIn(b'Shopping List item Vegetables already exists', create_duplicate_item.data)
		# Test non existing items
		get_wrong_item = self.client().get(
			'/shoppinglist/{0}/item/3'.format(results['id'], results1['item_id']),
			headers=dict(Authorization=access_token)
		)
		self.assertIn('Requested value \\\'3\\\' was not found', str(get_wrong_item.data))
		self.assertEqual(get_wrong_item.status_code, 202)


	def test_update_shoppinglistitem(self):
		"""Test a user can update an item on shoppinglist"""
		self.register_user()
		access_token = self.access_token()
		response = self.client().post(
			'/shoppinglists',
			headers=dict(Authorization=access_token),
			data=self.shoppinglist
		)
		self.assertEqual(201, response.status_code)
		results = json.loads(response.data.decode())
		create_item = self.client().post(
			'/shoppinglist/{0}/items'.format(results['id']),
			headers=dict(Authorization=access_token),
			data=self.shoppinglistitem)
		self.assertEqual(201, create_item.status_code)
		results1 = json.loads(create_item.data.decode())
		update_resp = self.client().put(
			'/shoppinglist/{0}/item/{1}'.format(results['id'], results1['item_id']),
			headers=dict(Authorization=access_token),
			data={
				'owner_id': '1',
				'shoppinglist_id': '1',
				'item_title': "Sausages and stuff",
				'item_description': 'Carrots and Waffles'
			}
		)
		self.assertTrue(b"Carrots and Waffles" in update_resp.data)
		self.assertTrue(b"Shopping list item updated successfuly" in update_resp.data)
		self.assertEqual(update_resp.status_code, 200)
		# Test updating with existing name
		non_existing_updates = self.client().put(
			'/shoppinglist/{}/item/4'.format(results['id']),
			headers=dict(Authorization=access_token),
			data={
				'owner_id': '1',
				'shoppinglist_id': '1',
				'item_title': "Sausages and stuff",
				'item_description': 'Carrots and Waffles'
			}
		)
		self.assertTrue(b"Shopping list item Sausages and stuff already exists" in non_existing_updates.data)
		self.assertEqual(non_existing_updates.status_code, 202)

	def test_invalid_item_update(self):
		"""Test user can't update item with invalid title or description"""
		self.register_user()
		access_token = self.access_token()
		response = self.client().post(
			'/shoppinglists',
			headers=dict(Authorization=self.access_token()),
			data=self.shoppinglist
		)
		self.assertTrue(response.status_code, 201)
		results = json.loads(response.data.decode())
		create_item = self.client().post(
			'/shoppinglist/{0}/items'.format(results['id']),
			headers=dict(Authorization=access_token),
			data=self.shoppinglistitem)
		self.assertEqual(201, create_item.status_code)
		results1 = json.loads(create_item.data.decode())
		update_resp = self.client().put(
			'/shoppinglist/{0}/item/{1}'.format(results['id'], results1['item_id']),
			headers=dict(Authorization=access_token),
			data={
				'owner_id': '1',
				'shoppinglist_id': '1',
				'item_title': "Sausages and stuff",
				'item_description': 'Carrots and Waffles'
			}
		)
		response1 = self.client().put(
			'/shoppinglist/{0}/item/{1}'.format(results['id'], results1['item_id']),
			headers=dict(Authorization=self.access_token()),
			data={
			'owner_id': '1',
			'shoppinglist_id': results['id'],
			'item_title': 666666,
			'item_description': 'Carrots and Tomatoes'
			}
		)
		response2 = self.client().put(
			'/shoppinglist/{0}/item/{1}'.format(results['id'], results1['item_id']),
			headers=dict(Authorization=self.access_token()),
			data={
			'owner_id': '1',
			'shoppinglist_id': results['id'],
			'item_title': "Meat",
			'item_description': 'Carrots and Tomatoes'
			}
		)
		response3 = self.client().put(
			'/shoppinglist/{0}/item/{1}'.format(results['id'], results1['item_id']),
			headers=dict(Authorization=self.access_token()),
			data={
			'owner_id': '1',
			'shoppinglist_id': results['id'],
			'item_title': "Carrots and Tomatoes",
			'item_description': ''
			}
		)
		response4 = self.client().put(
			'/shoppinglist/{0}/item/{1}'.format(results['id'], results1['item_id']),
			headers=dict(Authorization=self.access_token()),
			data={
			'owner_id': '1',
			'shoppinglist_id': results['id'],
			'item_title': "9999",
			'item_description': "Fish"
			}
		)
		self.assertIn(b'Value can\'t be numbers', response1.data)
		self.assertEqual(202, response1.status_code)
		self.assertIn(b'Value should be more than 10 characters', response2.data)
		self.assertEqual(202, response2.status_code)
		self.assertIn(b'Value can\'t be empty', response3.data)
		self.assertEqual(202, response3.status_code)
		self.assertIn(b'Value can\'t be numbers', response4.data)
		self.assertIn(b'Value should be more than 10 characters', response4.data)
		self.assertEqual(202, response4.status_code)

	def test_delete_shoppinglistitem(self):
		"""Test a user can delete an item on a shopping list"""
		self.register_user()
		access_token = self.access_token()
		response = self.client().post(
			'/shoppinglists',
			headers=dict(Authorization=access_token),
			data=self.shoppinglist
		)
		self.assertEqual(201, response.status_code)
		results = json.loads(response.data.decode())
		create_item = self.client().post(
			'/shoppinglist/{0}/items'.format(results['id']),
			headers=dict(Authorization=access_token),
			data=self.shoppinglistitem)
		self.assertEqual(201, create_item.status_code)
		results1 = json.loads(create_item.data.decode())
		delete_item = self.client().delete(
			'/shoppinglist/{0}/item/{1}'.format(results['id'], results1['item_id']),
			headers=dict(Authorization=access_token)
		)
		self.assertFalse(b"Carrots and Cabbages" in delete_item.data)
		self.assertIn(b"Shopping list item \'Vegetables\' deleted successfuly", delete_item.data)
		self.assertEqual(delete_item.status_code, 201)

	def test_delete_wrong_shoppinglistitem(self):
		"""Test a user can delete an item on a shopping list"""
		self.register_user()
		access_token = self.access_token()
		response = self.client().post(
			'/shoppinglists',
			headers=dict(Authorization=access_token),
			data=self.shoppinglist
		)
		self.assertEqual(201, response.status_code)
		results = json.loads(response.data.decode())
		delete_item = self.client().delete(
			'/shoppinglist/{0}/item/7'.format(results['id']),
			headers=dict(Authorization=access_token)
		)
		self.assertTrue(b"Requested value '7' was not found" in delete_item.data)
		self.assertEqual(delete_item.status_code, 202)

	def test_token_unprovided(self):
		"""Test a token is always provided on login"""
		self.register_user()
		url_list_get = ['/shoppinglists', '/shoppinglist/1', '/shoppinglist/1/items', '/shoppinglist/1/item/1', '/user']
		for url in url_list_get:
			response = self.client().get(
				url
				)
			self.assertIn(b"Authorization is not provided", response.data)
			self.assertEqual(response.status_code, 500)
		url_list_post = ['/shoppinglists', '/shoppinglist/1/items', 'auth/logout']
		for post_url in url_list_post:
			# Test post requests without Authorization
			response2 = self.client().post(
				post_url
				)
			self.assertIn(b"Authorization is not provided", response2.data)
			self.assertEqual(response2.status_code, 500)
		url_list_put = ['/shoppinglist/1', '/shoppinglist/1/item/1', '/user']
		for put_url in url_list_put:
			# Test put requests without Authorization
			response3 = self.client().put(
				put_url
				)
			self.assertIn(b"Authorization is not provided", response3.data)
			self.assertEqual(response3.status_code, 500)
		url_list_delete = ['/shoppinglist/1', '/shoppinglist/2/item/2']
		for delete_url in url_list_delete:
			# Test delete requests without Authorization
			response4 = self.client().delete(
				delete_url
				)
			self.assertIn(b"Authorization is not provided", response4.data)
			self.assertEqual(response4.status_code, 500)
	

	def test_welcome_page(self):
		"""Test welcome page"""
		response = self.client().get('/')
		self.assertTrue(b"Welcome to Shopping List API" in response.data)
		self.assertEqual(response.status_code, 200)

	def test_valid_logout(self):
		"""Test a user can logout smoothly"""
		self.register_user()
		access_token = self.access_token()
		logout_response = self.client().post(
			'/auth/logout',
			headers=dict(Authorization=access_token)
		)
		self.assertIn(b"Successfully logged out.", logout_response.data)
		self.assertEquals(200, logout_response.status_code)

	def test_token_duplicate(self):
		"""Test that a token can't be used twice ever"""
		self.register_user()
		access_token = self.access_token()
		logout_response = self.client().post(
			'/auth/logout',
			headers=dict(Authorization=access_token)
		)
		self.assertIn(b"Successfully logged out.", logout_response.data)
		self.assertEquals(200, logout_response.status_code)
		response = self.client().get(
			'/shoppinglists',
			headers=dict(Authorization=access_token)
		)
		self.assertIn(b"Token created. Please log in again.", response.data)
		self.assertTrue(403, response.status_code)

	def test_logout_invalid_token(self):
		"""Test a logout requires a valid token"""
		self.register_user()
		mess_up_token = self.access_token() + "Mess up token"
		logout_response = self.client().post(
			'/auth/logout',
			headers=dict(Authorization=mess_up_token)
		)
		self.assertEqual(logout_response.status_code, 403)
		self.assertIn(b"Invalid token. Please log in again.", logout_response.data)

	def test_question(self):
		"""Test user's question to reset password"""
		create_question = self.register_user()
		# Test create question
		self.assertIn(b"User account created successfuly", create_question.data)
		self.assertTrue(200, create_question.data)
		# Test create an invalid question
		create_invalid_question = self.client().post(
			'/auth/register', data={
				'username': 'Stallion',
				'email': 'rocky@test.com',
				'password': 'secret',
				'confirm_password': 'secret',
				'question': 'What is your favorite pet name',
				'answer': '1'
			}
		)
		self.assertIn(b"Invalid security question!!", create_invalid_question.data)
		self.assertTrue(202, create_invalid_question.status_code)

	def test_reset_password(self):
		"""Test a user can reset password using a security question"""
		register_user = self.register_user()
		self.assertIn("User account created successfuly", str(register_user.data))
		access_token = self.access_token()
		reset_password = self.client().post(
			'/resetpassword',
			headers=dict(Authorization=access_token),
			data={
			'question':'What is your favorite pet name?',
			'answer': 'Tiger',
			'old_password': 'secret',
			'new_password': '123456'
			}
		)
		self.assertTrue(200, reset_password.status_code)
		self.assertIn(b'Your password was resetted successfuly', reset_password.data)
		# Test reset password requires an authorization
		mess_up_token = access_token + "Mess up token"
		chech_authorization = self.client().post(
			'/resetpassword',
			headers=dict(Authorization=mess_up_token),
			data={
			'question':'What is your favorite pet name?',
			'answer': 'Tiger',
			'old_password': 'secret',
			'new_password': '123456'
			}
		)
		self.assertTrue(200, chech_authorization.status_code)
		self.assertIn(b'Invalid token. Please log in again.', chech_authorization.data)
		# Test question can not be empty
		invalid_security_question = self.client().post(
			'/resetpassword',
			headers=dict(Authorization=access_token),
			data={
			'question':'',
			'answer': 'Tiger',
			'old_password': 'secret',
			'new_password': '123456'
			}
		)
		self.assertTrue(202, invalid_security_question.status_code)
		self.assertIn(b'Invalid security question, please try again!', invalid_security_question.data)
		# Test a user is not using a wrong previous password
		check_invalid_oldpassword = self.client().post(
			'/resetpassword',
			headers=dict(Authorization=access_token),
			data={
			'question':'What is your favorite pet name?',
			'answer': 'Tiger',
			'old_password': 'secret_society',
			'new_password': '123456'
			}
		)
		self.assertTrue(202, check_invalid_oldpassword.status_code)
		self.assertIn(b'Invalid password!!', check_invalid_oldpassword.data)
		# Logout the user to test the new password
		logout_user = self.client().post(
			'/auth/logout',
			headers=dict(Authorization=access_token)
		)
		self.assertIn(b'Successfully logged out.', logout_user.data)
		# Test a user can login with his new password
		use_new_password = self.client().post('/auth/login', data={
			'email':'rocky@test.com',
			'password':'123456'
			}
		)
		self.assertEqual(200, use_new_password.status_code)
		self.assertIn(b'', use_new_password.data)

	def test_update_accountinfo(self):
		""" Test a user can change username and email"""
		self.register_user()
		access_token = self.access_token()
		# change user information
		change_userinfo = self.client().put('/user',
			headers=dict(Authorization=access_token),
			data={'new_email': 'johndoe@test.com', 'new_username':'John Doe', 'password': 'secret'})
		self.assertEqual(200, change_userinfo.status_code)
		self.assertIn(b"Account information changed successfuly", change_userinfo.data)
		# check update can't happen without password
		wrong_password_userupdate = self.client().put('/user',
			headers=dict(Authorization=access_token),
			data={
			'new_email': 'johndoe@test.com',
			'new_username':'John Doe',
			'password': 'my_wrong_password'}
		)
		self.assertEqual(202, wrong_password_userupdate.status_code)
		self.assertIn(b"You need your password to update account info.", wrong_password_userupdate.data)
		# check email and username were updated
		check_update = self.client().get('/user', headers=dict(Authorization=access_token))
		self.assertEqual(200, check_update.status_code)
		self.assertIn(b"johndoe@test.com", check_update.data)
		self.assertIn(b"John Doe", check_update.data)


	def test_token_expiration(self):
		""" Test if a token has expired after a certain time"""
		self.register_user()
		access_token = self.access_token()
		time.sleep(6)
		response = self.client().post(
			'/shoppinglists',
			headers=dict(Authorization=access_token),
			data=self.shoppinglist
		)
		self.assertIn(b"Signature expired. Please log in again.", response.data)


	def tearDown(self):
	    """teardown all initialized variables."""
	    with self.app.app_context():
	        # drop all tables
	        db.session.remove()
	        db.drop_all()

