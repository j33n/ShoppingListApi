import datetime
from functools import wraps
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
	from app.models import Users, ShoppingList, ShoppingListItem
	app = Flask(__name__, instance_relative_config=True)
	api = Api(app)
	bcrypt = Bcrypt(app)
	app.config.from_object(app_config[config_name])
	app.config.from_pyfile('config.py')
	app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
	print(app.config)
	db.init_app(app)

	parser = reqparse.RequestParser()

	class Home(Resource):
		def get(self):
			response = {'message': "Welcome to Shopping List API"}
			return response, 200

	
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
				print(token)
				response = {
                    'status': 'success',
                    'message': 'Successfully logged in.',
                    'token': token
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
		
	class ShoppingListAPI(Resource):

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


	class SingleShoppingListAPI(Resource):

		def get(self, shoppinglist_id):
			shoppinglist = ShoppingList.query.filter_by(id=shoppinglist_id).first()
			if shoppinglist:
				response = {
					'id': shoppinglist.id,
					'owner': shoppinglist.owner_id,
					'title': shoppinglist.title,
					'description': shoppinglist.description,
					'message': 'success'
				}
				return response, 201
			response = {
				'message': 'Requested value \'{}\' was not found'.format(shoppinglist_id)
			}
			return response, 202

		def put(self, shoppinglist_id):
			post_data = ['title', 'description']
			for arg in range(len(post_data)):
				parser.add_argument(post_data[arg])
			args = parser.parse_args()
			title = args['title']
			description = args['description']
			valid_title = is_valid(value=title, min_length=10, _type="text")
			valid_description = is_valid(value=description, min_length=10, _type="text")
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
							'message': 'Shopping List updated successfuly'
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

		def delete(self, shoppinglist_id):
			shoppinglist = ShoppingList.query.filter_by(id=shoppinglist_id).first()
			if shoppinglist:
				shoppinglist.delete_shoppinglist()
				response = {
					'message': 'Shopping List \'{}\' deleted successfuly'.format(shoppinglist.title)
				}
				return response, 201
			response = {
				'message': 'Requested value \'{}\' was not found'.format(shoppinglist_id)
			}
			return response, 202

	class ShoppingListItemsAPI(Resource):

		def get(self, shoppinglist_id):
			user_id = middleware()
			
			if not isinstance(user_id, str):
				shoppinglistitems = ShoppingListItem.query.filter_by(shoppinglist_id=shoppinglist_id)
				results = []
				for shoppinglistitem in shoppinglistitems:
					obj = {
						'item_id': shoppinglistitem.item_id,
                        'item_title': shoppinglistitem.item_title,
                        'item_description': shoppinglistitem.item_description,
                        'shoppinglist_id': shoppinglistitem.shoppinglist_id,
                        'date_created': shoppinglistitem.date_created,
                        'date_modified': shoppinglistitem.date_modified,
                        'owner_id': shoppinglistitem.owner_id
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
		def post(self, shoppinglist_id):
			post_data = ['item_title', 'item_description']
			for arg in range(len(post_data)):
				parser.add_argument(post_data[arg])
			args = parser.parse_args()
			item_title = args['item_title']
			item_description = args['item_description']
			valid_item_title = is_valid(value=item_title, min_length=10, _type="text")
			valid_item_description = is_valid(value=item_description, min_length=10, _type="text")
			if valid_item_title is True and valid_item_description:
				user_id = middleware()
				if not isinstance(user_id, str):
					check_exists = ShoppingListItem.query.filter_by(item_title=item_title).first()
					if check_exists is None:
						shoppinglistitem = ShoppingListItem(item_title=item_title, item_description=item_description, shoppinglist_id=shoppinglist_id, owner_id=user_id)
						shoppinglistitem.save_shoppinglistitem()
						# Return Response
						response = {
							'item_id': shoppinglistitem.item_id,
							'owner_id': shoppinglistitem.owner_id,
							'shoppinglist_id': shoppinglistitem.shoppinglist_id,
							'item_title': shoppinglistitem.item_title,
							'item_description': shoppinglistitem.item_description,
							'message': 'Shopping List created successfuly'
						}
						return response, 201
					response = {
						'message': 'Shopping List item {} already exists'.format(item_title)
					}
					return response, 202
				response = jsonify({
					'message': user_id
				})
				return response
			response = {
				'message': valid_item_title
			}
			return response, 202

	class SingleShoppingListItemAPI(Resource):

		def get(self, shoppinglist_id, shoppinglistitem_id):
			shoppinglistitem = ShoppingListItem.query.filter_by(
				item_id=shoppinglistitem_id,
				shoppinglist_id=shoppinglist_id
			).first()
			if shoppinglistitem:
				response = {
					'item_id': shoppinglistitem.item_id,
					'owner_id': shoppinglistitem.owner_id,
					'owner_id': shoppinglistitem.shoppinglist_id,
					'item_title': shoppinglistitem.item_title,
					'item_description': shoppinglistitem.item_description,
					'message': 'success'
				}
				return response, 201
			response = {
				'message': 'Requested value \'{}\' was not found'.format(shoppinglistitem_id)
			}
			return response, 202

		def put(self, shoppinglist_id, shoppinglistitem_id):
			post_data = ['item_title', 'item_description']
			for arg in range(len(post_data)):
				parser.add_argument(post_data[arg])
			args = parser.parse_args()
			item_title = args['item_title']
			item_description = args['item_description']
			valid_item_title = is_valid(value=item_title, min_length=10, _type="text")
			valid_item_description = is_valid(value=item_description, min_length=10, _type="text")
			if valid_item_title is True and valid_item_description:
				user_id = middleware()
				if not isinstance(user_id, str):
					check_exists = ShoppingListItem.query.filter_by(item_title=item_title).first()
					if check_exists is None:
						shoppinglistitem = ShoppingListItem(item_title=item_title, item_description=item_description, owner_id=user_id, shoppinglist_id=shoppinglist_id)
						shoppinglistitem.save_shoppinglistitem()
						# Return Response
						response = {
							'item_id': shoppinglistitem.item_id,
							'owner': shoppinglistitem.owner_id,
							'shoppinglist_id': shoppinglistitem.shoppinglist_id,
							'item_title': shoppinglistitem.item_title,
							'item_description': shoppinglistitem.item_description,
							'message': 'Shopping list item updated successfuly'
						}
						return response, 201
					response = {
						'message': 'Shopping List {} already exists'.format(item_title)
					}
					return response, 202
				response = jsonify({
					'message': user_id
				})
				return response
			response = {
				'message': valid_item_title
			}
			return response, 202

		def delete(self, shoppinglist_id, shoppinglistitem_id):
			shoppinglistitem = ShoppingListItem.query.filter_by(item_id=shoppinglistitem_id, shoppinglist_id=shoppinglist_id).first()
			if shoppinglistitem:
				shoppinglistitem.delete_shoppinglistitem()
				response = {
					'message': 'Shopping list item \'{}\' deleted successfuly'.format(shoppinglistitem.item_title)
				}
				return response, 201
			response = {
				'message': 'Requested value \'{}\' was not found'.format(shoppinglistitem_id)
			}
			return response, 202
	
	api.add_resource(Home, '/')
	api.add_resource(Register, '/auth/register')
	api.add_resource(Login, '/auth/login')
	api.add_resource(ShoppingListAPI, '/shoppinglists')
	api.add_resource(SingleShoppingListAPI, '/shoppinglist/<int:shoppinglist_id>', endpoint='shoppinglist')
	api.add_resource(ShoppingListItemsAPI, '/shoppinglist/<int:shoppinglist_id>/items', endpoint='shoppinglistitems')
	api.add_resource(SingleShoppingListItemAPI, '/shoppinglist/<int:shoppinglist_id>/item/<int:shoppinglistitem_id>', endpoint='singleshoppinglistitem')
	return app
