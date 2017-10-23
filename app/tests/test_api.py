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
		response = self.client().post(
			'/shoppinglists',
			headers=dict(Authorization=self.access_token()),
			data=self.shoppinglist
		)
		self.assertTrue('My favorite meal' in str(response.data))
		self.assertEqual(201, response.status_code)
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
		self.assertEqual(update_resp.status_code, 201)

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
		self.assertIn(b'Value can\'t be numbers', response1.data)
		self.assertEqual(202, response1.status_code)
		self.assertIn(b'Value should be more than 10 characters', response2.data)
		self.assertEqual(202, response2.status_code)
		self.assertIn(b'Value can\'t be empty', response3.data)
		self.assertEqual(202, response3.status_code)


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
		create_item = self.client().post(
			'/shoppinglist/{0}/items'.format(results['id']),
			headers=dict(Authorization=access_token),
			data=self.shoppinglistitem
		)
		self.assertIn(b'Vegetables', create_item.data)
		self.assertEqual(201, create_item.status_code)

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
		get_single_item = self.client().get(
			'/shoppinglist/{0}/item/{1}'.format(results['id'], results1['item_id']),
			headers=dict(Authorization=access_token)
		)
		self.assertEqual(get_single_item.status_code, 201)
		self.assertIn('Carrots and Cabbages', str(get_single_item.data))

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
		self.assertEqual(update_resp.status_code, 201)

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

	def test_delete_shoppinglist(self):
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

	def test_delete_shoppinglist(self):
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



	def tearDown(self):
	    """teardown all initialized variables."""
	    with self.app.app_context():
	        # drop all tables
	        db.session.remove()
	        db.drop_all()

# Make the tests conveniently executable
if __name__ == "__main__":
    unittest.main()

