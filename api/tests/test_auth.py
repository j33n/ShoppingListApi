"""
This module contains all the test suite for Authentication
"""
from api.tests.basetest import TestBase

class AUTHTestCase(TestBase):
    """Authentication(Registration and Login) test case"""

    def test_user_creation(self):
        """Test we can create a user"""
        response = self.register_user()
        self.assertEqual(response.status_code, 200)
        self.assertIn("User account created successfuly", str(response.data))

    def test_security_question(self):
        """Ensure a user provides a security question"""
        self.register_user()
        check_security_question = self.client().post('/api/v1/auth/register', data={
            'username': 'Stallion',
            'email': 'rocky@test.com',
            'password': 'secret',
            'confirm_password': 'secret'
        })
        self.assertEqual(check_security_question.status_code, 400)
        self.assertIn("Question is required", str(
            check_security_question.data))

    def test_special_chars_denial(self):
        """Test special are not allowed in forms"""
        response = self.client().post('/api/v1/auth/register', data={
            'username': '&#^@*$^$$#',
            'email': 'rocky@test.com',
            'password': 'secret',
            'confirm_password': 'secret',
            'question': 'What is your favorite pet name?',
            'answer': 'Monster'
        })
        self.assertIn(b'Your username has special characters that are not allowed', response.data)
        self.assertEqual(400, response.status_code)

    def test_password_mismatch(self):
        """Test user creates an account when he confirms password"""
        response = self.client().post('/api/v1/auth/register', data={
            'username': 'Stallion',
            'email': 'rocky@test.com',
            'password': 'secret',
            'confirm_password': 'secreto',
            'question': 'What is your pet name?',
            'answer': 'Monster'
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn("Password does not match", str(response.data))

    def test_missing_registration_data(self):
        """Test a user is not missing out a password"""
        response = self.client().post('/api/v1/auth/register', data={
            'username': 'Stallion',
            'email': 'rocky@test.com'
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn("Password is required", str(response.data))

    def test_account_duplicate(self):
        """Test users can't create similar accounts"""
        self.register_user()
        # Duplicate the account
        response1 = self.register_user()
        self.assertEqual(response1.status_code, 400)
        self.assertIn("User account already exists.", str(response1.data))

    def test_empty_values(self):
        """Test a user is not missing out an email"""
        response = self.client().post('/api/v1/auth/register', data={
            'username': 'Stallion',
            'email': '',
            'password': 'secret',
            'confirm_password': 'secret',
            'question': 'What is your pet name?',
            'answer': 'Monster'
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn(b"Your email is not valid", response.data)

    def test_user_login(self):
        """Test user can login"""
        self.register_user()
        response = self.login_user()
        self.assertEqual(response.status_code, 200)
        self.assertIn("token", str(response.data))

    def test_invalid_credentials(self):
        """Test invalid credentials rejection"""
        self.register_user()
        self.login_user()
        wrong_cred_login = self.client().post('/api/v1/auth/login', data={
            'email': 'Stallion',
            'password': 'secret'
        })
        self.assertEqual(wrong_cred_login.status_code, 400)
        self.assertIn("Your email is not valid", str(wrong_cred_login.data))

    def test_invalid_middleware(self):
        """Test a our middleware can't be broken"""
        self.register_user()
        mess_up_token = self.access_token() + "Mess up token"
        response1 = self.client().get(
            '/api/v1/shoppinglists/1',
            headers=dict(Authorization=mess_up_token)
        )
        self.assertEqual(response1.status_code, 401)
        self.assertIn(b"Invalid token. Please log in again.", response1.data)

    def test_authorization_missing(self):
        """Check authorization is missing and valid message is returned"""
        self.register_user()
        response2 = self.client().get('/api/v1/shoppinglists/1',
                                      headers=dict(Authorization=""))
        self.assertEqual(response2.status_code, 500)
        self.assertIn(b"Authorization is not provided", response2.data)
