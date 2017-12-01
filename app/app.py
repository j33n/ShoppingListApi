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
	from app.models import Users, ShoppingList, ShoppingListItem, UserToken
	from app.helpers import is_valid, authenticate
	app = Flask(__name__, instance_relative_config=True)
	api = Api(app)
	bcrypt = Bcrypt(app)
	app.config.from_object(app_config[config_name])
	app.config.from_pyfile('config.py')
	token_expiration = app.config['TOKEN_EXPIRATION_TIME']
	per_page = app.config['POSTS_PER_PAGE']
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
			post_data = ['username', 'email', 'password', 'confirm_password', 'question', 'answer']
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
			question = args['question']
			answer = args['answer']			
			if email and username:
				if question and answer:
					valid_question = is_valid(value=question, min_length=4, _type="text")
					valid_answer = is_valid(value=answer, min_length=4, _type="text")
					if valid_question is True and valid_answer is True:
						# Get user from db
						check_user = Users.query.filter_by(email=email).first()
						# Check user account exists
						if check_user is None:	
							user = Users(username=username, email=email, password=password, question=question, answer=answer)
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
							response.status_code = 200
							return response
						response = jsonify({
			                'status': 'fail',
			                'message': 'User account already exists.',
			            })
						response.status_code = 202
						return response
					response = jsonify({
						'status': 'fail',
						'message': 'Invalid security question!!'
					})
					return make_response(response, 202)
				response = jsonify({
					'status': 'fail',
					'message': 'Please provide a security question!!'
				})
				return make_response(response, 202)
			response = jsonify({
                'status': 'fail',
                'message': 'Email or Username can\'t be empty.',
            })
			return make_response(response, 500)

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
				token = user.encode_token(user.id, token_expiration)
				response = {
					'id': user.id,
                    'message': 'Successfully logged in.',
                    'token': token.decode()
                }
				return response, 200
			response = {
				'status': "fail",
				'message': 'Invalid credentials'
			}
			return response, 202

	class Logout(Resource):
		"""This class ensures a user can logout"""
		method_decorators = [authenticate]

		def post(self, user_id):
			auth_header = request.headers.get('Authorization')
			access_token = auth_header.split(" ")[1]
			save_used_token = UserToken(token=access_token)
			# insert the token
			db.session.add(save_used_token)
			db.session.commit()
			responseObject = {
				'status': 'success',
				'message': 'Successfully logged out.'
			}
			return make_response(jsonify(responseObject), 200)

	class ResetPassowrd(Resource):
		"""Allow a user to reset a password using a security question"""
		method_decorators = [authenticate]
		def post(self, user_id):
			# Get data posted
			post_data = ['question', 'answer', 'old_password', 'new_password']
			for arg in range(len(post_data)):
				parser.add_argument(post_data[arg])
			args = parser.parse_args()
			user = Users.query.filter_by(id=user_id).first()
			if user.question == args['question'] and user.answer == args['answer']:
				check_old_password = bcrypt.check_password_hash(user.password, args['old_password'])
				if check_old_password:
					make_new_password = bcrypt.generate_password_hash(
						args['new_password'], app.config.get('BCRYPT_LOG_ROUNDS')
						).decode('utf-8')
					user.password = make_new_password
					user.save_user()
					invalid_old_password = jsonify({
						'status': 'fail',
						'message': 'Your password was resetted successfuly'
					})
					return make_response(invalid_old_password, 200)
				invalid_old_password = jsonify({
					'status': 'fail',
					'message': 'Invalid password!!'
				})
				return make_response(invalid_old_password, 202)
			invalid_question = jsonify({
				'status': 'fail',
				'message': 'Invalid security question, please try again!'
			})
			return make_response(invalid_question, 202)

	class User(Resource):
		""" This class helps manage user's information"""
		method_decorators = [authenticate]

		def get(self, user_id):
			user = Users.query.filter_by(id=user_id).first()
			response = jsonify({
				'status': 'success',
				'email': user.email,
				'username': user.username
			})
			return make_response(response, 200)

		def put(self, user_id):
			post_data = ['new_email', 'new_username', 'password']
			for arg in range(len(post_data)):
				parser.add_argument(post_data[arg])
			args = parser.parse_args()
			user = Users.query.filter_by(id=user_id).first()
			check_password = bcrypt.check_password_hash(user.password, args['password'])
			if check_password:					
				new_email = args['new_email']
				new_username = args['new_username']
				valid_new_email = is_valid(value=new_email, min_length=5, _type="text")
				valid_new_username = is_valid(value=new_username, min_length=5, _type="text")
				if valid_new_username is True and valid_new_email is True:
					user.email = new_email
					user.username = new_username
					user.save_user()
					response = jsonify({
						'status': 'success',
						'message': 'Account information changed successfuly',
						'new_user': new_username,
						'new_email': new_email
					})
					return make_response(response, 200)
				else:
					if valid_new_username is True:
						message = valid_new_email
					elif valid_new_email is True:
						message = valid_new_username
					else:
						message = [valid_new_username, valid_new_email]
					response = jsonify({
						'message': message,
						'status': 'fail'						
					})
					return make_response(response, 202)
			response = jsonify({
				'status': 'fail',
				'message': 'You need your password to update account info.'
			})
			return make_response(response, 202)

		
	class ShoppingListAPI(Resource):
		"""This class will manage paginations on shoppinglists"""
		method_decorators = [authenticate]

		def get(self, user_id, page):
			shoppinglists = ShoppingList.query.filter_by(owner_id=user_id)
			paginated_shoppinglists = shoppinglists.paginate(page, per_page, False)
			results = []
			for shoppinglist in paginated_shoppinglists.items:
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
					'message': "No shoppinglists found here, please add them."
				}
				return response, 200
			response = jsonify(results)
			response.status_code = 200
			return response

		def post(self, user_id):
			post_data = ['title', 'description']
			for arg in range(len(post_data)):
				parser.add_argument(post_data[arg])
			args = parser.parse_args()
			title = args['title']
			description = args['description']
			valid_title = is_valid(value=title, min_length=10, _type="text")
			valid_description = is_valid(value=description, min_length=10, _type="text")
			if valid_title is True and valid_description:
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
			response = {
				'message': valid_title
			}
			return response, 202


	class SingleShoppingListAPI(Resource):
		method_decorators = [authenticate]

		def get(self, user_id, shoppinglist_id):
			shoppinglist = ShoppingList.query.filter_by(id=shoppinglist_id).first()
			if shoppinglist:
				response = jsonify({
					'id': shoppinglist.id,
					'owner': shoppinglist.owner_id,
					'title': shoppinglist.title,
					'description': shoppinglist.description,
					'status': 'success'
				})
				return make_response(response, 200)
			response = {
				'message': 'Requested value \'{}\' was not found'.format(shoppinglist_id)
			}
			return response, 202

		def put(self, user_id, shoppinglist_id):
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
						'message': 'Shopping List updated successfuly',
						'status': 'success'
					}
					return response, 200
				response = {
					'status': "fail",
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
				response = {
					'message': message,
					'status': 'fail'						
				}
				return response, 202

		def delete(self, user_id, shoppinglist_id):
			shoppinglist = ShoppingList.query.filter_by(id=shoppinglist_id).first()
			if shoppinglist:
				shoppinglist.delete_shoppinglist()
				response = {
					'status': 'success',
					'message': 'Shopping List \'{}\' deleted successfuly'.format(shoppinglist.title)
				}
				return response, 201
			response = {
				'status': 'fail',
				'message': 'Requested value \'{}\' was not found'.format(shoppinglist_id)
			}
			return response, 202

	class ShoppingListItemsAPI(Resource):
		method_decorators = [authenticate]

		def get(self, user_id, shoppinglist_id):
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
					'status': 'success',
					'message': "You don't have any items for now"
				}
				return response, 202
			response = jsonify(results)
			response.status_code = 202
			return response

		def post(self, user_id, shoppinglist_id):
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
				response = {
					'message': message,
					'status': 'fail'
				}
				return response, 202

	class SingleShoppingListItemAPI(Resource):
		method_decorators = [authenticate]

		def get(self, user_id, shoppinglist_id, shoppinglistitem_id):
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

		def put(self, user_id, shoppinglist_id, shoppinglistitem_id):
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
					return response, 200
				response = {
					'message': 'Shopping list item {} already exists'.format(item_title),
					'status': 'fail'
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
					'status': "fail"
				})
				return make_response(response, 202)

		def delete(self, user_id, shoppinglist_id, shoppinglistitem_id):
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

	class SearchQuery(Resource):
		"""Implement search through items"""
		method_decorators = [authenticate]

		def get(self, user_id, search_query):
			search_results = ShoppingList.query.filter(ShoppingList.title.like('%'+search_query+'%')).all()
			results = []
			for shoppinglist in search_results:
				obj = {
					'id': shoppinglist.id,
                    'title': shoppinglist.title,
                    'description': shoppinglist.description,
                    'date_created': shoppinglist.date_created,
                    'date_modified': shoppinglist.date_modified,
                    'owner_id': shoppinglist.owner_id
                }
				results.append(obj)
			if results == []:
				response = jsonify({
					'status': 'fail',
					'message': 'Item not found!!'
				})
				return make_response(response, 200)
			response = jsonify({
				'status': 'success',
				'search_results': results
				})
			return make_response(response, 200)


	@app.errorhandler(404)
	def page_not_found(e):
		response = jsonify({
			'status':'fail',
			'message': 'Page Not Found!!'
			})

		return make_response(response, 404)
	
	api.add_resource(Home, '/')
	api.add_resource(Register, '/auth/register')
	api.add_resource(Login, '/auth/login')
	api.add_resource(Logout, '/auth/logout')
	api.add_resource(ResetPassowrd, '/resetpassword')
	api.add_resource(User, '/user', endpoint='useraccounts')
	api.add_resource(SearchQuery, '/search/q=<search_query>', endpoint='searchquery')
	api.add_resource(ShoppingListAPI, '/shoppinglists/<int:page>', '/shoppinglists', endpoint='shoppinglists')
	api.add_resource(SingleShoppingListAPI, '/shoppinglist/<int:shoppinglist_id>', endpoint='shoppinglist')
	api.add_resource(ShoppingListItemsAPI, '/shoppinglist/<int:shoppinglist_id>/items', endpoint='shoppinglistitems')
	api.add_resource(SingleShoppingListItemAPI, '/shoppinglist/<int:shoppinglist_id>/item/<int:shoppinglistitem_id>', endpoint='singleshoppinglistitem')
	return app
