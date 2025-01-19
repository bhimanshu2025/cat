import sys
 
sys.path.insert(0, '/var/www/flaskapp/')

from cat import create_app
application = create_app()
