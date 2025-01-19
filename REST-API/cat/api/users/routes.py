from cat.utils.users import utils
from flask import jsonify, Blueprint, request, current_app
import json
from datetime import datetime
from cat.api.users.auth import basic_auth
from flask_login import logout_user

users = Blueprint('users', __name__)

@users.route("/api/users", methods=['GET'])
@basic_auth.login_required
def get_users():
    response, response_code = utils.users()
    logout_user()
    if response_code == 200:
        return jsonify(response)
    else:
        return response, response_code
    
@users.route("/api/jobs/<int:page>", methods=['GET'])
@basic_auth.login_required
def get_jobs(page):
    jobs = utils.jobs(page)
    l_jobs = [] 
    for job in jobs.items:
        l_jobs.append(job.schema())
    logout_user()
    return jsonify(l_jobs)

@users.route("/api/job/<string:id>", methods=['GET'])
@basic_auth.login_required
def get_job(id):
    response, response_code = utils.get_job(id)
    if response_code == 200:
        return response
    else:
        return response, response_code

# {
# *     "username": "user1",
# *     "password": "pass123",
#       "muleuser": False
# }
@users.route("/api/login", methods=['POST'])
def login():
    try:
        d = json.loads(request.data)
    except json.decoder.JSONDecodeError as error:
        current_app.logger.exception(error)
        return f"Failed to load the request json data. Error: {error}", 400
    logout_user()
    return utils.login(d)

# For POST request, below are fields that can be updated
# {
#      "email": "nishant@gmail.com",
#      "teamname": "T6",
#      "active": True,
#      "timezone": "US\Pacific",
#      "shift_start": "09:00:00",
#      "shift_end": "18:00:00",
#      "admin": False,
#      "first_name": "Tom",
#      "last_name": "Kumar",
#      "team_email_notifications": False,
#      "monitor_case_updates": False
# }
@users.route("/api/user/<string:id>", methods=['GET', 'POST', 'DELETE'])
@basic_auth.login_required
def user(id):
    if request.method == 'GET':
        ret = utils.user(id)
    elif request.method == 'DELETE':
        ret = utils.del_user(id)
    else:
        try:
            d = json.loads(request.data)
        except json.decoder.JSONDecodeError as error:
            current_app.logger.exception(error)
            ret = f"Failed to load the request json data. Error: {error}", 400
        else:
            ret = utils.edit_user(id, d)
    logout_user()
    return ret

# {
# *    "username": "nishant",
#      "email": "nishant@gmail.com",
# *    "password": "abc",
# *    "teamname": "T6",
#      "active": True,
#      "admin": False,
#      "timezone": "US\Pacific",
#      "shift_start": "09:00:00",
#      "shift_end": "18:00:00",
#      "first_name": "Tom",
#      "last_name": "Kumar",
#      "team_email_notifications": False,
#      "monitor_case_updates": False
# }
@users.route("/api/user", methods=['POST'])
@basic_auth.login_required
def add_user():
    try:
        d = json.loads(request.data)
    except json.decoder.JSONDecodeError as error:
        current_app.logger.exception(error)
        ret = f"Failed to load the request json data. Error: {error}", 400
    else:
        ret = utils.add_user(d)      
    logout_user()
    return ret      

# {
# *    "current_password": "xzy",
# *    "new_password": "abc"
# }
@users.route("/api/user/change-password/<string:username>", methods=['POST'])
@basic_auth.login_required
def change_password(username):
    try:
        d = json.loads(request.data)
    except json.decoder.JSONDecodeError as error:
        current_app.logger.exception(error)
        ret = f"Failed to load the request json data. Error: {error}", 400
    else:
        ret = utils.change_password(username, d)     
    logout_user()
    return ret   

@users.route("/api/user/reset-password/<string:email>", methods=['POST'])
def reset_password(email):
    return utils.reset_password(email)     

# {
# *    "datetime": "2023/10/19 13:12",
# *    "timezone": "US/Pacific",
# *    "active": True
# }
@users.route("/api/user/reactivate/<string:username>", methods=['POST'])
@basic_auth.login_required
def reactivate_user(username):
    try:
        d = json.loads(request.data)
    except json.decoder.JSONDecodeError as error:
        current_app.logger.exception(error)
        response, response_code = f"Failed to load the request json data. Error: {error}", 400
    else:
        datetime_str = d.get("datetime")
        timezone_str = d.get("timezone")
        active = d.get("active")
        if not datetime_str or not timezone_str or active is None:
            response, response_code = "Invalid Input", 400
        else:
            # convert the string to datetime objects, timezone is just a string
            datetime_obj = datetime.strptime(datetime_str, '%Y/%m/%d %H:%M')
            d_obj = {
                "username": username,
                "datetime": datetime_obj,
                "timezone": timezone_str,
                "active": active
            }
            response, response_code = utils.reactivate_user(d_obj)
    logout_user()
    if response_code == 200:
        return response
    else:
        return response, response_code

# {
# *    "datetime": "2023/10/19 13:12",
# *    "timezone": "US/Pacific",
# *    "shift_start": "10:00:00",
# *    "shift_end": "18:00:00"
# }
@users.route("/api/user/schedule-shift-change/<string:username>", methods=['POST'])
@basic_auth.login_required
def schedule_shift_change(username):
    try:
        d = json.loads(request.data)
    except json.decoder.JSONDecodeError as error:
        current_app.logger.exception(error)
        response, response_code = f"Failed to load the request json data. Error: {error}", 400
    else:
        # convert the string to datetime objects, timezone is just a string
        datetime_str = d.get("datetime")
        timezone_str = d.get("timezone")
        shift_start = d.get("shift_start")
        shift_end = d.get("shift_end")
        if not datetime_str or not timezone_str or not shift_start or not shift_end:
            response, response_code = "Invalid Input", 400
        else:
            datetime_obj = datetime.strptime(datetime_str, '%Y/%m/%d %H:%M')
            d_obj = {
                "username": username,
                "datetime": datetime_obj,
                "timezone": timezone_str,
                "shift_start": shift_start,
                "shift_end": shift_end
            }
            response, response_code = utils.schedule_shift_change(d_obj)
    logout_user()
    if response_code == 200:
        return response
    else:
        return response, response_code

# {
# *    "datetime": "2023/10/19 13:12",
# *    "timezone": "US/Pacific",
#      "check_in_shift": false
# }
@users.route("/api/user/schedule-handoffs/<string:username>", methods=['POST'])
@basic_auth.login_required
def schedule_handoffs(username):
    try:
        d = json.loads(request.data)
    except json.decoder.JSONDecodeError as error:
        current_app.logger.exception(error)
        response, response_code = f"Failed to load the request json data. Error: {error}", 400
    else:
        # convert the string to datetime objects, timezone is just a string
        datetime_str = d.get("datetime")
        timezone_str = d.get("timezone")
        check_in_shift = d.get("check_in_shift")
        if not datetime_str or not timezone_str:
            response, response_code = "Invalid Input", 400
        else:
            datetime_obj = datetime.strptime(datetime_str, '%Y/%m/%d %H:%M')
            d_obj = {
                "username": username,
                "datetime": datetime_obj,
                "timezone": timezone_str,
                "check_in_shift": check_in_shift
            }
            response, response_code = utils.schedule_handoffs(d_obj)
    logout_user()
    if response_code == 200:
        return response
    else:
        return response, response_code
    
@users.route("/api/delete-job/<string:jobid>", methods=['DELETE'])
@basic_auth.login_required
def delete_job(jobid):
    response, response_code = utils.del_job(jobid)
    logout_user()
    if response_code == 200:
        return jsonify(response)
    else:
        return response, response_code

@users.route("/api/salesforce-emails")
@basic_auth.login_required
def salesforce_emails():
    response, response_code = utils.salesforce_emails()
    logout_user()
    if response_code == 200:
        return jsonify(response)
    else:
        return response, response_code

# {
# *    "email_name": "email1",
# *    "email_body": "This is a test email body",
#      "email_subject": "Test Subject",
# }
@users.route("/api/add-salesforce-email", methods=['POST'])
@basic_auth.login_required
def add_salesforce_email():
    try:
        d = json.loads(request.data)
    except json.decoder.JSONDecodeError as error:
        current_app.logger.exception(error)
        ret = f"Failed to load the request json data. Error: {error}", 400
    else:
        ret = utils.add_salesforce_email(d)      
    logout_user()
    return ret   

# For POST call, below are editable fields
# {
#      "email_body": "This is a test email body",
#      "email_subject": "Test Subject",
# }
@users.route("/api/salesforce-email/<string:email_name>", methods=['GET', 'POST', 'DELETE'])
@basic_auth.login_required
def salesforce_email(email_name):
    if request.method == 'GET':
        ret = utils.salesforce_email(email_name)
    elif request.method == 'DELETE':
        ret = utils.delete_salesforce_email(email_name)
    else:
        try:
            d = json.loads(request.data)
        except json.decoder.JSONDecodeError as error:
            current_app.logger.exception(error)
            ret = f"Failed to load the request json data. Error: {error}", 400
        else:
            ret = utils.edit_salesforce_email(email_name, d)
    logout_user()
    return ret

@users.route("/api/jinja2_variables", methods=['GET'])
@basic_auth.login_required
def jinja2_variables():
    logout_user()
    return {
        "assigned_to": "The username who got the case assigned",
        "assigned_to_full_name": "The full name of user who got the case assigned",
        "assigned_to_email": "The email of user who got the case assigned",
        "assigned_by": "The username who assigned the case",
        "assigned_by_full_name": "The full name of user who assigned the case",
        "assigned_by_email": "The email of user who assigned the case"
    }
