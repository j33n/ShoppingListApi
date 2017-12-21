from flask import jsonify, make_response, request, current_app
from flask_restful import Resource
from api.common.utils import validate, parser, authenticate
from api.models import Users, UserToken
from api import db, bcrypt

class Home(Resource):

    def get(self):
        response = {'message': "Welcome to Shopping List API"}
        return response, 200


class Register(Resource):

    """Register a user account"""

    def post(self):
        """Method to register a user"""
        # Get data posted
        args = parser(['username', 'email', 'password',
                       'confirm_password', 'question', 'answer'])
        # Check that the arguments passed are valid
        invalid = validate(args)

        if invalid:
            response = jsonify({
                'status': 'fail',
                'message': invalid
            })
            return make_response(response, 400)
        if args['password'] != args['confirm_password']:
            response = {
                'status': 'fail',
                'message': 'Password does not match'
            }
            return response, 400
        # Encrypt password
        password = bcrypt.generate_password_hash(
            args['password'], current_app.config['BCRYPT_LOG_ROUNDS']
        ).decode('utf-8')
        email = args['email'].lower()
        username = args['username']
        question = args['question'].lower()
        answer = args['answer'].lower()
        # Get user from db
        check_user = Users.query.filter_by(email=email).first()
        # Check user account exists
        if check_user is None:
            user = Users(
                username=username,
                email=email,
                password=password,
                question=question,
                answer=answer
            )
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
        return make_response(response, 400)


class Login(Resource):

    def post(self):
        args = parser(['email', 'password'])
        # Check if values are valid
        invalid = validate(args)
        if invalid:
            response = jsonify({
                'status': 'fail',
                'message': invalid
            })
            return make_response(response, 400)
        email = args['email'].lower()
        password = args['password']
        user = Users.query.filter_by(email=email).first()
        # Check user and password match
        if user is not None and bcrypt.check_password_hash(
                user.password, password):
            token = user.encode_token(user.id, current_app.config['TOKEN_EXPIRATION_TIME'])
            # Return token to the user
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
        return response, 400

class Logout(Resource):
    """This class ensures a user can logout"""
    method_decorators = [authenticate]

    def post(self, user_id):
        auth_header = request.headers.get('Authorization')
        access_token = auth_header.split(" ")[1]
        # Save used token to the DB, a token is used once only
        save_used_token = UserToken(token=access_token)
        # Insert the token
        db.session.add(save_used_token)
        db.session.commit()
        responseObject = {
            'status': 'success',
            'message': 'Successfully logged out.'
        }
        return make_response(jsonify(responseObject), 200)
