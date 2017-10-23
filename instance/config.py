"""Configurations for different environments"""
import os
basedir = os.path.abspath(os.path.dirname(__file__))
postgres_local_database = os.getenv('DATABASE_URL')


class Config(object):
    """Global configurations"""
    DEBUG = False
    TESTING = False
    CSRF_ENABLED = True
    SECRET_KEY = os.getenv('SECRET')
    SQLALCHEMY_TRACK_MODIFICATIONS = True
    BCRYPT_LOG_ROUNDS = 13
    DEBUG = False

class DevelopmentConfig(Config):
    """Development configurations"""

    DEVELOPMENT = True
    DEBUG = True
    BCRYPT_LOG_ROUNDS = 4
    SQLALCHEMY_DATABASE_URI = postgres_local_database

class TestingConfig(Config):
    """Testing configurations"""

    CSRF_ENABLED = False
    WTF_CSRF_ENABLED = False
    DEBUG = True
    TESTING = True
    BCRYPT_LOG_ROUNDS = 4
    SQLALCHEMY_DATABASE_URI = postgres_local_database+"{}".format('_test')

class ProductionConfig(Config):
    """Testing configurations"""

    DEBUG = False
    TESTING = False
    SQLALCHEMY_DATABASE_URI = postgres_local_database

app_config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
}
