from flask_restful import Resource
from flask import jsonify, make_response, abort
from api.common.utils import validate, parser, authenticate
from api.models import ShoppingList, ShoppingListItem

class ShoppingListItemsAPI(Resource):
    """This"""
    method_decorators = [authenticate]

    def get(self, user_id, shoppinglist_id):
        shoppinglistitems = ShoppingListItem.query.filter_by(
            shoppinglist_id=shoppinglist_id, owner_id=user_id)
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
            return response, 400
        response = jsonify(results)
        response.status_code = 200
        return response

    def post(self, user_id, shoppinglist_id):
        check_sl = ShoppingList.query.filter_by(
            id=shoppinglist_id, owner_id=user_id).first()
        if check_sl:
            args = parser(['item_title', 'item_description'])
            # Validate arguments
            invalid = validate(args)
            if invalid:
                response = jsonify({
                    'status': 'fail',
                    'message': invalid
                })
                return make_response(response, 400)

            item_title = args['item_title'].lower()
            item_description = args['item_description']
            check_exists = ShoppingListItem.query.filter_by(
                item_title=item_title, owner_id=user_id).first()
            if check_exists is None:
                shoppinglistitem = ShoppingListItem(
                    item_title=item_title,
                    item_description=item_description,
                    shoppinglist_id=shoppinglist_id,
                    owner_id=user_id
                )
                shoppinglistitem.save_shoppinglistitem()
                # Return Response
                response = {
                    'item_id': shoppinglistitem.item_id,
                    'owner_id': shoppinglistitem.owner_id,
                    'shoppinglist_id': shoppinglistitem.shoppinglist_id,
                    'item_title': shoppinglistitem.item_title,
                    'item_description': shoppinglistitem.item_description,
                    'message':
                    'Shopping list item {} created successfuly'.format(
                        item_title)
                }
                return response, 200
            response = {
                'message':
                'Shopping List item {} already exists'.format(item_title)
            }
            return response, 400
        response = {
            'message':
            'Requested value \'{}\' was not found'.format(
                shoppinglist_id)
        }
        return response, 500

class SingleShoppingListItemAPI(Resource):
    method_decorators = [authenticate]

    def get(self, user_id, shoppinglist_id, shoppinglistitem_id):
        check_sl = ShoppingList.query.filter_by(
            id=shoppinglist_id, owner_id=user_id).first()
        if check_sl:
            shoppinglistitem = ShoppingListItem.query.filter_by(
                item_id=shoppinglistitem_id,
                shoppinglist_id=shoppinglist_id,
                owner_id=user_id
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
                return response, 200
            response = {
                'message':
                'Requested value \'{}\' was not found'.format(
                    shoppinglistitem_id)
            }
            return response, 500
        response = {
            'message':
            'Requested value \'{}\' was not found'.format(
                shoppinglist_id)
        }
        return response, 500

    def put(self, user_id, shoppinglist_id, shoppinglistitem_id):
        check_sl = ShoppingList.query.filter_by(
            id=shoppinglist_id, owner_id=user_id).first()
        if check_sl:
            args = parser(['item_title', 'item_description'])
            # Validate arguments
            invalid = validate(args)
            if invalid:
                response = jsonify({
                    'status': 'fail',
                    'message': invalid
                })
                return make_response(response, 400)
            item_title = args['item_title'].lower()
            item_description = args['item_description']

            check_exists = ShoppingListItem.query.filter_by(
                item_title=item_title, owner_id=user_id).first()
            if check_exists is None:
                shoppinglistitem = ShoppingListItem.query.filter_by(
                    owner_id=user_id,
                    item_id=shoppinglistitem_id,
                    shoppinglist_id=shoppinglist_id
                ).first()
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
                'message':
                'Shopping list item {} already exists'.format(item_title),
                'status': 'fail'
            }
            return response, 400
        response = {
            'message':
            'Requested value \'{}\' was not found'.format(
                shoppinglist_id)
        }
        return response, 500

    def delete(self, user_id, shoppinglist_id, shoppinglistitem_id):
        check_sl = ShoppingList.query.filter_by(
            id=shoppinglist_id, owner_id=user_id).first()
        if check_sl:
            shoppinglistitem = ShoppingListItem.query.filter_by(
                item_id=shoppinglistitem_id,
                owner_id=user_id,
                shoppinglist_id=shoppinglist_id
            ).first()
            if shoppinglistitem:
                shoppinglistitem.delete_shoppinglistitem()
                response = {
                    'message':
                    'Shopping list item \'{}\' deleted successfuly'.format(
                        shoppinglistitem.item_title)
                }
                return response, 200
            response = {
                'message':
                'Requested value \'{}\' was not found'.format(
                    shoppinglistitem_id)
            }
            return response, 500
        response = {
            'message':
            'Requested value \'{}\' was not found'.format(
                shoppinglist_id)
        }
        return response, 500