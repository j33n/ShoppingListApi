from flask import jsonify, make_response, current_app
from flask_restful import Resource
from api.common.utils import validate, parser, authenticate
from api.models import Users
from api import bcrypt


class ResetPassword(Resource):
    """Allow a user to reset a password using a security question"""
    method_decorators = [authenticate]

    def post(self, user_id):
        # Get data posted
        args = parser(
            ['question', 'answer', 'old_password', 'new_password'])
        # Validate arguments
        invalid = validate(args)
        if invalid:
            response = jsonify({
                'status': 'fail',
                'message': invalid
            })
            return make_response(response, 400)
        user = Users.query.filter_by(id=user_id).first()
        # Check if question and answer matches
        if user.question == args['question'].lower() \
                and user.answer == args['answer'].lower():
            # Check old password is the same as what we have
            check_old_password = bcrypt.check_password_hash(
                user.password, args['old_password'])
            if check_old_password:
                # Create new password
                make_new_password = bcrypt.generate_password_hash(
                    args['new_password'],
                    current_app.config.get('BCRYPT_LOG_ROUNDS')).decode('utf-8')
                # Save new password
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
            return make_response(invalid_old_password, 400)
        invalid_question = jsonify({
            'status': 'fail',
            'message': 'Invalid security question, please try again!'
        })
        return make_response(invalid_question, 400)

class User(Resource):
    """ This class helps manage user's information"""
    method_decorators = [authenticate]

    def get(self, user_id):
        """Return  a user's information"""
        user = Users.query.filter_by(id=user_id).first()
        response = jsonify({
            'status': 'success',
            'email': user.email,
            'username': user.username
        })
        return make_response(response, 200)

    def put(self, user_id):
        """Edit account information"""
        args = parser(['new_email', 'new_username', 'password'])
        invalid = validate(args)
        if invalid:
            response = jsonify({
                'status': 'fail',
                'message': invalid
            })
            return make_response(response, 400)

        user = Users.query.filter_by(id=user_id).first()
        check_password = bcrypt.check_password_hash(
            user.password, args['password'])
        if check_password:
            new_email = args['new_email'].lower()
            new_username = args['new_username']
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
        response = jsonify({
            'status': 'fail',
            'message': 'You need your password to update account info.'
        })
        return make_response(response, 400)
