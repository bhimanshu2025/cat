from flask_httpauth import HTTPBasicAuth, HTTPTokenAuth
from cat.models import User
from cat.errors.api.errors import error_response
from flask_login import login_user
'''
Flask-HTTPAuth supports a few different authentication mechanisms, all API friendly. 
To integrate with Flask-HTTPAuth, the application needs to provide two functions: one that defines the logic to 
check the username and password provided by the user, and another that returns the error response in the case of an authentication failure. 
These functions are registered with Flask-HTTPAuth through decorators, and then are 
automatically called by the extension as needed during the authentication flow. 
Ref:
https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-xxiii-application-programming-interfaces-apis
'''
basic_auth = HTTPBasicAuth()

token_auth = HTTPTokenAuth()

@basic_auth.verify_password
def verify_password(username, password):
    user = User.query.filter_by(username=username).first()
    if user and User.validate_user_password(username, password):
        login_user(user)
        return user
    else:
        return False

@basic_auth.error_handler
def basic_auth_error(status):
    return error_response(status)
