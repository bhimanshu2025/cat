from cat.utils.cases import utils
from flask import request, Blueprint, current_app, jsonify
import json
from cat.api.users.auth import basic_auth
from flask_login import logout_user

cases = Blueprint('cases', __name__)

def format_response(response, response_code):
    if response_code == 200:
        li_cases = response
        cases = []
        for case in li_cases.items:
            cases.append(case.schema())
        return jsonify(cases)
    else:
        return response, response_code
    
@cases.route("/api/cases-of-product/<string:productname>", methods=['GET'])
@basic_auth.login_required
def get_cases_of_product(productname):
    page = request.args.get('page', 1, type=int)
    response, response_code = utils.cases_of_product(productname, page=page)
    logout_user()
    return format_response(response, response_code)

@cases.route("/api/cases-of-team/<string:teamname>", methods=['GET'])
@basic_auth.login_required
def get_cases_of_team(teamname):
    page = request.args.get('page', 1, type=int)
    response, response_code = utils.cases_of_team(teamname, page=page)
    logout_user()
    return format_response(response, response_code)

@cases.route("/api/cases-assigned-by-user/<string:username>", methods=['GET'])
@basic_auth.login_required
def get_cases_assigned_by_user(username):
    page = request.args.get('page', 1, type=int)
    response, response_code = utils.cases_assigned_by_user(username, page=page)
    logout_user()
    return format_response(response, response_code)

@cases.route("/api/cases-of-user/<string:username>", methods=['GET'])
@basic_auth.login_required
def get_cases_of_user(username):
    page = request.args.get('page', 1, type=int)
    response, response_code = utils.cases_of_user(username, page=page)
    logout_user()
    return format_response(response, response_code)

# pefiod defines how long back to look up and interval defines the frequency in that period
# {
#*     "period" : 300,
#*     "interval": 30,
#      "teamname": "T1",
#      "productname": "P1"
# }
@cases.route("/api/case-count-of-all-users", methods=['POST'])
@basic_auth.login_required
def get_case_count_of_all_users():
    try:
        d = json.loads(request.data)
    except json.decoder.JSONDecodeError as error:
        current_app.logger.exception(error)
        ret = f"Failed to load the request json data. Error: {error}", 400
    else:
        ret = utils.case_count_of_all_users(d)
    logout_user()
    return ret

# {
# *     "case_id": "2023-0927-778983",
# *     "product": "P1",
#     "priority": "P3",
#     "comments": "Test",
#     "mode": "manual",
#     "user": "bhimanshu",
#     "check_in_shift": True,
#     "sf_account_name": "xyz",
#     "sf_email_name": "test_email",
#     "sf_account_name": "XYZ",
#     "delayed_assignment": "16:00:00"
# }
@cases.route("/api/assign-case", methods=['POST'])
@basic_auth.login_required
def assign_a_case():
    try:
        d = json.loads(request.data)
    except json.decoder.JSONDecodeError as error:
        current_app.logger.exception(error)
        ret = f"Failed to load the request json data. Error: {error}", 400
    else:
        response, response_code = utils.assign_case(d)
        if response_code == 200:
            ret = response
        else:
            ret = response, response_code
    logout_user()
    return ret

# {
#     "comments": "Test"
# }
@cases.route("/api/unassign-case/<string:id>", methods=['POST'])
@basic_auth.login_required
def unassign_a_case(id):
    try:
        d = json.loads(request.data)
    except json.decoder.JSONDecodeError as error:
        current_app.logger.exception(error)
        ret = f"Failed to load the request json data. Error: {error}", 400
    else:
        ret = utils.unassign_case(d, id)
    logout_user()
    return ret 

@cases.route("/api/case/<string:id>", methods=['GET'])
@basic_auth.login_required
def get_case_details(id):
    ret = utils.case_details(id)
    logout_user()
    return ret 

@cases.route("/api/cases", methods=['GET'])
@basic_auth.login_required
def get_cases():
    page = request.args.get('page', 1, type=int)
    response, response_code = utils.cases(page)
    logout_user()
    return format_response(response, response_code)
    