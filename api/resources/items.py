from flask_restful import Resource
from flask import jsonify, make_response, abort
from api.common.utils import validate, parser, authenticate
from api.models import ShoppingList, ShoppingListItem


class ShoppingListItemsAPI(Resource):
    """This"""
    method_decorators = [authenticate]

    def get(self, user_id, shoppinglist_id):
        """Fetch items on a shoppinglist"""
        args = parser(['page', 'per_page'])
        page = args['page']
        per_page = args['per_page']
        results = []
        items = {}
        pagination = {}
        all_items = []

        if page and per_page is None or page and per_page == '':
            per_page = "5"
        if page and per_page and page != '':
            # Check that our page and per_page are valid integers
            validate_page = page.isdigit()
            validate_per_page = per_page.isdigit()
            if not validate_page or not validate_per_page:
                response = {
                    'status': 'fail',
                    'message': "Page and per page should be integers"
                }
                return response, 400
            # Check that our page and per_page are not 0 or less
            elif int(page) <= 0 or int(per_page) <= 0:
                response = {
                    'status': 'fail',
                    'message': "Page and per page should be more than 0"
                }
                return response, 400
            all_shoppinglistitems = ShoppingListItem.query.filter_by(
                shoppinglist_id=shoppinglist_id, owner_id=user_id).order_by("item_id desc")
            paginated_items = all_shoppinglistitems.paginate(
                int(page), int(per_page), False)
            get_items = paginated_items.items
            # Add item pagination
            pagination['pagination'] = {
                'has_next': paginated_items.has_next,
                'has_prev': paginated_items.has_prev,
                'prev_page_number': paginated_items.prev_num,
                'next_page_number': paginated_items.next_num,
                'total_items': paginated_items.total,
                'number_of_pages': paginated_items.pages,
            }
        else:
            # Perform a fetch of all non-paginated items
            paginated_items = ShoppingListItem.query.filter_by(
                shoppinglist_id=shoppinglist_id, owner_id=user_id).all()
            get_items = paginated_items

        for shoppinglistitem in get_items:
            obj = {
                'item_id': shoppinglistitem.item_id,
                'item_title': shoppinglistitem.item_title,
                'item_description': shoppinglistitem.item_description,
                'shoppinglist_id': shoppinglistitem.shoppinglist_id,
                'date_created': shoppinglistitem.date_created,
                'date_modified': shoppinglistitem.date_modified,
                'owner_id': shoppinglistitem.owner_id
            }
            all_items.append(obj)
        # Check if we don't have any items for now
        if len(all_items) == 0:
            response = {
                'status': 'success',
                'message': "You don't have any items for now"
            }
            return response, 400
        items['items'] = all_items
        results.append(items)
        results.append(pagination)
        response = jsonify(results)
        response.status_code = 200
        return response

    def post(self, user_id, shoppinglist_id):
        """This endpoint creates a new item"""
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
            # Check our item doesn't exist
            check_exists = ShoppingListItem.query.filter_by(
                item_title=item_title, owner_id=user_id).first()
            if check_exists:
                response = {
                    'message':
                    'Shopping List item {} already exists'.format(item_title)
                }
                return response, 400
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
            if check_exists and check_exists.item_id != shoppinglistitem_id:
                response = {
                    'message':
                    'Shopping list item {} already exists'.format(item_title),
                    'status': 'fail'
                }
                return response, 400
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
