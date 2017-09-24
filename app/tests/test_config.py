import unittest
from flask_testing import TestCase
from flask import current_app
from app import app


class TestDevelopmentConfig(TestCase):
    """Test the DEVELOPMENT configuration"""

    def create_app(self):
        app.config.from_object('config.DevelopmentConfig')
        return app

    def test_app_is_development(self):
        print(app.config)
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
                'postgresql://postgres:postgres@localhost/shoppinglist'
        )


class TestTestingConfig(TestCase):
    """Test the TESTING configuration"""

    def create_app(self):
        app.config.from_object('config.TestingConfig')
        return app

    def test_app_is_testing(self):
        print(app.config)
        self.assertTrue(app.config['DEBUG'])
        self.assertTrue(app.config['DEVELOPMENT'] is True)
        self.assertTrue(app.config['TESTING'] is True)
        self.assertTrue(
            app.config['SQLALCHEMY_DATABASE_URI'] ==
                'postgresql://postgres:postgres@localhost/shoppinglist_test'
        )

if __name__ == '__main__':
    unittest.main()