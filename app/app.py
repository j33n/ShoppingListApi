import os
from flask import Flask, request, make_response, jsonify
from flask.views import MethodView
from flask_sqlalchemy import SQLAlchemy
import sqlalchemy


app = Flask(__name__)


class RegisterUserAPI(MethodView):

    def post(self):
        post_data = request.get_json()
        print(post_data.get('email'))
        return 'Ok'

app.add_url_rule('/register', view_func=RegisterUserAPI.as_view('register'))

if __name__ == '__main__':
    app.run()
