import datetime
from flask import Flask, request, jsonify, make_response, json
from flask_restful import reqparse, abort, Api, Resource
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
import jwt

# local import
from instance.config import app_config

# initialize sql-alchemy
db = SQLAlchemy()

JWT_SECRET = 'secret'
JWT_ALGORITHM = 'HS256'
JWT_EXP_DELTA_SECONDS = 20


def create_app(config_name):
	from app.models import Users, ShoppingList
	app = Flask(__name__, instance_relative_config=True)
	api = Api(app)
	bcrypt = Bcrypt(app)
	app.config.from_object(app_config[config_name])
	app.config.from_pyfile('config.py')
	app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
	db.init_app(app)

	parser = reqparse.RequestParser()	

	
	class Register(Resource):
		"""Register a user account"""

		def post(self):
			# Get data posted
			post_data = ['username', 'email', 'password', 'confirm_password']
			for arg in range(len(post_data)):
				parser.add_argument(post_data[arg])
			args = parser.parse_args()
			if args['password'] != args['confirm_password']:
				return "Password does not match"
			# Encrypt password
			password = bcrypt.generate_password_hash(
				args['password'], app.config.get('BCRYPT_LOG_ROUNDS')
				).decode('utf-8')
			email = args['email']
			username = args['username']
			# Get user from db
			check_user = Users.query.filter_by(email=email).first()
			# Check user account exists
			if check_user is None:
				user = Users(username=username, email=email, password=password)
				# Save user
				user.save_user()
				# Return Response
				response = jsonify({
					'id': user.id,
					'username': user.username,
					'email': user.email,
					'date_created': user.date_created,
					'message': 'User account created successfuly'
				})
				response.status_code = 201
				return response
			response = jsonify({
                'status': 'fail',
                'message': 'User account already exists.',
            })
			response.status_code = 202
			return response

	class Login(Resource):

		def post(self):
			post_data = ['email', 'password']
			for arg in range(len(post_data)):
				parser.add_argument(post_data[arg])
			args = parser.parse_args()
			email = args['email']
			password = args['password']
			user = Users.query.filter_by(email=email).first()
			if user is not None and bcrypt.check_password_hash(
                user.password, password):
				token = Users.encode_token(user.id)
				response = {
                    'status': 'success',
                    'message': 'Successfully logged in.',
                    'token': token.decode()
                }
				return response, 200
			response = {
				'status': 'fail',
				'message': 'Invalid credentials'
			}
			return response, 202

	def middleware():
		auth_header = request.headers.get('Authorization')
		access_token = auth_header.split(" ")[1]
		if access_token:
			user_id = Users.decode_token(access_token)
			return user_id
		response = {
	    	'status': 'fail',
	    	'message': 'Bearer token malformed.'
	    }
		return response, 401

	def is_valid(value, min_length, _type):
		message = []
		if len(value) != 0:
			if _type is 'text':
				if not value.isdigit():
					if len(value) < min_length:
						message.append("Value should be more than {} characters".format(min_length))
						return message
					return True
				message.append("Value can't be numbers")
				return message
		message.append("Value can't be empty")
		return message
		
	class CreateShoppingList(Resource):

		def get(self):
			user_id = middleware()
			
			if not isinstance(user_id, str):
				shoppinglists = ShoppingList.query.filter_by(owner_id=user_id)
				results = []
				for shoppinglist in shoppinglists:
					obj = {
						'id': shoppinglist.id,
                        'title': shoppinglist.title,
                        'description': shoppinglist.description,
                        'date_created': shoppinglist.date_created,
                        'date_modified': shoppinglist.date_modified,
                        'owner_id': shoppinglist.owner_id
                    }
					results.append(obj)

				response = jsonify(results)
				response.status_code = 202
				return response
			else:
                # Return token error message
				response = {
                    'message': user_id
                }
				return response, 401
		def post(self):
			post_data = ['title', 'description']
			for arg in range(len(post_data)):
				parser.add_argument(post_data[arg])
			args = parser.parse_args()
			title = args['title']
			description = args['description']
			valid_title = is_valid(value=title, min_length=10, _type="text")
			valid_description = is_valid(value=description, min_length=10, _type="text")
			# print(valid_description)
			if valid_title is True and valid_description:
				user_id = middleware()
				if not isinstance(user_id, str):
					check_exists = ShoppingList.query.filter_by(title=title).first()
					if check_exists is None:
						shoppinglist = ShoppingList(title=title, description=description, owner_id=user_id)
						shoppinglist.save_shoppinglist()
						# Return Response
						response = {
							'id': shoppinglist.id,
							'owner': shoppinglist.owner_id,
							'title': shoppinglist.title,
							'description': shoppinglist.description,
							'message': 'Shopping List created successfuly'
						}
						return response, 201
					response = {
						'message': 'Shopping List {} already exists'.format(title)
					}
					return response, 202
				response = jsonify({
					'message': user_id
				})
				return response
			response = {
				'message': valid_title
			}
			return response, 202
			
	
	api.add_resource(Register, '/auth/register')
	api.add_resource(Login, '/auth/login')
	api.add_resource(CreateShoppingList, '/shoppinglists')
	return app
