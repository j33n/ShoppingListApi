"""
This module contains all the test suite for Items
"""

from api.tests.basetest import TestBase

class ItemsTestCase(TestBase):
    """Items test case"""

    def test_add_shoppinglistitem(self):
        """Test a user can add an item to shoppinglist"""
        self.register_user()
        create_item = self.create_item()
        self.assertIn(b'vegetables', create_item.data)
        self.assertEqual(200, create_item.status_code)

    def test_emptiness_items(self):
        """Test empty values are not saved"""
        self.register_user()
        access_token = self.access_token()
        self.create_shoppinglist()
        empty_item = self.client().post(
            '/api/v1/shoppinglists/1/items',
            headers=dict(Authorization=access_token),
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
        access_token = self.access_token()
        self.create_shoppinglist()
        create_item = self.client().post(
            '/api/v1/shoppinglists/1/items',
            headers=dict(Authorization=access_token),
            data={
                'item_title': "Carrots and Cabbages",
                'item_description': '66666'
            }
        )
        self.assertIn(b'Item_Description can\'t be numbers only',
                      create_item.data)
        self.assertEqual(400, create_item.status_code)
