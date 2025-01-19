from cat import api_utils as utils
from cat.models import User, Cases, Team, UserProduct, Product, Audit, SalesforceCases
from flask import current_app, request
import pytz, ast
from datetime import datetime, timedelta
from flask_login import current_user
from cat.email import email
from cat.salesforce import Case
from cat.utils.products import utils as product_utils

def assign_case(d_case):
    '''
    d_case : dict object containing case details explained below.
    assignment_history : a list of usernames that the case was assigned to. Saved in the database as a string object
    case_id : case id string
    product :  product name string
    priority : priority string
    check_in_shift : boolean to consider users shifthours when assigning cases, default is True
    mode : manual or auto or auto-reassign assignment
    delayed_reassignment : if set will check for users that are in shift at that specific time of the day. 
    default is none and it uses current time to find list of users that are in shift
    sf_email_name : doesnt get used in this function but it gets passed on to email function.
    '''
    res, res_code = get_sf_details(d_case)
    if res_code != 200:
        return res, res_code
    d_case = res
    case_id = d_case.get('case_id').strip() # remove spaces
    product = d_case.get('product')
    priority = d_case.get('priority')
    assignment_history = []
    if d_case.get('check_in_shift') is not None:
        check_in_shift = d_case.get('check_in_shift')
    else:
        check_in_shift = True
    if case_id == None:
        return f"Please provide a case id", 400
    if product == None:
        return f"Please provide a product name", 400
    p = Product.query.filter_by(productname=product).first()
    if not p:
        return f"Product {product} not found", 404
    if not utils.check_case_id_format(case_id, p):
        return f"Case id {case_id} format incorrect", 400
    existing_c = Cases.query.filter_by(id=case_id).first()
    # If its an existing case, then find the list of cat assigned users of this case.
    if existing_c:
        existing_c_schema = existing_c.schema()
        if existing_c_schema.get('assignment_history'):
            # db column max is 2000 chars for this field
            if len(existing_c_schema.get('assignment_history')) > 1990:
                current_app.logger.info(f"Case {case_id} cant be reassigned. Reached max length for assignment_history column size \
{len(existing_c_schema.get('assignment_history'))}")
                return f"This case can not be reassigned. Please unassign the case first. See logs for details", 400
            assignment_history = ast.literal_eval(existing_c_schema.get('assignment_history'))
    mode = d_case.get('mode') or "auto"
    if (mode == "manual" and existing_c) or (mode == "manual" and not existing_c):
        if not d_case.get('user') and existing_c:
            return f"Please provide a username and select mode as manual for case reassignment. This case is already assigned to {existing_c.user}", 400
        elif not d_case.get('user'):
            return f"User is required when mode is manual", 400
        user = User.query.filter_by(username=d_case.get('user')).first()
        r = UserProduct.query_user_product(user, p, check_in_shift)
        if user == None:
            return f"Incorrect user or user not found: {d_case.get('user')}", 404
        elif r != 0:
            return r, 400
    elif mode == "auto" and existing_c:
        return f"Mode cannot be auto for case reassignment. Please select mode as auto-reassign. \
The case {case_id} is already assigned to {existing_c.user}", 400
    elif mode == "manual" and not d_case.get('user'):
        return f"User is required when mode is manual", 400
    # Auto assign or auto reassign
    else:
        user = utils.assign_case(product, check_in_shift=check_in_shift, exclude_users_list=assignment_history, 
                                 delayed_assignment=d_case.get("delayed_assignment"))
        if user == None:
            return f"No user found for {product}. This may be due to various reasons like users not in shift or inactive users etc", 404
    if current_user:
        curr_user = current_user.username
    else:
        curr_user = "scheduler"
    # Delete existing case object from database
    if existing_c:
        utils.delete_all([existing_c])
        case_exists = True
    else:
        case_exists =  False
        # not an existing case and auto-reassign selected, correct mode to auto
        if mode == "auto-reassign":
            mode = "auto"
    # Add newly assigned user to the list of assigned user for this case to maintain assign case history
    assignment_history.append(user.username)
    c = Cases(id=case_id, user=user.username, product=product, comments=d_case.get('comments'), assigned_by=curr_user, mode=mode, priority=priority,
              sf_account_name=d_case.get('sf_account_name'), assignment_history=str(assignment_history))
    utils.add_all([c])
    case_schema = c.schema()
    case_schema['delayed_assignment'] = d_case.get("delayed_assignment")
    if case_exists:
        a = Audit(user=curr_user, task_type="REASSIGN CASE", task=str([existing_c_schema, case_schema]))
        email.send_case_assign_email(d_case, reassign=True)
    else:
        a = Audit(user=curr_user, task_type="ASSIGN CASE", task=str([case_schema]))
        email.send_case_assign_email(d_case)
    utils.add_all([a])
    current_app.logger.info(f"Case {case_id}:{product}:{priority} assigned to {user.username}")
    return c.schema(), 200
    
def get_sf_details(d_case):
    caseid = d_case.get('case_id').strip() # remove spaces
    product = d_case.get('product')
    # If productname is provided, skip fetching case details from salesforce
    if product:
        # if priority is not provided, set it to a default value
        d_case['priority'] = d_case.get('priority') or 'P2'
        pass
    # No productname provided
    else:
        sf_response, sf_res_code = salesforce_case_details(caseid)
        # Failed to get case data from Salesforce.
        if sf_res_code != 200:
            return sf_response + ". Try again or select a product from dropdown to skip connecting to Salesforce Server.", 500
        # Got case data from Salesforce.
        else:
            d_case['sf_account_name'] = sf_response.account_name
            d_case['priority'] = sf_response.priority.split()[0]
            product_obj = product_utils.find_product_series(sf_response.product_series, sf_response.mist_product)
            if product_obj is None:
                return f"Case {caseid} belongs to product series {sf_response.product_series} thats not associated with any product in CAT", 404
            d_case['product'] = product_obj.productname
        # If current user is None i.e scheduler, skip this check
        if current_user and d_case['product'] not in current_user.product_names():
            return f"Case {caseid} belongs to product {product}. User {current_user.full_name} isnt added to the product in CAT.", 404   
    return d_case, 200
        
def cases_of_product(productname, page):
    product = Product.query.filter_by(productname=productname).first()
    if product is None:
        return f"Product {productname} not found", 404
    li = utils.cases_of_product(product, page)
    return li, 200

def cases_of_team(teamname, page=1, per_page=10, mode=None, priority=None):
    team = Team.query.filter_by(teamname=teamname).first()
    if team is None:
        return f"Team {teamname} not found", 404
    li = utils.cases_of_team(teamname=teamname, page=page, per_page=per_page, mode=mode, priority=priority)
    return li, 200

def cases_assigned_by_user(username, page):
    user = User.query.filter_by(username=username).first()
    if user == None:
        msg = f"User {username} not found"
        current_app.logger.info(msg)
        return msg, 404
    li = utils.cases_assigned_by_user(username, page)
    return li, 200

def cases_of_user(username, page):
    user = User.query.filter_by(username=username).first()
    if user == None:
        return f"User {username} not found", 404
    li = utils.cases_of_user(username, page)
    return li, 200

def case_count_of_all_users(d):
    if d.get('period')  is None:
        return f"Please provide a period", 400
    if d.get('interval') is None:
        return f"Please provide interval", 400
    period = int(d.get('period'))
    interval = int(d.get('interval'))
    product = d.get('productname')
    team = d.get('teamname')
    if period < interval:
        return f"Period cant be less than interval", 400
    if product is not None:
        p = Product.query.filter_by(productname=product).first()
        if p is None:
            return f"Product {product} not found", 404
    if team is None:
        users = User.query.all()
    else:
        t = Team.query.filter_by(teamname=team).first()
        if t is None:
            return f"Team {team} not found", 404
        users = User.query.filter_by(teamname=team)
    l_date = datetime.now(tz=pytz.UTC)
    f_date =  datetime.now(tz=pytz.UTC) - timedelta(interval)
    e_date = datetime.now(tz=pytz.UTC) - timedelta(period)
    r = {}
    format = f"{f_date.day}:{f_date.strftime('%b')}:{f_date.year}-{l_date.day}:{l_date.strftime('%b')}:{l_date.year}"
    while f_date >= e_date:
        d = {}
        for user in users:
            count = len(Cases.get_all_cases_of_user(user.username, f_date, l_date, product))
            d[user.username] = count
        format = f"{f_date.day}:{f_date.strftime('%b')}:{f_date.year}-{l_date.day}:{l_date.strftime('%b')}:{l_date.year}"
        r[format] = d
        l_date = l_date - timedelta(interval)
        f_date = f_date - timedelta(interval)
    return r, 200

def unassign_case(d, id):
    case_id = id.strip() # remove spaces
    c = Cases.query.filter_by(id=case_id).first()
    if c is None:
        return f"Case {id} not found", 404
    c_schema = c.schema()
    task = c_schema
    task["comments"] = d.get('comments')
    a = Audit(user=current_user.username, task_type="UNASSIGN CASE", task=str(task))
    utils.add_all([a])
    utils.delete_all([c])
    email.send_case_unassign_email(task)
    current_app.logger.info(f"Case {case_id}:{c_schema.get('product')}:{c_schema.get('priority')} unassigned")
    return c_schema, 200

def case_details(id):
    case = Cases.query.filter_by(id=id).first()
    if case == None:
        return f"Record not found of case {id}", 404
    return case.schema(), 200

def cases(page=1, per_page=10):
    if current_user and current_user.username == "admin":
        return utils.cases_of_team(page=page, per_page=per_page), 200
    else:
        return cases_of_team(current_user.teamname, page=page, per_page=per_page)

def cases_assigned_by_mode(mode, page):
    if mode not in ["manual", "auto", "auto-reassign"]:
        return f"Invalid mode {mode}", 400
    if current_user and current_user.username == "admin":
        return utils.cases_of_team(page=page, mode=mode), 200
    else:
        return cases_of_team(current_user.teamname, page, mode=mode)

def cases_assigned_by_priority(priority, page):
    if priority not in current_app.config.get("PRIORITY_LIST"):
        return f"Invalid priority {priority}", 400
    if current_user and current_user.username == "admin":
        return utils.cases_of_team(page=page, priority=priority)
    else:
        return cases_of_team(current_user.teamname, page, priority=priority)
    
def salesforce_case_details(case_id):
    instance_url = current_app.config['SF_INSTANCE_URL']
    case =  Case.SFCases(instance_url=instance_url).get_case_details(case_id=case_id)
    if case == None:
        return f'Case {case_id} not found', 404
    elif case == 500:
        return 'Failed to connect to Salesforce Server', 500
    else:
        return case, 200
    
def salesforce_open_cases_of_accounts(account_name):
    instance_url = current_app.config['SF_INSTANCE_URL']
    cases =  Case.SFCases(instance_url=instance_url).get_open_cases_of_accounts(account_name_list=[account_name])
    if cases == 500:
        return 'Failed to connect to Salesforce Server', 500
    else:
        return cases, 200
    
def get_uncated_cases_list(days=0, productnames=None):
    return SalesforceCases.get_cases(days=days, productnames=productnames), 200