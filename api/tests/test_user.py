"""
This module contains all the test suite for User
"""

from api.tests.basetest import TestBase

class UserTestCase(TestBase):
    """User test case"""

    def test_token_unprovided(self):
        """Test a token is always provided on login"""
        response = self.client().get('/api/v1/shoppinglists')
        self.assertIn(b"Authorization is not provided", response.data)
        self.assertEqual(response.status_code, 500)

    def test_welcome_page(self):
        """Test welcome page"""
        response = self.client().get('/api/v1/')
        self.assertTrue(b"Welcome to Shopping List API" in response.data)
        self.assertEqual(response.status_code, 200)

    def test_valid_logout(self):
        """Test a user can logout smoothly"""
        self.register_user()
        logout_user = self.logout_user()
        self.assertIn(b"Successfully logged out.", logout_user.data)
        self.assertEqual(200, logout_user.status_code)

    def test_token_duplicate(self):
        """Test that a token can't be used twice ever"""
        self.register_user()
        self.logout_user()
        resp = self.client().get(
            '/api/v1/shoppinglists',
            headers=dict(Authorization=self.access_token())
        )
        self.assertIn(b"Token created. Please log in again.", resp.data)
        self.assertEqual(401, resp.status_code)

    def test_logout_invalid_token(self):
        """Test a logout requires a valid token"""
        self.register_user()
        mess_up_token = self.access_token() + "Mess up token"
        logout_response = self.client().post(
            '/api/v1/auth/logout',
            headers=dict(Authorization=mess_up_token)
        )
        self.assertEqual(logout_response.status_code, 401)
        self.assertIn(b"Invalid token. Please log in again.",
                      logout_response.data)

    def test_reset_password(self):
        """Test a user can reset password using a security question"""
        self.register_user()
        reset_password = self.client().post(
            '/api/v1/resetpassword',
            headers=dict(Authorization=self.access_token()),
            data={
                'question': 'What is your favorite pet name?',
                'answer': 'Monster',
                'old_password': 'secret',
                'new_password': 'Secreto'
            }
        )
        self.assertEqual(200, reset_password.status_code)
        self.assertIn(b'Your password was resetted successfuly',
                      reset_password.data)

    def test_wrong_answer(self):
        """Test a user can't procceed with wrong answer'"""
        self.register_user()
        reset_password = self.client().post(
            '/api/v1/resetpassword',
            headers=dict(Authorization=self.access_token()),
            data={
                'question': 'What is your favorite pet name?',
                'answer': 'Morgan',
                'old_password': 'secret',
                'new_password': 'Secreto'
            }
        )
        self.assertEqual(400, reset_password.status_code)
        self.assertIn(b'Invalid security question, please try again!',
                      reset_password.data)

    def test_empty_question(self):
        """Test question can not be empty"""
        self.register_user()
        empty_question = self.client().post(
            '/api/v1/resetpassword',
            headers=dict(Authorization=self.access_token()),
            data={
                'question': '',
                'answer': 'Tiger',
                'old_password': 'secret',
                'new_password': '123456'
            }
        )
        self.assertEqual(400, empty_question.status_code)
        self.assertIn(b'Your question is not valid',
                      empty_question.data)

    def test_old_password(self):
        """Test a user is not using a wrong previous password"""
        self.register_user()
        old_password = self.client().post(
            '/api/v1/resetpassword',
            headers=dict(Authorization=self.access_token()),
            data={
                'question': 'What is your favorite pet name?',
                'answer': 'Monster',
                'old_password': 'secret_society',
                'new_password': '123-456'
            }
        )
        self.assertEqual(400, old_password.status_code)
        self.assertIn(b'Invalid password!!', old_password.data)

    def test_new_password(self):
        """Test a user can login with his new password"""
        self.register_user()
        access_token = self.access_token()
        self.client().post(
            '/api/v1/resetpassword',
            headers=dict(Authorization=self.access_token()),
            data={
                'question': 'What is your favorite pet name?',
                'answer': 'Monster',
                'old_password': 'secret',
                'new_password': 'Secreto'
            }
        )
        self.client().post(
            '/api/v1/auth/logout',
            headers=dict(Authorization=access_token)
        )
        new_password = self.client().post(
            '/api/v1/auth/login',
            data={
                'email': 'rocky@test.com',
                'password': 'Secreto'
            }
        )
        self.assertEqual(200, new_password.status_code)
        self.assertIn(b'token', new_password.data)

    def test_user_info(self):
        """Ensure a user can see his infos"""
        self.register_user()
        check_info = self.client().get(
            '/api/v1/user',
            headers=dict(Authorization=self.access_token())
        )
        self.assertIn(b"rocky@test.com", check_info.data)
        self.assertIn(b"Stallion", check_info.data)
        self.assertEqual(200, check_info.status_code)

    def test_update_accountinfo(self):
        """ Test a user can change username and email"""
        self.register_user()
        # change user information
        change_userinfo = self.client().put(
            '/api/v1/user',
            headers=dict(Authorization=self.access_token()),
            data={
                'new_email': 'johndoe@test.com',
                'new_username': 'John Doe',
                'password': 'secret'}
        )
        self.assertEqual(200, change_userinfo.status_code)
        self.assertIn(b"Account information changed successfuly",
                      change_userinfo.data)

    def test_wrong_password(self):
        """check update can't happen with wrong password"""
        self.register_user()
        wrong_password = self.client().put(
            '/api/v1/user',
            headers=dict(Authorization=self.access_token()),
            data={'new_email': 'johndoe@test.com',
                  'new_username': 'John Doe',
                  'password': 'my_wrong_password'})
        self.assertEqual(400, wrong_password.status_code)
        self.assertIn(b"You need your password to update account info.",
                      wrong_password.data)

    def test_invalid_values(self):
        """check invalid new username"""
        self.register_user()
        update_user = self.client().put(
            '/api/v1/user',
            headers=dict(Authorization=self.access_token()),
            data={
                'new_email': 'johndoe@test.com',
                'new_username': '566',
                'password': 'secret'
            }
        )
        self.assertEqual(400, update_user.status_code)
        self.assertIn(b"New_Username can\'t be numbers only", update_user.data)
