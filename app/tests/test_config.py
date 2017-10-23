import unittest
from flask import current_app
from app.app import create_app, db


class TestDevelopmentConfig(unittest.TestCase):
    """Test the DEVELOPMENT configuration"""  
    def test_app_is_development(self):
        app = create_app(config_name="development")
        self.assertTrue(app.config['DEBUG'] is True)
        self.assertTrue(app.config['DEVELOPMENT'] is True)
        self.assertTrue(app.config['TESTING'] is False)
        with app.app_context():
            self.assertEqual(current_app.name, 'app.app')
        self.assertFalse(
           app.config['SECRET_KEY'] == "my_precious"
        )
        self.assertTrue(
           app.config['SQLALCHEMY_DATABASE_URI'] ==
                'postgresql://postgres:test_user@localhost/shoppinglist'
        )


class TestTestingConfig(unittest.TestCase):
    """Test the TESTING configuration"""
    def test_app_is_testing(self):
        app = create_app(config_name="testing")
        self.assertTrue(app.config['DEBUG'])
        self.assertTrue(app.config['TESTING'] is True)
        self.assertTrue(
           app.config['SQLALCHEMY_DATABASE_URI'] ==
                'postgresql://postgres:test_user@localhost/shoppinglist_test'
        )


if __name__ == '__main__':
    unittest.main()