import os
from flasgger import Swagger

from app.app import create_app
# Get the configuration name 
config_name = os.getenv('APP_SETTINGS')
app = create_app(config_name)

# Initialize Flasgger for Swagger documentation
Swagger(app, template_file='../docs/index.yml')

if __name__ == '__main__':
    app.run()
