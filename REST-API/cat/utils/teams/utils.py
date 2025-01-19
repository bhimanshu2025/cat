from cat.models import Team, Audit
import cat.api_utils as utils
from flask_login import current_user
from flask import current_app

def teams():
    li_teams = []
    teams = Team.query.all()
    for team in teams:
        li_teams.append(team.schema())
    return li_teams, 200

def team(teamname):
    team = Team.query.filter_by(teamname=teamname).first()
    if team == None:
        return f"Team {teamname} not found", 404
    return team.schema(), 200
    
def del_team(teamname):
    if (current_user.teamname == teamname and current_user.admin) or current_user.username == "admin":
        team = Team.query.filter_by(teamname=teamname).first()
        if team == None:
            return f"Team {teamname} not found", 404    
        else:
            if len(team.users) != 0:
                l_users = utils.get_user_names(team.users)
                return f"Team {teamname} still has users that are part of it: {l_users}. Remove all users from this team first.", 400
            t = team.schema()
            a = Audit(user=current_user.username, task_type="DELETE TEAM", task=str(t))
            utils.delete_all([team])
            utils.add_all([a])
            current_app.logger.info(f"Team {teamname} deleted successfully")
            return t, 200
    else:
        return "Unauthorized Access", 401
    
def edit_team(teamname, d):
    if (current_user.teamname == teamname and current_user.admin) or current_user.username == "admin":
        team = Team.query.filter_by(teamname=teamname).first()
        if team == None:
            return f"Team {teamname} not found", 404    
        else:
            a = Audit(user=current_user.username, task_type="UPDATE TEAM", task=str([d, team.schema()]))
            team.update(d)
            utils.add_all([team, a])
            current_app.logger.info(f"Team {teamname} updated successfully")
            return team.schema(), 200
    else:
        return "Unauthorized Access", 401

def add_team(d):
    if d.get('teamname') == None:
        return f"Please provide a teamname", 400
    if Team.query.filter_by(teamname=d['teamname']).first() != None:
        return f"Team {d['teamname']} already exists", 400
    t = Team(teamname=d.get('teamname'), email=d.get('email'), mswebhook=d.get('mswebhook'))
    utils.add_all([t])
    if current_user:
        a = Audit(user=current_user.username, task_type="ADD TEAM", task=str(t.schema()))
        utils.add_all([a])
    current_app.logger.info(f"Team {d.get('teamname')} added successfully")
    return t.schema(), 200

def users(teamname):
    l = []
    team = Team.query.filter_by(teamname=teamname).first()
    if team is None:
        return f"Team {teamname} not found", 404
    users = team.users
    for user in users:
        l.append(user.schema())
    return l, 200

def usernames(teamname):
    l = []
    team = Team.query.filter_by(teamname=teamname).first()
    if team is None:
        return f"Team {teamname} not found", 404
    users = team.users
    for user in users:
        l.append(user.username)
    return l, 200