from flask import request
from app.models import Users

def middleware():
		auth_header = request.headers.get('Authorization')
		if auth_header:
			access_token = auth_header.split(" ")[1]
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