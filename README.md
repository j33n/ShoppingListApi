ShoppingListApi

[![Build Status](https://travis-ci.org/JeanAbayo/ShoppingListApi.svg?branch=develop)](https://travis-ci.org/JeanAbayo/ShoppingListApi)
[![Coverage Status](https://coveralls.io/repos/github/JeanAbayo/ShoppingListApi/badge.svg?branch=master)](https://coveralls.io/github/JeanAbayo/ShoppingListApi?branch=master)
<a href="https://codeclimate.com/github/JeanAbayo/ShoppingListApi/test_coverage"><img src="https://api.codeclimate.com/v1/badges/56250b6d23973fc9fde8/test_coverage" /></a>
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)

An api to make shopping quick, easy and fun by organizing and keeping track of your lists

The api can be accessed [here](myshoppinglistapi.herokuapp.com) and the documentation [here](http://myshoppinglistapi.herokuapp.com/apidocs)

## Prerequisites

- Python 3.5
- Flask
- Postgres

## Database

```powershell
sudo su - postgres
```

```mariadb
psql
```

```mariadb
CREATE USER test_user with password 'secret';
```

```mariadb
CREATE DATABASE shoppinglist owner test_user encoding 'utf-8';
```

```mariadb
CREATE DATABASE shoppinglist_test owner test_user encoding 'utf-8';
```

## Installation

Clone this repo, switch in the repo and create an environment

```powershell
git clone https://github.com/JeanAbayo/ShoppingListApi.git
cd ShoppingListApi
virtualenv venv

```

Create a .env file and export it like `source .env`

```php
source venv/bin/activate
export FLASK_APP="run.py"
export SECRET="Your choosen secret key"
export APP_SETTINGS="development"
export DATABASE_URL="postgresql://db_username:db_password@localhost/db_name"
```

Install used packages

```
pip install -r requirements.txt
```

Initialize, migrate and update the database:

```python
python manage.py db init
python manage.py db migrate
python manage.py db upgrade
```

## Usage

### Test our app

`python manage.py test`

with coverage

`coverage run --source=app -m py.test && coverage report`

### Run our app

`flask run`

## Endpoints
| Resource URL                           | Methods |              Description              | Requires Token |
| -------------------------------------- | :-----: | :-----------------------------------: | -------------- |
| /auth/register                         |  POST   |           User Registration           | FALSE          |
| /auth/login                            |  POST   |             User Sign in              | FALSE          |
| /shoppinglists                         |  POST   |      User create a shoppinglist       | TRUE           |
| /shoppinglists                         |   GET   |    User can view all shoppinglists    | TRUE           |
| /shoppinglist/<list_id>                |   GET   |    User view a single shoppinglist    | TRUE           |
| /shoppinglist/<list_id>                |   PUT   |    User Edit a single shoppinglist    | TRUE           |
| /shoppinglist/<list_id>                | DELETE  |   User Delete a single shoppinglist   | TRUE           |
| /shoppinglist/<list_id>/items          |  POST   |   User create item in shoppinglist    | TRUE           |
| /shoppinglist/<list_id>/items          |   GET   |   User list items in a shoppinglist   | TRUE           |
| /shoppinglist/<list_id>/item/<item_id> |   GET   |  User view an item in a shoppinglist  | TRUE           |
| /shoppinglist/<list_id>/item/<item_id> |   PUT   |  User Edit an item in a shoppinglist  | TRUE           |
| /shoppinglist/<list_id>/item/<item_id> | DELETE  | User delete an item in a shoppinglist | TRUE           |
## Credits
[Jean Abayo](https://github.com/JeanAbayo)
## License
This project is licensed under the MIT License - see the [LICENSE.md](https://github.com/machariamarigi/shopping_list_api/blob/master/LICENSE.md) file for details
