from datetime import datetime, timedelta
from flask import current_app
from cat import scheduler
from cat.utils.products import utils as products_utils
from cat.utils.users import utils as users_utils
from cat.utils.teams import utils as teams_utils
from cat.utils.cases import utils as cases_utils
from cat.utils.userproduct import utils as userproduct_utils
from flask_login import current_user

def check_user_access(username):
    response, response_code = users_utils.user(username)
    if response_code == 200:
        user_schema = response
        if current_user.username == username or (current_user.admin and current_user.teamname == user_schema.get("teamname")) or current_user.username == "admin":
            return True
        else:
            return False
    else:
        return False
    
def get_time_list(diff=1):
    dt = datetime(2023,1,1)
    l = []
    for i in range(0,24):
        temp = (dt + timedelta(hours=i))
        for j in range(0,60,diff):
            str = (temp + timedelta(minutes=j)).strftime('%H:%M:00')
            l.append(str)
    return l

def get_product_names(username=None, object=False):
    '''
    if username is specified, filters list of returned products to products supported by user <username>
    '''
    l = []
    products, res_code = products_utils.products(username)
    if object:
        return products
    for product in products:
        l.append(product.get('productname'))
    return l

def get_user_names(object=False, teamname=None):
    l = []
    if teamname:
        users, res_code = teams_utils.users(teamname)
    else:
        users, res_code = users_utils.users()
    if object:
        return users
    for user in users:
        l.append(user.get('username'))
    return l

def get_team_names(object=False):
    l = []
    teams, res_code = teams_utils.teams()
    if object:
        return teams
    for team in teams:
        l.append(team.get('teamname'))
    return l

def get_team(teamname, object=False):
    team, _ = teams_utils.team(teamname)
    if object:
        return team
    return team.schema()

def get_scheduled_jobs(scheduler=scheduler, object=False):
    if not scheduler:
        return []
    l = []
    jobs = scheduler.get_jobs()
    if object:
        return jobs
    for job in jobs:
        l.append( {
            "jobname": job.name
        })
    return l

def get_cases_list(object=False, per_page=10):
    l = []
    cases, _ = cases_utils.cases(per_page=per_page)
    if object:
        return cases
    for case in cases.items:
        l.append(case.id)
    return l

def get_team_schema(teamname):
    team, res_code = teams_utils.team(teamname)
    if res_code == 200:
        return team
    else:
        return {}
    
def get_user_schema(username):
    user, res_code = users_utils.user(username)
    if res_code == 200:
        return user
    else:
        return {}

def get_product_schema(productname):
    product, res_code = products_utils.product(productname)
    if res_code == 200:
        return product
    else:
        return {}
    
def get_user_product_schema(username, productname):
    userproduct, res_code = userproduct_utils.user_product(username, productname)
    if res_code == 200:
        return userproduct
    else:
        return {}

# Get list of cases that failed to get cat'ed due to various reasons. days=0 means today. This will query salesforcecases table and not the cases table
def get_uncated_cases_list(object=False, days=0):
    l = []
    if current_user.username == "admin":
        productnames, _ = products_utils.product_names()
        cases, _ = cases_utils.get_uncated_cases_list(days=days, productnames=productnames)
    else:
        cases, _ = cases_utils.get_uncated_cases_list(days=days, productnames=current_user.product_names())
    if object:
        return cases
    for case in cases.items:
        l.append(case.id)
    return l