from cat.models import UserProduct, Audit
from flask import Blueprint, jsonify, request, current_app
from cat.utils.userproduct import utils
import json
from cat.api.users.auth import basic_auth
from flask_login import logout_user

ups = Blueprint('up', __name__)

@ups.route("/api/all-user-product", methods=['GET'])
@basic_auth.login_required
def get_all_user_product():
    response, response_code =  utils.all_user_product()
    logout_user()
    if response_code == 200:
        return jsonify(response)
    else:
        return response, response_code
    
# { 
# *    "username" : "nishant",
# *    "productname" : "P2",
#     "active" : True,
#     "quota" : 1
# }
@ups.route("/api/user-product", methods=['POST'])
@basic_auth.login_required
def user_product():
    try:
        d = json.loads(request.data)
    except json.decoder.JSONDecodeError as error:
        current_app.logger.exception(error)
        ret = f"Failed to load the request json data. Error: {error}", 400
    else:
        ret = utils.update_user_product(d)
    logout_user()
    return ret

@ups.route("/api/user-product/<string:username>/<string:productname>", methods=['GET', 'DELETE'])
@basic_auth.login_required
def delete_user_product(username, productname):
    if request.method == 'GET':
        response, response_code = utils.user_product(username, productname)
    else:
        response, response_code = utils.del_user_product(username, productname)
    logout_user()
    if response_code == 200:
        return jsonify(response)
    else:
        return response, response_code