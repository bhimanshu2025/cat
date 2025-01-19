from flask import request, Blueprint, current_app, jsonify
from cat.utils.teams import utils
import json
from cat.api.users.auth import basic_auth
from flask_login import logout_user

teams = Blueprint('teams', __name__)

# Use below body for update teams
# {
#     "email": "xyz@abc.com"
#     "mxwebhook": "https://xxxx
# }
@teams.route("/api/team/<string:teamname>", methods=['GET', 'POST', 'DELETE'])
@basic_auth.login_required
def team(teamname):
    if request.method == "GET":
        ret = utils.team(teamname)
    elif request.method == 'DELETE':
        ret = utils.del_team(teamname)
    else:
        try:
            d = json.loads(request.data)
        except json.decoder.JSONDecodeError as error:
            current_app.logger.exception(error)
            ret = f"Failed to load the request json data. Error: {error}", 400
        else:
            ret = utils.edit_team(teamname, d)
    logout_user()
    return ret
    
@teams.route("/api/teams", methods=['GET'])
@basic_auth.login_required
def get_teams():
    response, response_code = utils.teams()
    logout_user()
    if response_code == 200:
        return jsonify(response)
    else:
        return response, response_code

#   { 
#*  "teamname" : "TeamX" ,
#   "email" : "abc.xzy.com"
#   "mswebhook" : "https://xxxx"
#   }
@teams.route("/api/team", methods=['POST'])
@basic_auth.login_required
def add_team():
    try:
        d = json.loads(request.data)
    except json.decoder.JSONDecodeError as error:
        current_app.logger.exception(error)
        ret = f"Failed to load the request json data. Error: {error}", 400
    else:
        ret = utils.add_team(d)
    logout_user()
    return ret 

@teams.route("/api/users-of-team/<string:teamname>", methods=['GET'])
@basic_auth.login_required
def get_users(teamname):
    response, response_code = utils.users(teamname)
    logout_user()
    if response_code == 200:
        return jsonify(response)
    else:
        return response, response_code