from flask import Flask, Blueprint
from flask_sqlalchemy import SQLAlchemy
from flask_restful import Api
from flask_bcrypt import Bcrypt
from flask_cors import CORS

# local imports
from instance.config import app_config

# Initialize the db extension
db = SQLAlchemy()
bcrypt = Bcrypt()

from api.v1 import api_v1_bp, API_VERSION_V1

def create_app(config_name):
	""" Function to setup our app """
	app = Flask(__name__, instance_relative_config=True)

	app.config.from_object(app_config[config_name])
	app.config.from_pyfile('config.py')
	app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
	db.init_app(app)
	bcrypt.init_app(app)
	CORS(app)

	app.register_blueprint(
        api_v1_bp,
        url_prefix='{prefix}/v{version}'.format(
            prefix=app.config['URL_PREFIX'],
            version=API_VERSION_V1))

	return app
