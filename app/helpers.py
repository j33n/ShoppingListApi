import re
from functools import wraps

from flask import request
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

def is_valid(value, min_length, _type):
	message = []
	if len(value) != 0:
		if _type is 'text':
			if not value.isdigit():
				if len(value) < min_length:
					message.append("Value should be more than {} characters".format(min_length))
					return message
					# if len(value.strip()) == 0 or not re.match("^[-a-zA-Z0-9_\\s]*$", value):
					# 	message.append("Name shouldn't be empty. No special characters")
					# 	return message
				return True
								
			message.append("Value can't be numbers")
			return message
	message.append("Value can't be empty")
	return message
