from flask_restful import Resource
from flask import jsonify, make_response, abort
from api.common.utils import validate, parser, authenticate
from api.models import ShoppingList


class ShoppingListAPI(Resource):
    """This class will manage paginations on shoppinglists"""
    method_decorators = [authenticate]

    def get(self, user_id):
        """A method to fetch shoppinglists using different properties"""
        args = parser(['page', 'per_page'])
        page = args['page']
        per_page = args['per_page']
        if page and per_page is None or page and per_page == '':
            per_page = "5"
        
        if page and per_page and page != '':
            # Check that our page and per_page are valid integers
            validate_page = page.isdigit()
            validate_per_page = per_page.isdigit()
            if not validate_page or not validate_per_page:
                response = {
                    'status':'fail',
                    'message': "Page and per page should be integers"
                }
                return response, 400
            # Check that our page and per_page are not 0 or less
            elif int(page) <= 0 or int(per_page) <= 0:
                response = {
                    'status':'fail',
                    'message': "Page and per page should be more than 0"
                }
                return response, 400
            shoppinglists = ShoppingList.query.filter_by(owner_id=user_id)
            # Perform fetch with pagination
            paginated_shoppinglists = shoppinglists.paginate(
                int(page), int(per_page), False)
            get_shoppinglists = paginated_shoppinglists.items
        else:
            # Perform a fetch all non-paginated
            paginated_shoppinglists = ShoppingList.query.filter_by(owner_id=user_id).all()
            get_shoppinglists = paginated_shoppinglists
        results = []
        for shoppinglist in get_shoppinglists:
            obj = {
                'id': shoppinglist.id,
                'title': shoppinglist.title,
                'description': shoppinglist.description,
                'date_created': shoppinglist.date_created,
                'date_modified': shoppinglist.date_modified,
                'owner_id': shoppinglist.owner_id
            }
            results.append(obj)
        # Check if we don't have any shoppinglists
        if len(results) == 0:
            response = {
                'message': "No shoppinglists found here, please add them."
            }
            return response, 200
        response = jsonify(results)
        response.status_code = 200
        return response

    def post(self, user_id):
        """This endpoint creates a shoppinglist"""
        args = parser(['title', 'description'])
        # Validate using our validate helper
        invalid = validate(args)
        # Check if valid and return various error messages
        if invalid:
            response = jsonify({
                'status': 'fail',
                'message': invalid
            })
            return make_response(response, 400)
        # Lowercase before saving/checking in DB
        title = args['title'].lower()
        description = args['description']
        # Check a shoppinglist exists
        check_exists = ShoppingList.query.filter_by(title=title).first()
        if check_exists is None:
            shoppinglist = ShoppingList(
                title=title, description=description, owner_id=user_id)
            shoppinglist.save_shoppinglist()
            # Return Response
            response = {
                'id': shoppinglist.id,
                'owner': shoppinglist.owner_id,
                'title': shoppinglist.title,
                'description': shoppinglist.description,
                'message': 'Shopping List created successfuly'
            }
            return response, 200
        response = {
            'message': 'Shopping List {} already exists'.format(title)
        }
        return response, 400

class SingleShoppingListAPI(Resource):
    method_decorators = [authenticate]

    def get(self, user_id, shoppinglist_id):
        """Fetch all items on a shoppinglist"""
        shoppinglist = ShoppingList.query.filter_by(
            id=shoppinglist_id, owner_id=user_id).first()
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
            "message":
            "Requested value \'{}\' was not found".format(shoppinglist_id)
        }
        return response, 500

    def put(self, user_id, shoppinglist_id):
        """Update an item on a shoppinglist"""
        args = parser(['title', 'description'])
        invalid = validate(args)
        if invalid:
            response = jsonify({
                'status': 'fail',
                'message': invalid
            })
            return make_response(response, 400)
        title = args['title'].lower()
        description = args['description']
        title_exists = ShoppingList.query.filter_by(
            owner_id=user_id, title=title, id=shoppinglist_id).first()
        if not title_exists:
            shoppinglist = ShoppingList.query.filter_by(
                owner_id=user_id, id=shoppinglist_id).first()
            if shoppinglist is None:
                return abort(
                    500,
                    description="The shopping list requested is invalid"
                )
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
        return response, 400

    def delete(self, user_id, shoppinglist_id):
        """This function deletes an item"""
        shoppinglist = ShoppingList.query.filter_by(
            owner_id=user_id, id=shoppinglist_id).first()
        if shoppinglist is None:
            return abort(
                500,
                description="The shopping list requested is invalid"
            )
        shoppinglist.delete_shoppinglist()
        response = {
            'status': 'success',
            'message':
            'Shopping List \'{}\' deleted successfuly'.format(
                shoppinglist.title)
        }
        return response, 200

class SearchQuery(Resource):
    """Implement search through items"""
    method_decorators = [authenticate]

    def get(self, user_id):
        """Get endpoint to search through shopping lists"""
        args = parser(['q'])
        search_query = args['q']
        if not search_query:
            response = jsonify({
                'status': 'fail',
                'message': "Please provide a search keyword"
            })
            return make_response(response, 400)
        search_results = ShoppingList.query.filter(ShoppingList.title.like(
            '%'+search_query+'%')).filter_by(owner_id=user_id).all()
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
