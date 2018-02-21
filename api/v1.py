'''
Copyright (c) 2017
@author: Jean Abayo <jean.abayo@andela.com>
'''

from flask import Blueprint
from flask_restful import Api

from .resources.auth import Home
from .resources.auth import Register, Login, Logout
from .resources.items import ShoppingListItemsAPI, SingleShoppingListItemAPI
from .resources.shoppinglists import ShoppingListAPI, SingleShoppingListAPI, SearchQuery, SearchItemsQuery
from .resources.user import ResetPassword, User

API_VERSION_V1 = 1
API_VERSION = API_VERSION_V1

api_v1_bp = Blueprint('api_v1', __name__)
api = Api(api_v1_bp, catch_all_404s=True)

api.add_resource(Home, '/', endpoint='welcome')
api.add_resource(Register, '/auth/register', endpoint='register')
api.add_resource(Login, '/auth/login', endpoint='login')
api.add_resource(Logout, '/auth/logout', endpoint='logout')
api.add_resource(ResetPassword, '/resetpassword', endpoint='resetpassword')
api.add_resource(User, '/user', endpoint='useraccounts')
api.add_resource(SearchQuery, '/search',
                 endpoint='searchquery')
api.add_resource(SearchItemsQuery, '/search/<int:shoppinglist_id>',
                 endpoint='searchitemquery')

api.add_resource(
    ShoppingListAPI,
    '/shoppinglists',
    endpoint='shoppinglists')
api.add_resource(
    SingleShoppingListAPI,
    '/shoppinglists/<int:shoppinglist_id>',
    endpoint='single_shoppinglist'
)
api.add_resource(
    ShoppingListItemsAPI,
    '/shoppinglists/<int:shoppinglist_id>/items',
    endpoint='shoppinglistitems'
)
api.add_resource(
    SingleShoppingListItemAPI,
    '/shoppinglists/<int:shoppinglist_id>/items/<int:shoppinglistitem_id>',
    endpoint='singleshoppinglistitem'
)
