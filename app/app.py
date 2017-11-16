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
				response = {
					'status': 'fail',
					'message': 'Password does not match'
				}
				return response, 202
			# Encrypt password

			try:
				password = bcrypt.generate_password_hash(
					args['password'], app.config.get('BCRYPT_LOG_ROUNDS')
					).decode('utf-8')
			except ValueError as err:
				response = jsonify({
					'status': 'fail',
					'message': str(err)
				})
				response.status_code = 500
				return response

			email = args['email']
			username = args['username']
			if email and username:
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
			response = jsonify({
                'status': 'fail',
                'message': 'Email or Username can\'t be empty.',
            })
			response.status_code = 500
			return response

	class Login(Resource):

		def post(self):
			post_data = ['email', 'password']
			for arg in range(len(post_data)):
				parser.add_argument(post_data[arg])
			args = parser.parse_args()
			email = args['email']
			password = args['password']
			try:
				user = Users.query.filter_by(email=email).first()
				if user is not None and bcrypt.check_password_hash(
	                user.password, password):
					token = user.encode_token(user.id)
					response = {
						'id': user.id,
	                    'message': 'Successfully logged in.',
	                    'token': token.decode()
	                }
					return response, 200
				response = {
					'status': 'fail',
					'message': 'Invalid credentials'
				}
				return response, 202

			except Exception as e:
				response = {
					'message': str(e)
				},
				return response, 500

	def middleware():
		auth_header = request.headers.get('Authorization')
		if auth_header:
			access_token = auth_header.split(" ")[1]
			if access_token:
				user_id = Users.decode_token(access_token)
				if not isinstance(user_id, int):
					response = {
						'status': 'fail',
						'message': user_id
					}
					return response, 403
				return user_id
			response = {
		    	'status': 'fail',
		    	'message': 'Bearer token malformed.'
		    }
			return response, 401
		response = {
			'status': 'fail',
			'message': 'Authorization is not provided'
		}
		return response, 500

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
			if isinstance(user_id, int):				
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
				if len(results) == 0:
					response = {
						'message': "You don't have any shoppinglists for now"
					}
					return response, 200
				response = jsonify(results)
				response.status_code = 202
				return response
			else:
                # Return token error message
				return user_id
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
			user_id = middleware()
			if isinstance(user_id, int):
				post_data = ['title', 'description']
				for arg in range(len(post_data)):
					parser.add_argument(post_data[arg])
				args = parser.parse_args()
				title = args['title']
				description = args['description']
				valid_title = is_valid(value=title, min_length=10, _type="text")
				valid_description = is_valid(value=description, min_length=10, _type="text")			
				if valid_title is True and valid_description is True:
					title_exists = ShoppingList.query.filter_by(title=title).first()
					if not title_exists:
						shoppinglist = ShoppingList.query.filter_by(owner_id=user_id, id=shoppinglist_id).first()
						shoppinglist.title = title
						shoppinglist.description = description
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
				else:
					if valid_title is True:
						message = valid_description
					elif valid_description is True:
						message = valid_title
					else:
						message = [valid_title, valid_description]
					response = jsonify({
						'message': message,
						'status_code': 202
					})
					return response
			else:
                # Return token error message
				return user_id

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
			if isinstance(user_id, int):
				shoppinglistitems = ShoppingListItem.query.filter_by(shoppinglist_id=shoppinglist_id, owner_id=user_id)
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
				if len(results) == 0:
					response = {
						'message': "You don't have any items for now"
					}
					return response, 200
				response = jsonify(results)
				response.status_code = 202
				return response
			else:
                # Return token error message
				return user_id

		def post(self, shoppinglist_id):
			user_id = middleware()
			if user_id:
				post_data = ['item_title', 'item_description']
				for arg in range(len(post_data)):
					parser.add_argument(post_data[arg])
				args = parser.parse_args()
				item_title = args['item_title']
				item_description = args['item_description']
				valid_item_title = is_valid(value=item_title, min_length=10, _type="text")
				valid_item_description = is_valid(value=item_description, min_length=10, _type="text")
				if valid_item_title is True and valid_item_description is True:
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
							'message': 'Shopping list item {} created successfuly'.format(item_title)
						}
						return response, 201
					response = {
						'message': 'Shopping List item {} already exists'.format(item_title)
					}
					return response, 202
				else:
					if valid_item_title is True:
						message = valid_item_description
					elif valid_item_description is True:
						message = valid_item_title
					else:
						message = [valid_item_title, valid_item_description]
					response = jsonify({
						'message': message,
						'status_code': 202
					})
					return response
			else:
                # Return token error message
				return user_id

	class SingleShoppingListItemAPI(Resource):
		def get(self, shoppinglist_id, shoppinglistitem_id):
			user_id = middleware()
			if isinstance(user_id, int):
				shoppinglistitem = ShoppingListItem.query.filter_by(
					item_id=shoppinglistitem_id,
					shoppinglist_id=shoppinglist_id
				).first()
				if shoppinglistitem:
					response = {
						'item_id': shoppinglistitem.item_id,
						'owner_id': shoppinglistitem.owner_id,
						'shoppinglist_id': shoppinglistitem.shoppinglist_id,
						'item_title': shoppinglistitem.item_title,
						'item_description': shoppinglistitem.item_description,
						'message': 'success'
					}
					return response, 201
				response = {
					'message': 'Requested value \'{}\' was not found'.format(shoppinglistitem_id)
				}
				return response, 202
			else:
                # Return token error message
				return user_id

		def put(self, shoppinglist_id, shoppinglistitem_id):
			user_id = middleware()
			if isinstance(user_id, int):
				post_data = ['item_title', 'item_description']
				for arg in range(len(post_data)):
					parser.add_argument(post_data[arg])
				args = parser.parse_args()
				item_title = args['item_title']
				item_description = args['item_description']
				valid_item_title = is_valid(value=item_title, min_length=10, _type="text")
				valid_item_description = is_valid(value=item_description, min_length=10, _type="text")
				if valid_item_title is True and valid_item_description is True:
					check_exists = ShoppingListItem.query.filter_by(item_title=item_title).first()
					if check_exists is None:
						shoppinglistitem = ShoppingListItem.query.filter_by(owner_id=user_id, item_id=shoppinglistitem_id, shoppinglist_id=shoppinglist_id).first()
						shoppinglistitem.item_title = item_title
						shoppinglistitem.item_description = item_description
						shoppinglistitem.save_shoppinglistitem()
						# Return Response
						response = {
							'item_id': shoppinglistitem.item_id,
							'item_title': shoppinglistitem.item_title,
							'item_description': shoppinglistitem.item_description,
							'message': 'Shopping list item updated successfuly'
						}
						return response, 201
					response = {
						'message': 'Shopping List {} already exists'.format(item_title)
					}
				else:
					if valid_item_title is True:
						message = valid_item_description
					elif valid_item_description is True:
						message = valid_item_title
					else:
						message = [valid_item_title, valid_item_description]
					response = jsonify({
						'message': message,
						'status_code': 202
					})
					return response
			else:
                # Return token error message
				return user_id

		def delete(self, shoppinglist_id, shoppinglistitem_id):
			user_id = middleware()
			if isinstance(user_id, int):
				shoppinglistitem = ShoppingListItem.query.filter_by(item_id=shoppinglistitem_id, owner_id=user_id, shoppinglist_id=shoppinglist_id).first()
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
			else:
                # Return token error message
				return user_id
	
	api.add_resource(Home, '/')
	api.add_resource(Register, '/auth/register')
	api.add_resource(Login, '/auth/login')
	api.add_resource(ShoppingListAPI, '/shoppinglists')
	api.add_resource(SingleShoppingListAPI, '/shoppinglist/<int:shoppinglist_id>', endpoint='shoppinglist')
	api.add_resource(ShoppingListItemsAPI, '/shoppinglist/<int:shoppinglist_id>/items', endpoint='shoppinglistitems')
	api.add_resource(SingleShoppingListItemAPI, '/shoppinglist/<int:shoppinglist_id>/item/<int:shoppinglistitem_id>', endpoint='singleshoppinglistitem')
	return app
