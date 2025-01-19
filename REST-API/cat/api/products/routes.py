from flask import Blueprint, request, current_app, jsonify
from cat.utils.products import utils
import json
from cat.api.users.auth import basic_auth
from flask_login import logout_user
from datetime import datetime

products = Blueprint('products', __name__)

@products.route("/api/products", methods=['GET'])
@basic_auth.login_required
def get_products():
    response, response_code = utils.products()
    logout_user()
    if response_code == 200:
        return jsonify(response)
    else:
        return response, response_code

# Below values are modifiable
# {
#     "strategy": "s1",
#     "max_days": 2,
#     "max_days_month": "300",
#     "quota_over_days": 1,
#     "case_regex": "^[0-9]{4}-[0-9]{4}-[0-9]{6}$",
#     "sf_api": "https://xxxx",
#     "sf_job_cron": "* 6-18 * * 1-5",
#     "sf_job_timezone": "US/Pacific",
#     "sf_job_query_interval": 1,
#     "sf_platform": "SRX",
#     "sf_product_series": "SRX",
#     "sf_enabled": False,
#     "sf_init_email_name": "email1"
# }
@products.route("/api/product/<string:productname>", methods=['GET', 'POST', 'DELETE'])
@basic_auth.login_required
def product(productname):
    if request.method == 'GET':
        ret =  utils.product(productname)
    elif request.method == 'DELETE':
        ret = utils.del_product(productname)
    else:
        try:
            d = json.loads(request.data)
        except json.decoder.JSONDecodeError as error:
            current_app.logger.exception(error)
            ret = f"Failed to load the request json data. Error: {error}", 400
        else:
            ret = utils.edit_product(productname, d)
    logout_user()
    return ret
    
# {
# *   "productname": "P4",
#     "strategy": "s1",
#     "max_days": 2,
#     "max_days_month": "300"
#     "quota_over_days": 1,
#     "case_regex": "^[0-9]{4}-[0-9]{4}-[0-9]{6}$",
#     "sf_api": "https://xxxx",
#     "sf_job_cron": "* 6-18 * * 1-5",
#     "sf_job_timezone": "US/Pacific",
#     "sf_job_query_interval": 1,
#     "sf_platform": "SRX",
#     "sf_product_series": "SRX",
#     "sf_enabled": False,
#     "sf_init_email_name": "email1"
# }
@products.route("/api/product", methods=['POST'])
@basic_auth.login_required
def add_product():
    try:
        d = json.loads(request.data)
    except json.decoder.JSONDecodeError as error:
        current_app.logger.exception(error)
        ret = f"Failed to load the request json data. Error: {error}", 400
    else:
        ret = utils.add_product(d)
    logout_user()
    return ret

@products.route("/api/users-of-product/<string:productname>", methods=['GET'])
@basic_auth.login_required
def get_users(productname):
    response, response_code = utils.users(productname)
    logout_user()
    if response_code == 200:
        return jsonify(response)
    else:
        return response, response_code

# if holiday_list is provided, then datetime, sf_enabled variables are ignored
# {
#*     "datetime": "2023/10/19 13:12",
#*     "timezone": "US/Pacific",
#*     "sf_enabled": True,
#      "holiday_list": {...}
# }  
@products.route("/api/product/schedule-sf-integration/<string:productname>", methods=['POST'])
@basic_auth.login_required
def schedule_sf_integration(productname):
    try:
        d = json.loads(request.data)
    except json.decoder.JSONDecodeError as error:
        current_app.logger.exception(error)
        response, response_code = f"Failed to load the request json data. Error: {error}", 400
    else:
        datetime_str = d.get('datetime')
        timezone = d.get('timezone')
        sf_enabled = d.get('sf_enabled')
        holiday_list = d.get('holiday_list')
        datetime_obj = datetime.strptime(datetime_str, '%Y/%m/%d %H:%M')
        d_obj = {
            "productname" : productname,
            "datetime": datetime_obj,
            "timezone": timezone,
            "sf_enabled": sf_enabled,
            "holiday_list": holiday_list
        }
        response, response_code = utils.schedule_sf_integration(d_obj)
    logout_user()
    if response_code == 200:
        return jsonify(response)
    else:
        return response, response_code

@products.route("/api/product/delete-job/<string:jobid>", methods=['DELETE'])
@basic_auth.login_required
def products_delete_job(jobid):
    response, response_code = utils.del_job(jobid)
    logout_user()
    if response_code == 200:
        return jsonify(response)
    else:
        return response, response_code