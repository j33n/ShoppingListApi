import re
from functools import wraps

from flask import request
from flask_restful import reqparse
from app.models import Users


def authenticate(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if auth_header:
            access_token = auth_header.split(" ")[1]
            user_id = Users.decode_token(access_token)
            if not isinstance(user_id, int):
                response = {
                    'status': 'fail',
                    'message': user_id
                }
                return response, 401
            return func(*args, user_id, **kwargs)
        response = {
            'status': 'fail',
            'message': 'Authorization is not provided'
        }
        return response, 500
    return wrapper


def validate(*values):
        # Helper function to validate all the data supplied from the user
    min_length = 6
    message = []
    # Value is value that needs to be validated
    for value in values:
        for value_key in value.keys():
            # Check the value is not empty
            if value[value_key] is None:
                message.append(value_key.title() + " is required")
                return message
            # Check the value should not be less than min length chars
            if len(value[value_key]) < min_length:
                message.append("Your " + value_key +
                               " should be more than 6 characters")
            # Check the value can not be numbers only
            if value[value_key].isdigit():
                message.append(value_key.title() + " can't be numbers only")
            # Use regex to validate email
            if value_key is "email" or value_key is "new_email":
                if not re.match(r"(^[a-zA-Z0-9_.]+@[a-zA-Z0-9-]+\.[a-z]+$)",
                                value[value_key]):
                    message.append("Your " + value_key + " is not valid")
            # Use regex to validate question
            elif value_key is "question":
                if not re.match(r"(^[a-zA-Z0-9_\W.]+$)",
                                value[value_key]):
                    message.append("Your " + value_key + " is not valid")
            else:
                # Check the value is not empty
                if len(value[value_key].strip()) == 0:
                    message.append("Your " + value_key + " is empty")
                # Check special characters are being rejected
                elif not re.match("^[-a-zA-Z0-9_\\s]*$", value[value_key]):
                    message.append(
                        "Your " + value_key +
                        " has special characters that are not allowed"
                    )
    # Return an array that contains all the error messages else false
    if message == []:
        return False
    return message


def parser(form_data):
    """Helper function that parses the data from user"""
    # Get data to parse from the form
    post_data = form_data
    parser = reqparse.RequestParser()
    for arg in range(len(post_data)):
        parser.add_argument(post_data[arg])
        unformatted_args = parser.parse_args()
    args = {}
    for unformatted_arg in unformatted_args.keys():
        if unformatted_args[unformatted_arg] is None:
            args[unformatted_arg] = None
        else:
            # Format the arguments for spaces
            formatted_arg = " ".join(unformatted_args[unformatted_arg].split())
            args[unformatted_arg] = formatted_arg
    return args
