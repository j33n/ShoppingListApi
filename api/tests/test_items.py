"""
This module contains all the test suite for Items
"""
import json

from api.tests.basetest import TestBase


class ItemsTestCase(TestBase):
    """Items test case"""

    def test_add_shoppinglistitem(self):
        """Test a user can add an item to shoppinglist"""
        self.register_user()
        create_item = self.create_item()
        self.assertIn(b'vegetables', create_item.data)
        self.assertEqual(200, create_item.status_code)

    def test_no_items_yet(self):
        """Test a user gets a valid message when his list is empty"""
        self.register_user()
        self.create_shoppinglist()
        get_items = self.client().get(
            '/api/v1/shoppinglists/1/items',
            headers=dict(Authorization=self.access_token())
        )
        self.assertIn(b'You don\'t have any items for now', get_items.data)
        self.assertEqual(400, get_items.status_code)

    def test_emptiness_items(self):
        """Test empty values are not saved"""
        self.register_user()
        access_token = self.access_token()
        self.create_shoppinglist()
        empty_item = self.client().post(
            '/api/v1/shoppinglists/1/items',
            headers=dict(Authorization=self.access_token()),
            data={
                'item_title': "",
                'item_description': 'Carrots and Cabbages'
            }
        )
        self.assertIn(b'Your item_title is empty', empty_item.data)
        self.assertEqual(400, empty_item.status_code)

    def test_numbers_items(self):
        """Test items are not digits"""
        self.register_user()
        self.create_shoppinglist()
        create_item = self.client().post(
            '/api/v1/shoppinglists/1/items',
            headers=dict(Authorization=self.access_token()),
            data={
                'item_title': "Carrots and Cabbages",
                'item_description': '66666'
            }
        )
        self.assertIn(b'Item_Description can\'t be numbers only',
                      create_item.data)
        self.assertEqual(400, create_item.status_code)

    def test_empty_items(self):
        """Test items are not digits"""
        self.register_user()
        self.create_shoppinglist()
        empty_item = self.client().post(
            '/api/v1/shoppinglists/1/items',
            headers=dict(Authorization=self.access_token()),
            data={
                'item_title': "",
                'item_description': 'Carrots and Tomatoes'
            }
        )
        self.assertIn(b'Your item_title is empty', empty_item.data)
        self.assertEqual(400, empty_item.status_code)

    def test_fetch_items(self):
        """Test that a user can fetch items on a shoppiglist"""
        self.register_user()
        self.create_item()
        get_items = self.client().get(
            '/api/v1/shoppinglists/1/items',
            headers=dict(Authorization=self.access_token())
        )
        self.assertEqual(get_items.status_code, 200)
        self.assertIn('Carrots and Cabbages', str(get_items.data))

    def test_fetch_single_item(self):
        """Test user can get a single item on the shoppiglist"""
        self.register_user()
        self.create_item()
        # Test one item can be fetched
        get_single_item = self.client().get(
            '/api/v1/shoppinglists/1/items/1',
            headers=dict(Authorization=self.access_token())
        )
        self.assertEqual(get_single_item.status_code, 200)
        self.assertIn('Carrots and Cabbages', str(get_single_item.data))

    def test_item_duplicate(self):
        """Test item title can't be duplicated"""
        self.register_user()
        self.create_item()
        duplicate_item = self.client().post(
            '/api/v1/shoppinglists/1/items',
            headers=dict(Authorization=self.access_token()),
            data=self.shoppinglistitem)
        self.assertEqual(duplicate_item.status_code, 400)
        self.assertIn(b'Shopping List item vegetables already exists',
                      duplicate_item.data)

    def test_unexisting_items(self):
        """Test non existing items"""
        self.register_user()
        self.create_shoppinglist()
        wrong_item = self.client().get(
            '/api/v1/shoppinglists/1/items/3',
            headers=dict(Authorization=self.access_token())
        )
        self.assertIn('Requested value \\\'3\\\' was not found',
                      str(wrong_item.data))
        self.assertEqual(wrong_item.status_code, 500)

    def test_update_item(self):
        """Test a user can update an item on shoppinglist"""
        self.register_user()
        self.create_item()
        update_item = self.client().put(
            '/api/v1/shoppinglists/1/items/1',
            headers=dict(Authorization=self.access_token()),
            data={
                'item_title': "Sausages and stuff",
                'item_description': 'Carrots and Waffles'
            }
        )
        self.assertTrue(b"Carrots and Waffles" in update_item.data)
        self.assertTrue(
            b"Shopping list item updated successfuly" in update_item.data)
        self.assertEqual(update_item.status_code, 200)

    def test_update_unexisting(self):
        """Test update item with used title is denied"""
        self.register_user()
        self.create_item()
        existing_update = self.client().put(
            '/api/v1/shoppinglists/1/items/1',
            headers=dict(Authorization=self.access_token()),
            data={
                'item_title': "Vegetables",
                'item_description': 'Carrots and Waffles'
            }
        )
        self.assertTrue(
            b"Shopping list item vegetables already exists"
            in existing_update.data
        )
        self.assertEqual(existing_update.status_code, 400)

    def test_invalid_item_update(self):
        """Test user can't update item with digits only"""
        self.register_user()
        self.create_item()
        digit_update = self.client().put(
            '/api/v1/shoppinglists/1/items/1',
            headers=dict(Authorization=self.access_token()),
            data={
                'item_title': 666666,
                'item_description': 'Carrots and Tomatoes'
            }
        )
        self.assertIn(b'Item_Title can\'t be numbers only', digit_update.data)
        self.assertEqual(400, digit_update.status_code)
        
    def test_short_item_update(self):
        """Test user can't update item with short values"""
        self.register_user()
        self.create_item()
        short_update = self.client().put(
            '/api/v1/shoppinglists/1/items/1',
            headers=dict(Authorization=self.access_token()),
            data={
                'item_title': "Meat",
                'item_description': 'Carrots and Tomatoes'
            }
        )
        self.assertIn(
            b'Your item_title should be more than 6 characters',
            short_update.data
        )
        self.assertEqual(400, short_update.status_code)

    def test_empty_item_update(self):
        """Ensure user can't update item with empty values"""
        self.register_user()
        self.create_item()
        empty_update = self.client().put(
            '/api/v1/shoppinglists/1/items/1',
            headers=dict(Authorization=self.access_token()),
            data={
                'item_title': "Carrots and Tomatoes",
                'item_description': ''
            }
        )
        self.assertIn(b'Your item_description is empty', empty_update.data)
        self.assertEqual(400, empty_update.status_code)

    def test_delete_shoppinglistitem(self):
        """Test a user can delete an item on a shopping list"""
        self.register_user()
        self.create_item()
        delete_item = self.client().delete(
            '/api/v1/shoppinglists/1/items/1',
            headers=dict(Authorization=self.access_token())
        )
        self.assertIn(
            b"Shopping list item \'vegetables\' deleted successfuly",
            delete_item.data
        )
        self.assertEqual(delete_item.status_code, 200)

    def test_delete_wrong_shoppinglist(self):
        """Test delete on wrong shoppinglist"""
        self.register_user()
        resp = self.client().delete(
            '/api/v1/shoppinglists/1/items/1',
            headers=dict(Authorization=self.access_token())
        )
        self.assertTrue(
            b"Requested value '1' was not found" in resp.data)
        self.assertEqual(resp.status_code, 500)

    def test_put_wrong_shoppinglist(self):
        """Test put on wrong shoppinglist"""
        self.register_user()
        resp = self.client().put(
            '/api/v1/shoppinglists/1/items/1',
            headers=dict(Authorization=self.access_token())
        )
        self.assertTrue(
            b"Requested value '1' was not found" in resp.data)
        self.assertEqual(resp.status_code, 500)

    def test_post_wrong_shoppinglist(self):
        """Test post on wrong shoppinglist"""
        self.register_user()
        resp = self.client().post(
            '/api/v1/shoppinglists/1/items',
            headers=dict(Authorization=self.access_token())
        )
        self.assertTrue(
            b"Requested value '1' was not found" in resp.data)
        self.assertEqual(resp.status_code, 500)

    def test_get_wrong_shoppinglist(self):
        """Test post on wrong shoppinglist"""
        self.register_user()
        resp = self.client().get(
            '/api/v1/shoppinglists/1/items/1',
            headers=dict(Authorization=self.access_token())
        )
        self.assertTrue(
            b"Requested value '1' was not found" in resp.data)
        self.assertEqual(resp.status_code, 500)

    def test_delete_wrong_item(self):
        """Test delete wrong item returns a valid message"""
        self.register_user()
        self.create_shoppinglist()
        delete_item = self.client().delete(
            '/api/v1/shoppinglists/1/items/1',
            headers=dict(Authorization=self.access_token())
        )
        self.assertTrue(
            b"Requested value '1' was not found" in delete_item.data)
        self.assertEqual(delete_item.status_code, 500)
