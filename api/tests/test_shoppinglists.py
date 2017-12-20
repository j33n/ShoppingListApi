"""
This module contains all the test suite for Shoppinglists
"""

from api.tests.basetest import TestBase


class ShoppinglistTestCase(TestBase):
    """Shoppinglist manipulations test case"""

    def test_empty_shoppinglists(self):
        """Test empty shoppinglists"""
        self.register_user()
        response = self.client().get(
            '/api/v1/shoppinglists',
            headers=dict(Authorization=self.access_token())
        )
        self.assertTrue("No shoppinglists found here, please add them.",
                        response.data)
        self.assertEqual(200, response.status_code)

    def test_shoppinglists_auth(self):
        """Test shoppinglists without authorization"""
        self.register_user()
        response = self.client().post(
            '/api/v1/shoppinglists',
            headers=dict(Authorization=self.access_token() + '_'),
            data=self.shoppinglist
        )
        self.assertTrue('fail' in str(response.data))
        self.assertEqual(401, response.status_code)

    def test_create_shoppinglist(self):
        """Test user can create a shoppinglist"""
        self.register_user()
        response = self.create_shoppinglist()
        self.assertTrue('my favorite meal' in str(response.data))
        self.assertEqual(200, response.status_code)

    def test_numbers_shoppinglists(self):
        """Test a shoppinglist can't be numbers only"""
        self.register_user()
        response = self.client().post(
            '/api/v1/shoppinglists',
            headers=dict(Authorization=self.access_token()),
            data={
                'title': 666666,
                'description': 'Items to cook my favorite meal'
            }
        )
        self.assertIn(b'Title can\'t be numbers only', response.data)
        self.assertEqual(400, response.status_code)

    def test_input_length(self):
        """Test user data length are more than 6 chars"""
        self.register_user()
        response = self.client().post(
            '/api/v1/shoppinglists',
            headers=dict(Authorization=self.access_token()),
            data={
                'title': "Nyama",
                'description': 'Items to cook my favorite meal'
            }
        )
        self.assertIn(
            b'Your title should be more than 6 characters', response.data)
        self.assertEqual(400, response.status_code)

    def test_empty_values(self):
        """Test our shoppinglist input can't be empty"""
        self.register_user()
        response = self.client().post(
            '/api/v1/shoppinglists',
            headers=dict(Authorization=self.access_token()),
            data={
                'title': "",
                'description': 'Items to cook my favorite meal'
            }
        )
        self.assertIn(b'Your title is empty', response.data)
        self.assertEqual(400, response.status_code)

    def test_duplicate_shoppinglist(self):
        """Test user can't create two similar shoppinglists"""
        self.register_user()
        self.create_shoppinglist()
        response = self.create_shoppinglist()
        self.assertIn(
            b'Shopping List my favorite meal already exists', response.data)
        self.assertEqual(response.status_code, 400)

    def test_fetch_all_shoppinglists(self):
        """Test user is able to display all shopping lists"""
        self.register_user()
        access_token = self.access_token()
        self.create_shoppinglist()
        response = self.client().get(
            '/api/v1/shoppinglists/1',
            headers=dict(Authorization=access_token)
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('my favorite meal', str(response.data))

    def test_fetch_shoppinglist(self):
        """Test user is able to display shopping lists"""
        self.register_user()
        access_token = self.access_token()
        self.create_shoppinglist()
        get_single_sl = self.client().get(
            '/api/v1/shoppinglists?page=1&per_page=1',
            headers=dict(Authorization=access_token)
        )
        self.assertIn(b"my favorite meal", get_single_sl.data)
        self.assertEqual(get_single_sl.status_code, 200)

    def test_non_existent_shoppinglist(self):
        """Test user can't access non existent shoppinglist"""
        self.register_user()
        access_token = self.access_token()
        response = self.client().get(
            '/api/v1/shoppinglists/1',
            headers=dict(Authorization=access_token)
        )
        self.assertIn(b"Requested value '1' was not found", response.data)
        self.assertEqual(response.status_code, 500)

    def test_update_shoppinglist(self):
        """Test a user can update a shopping list"""
        self.register_user()
        access_token = self.access_token()
        self.create_shoppinglist()
        update_resp = self.client().put(
            '/api/v1/shoppinglists/1',
            headers=dict(Authorization=access_token),
            data={
                'title': "My favorite shoes",
                'description': 'Converse and Jordan 2015'
            }
        )
        self.assertTrue(b"Converse and Jordan 2015" in update_resp.data)
        self.assertTrue(
            b"Shopping List updated successfuly" in update_resp.data)

    def test_update_duplication(self):
        """ Test put_url can not take an existing name"""
        self.register_user()
        access_token = self.access_token()
        self.create_shoppinglist()
        duplicate_update = self.client().put(
            '/api/v1/shoppinglists/1',
            headers=dict(Authorization=access_token),
            data=self.shoppinglist
        )
        self.assertTrue(
            b'Shopping List my favorite meal already exists'
            in duplicate_update.data
        )
        self.assertEqual(duplicate_update.status_code, 400)

    def test_updatewith_numbers(self):
        """ Test invalid use of data on PUT"""
        self.register_user()
        access_token = self.access_token()
        digit_update = self.client().put(
            '/api/v1/shoppinglists/1',
            headers=dict(Authorization=access_token),
            data={
                'title': "666",
                'description': 'Converse and Jordan 2016'
            }
        )
        self.assertIn(b"Title can\'t be numbers only",
                      digit_update.data)
        self.assertEqual(400, digit_update.status_code)

    def test_short_shoppinglists(self):
        """ Test a user can not create short shoppinglists"""
        self.register_user()
        access_token = self.access_token()
        short_update = self.client().put(
            '/api/v1/shoppinglists/1',
            headers=dict(Authorization=access_token),
            data={
                'title': 'Fish',
                'description': 'Converse and Jordan 2016'
            }
        )
        self.assertIn(b"Your title should be more than 6 characters",
                      short_update.data)
        self.assertEqual(400, short_update.status_code)

    def test_delete_shoppinglist(self):
        """Test a user can delete a shopping list"""
        self.register_user()
        access_token = self.access_token()
        self.create_shoppinglist()
        delete_resp = self.client().delete(
            '/api/v1/shoppinglists/1',
            headers=dict(Authorization=access_token)
        )
        self.assertIn(
            b"Shopping List \'my favorite meal\' deleted successfuly",
            delete_resp.data
        )
        self.assertEqual(delete_resp.status_code, 200)

    def test_invalid_deletion(self):
        """Test delete non existing value"""
        self.register_user()
        access_token = self.access_token()
        invalid_deletion = self.client().delete(
            '/api/v1/shoppinglists/1',
            headers=dict(Authorization=access_token)
        )
        self.assertIn(b"The shopping list requested is invalid",
                      invalid_deletion.data)
        self.assertEqual(500, invalid_deletion.status_code)
