import sys, re, pytz
from cat.models import Product, UserProduct, User, Cases, Team, Jobs, SalesforceCases, SalesforceApiRequests
from cat import db, bcrypt, scheduler, scheduler_sf
from flask import current_app
from cat.utils.users import utils as users_utils
from datetime import datetime
import json, string, random
from apscheduler.triggers.cron import CronTrigger
from flask_login import current_user
from cat.Oauth2.get_token import OAuth2Client
from cat.salesforce import Case

# Custom request to generate a report of number of api calls made
def audit_sf_api_requests(days=7):
    from cat import scheduler_sf
    app = scheduler_sf.app
    with app.app_context(): 
        current_app.logger.info(f"Running audit sf api requests job")
        list_requests = SalesforceApiRequests.number_of_requests(days=days)
        from cat.email import email
        email.send_sf_api_request_summary_report_email(current_app.config['SF_API_REQ_REPORT_EMAILS_LIST'], list_requests, days)

# Returns list of email address of users belonging to team teamname who have team_email_notifications set to True
def team_users_email_list(teamname):
    users_list = Team.query.filter_by(teamname=teamname).first().users
    email_list = []
    for user in users_list:
        if user.team_email_notifications:
            email_list.append(user.email)
    return email_list 

def check_user_access(username):
    response, response_code = users_utils.user(username)
    if response_code == 200:
        user_schema = response
        if current_user.username == username or (current_user.admin and current_user.teamname == user_schema.get("teamname")) \
            or current_user.username == "admin":
            return True
        else:
            return False
    else:
        return False

# For scheduling product related jobs and external update jobs
def schedule_sf_jobs(l_productnames=None):
    current_app.logger.info(f"Scheduling Salesforce jobs for fetching list of newly created cases")
    if l_productnames:
        for productname in l_productnames:
            # delete the job if it exists and let it schedule again. This scenario happens when a product is updated
            delete_sf_jobs(productname)
    products = Product.query.all()
    for product in products:
        productname = product.productname
        job = scheduler_sf.get_job(id=f"get_salesforce_cases_{productname}")
        # delete a job if product doesnt have sf integration enabled or incase product gets updated
        if not product.sf_enabled and job is not None:
            delete_sf_jobs(productname)
        if product.sf_enabled:
            if job is not None:
                current_app.logger.info(f"There is already salesforce job scheduled for product {productname}. \
                                        Skipping creating job for this product.")
            else:
                cron = product.sf_job_cron
                sf_job_timezone = product.sf_job_timezone
                current_app.logger.info(f"Scheduling salesforce job for product {productname}")
                try:
                    scheduler_sf.add_job(id=f"get_salesforce_cases_{productname}", func=get_salesforce_cases, 
                                        args=[productname], trigger=CronTrigger.from_crontab(cron, timezone=pytz.timezone(sf_job_timezone)))
                    current_app.logger.info(f"Scheduled salesforce job for product {productname}")
                except ValueError as err:
                    current_app.logger.error(f"Failed to Scheduled salesforce job for product {productname}. Invalid cron format. {err}")
    check_external_updates_job = scheduler_sf.get_job(id=f"check_sf_cases_for_external_updates")
    if check_external_updates_job is None:
        current_app.logger.info(f"Scheduling Salesforce jobs for monitoring external case updates")
        external_case_update_check_interval = current_app.config['EXTERNAL_CASE_UPDATE_CHECK_INTERVAL']
        scheduler_sf.add_job(id=f"check_sf_cases_for_external_updates", func=check_sf_cases_for_external_updates, 
                                        trigger='interval', minutes=external_case_update_check_interval)

def delete_sf_jobs(productname):
    job = scheduler_sf.get_job(id=f"get_salesforce_cases_{productname}")
    if job is None:
        current_app.logger.info(f"There is no salesforce job running for product {productname}")
    else:
        current_app.logger.info(f"Deleting salesforce job for product {productname}")
        scheduler_sf.delete_job(id=f"get_salesforce_cases_{productname}")

def get_salesforce_cases(productname):
    from cat import scheduler_sf
    app = scheduler_sf.app
    with app.app_context():
        current_app.logger.info(f"Running get salesforce cases job for product {productname}")
        product = Product.query.filter_by(productname=productname).first()
        sf_cases = Case.SFCases(instance_url=current_app.config['SF_INSTANCE_URL'])
        list_cases = sf_cases.get_product_cases(product_series=product.get_product_series_list(), 
                                                 platform=product.get_platform_list(), minutes=product.sf_job_query_interval)
        if list_cases:
            assign_salesforce_cases(list_cases)
        else:
            current_app.logger.info(f"No new cases for product {productname} in last {product.sf_job_query_interval} mins")

def get_sf_token():
    sf_client_id = current_app.config['SF_CLIENT_ID']
    sf_client_secret = current_app.config['SF_CLIENT_SECRET']
    sf_token_url = current_app.config['SF_TOKEN_URL']
    sf_username = current_app.config['SF_USERNAME']
    sf_password = current_app.config['SF_PASSWORD']
    sf_grant_type = current_app.config['SF_GRANT_TYPE']
    oauth_client1 = OAuth2Client(sf_client_id, sf_client_secret, sf_username, sf_password, sf_token_url, sf_grant_type)
    if oauth_client1.access_token:
        current_app.logger.debug("Token fetch was successful")
        return oauth_client1.access_token
    else:
        return None

def assign_salesforce_cases(cases, check_in_shift=True, handoffs=False):
    cat_d = []
    for case in cases:
        cated_to = None
        # if salesforce job already assigned the case, then ignore. Dont do this particular check if its a handoff
        if not handoffs and check_if_already_assigned(case.case_id):
            current_app.logger.info(f"Case {case.case_id}({case.product_series}) was already assigned by salesforce job. \
Ignoring and moving to next case in the list")
            continue
        failed_reason = ""
        product_object = Product.find_product_series(case.product_series, case.mist_product)
        if product_object is None:
            msg = f"Case {case.case_id} belongs to a product thats not added in CAT : {case.product_series}"
            current_app.logger.info(msg)
            failed_reason = msg
        # if case status is dispatch, ignore
        elif case.status == "Dispatch":
            msg = f"Case {case.case_id}({product_object.productname}) status is Dispatch. \
Ignoring and moving to next case in the list"
            current_app.logger.info(msg)
            failed_reason = msg
        # if priority is P1, then ignore
        elif case.priority.split()[0] == "P1":
            msg = f"Case {case.case_id}({product_object.productname}) is a P1. \
Ignoring and moving to next case in the list"
            current_app.logger.info(msg)
            failed_reason = msg
        # if the case already got assigned to someone who is not part of the team defined in CAT, then ignore
        elif case.case_owner and case.case_owner not in product_object.get_users_fullname():
            msg = f"Case {case.case_id}({product_object.productname}) got assigned to user {case.case_owner} which does not support the product in CAT. \
Ignoring and moving to next case in the list"
            current_app.logger.info(msg)
            failed_reason = msg
        else:
            case_id = case.case_id
            subject = case.subject
            priority = case.priority.split()[0]
            account_name = case.account_name
            productname = product_object.productname
            current_sf_owner_object = User.query.filter_by(full_name=case.case_owner).first()
            if product_object.sf_init_email_name:
                sf_email_name = product_object.sf_init_email_name
            else:
                sf_email_name = f"_{current_sf_owner_object.username}"
            # set mode to auto-reassign to take care of both new case assignment and handoff scenarios
            case_d = {
                "case_id": case_id,
                "priority": priority,
                "product": productname,
                "sf_account_name": account_name,
                "sf_email_name": sf_email_name,
                "subject": subject, 
                "check_in_shift": check_in_shift,
                "comments": "queue",
                "current_sf_owner_email": current_sf_owner_object.email,
                "mode": "auto-reassign"
            }
            if handoffs:
                case_d['sf_email_name'] = None
                case_d['comments'] = "handoffs"
            from cat.utils.cases import utils as cases_utils
            response, response_code = cases_utils.assign_case(case_d)
            if response_code == 200:
                current_app.logger.info(f"Case {case_id}({productname}) assigned to {response.get('assigned_to')}")
                cated_to = response.get('assigned_to')
            else:
                msg = f"Case {case_id}({productname}) not assigned. Reason : {response}"
                current_app.logger.info(msg)
                failed_reason = msg
        # circular import issue. Need to get back to this later.
        if failed_reason:
            from cat.email import email
            email.send_case_assigned_failed_email(case, failed_reason)
        cat_details = {
            "case_id": case.case_id,
            "cated_to": cated_to,
            "account_name": case.account_name,
            "status": case.status,
            "priority": case.priority.split()[0],
            "case_owner": case.case_owner,
            "product_series": case.product_series,
            "subject": case.subject,
            "failed_reason": failed_reason,
            "handoffs": handoffs,
            "product": product_object.productname
        }
        cat_d.append(cat_details)
        # add the case details to salesforcecases table
        salesforcecase = SalesforceCases.add_case(cat_details)
        if salesforcecase and product_object is not None:
            add_all([salesforcecase])
            current_app.logger.debug(f'Case {case.case_id}({case.product_series}) added to salesforcecase table')
        else:
            current_app.logger.debug(f'Case {case.case_id}:({case.product_series}) already added to salesforcecase table.')
    return cat_d

def check_if_already_assigned(case_id):
    return Cases.case_exists(case_id)

# fetches list of open cases for list of users
# checks each case for updates from external emails in past 1 hour
# notifies teams via teams messages / emails 
# case is an object of class Case defined in salesforce/Case.py
def check_sf_cases_for_external_updates():
    from cat import scheduler_sf
    app = scheduler_sf.app
    with app.app_context():
        users_list_objects = User.query.filter_by(monitor_case_updates=True).all()
        users_list = []
        for user in users_list_objects:
            users_list.append(user.full_name)
        sf_cases = Case.SFCases(instance_url=current_app.config['SF_INSTANCE_URL'])
        list_cases = sf_cases.get_open_cases_of_users(users_list=users_list)
        if list_cases:
            for case in list_cases:
                case_owner_object = User.query.filter_by(full_name=case.case_owner).first()
                current_app.logger.debug(f'Evaluating case {case.case_id} : {case.case_owner} for external case update notifications')
                if sf_external_update_conditions(case):
                    from cat.email import email
                    email.send_external_case_update_email(case_owner_object.username, case)
        else:
            current_app.logger.debug(f'Got an empty list of cases when checking for external case updates.')

def sf_external_update_conditions(case, check_weekdays=False, check_external_only_updates=True, within_working_hours=True):
    # if last external update email is none, return false
    if not case.last_external_update_email:
        return False
    case_owner_object = User.query.filter_by(full_name=case.case_owner).first()
    # check if its an external email address or internal
    if check_email_domain_match(case, case_owner_object, check_external_only_updates):
        return False
    # Get the time string from Case object and convert to a datetime timezone unaware object which is in UTC 
    datetime_last_external_update_utc_time = datetime.strptime(case.last_external_update_utc_time, "%b %d %Y %H:%M:%S")
    # convert to users timezone: datetime timezone(tz) aware object
    dt_users_tz_last_external_update = case_owner_object.user_datetime_object(datetime_last_external_update_utc_time)
    # Find if the email update was within users working hours and if user status is active. By default, monitoring happens
    # if user status is inactive and the last update is within users shift hours
    if compare_email_update_time_with_shift(case, case_owner_object, dt_users_tz_last_external_update, within_working_hours):
        return False
    # if its a weekday, ignore unless check_weekdays is True. Only execute below condition if user status is active. Skip
    # below condition if user is inactive.
    if case_owner_object.active:
        if dt_users_tz_last_external_update.weekday() in [0,1,2,3,4] or check_weekdays:
            current_app.logger.debug(f'Case {case.case_id}, owner {case.case_owner} : Last external update was on a weekday and user status is active. \
Not sending external case update notifcations')
            return False
    # Ignore if the last update is older than the configured sf check interval
    if check_how_old_external_update_is(case, dt_users_tz_last_external_update):
        return False
    current_app.logger.info(f"Sending notification for case {case.case_id}, owner {case.case_owner}")
    return True

def check_how_old_external_update_is(case, dt_users_tz_last_external_update):
    # Calculate the time difference between last external case update and current time.
    external_case_update_check_interval = current_app.config['EXTERNAL_CASE_UPDATE_CHECK_INTERVAL']
    delta = datetime.utcnow().astimezone() - dt_users_tz_last_external_update
    # if the last case update is older than the configured SF check interval, ignore. Added a 5mins offset to SF check interval 
    # for the time it can take to process all the case updates.
    if (delta.total_seconds() / 60) > (external_case_update_check_interval + 5):
        current_app.logger.debug(f'Case {case.case_id}, owner {case.case_owner} : Last case update older than \
                                 {external_case_update_check_interval} mins. Not sending external case update notifcations')
        return True
    else:
        return False

def compare_email_update_time_with_shift(case, case_owner_object, dt_users_tz_last_external_update, within_working_hours):
    shift_start = case_owner_object.shift_start_datetime()
    shift_end = case_owner_object.shift_end_datetime()
    # if the external update time was outside users working hours and user status is inactive, ignore the update unless within_working_hours is False
    if (shift_start > dt_users_tz_last_external_update and dt_users_tz_last_external_update > shift_end) and within_working_hours:
        current_app.logger.debug(f'Case {case.case_id}, owner {case.case_owner} : User is active or external update is within shift hours. \
                                Not sending external case update notifcations')
        return True
    else:
        return False
    
def check_email_domain_match(case, case_owner_object, check_external_only_updates):
    last_external_update_email_domain = case.last_external_update_email.split('@')[1]
    case_owner_email_domain = case_owner_object.email.split('@')[1]
    # if its an internal update, ingore unless check_external_only_updates is False
    if case_owner_email_domain == last_external_update_email_domain and check_external_only_updates:
        current_app.logger.debug(f'Case {case.case_id}, owner {case.case_owner} : Email domains match. \
                                 Not sending external case update notifcations')
        return True
    else:
        return False
    
def generate_random_string(length):
    letters = string.ascii_letters
    random_string = ''.join(random.choice(letters) for i in range(length))
    return random_string

def assign_case(product_name, check_in_shift=True, exclude_users_list=[], delayed_assignment=None):
    '''
    product_name : string, the product whose case needs to be cat'ed
    check_in_shift : boolean, consider users shift hours when cat'ing the case or not
    exclude_users_list : list, list of user names that needs to be excluded from cat'in the case
    delayed_assignment : time of the day to consider when filtering users by their shift timings eg 16:00:00 will
    check of users that are in shift at 4pm <user that cats the case timezone>
    '''
    fu = find_user(product_name, check_in_shift=check_in_shift, exclude_users_list=exclude_users_list, delayed_assignment=delayed_assignment)
    fu.filter_by_day()
    if len(fu.users) <= 1:
        n = fu.users
    else:
        # monthly check
        fu.max_days = fu.product.max_days_month
        fu.filter_by_day(diff=30)
        if len(fu.users) <= 1:
            n = fu.users
        else:
            # final tie breaker, use username to find the next eng
            n = fu.filter_by_name()
    return None if len(n) == 0 else n[0]

def check_user_product(d):
    if not d.get('username'):
        return f"Please provide a username", 400
    if not d.get('productname'):
        return f"Please provide a productname", 400
    user = User.query.filter_by(username=d.get('username')).first()
    product = Product.query.filter_by(productname=d.get('productname')).first()
    if user == None:
        return f"User {d.get('username')}  doesnt exists", 404
    if product == None:
        return f"Product {d.get('productname')} doesnt exists", 404
    return 0, 200

def get_user_names(users):
    l = []
    for user in users:
        l.append(user.username)
    return l

def cases_assigned_by_user(username, page):
    return Cases.get_cases_assigned_by_user(username, page=page)

def cases_of_user(username, page):
    return Cases.get_cases_of_user(username, page=page)

def cases_of_product(product, page):
    return Cases.get_cases_of_product(product.productname, page=page)

def cases_of_team(teamname=None, page=1, per_page=10, mode=None, priority=None):
    '''
    Finds the list of all users that are part of the team. It then searches cases database to list all cases owned by users.
    page is variable used for pagination
    '''
    return Cases.get_cases_of_team(t_name=teamname, page=page, per_page=per_page, mode=mode, priority=priority)

def check_case_id_format(case_id, product):
    return re.match(product.case_regex, case_id)

def add_all(l):
    db.session.add_all(l)
    db.session.commit()
    return l

def delete_all(l):
    for i in l:
        db.session.delete(i)
    db.session.commit()
    return l

def get_hash(str):
    return bcrypt.generate_password_hash(str).decode('utf-8')

def check_hash(str_hash, str):
    return bcrypt.check_password_hash(str_hash, str)

def reactivate_user(username, active, job_number):
    '''
    Changes user status to boolean "active" irrespective of their current status
    '''
    print(f"Activate User {username} called")
    d = {
        'active': active
    }
    response, res_code = users_utils.edit_user(username, d, "scheduler")
    if res_code == 200:
        # had to import the app context or else it was failing with error working outside app context. Can be revisited later to understand
        # this flow later
        from cat import scheduler
        app = scheduler.app
        with app.app_context():
            j = Jobs.query.filter_by(number=job_number).first()
            j.status = "Success"
            add_all([j])
            msg = f"User {username} reactivation job submitted"
            return msg
    else:
        msg = response
        return msg, 400

def schedule_sf_integration(productname, sf_enabled, job_number):
    '''
    Changes product salesforce polling status to boolean "sf_enabled" irrespective of their current status
    '''
    # had to import the app context or else it was failing with error working outside app context. Can be revisited later to understand
    # this flow later
    from cat import scheduler
    app = scheduler.app
    with app.app_context():
        # Running into circular imports issue with below import. Need to tackle it later
        from cat.utils.products import utils as products_utils
        current_app.logger.info(f"Schedule SF integration for Product {productname} called")
        d = {
            'sf_enabled': sf_enabled
        }
        response, res_code = products_utils.edit_product(productname, d, "scheduler")
        print(response)
        if res_code == 200:
                j = Jobs.query.filter_by(number=job_number).first()
                j.status = "Success"
                add_all([j])
                msg = f"Product {productname} SF Integration job submitted"
                return msg
        else:
            msg = response
            return msg, 400
    
def schedule_shift_change(username, shift_start, shift_end, job_number):
    '''
    Changes user shift timings to shift_start and shift_end
    '''
    d = {
        'shift_start': shift_start,
        'shift_end': shift_end
    }
    response, res_code = users_utils.edit_user(username, d, "scheduler")
    if res_code == 200:
        # had to import the app context or else it was failing with error working outside app context. Can be revisited later to understand
        # this flow later
        from cat import scheduler
        app = scheduler.app
        with app.app_context():
            current_app.logger.info(f"Schedule shift change for User {username} called")
            j = Jobs.query.filter_by(number=job_number).first()
            j.status = "Success"
            add_all([j])
            msg = f"User {username} shift change job submitted"
            return msg
    else:
        msg = response
        return msg, 400

def schedule_handoffs(username, check_in_shift, job_number):
    '''
    fetches list of open cases of user username from Salesforce
    cat's cases in users bin
    '''
    from cat import scheduler
    app = scheduler.app
    with app.app_context():
        user_object = User.query.filter_by(username=username).first()
        sf_cases = Case.SFCases(instance_url=current_app.config['SF_INSTANCE_URL'])
        list_cases = sf_cases.get_open_cases_of_users(users_list=[user_object.full_name])
        current_app.logger.info(f"Schedule handoffs for User {username} called")
        d_product_cases = {}
        for case in list_cases:
            product_series = case.product_series
            current_app.logger.info(f"Adding case {case.case_id}({product_series}) to list of handoff cases for user {username}")
            if product_series in d_product_cases:
                d_product_cases[product_series].append(case)
            else:
                d_product_cases[product_series] = [case]
        list_of_cated_cases = []
        for product_series, cases in d_product_cases.items():
            current_app.logger.info(f"Handing off {len(cases)} cases of product({product_series}) belonging to user {username}")
            l_cated_cases = assign_salesforce_cases(cases, check_in_shift=check_in_shift, handoffs=True)
            list_of_cated_cases = list_of_cated_cases + l_cated_cases
        from cat.email import email
        email.send_case_handoffs_summary_email(username, list_of_cated_cases)
        j = Jobs.query.filter_by(number=job_number).first()
        j.status = "Success"
        add_all([j])
        msg = f"User {username} handoffs job submitted"
        return msg
    
def convert_to_local_dt(dt, timezone):
    '''
    accepts a timezone unaware datetime object and pytz formatted timezone string 'timezone' 
    returns a timezone aware datetime object in local systems timezone
    '''
    tz_aware_dt = pytz.timezone(timezone).localize(dt)
    local_tz = datetime.now().astimezone().tzinfo
    local_tz_convereted_dt= tz_aware_dt.astimezone(local_tz)
    return local_tz_convereted_dt

# bootstrap
def create_system_users():
    from cat.utils.users import utils as users_utils
    from cat.utils.teams import utils as teams_utils
    adm = User.query.filter_by(username="admin").first()
    scheduler = User.query.filter_by(username="scheduler").first()
    team = Team.query.filter_by(teamname="global").first()
    if not team:
        d_team = {
            "teamname": "global"
        }
        teams_utils.add_team(d_team)
        current_app.logger.info("Team global doesnt exist. Created team global")
    else:
        current_app.logger.info("Team global already exist.")
    if not adm:
        d_user = {
            "username": "admin",
            "password": current_app.config["ADMIN_PASSWORD"],
            "teamname": "global",
            "admin": True,
            "email": current_app.config["ADMIN_EMAIL"]
        }
        users_utils.add_user(d_user)
        current_app.logger.info("User admin doesnt exist. Created system user admin")
    else:
        current_app.logger.info("User admin already exist.")
    if not scheduler:
        d_user = {
            "username": "scheduler",
            "password": current_app.config["ADMIN_PASSWORD"],
            "teamname": "global",
            "admin": True,
            "email": current_app.config["ADMIN_EMAIL"]
        }
        users_utils.add_user(d_user)
        current_app.logger.info("User scheduler doesnt exist. Created system user scheduler")
    else:
        current_app.logger.info("User scheduler already exist.")

# bootstrap, looks up db and reinitiates jobs that must have got killed due to app restart/stop
def check_scheduled_jobs():
    jobs = Jobs.active_jobs()
    # import pdb;pdb.set_trace()
    for job in jobs:
        if job.job_type in ["reactivate_user", "shift_change", "sf_integration", "handoffs"]:
            d = json.loads(job.details)
            dt = datetime.strptime(d.get("datetime"), '%Y-%m-%d %H:%M:%S')
            # Update the dict object "d" to convert key "datetime" back into a datetime object
            d['datetime'] = dt
            dt_zone = d.get("timezone")
            datetime_str = convert_to_local_dt(dt, dt_zone)
            if datetime_str < datetime.now().astimezone():
                job.status = "Failed"
                print(f"Job {job.id} status changed to Failed")
            elif not scheduler.get_job(id=job.id) or not scheduler_sf.get_job(id=job.id):
                print(f"Reschedule job {job.id}")
                job.status = "Cancelled"
                d['rescheduled_job_number'] = job.number
                if job.job_type == "sf_integration":
                    # Running into circular imports issue with below import. Need to tackle it later
                    from cat.utils.products import utils as products_utils
                    products_utils.schedule_sf_integration(d, True)
                elif job.job_type == "reactivate_user":
                    users_utils.reactivate_user(d, True)
                elif job.job_type == "shift_change":
                    users_utils.schedule_shift_change(d, True)
                elif job.job_type == "handoffs":
                    users_utils.schedule_handoffs(d, True)
            else:
                job.status = "Cancelled"
            add_all([job])

def get_scheduled_jobs(scheduler=scheduler, object=False):
    '''
    Returns the list of scheduled jobs dict objects if parameter object is set to true else returns list of job names
    '''
    if not scheduler:
        return []
    l = []
    jobs = scheduler.get_jobs()
    if object:
        return jobs
    for job in jobs:
        l.append(job.name)
    return l

class find_user:
    def __init__(self, productname, check_in_shift=True, exclude_users_list=[], delayed_assignment=None):
        self.users = []
        self.delayed_assignment = delayed_assignment
        self.product = Product.query.filter_by(productname=productname).first()
        self.check_in_shift = check_in_shift
        if self.product.strategy == "s2":  # Balance per product
            self.by_product = self.product.productname
        else: # Balance across products
            self.by_product = None
        self.max_days = self.product.max_days
        self.exclude_users_list = exclude_users_list
        self.find_initial_list_of_users_for_product()
        
    def filter_by_day(self, diff=1, days=0):
        new_list = []
        min = sys.maxsize
        for user in self.users:
            quota = UserProduct.query.filter_by(user_name=user.username, product_name=self.product.productname).first().quota
            current_app.logger.debug(f"User: {user.username}, quota_into_cases:{user.number_of_cases(days, self.by_product) * int(quota)}")
            if user.number_of_cases(days, self.by_product) * int(quota) == min:
                new_list.append(user)
            elif user.number_of_cases(days, self.by_product) * int(quota) < min:
                new_list = [user]
                min = user.number_of_cases(days, self.by_product) * int(quota) 
        self.users = new_list
        current_app.logger.debug(f"{self.users}, {self.max_days} , {days}, {self.product.strategy}")
        if len(self.users) <= 1 or self.max_days <= days:
            return self.users
        else:
            return self.filter_by_day(diff, days+diff)

    def filter_by_name(self):
        d = {}
        for user in self.users:
            d[user] = user.username
        sorted_d = dict(sorted(d.items(), key=lambda x: x[1]))
        for k,v in sorted_d.items():
            return [k] 
        
    def find_initial_list_of_users_for_product(self):
        # Find users supporting the product
        self.filter_by_product()
        current_app.logger.debug(f"filter by product list: {self.users}")
        # Find users currently in shift
        if self.check_in_shift:
            self.filter_by_shift()
            current_app.logger.debug(f"filter by in_shift list: {self.users}")
        # Filter out users that are inactive for this product
        self.filter_by_active()
        current_app.logger.debug(f"filter by active list: {self.users}")
        # Filter out users based on Quota
        # self.filter_by_quota()
        # current_app.logger.debug(f"filter by quota list: {self.users}")
        # Filter out users that are in exclude_users_list
        self.filter_by_exclude_users_list()
        current_app.logger.debug(f"filter by exclude_users_list {self.exclude_users_list} list: {self.users}")
        return self.users

    # Filter out users that are in self.exclude_users_list list
    def filter_by_exclude_users_list(self):
        r_list = []
        for user in self.users:
            if user.username not in self.exclude_users_list:
                r_list.append(user)
        self.users = r_list
        return self.users

    # Filter out users based on Quota
    def filter_by_quota(self):
        r_list = []
        d_quota = {}
        d_cases = {}
        productname = self.product.productname
        for user in self.users:
            d_quota[user.username] = UserProduct.query.filter_by(user_name=user.username, product_name=productname).first().quota
            d_cases[user.username] = user.number_of_cases(self.product.quota_over_days, productname)
        for user in self.users:
            temp1 = 1
            temp2 = 0
            for compare_user in self.users:
                if compare_user.username == user.username:
                    continue
                if d_quota[user.username] > d_quota[compare_user.username]:
                    temp1 = 0
                    if d_quota[user.username] <= d_cases[compare_user.username]:
                        pass
                    else:
                        temp2+=1
            if temp1 or temp2 == 0:
                r_list.append(user)
        self.users = r_list
        return self.users

    # Filter out users that are inactive for this product or are set to inactive status
    def filter_by_active(self):
        active_users = []
        productname = self.product.productname
        for user in self.users:
            if user.active:
                active_users.append(user)
        self.users = active_users
        # check user product active/inactive status
        up_active_users = []
        for user in self.users:
            if UserProduct.query.filter_by(user_name=user.username, product_name=productname).first().active:
                up_active_users.append(user)
        self.users = up_active_users
        return self.users

    # Find users supporting the product
    def filter_by_product(self):
        self.users = self.product.supported_by
        return self.users

    # Find users currently in shift
    def filter_by_shift(self):
        in_shift = []
        for user in self.users:
            if user.in_shift(self.delayed_assignment):
                in_shift.append(user)
        self.users = in_shift
        return self.users