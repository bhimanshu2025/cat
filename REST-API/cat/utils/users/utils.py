from cat import api_utils as utils
from cat.models import User, Team, Audit, Jobs, MuleUser, SalesforceEmails
from flask_login import current_user
from flask import current_app
from cat import scheduler
from datetime import datetime
import json
from cat.email import email

def users():
    l = []
    users = User.query.all()
    for user in users:
        l.append(user.schema())
    return l, 200

def get_job(id):
    if not id:
        return f"No job id provided", 401
    job_obj = Jobs.query.filter_by(id=id).first()
    if job_obj:
        return job_obj.schema(), 200
    else:
        return f"Job {id} not found", 404

def jobs(page, teamname=None):
    if teamname:
        team = Team.query.filter_by(teamname=teamname).first()
        if team:
            l_usernames = team.get_user_names()
            # append jobs from admin user as admin user reschedules jobs after app restart
            l_usernames.append('admin')
            return Jobs.query.filter(Jobs.username.in_(l_usernames)).order_by(Jobs.time.desc()).paginate(per_page=10, page=page)
        else:
            return []
    else:
        return Jobs.query.order_by(Jobs.time.desc()).paginate(per_page=10, page=page)

def active_jobs():
    l = []
    jobs = Jobs.active_jobs()
    for job in jobs:
        l.append(job.schema())
    return l, 200

def login(d):
    if d.get('username') == None:
        return f"Please provide a username", 400
    if d.get('password') == None:
        return f"Please provide a password", 400
    if d.get("muleuser"):
        r = MuleUser.validate_user_password(d.get('username'), d.get('password'))
    else:
        r = User.validate_user_password(d.get('username'), d.get('password'))
    if r:
        user = User.query.filter_by(username=d.get('username')).first()
        utils.add_all([user])
        current_app.logger.info(f"User {d.get('username')} successfully logged in.")
        return r.schema(), 200
    else:
        current_app.logger.info(f"User {d.get('username')} login failed.")
        return "Login Failed", 401

# no API for this
def login_ui(d):
    if d.get('username') == None:
        return f"Please provide a username", 400
    if d.get('password') == None:
        return f"Please provide a password", 400
    if d.get("muleuser"):
        r = MuleUser.validate_user_password(d.get('username'), d.get('password'))
    else:
        r = User.validate_user_password(d.get('username'), d.get('password'))
    if r:
        user = User.query.filter_by(username=d.get('username')).first()
        utils.add_all([user])
        current_app.logger.info(f"User {d.get('username')} successfully logged in.")
        return r, 200
    else:
        current_app.logger.info(f"User {d.get('username')} login failed.")
        return "Login Failed", 401
    
def user(username):
    user = User.query.filter_by(username=username).first()
    if user == None:
        return f"User {username} not found", 404
    else:
        return user.schema(), 200

def del_user(username):
    if not utils.check_user_access(username):
        return "Unauthorized Access", 401
    user = User.query.filter_by(username=username).first()
    if user == None:
        return f"User {username} not found", 404
    else:
        u_schema = user.schema()
        a = Audit(user=current_user.username, task_type="DELETE USER", task=str(user.schema()))
        utils.delete_all([user])
        utils.add_all([a])
        current_app.logger.info(f"USER DELETED : {u_schema}")
        email.send_delete_user_email(u_schema)
        return u_schema, 200
    
def edit_user(username, user_d, cur_user=None):
    '''
    username is users username that needs to be edited
    cur_user is the user name who is making the change.
    user_d is a dict object containing the key value mappings to update user properties
    '''
    from cat import scheduler
    app = scheduler.app
    with app.app_context():
        if not cur_user:
            cur_user = current_user.username
            if user_d.get('password'):
                return f"Password cant be updated through this method. Use a different method", 400
        user = User.query.filter_by(username=username).first()
        if user == None:
            return f"User {username} not found", 404
        else:
            if cur_user != "scheduler":
                if not utils.check_user_access(username):
                    return "Unauthorized Access", 401
            a = Audit(user=cur_user, task_type="UPDATE USER", task=str([user_d, user.schema()]))
            user.update(user_d)
            utils.add_all([user, a])
            utils.add_all([user])
            current_app.logger.info(f"USER UPDATED : Old values : {user_d}, New values : {user.schema()}")
            email.send_edit_user_email(username, cur_user)
            return user.schema(), 200   

def change_password(username, user_d):
    '''
    username is users username whose password needs to be changed
    user_d is a dict object containing the key value mappings to update user properties. it contains mandatory keys current_password and new_password keys
    '''
    if not user_d.get('new_password') or not user_d.get('current_password'):
        return f"Please provide new password and current password", 400
    user = User.query.filter_by(username=username).first()
    if user == None:
        return f"User {username} not found", 404
    if not current_user.validate_user_password(current_user.username, user_d.get('current_password')):
        return f"Invalid Password", 400
    else:
        password_d = {
            "password": user_d.get('new_password')
        }
        a = Audit(user=current_user.username, task_type="CHANGE PASSWORD")
        user.update(password_d)
        utils.add_all([user, a])
        utils.add_all([user])
        email.send_password_change_email(username)
        current_app.logger.info(f"User {username} password changed.")
        return user.schema(), 200   

def reset_password(user_email):
    '''
    email is users email whose password needs to be reset
    '''
    user = User.query.filter_by(email=user_email).first()
    if user == None:
        current_app.logger.info(f"Password reset requested. User not found with email {user_email}")
        return f"User with email {user_email} not found", 404
    else:
        random_string = utils.generate_random_string(15)
        password_d = {
            "password": random_string
        }
        a = Audit(user=user.username, task_type="RESET PASSWORD")
        email.send_password_reset_email(user_email, random_string)
        user.update(password_d)
        utils.add_all([user, a])
        utils.add_all([user])
        current_app.logger.info(f"User {user_email} password reset.")
        return user.schema(), 200   
       
def add_user(d):
    if d.get('username') == None:
        return f"Please provide a username", 400
    if d.get('teamname') == None:
        return f"Please provide a teamname", 400
    if d.get('password') == None:
        return f"Please provide a password", 400
    team = Team.query.filter_by(teamname=d.get('teamname')).first()
    if team == None:
        return f"Team {d.get('teamname')} not found", 404
    user = User.query.filter_by(username=d.get('username')).first()
    if user != None:
        return f"User {d.get('username')} already exists", 400
    u = User.add_user(d)
    utils.add_all([u])
    if current_user and not current_user.is_anonymous:
        a = Audit(user=current_user.username, task_type="ADD USER", task=str(u.schema()))
        utils.add_all([a])
    if current_user and current_user.is_anonymous:
        a = Audit(user=u.username, task_type="ADD USER", task=str(u.schema()))
        utils.add_all([a])
    current_app.logger.info(f"USER ADDED : {u.schema()}")
    email.send_add_user_email(d.get('username'), d.get('password'))
    return u.schema(), 200       

def reactivate_user(d, reschedule=False):
    '''
    username is the username that needs to be scheduled for reactivation
    d = {
        "username": <username>,
        "datetime": <datetime>,
        "timezone": <tz>,
        "active": True
    }
    username is users name whose status needs to be chaged
    datetime is a tz unaware datetime object
    timezone is a tz object from datetime class in string format eg : "US/Pacific"
    active is user status to set at scheduled time
    '''
    username = d.get("username")
    dt = d.get("datetime")
    dt_zone = d.get("timezone")
    active = d.get("active")
    datetime_str = utils.convert_to_local_dt(dt, dt_zone)
    if reschedule:
        job_status = "Rescheduled"
    else:
        job_status =  "Scheduled"
    if current_user and not current_user.is_anonymous:
        logged_user = current_user.username
    else:
        logged_user = "admin"
    if datetime_str < datetime.now().astimezone():
        return "Datetime has to be a time in future", 400
    year, month, day, hour, minute = datetime_str.year, datetime_str.month, datetime_str.day, \
                                datetime_str.hour, datetime_str.minute
    if active: 
        job_id = f"activate_user_{username}"
    else:
        job_id = f"deactivate_user_{username}"
    job = scheduler.get_job(id=job_id)
    if job is not None:
        return f"There is already a job of this type scheduled for user {username}", 400
    schema = {
        "username": username,
        "time": str(dt) + " " + str(dt_zone),
        "active": active
    }
    a = Audit(user=logged_user, task_type="SCHEDULE USER STATUS CHANGE", task=str(schema))
    j_object = Jobs(id=job_id, username=logged_user, job_type="reactivate_user", details=json.dumps(d, default=str), status=job_status)
    utils.add_all([a, j_object])
    r = scheduler.add_job(id=job_id, func=utils.reactivate_user, args=[username, active, j_object.number],
                        trigger='cron', year=year, month=month, day=day, hour=hour, minute=minute)
    current_app.logger.info(f"Schedule user status change job submitted successfully for user {username}, job_status is {job_status} \
                            job_id is {job_id}")
    email.send_job_scheduled_email(logged_user, j_object)
    return job_id, 200

def schedule_shift_change(d, reschedule=False):
    '''
    username is the username whose shift change needs to be  scheduled
    d = {
        "username": <username>,
        "datetime": <datetime>,
        "timezone": <tz>,
        "shift_start": shift_start,
        "shift_end": shift_end
    }
    username is users name whose status needs to be chaged
    datetime is a tz unaware datetime object
    timezone is a tz object from datetime class in string format eg : "US/Pacific". this is for the datetime object
    shift_start is time when shift starts eg 10:00:00 for 10am
    shift_end is time when shift ends eg 18:00:00 for 6pm
    '''
    username = d.get("username")
    dt = d.get("datetime")
    dt_zone = d.get("timezone")
    shift_start = d.get("shift_start")
    shift_end = d.get("shift_end")
    if reschedule:
        job_status = "Rescheduled"
    else:
        job_status =  "Scheduled"
    if current_user and not current_user.is_anonymous:
        logged_user = current_user.username
    else:
        logged_user = "admin"
    datetime_str = utils.convert_to_local_dt(dt, dt_zone)
    if datetime_str < datetime.now().astimezone():
        return "Datetime has to be a time in future", 400
    year, month, day, hour, minute = datetime_str.year, datetime_str.month, datetime_str.day, \
                                datetime_str.hour, datetime_str.minute
    schema = {
        "username": username,
        "time": str(dt) + " " + str(dt_zone),
        "shift_start": shift_start,
        "shift_end": shift_end
    }
    job_id = f"shiftchange_{datetime.utcnow()}_{username}"
    a = Audit(user=logged_user, task_type="SCHEDULE SHIFT CHANGE", task=str(schema))
    j_object = Jobs(id=job_id, username=logged_user, job_type="shift_change", details=json.dumps(d, default=str), status=job_status)
    utils.add_all([a, j_object])
    r = scheduler.add_job(id=job_id, func=utils.schedule_shift_change, args=[username, shift_start, shift_end, j_object.number],
                        trigger='cron', year=year, month=month, day=day, hour=hour, minute=minute)
    current_app.logger.info(f"Schedule user shift change job submitted successfully for user {username}, job_status is {job_status} \
                            job_id is {job_id}")
    email.send_job_scheduled_email(logged_user, j_object)
    return job_id, 200

def schedule_handoffs(d, reschedule=False):
    '''
    username is the users name whose case handoffs needs to be scheduled
    d = {
        "username": <username>,
        "datetime": <datetime>,
        "timezone": <tz>,
        "check_in_shift: False
    }
    username is users name whose status needs to be chaged
    datetime is a tz unaware datetime object
    timezone is a tz object from datetime class in string format eg : "US/Pacific". this is for the datetime object
    check_in_shift whether to consider users shift hours when cat'ing the cases, default is False
    '''
    username = d.get("username")
    dt = d.get("datetime")
    dt_zone = d.get("timezone")
    check_in_shift = d.get("check_in_shift") or False
    if reschedule:
        job_status = "Rescheduled"
    else:
        job_status =  "Scheduled"
    if current_user and not current_user.is_anonymous:
        logged_user = current_user.username
    else:
        logged_user = "admin"
    datetime_str = utils.convert_to_local_dt(dt, dt_zone)
    if datetime_str < datetime.now().astimezone():
        return "Datetime has to be a time in future", 400
    year, month, day, hour, minute = datetime_str.year, datetime_str.month, datetime_str.day, \
                                datetime_str.hour, datetime_str.minute
    schema = {
        "username": username,
        "time": str(dt) + " " + str(dt_zone),
        "check_in_shift": check_in_shift
    }
    job_id = f"handoffs_{datetime.utcnow()}_{username}"
    a = Audit(user=logged_user, task_type="SCHEDULE HANDOFFS", task=str(schema))
    j_object = Jobs(id=job_id, username=logged_user, job_type="handoffs", details=json.dumps(d, default=str), status=job_status)
    utils.add_all([a, j_object])
    r = scheduler.add_job(id=job_id, func=utils.schedule_handoffs, args=[username, check_in_shift, j_object.number],
                        trigger='cron', year=year, month=month, day=day, hour=hour, minute=minute)
    current_app.logger.info(f"Schedule handoff cases job submitted successfully for user {username}, job_status is {job_status} \
                            job_id is {job_id}")
    email.send_job_scheduled_email(logged_user, j_object)
    return job_id, 200

def del_job(jobid):
    '''
    deletes job with id jobid from scheduler
    '''
    job = scheduler.get_job(id=jobid)
    if job:
        scheduler.delete_job(id=jobid)
        j_object = Jobs.search_active_job(jobid)
        if j_object:
            j_object.status = "Deleted"
            j_object.username = current_user.username
            utils.add_all([j_object])
        d = {
            "jobid": jobid,
            "datetime": job.next_run_time
        }
        a = Audit(user=current_user.username, task_type="DELETE SCHEDULED JOB", task=str(d))
        utils.add_all([a])
        current_app.logger.info(f"Job successfully deleted. job_id : {jobid}")
        email.send_job_scheduled_email(current_user.username, j_object)
        return utils.get_scheduled_jobs(), 200
    else:
        current_app.logger.info(f"Delete job failed for job id {jobid}. Job id not found")
        return f"Job {jobid} not found", 404

def salesforce_emails():
    l_emails = []
    if current_user.username == "admin":
        emails = SalesforceEmails.query.all()
    else:
        emails = current_user.salesforce_emails
    for email in emails:
        l_emails.append(email.schema())
    return l_emails, 200

def salesforce_email(email_name):
    email = SalesforceEmails.query.filter_by(email_name=email_name).first()
    if email == None:
        return f"Email template {email_name} not found", 404
    else:
        return email.schema(), 200

def add_salesforce_email(d_sf_email):
    if d_sf_email.get('email_name') == None:
        return f"No name provided for the email template", 400
    if d_sf_email.get('email_body') == None:
        return f"No body provided for the email template", 400
    temp = SalesforceEmails.query.filter_by(email_name=d_sf_email.get('email_name')).first()
    if temp != None:
        return f"Email template with this name {d_sf_email.get('email_name')} already exists", 400
    sf_email = SalesforceEmails(user=current_user.username, email_name=d_sf_email.get('email_name'), 
                                email_body=d_sf_email.get('email_body'), email_subject=d_sf_email.get('email_subject'))
    utils.add_all([sf_email])
    a = Audit(user=current_user.username, task_type="ADD SF EMAIL TEMPLATE", task=str(sf_email.schema()))
    utils.add_all([a])
    current_app.logger.info(f"Email template {d_sf_email.get('email_name')} added successfully by {current_user.username}")
    return sf_email.schema(), 200    

def edit_salesforce_email(email_name, d_sf_email):
    if email_name not in current_user.sf_email_names():
        return f"Unauthorized Access", 401
    sf_email = SalesforceEmails.query.filter_by(email_name=email_name).first()
    if sf_email == None:
        return f"Email template {email_name} not found", 404
    sf_email_old_schema = sf_email.schema()
    sf_email.update(d_sf_email)
    utils.add_all([sf_email])
    a = Audit(user=current_user.username, task_type="UPDATE SF EMAIL TEMPLATE", task=str([d_sf_email, sf_email.schema()]))
    utils.add_all([a])
    current_app.logger.info(f"EMAIL TEMPLATE UPDATED : Old values : {sf_email_old_schema}, New values : {sf_email.schema()}")
    return sf_email.schema(), 200    

def delete_salesforce_email(email_name):
    sf_email = SalesforceEmails.query.filter_by(email_name=email_name).first()
    if sf_email == None:
        return f"Email template {email_name} not found", 404
    if email_name not in current_user.sf_email_names():
        return f"Unauthorized Access", 401
    sf_email_schema = sf_email.schema()
    a = Audit(user=current_user.username, task_type="DELETE SF EMAIL TEMPLATE", task=str(sf_email_schema))
    utils.delete_all([sf_email])
    utils.add_all([a])
    current_app.logger.info(f"SF EMAIL TEMPLATE DELETED : {sf_email_schema}")
    return sf_email_schema, 200   
