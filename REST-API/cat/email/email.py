from flask_mail import Message
from cat import mail
import pymsteams, csv
from flask_login import current_user
from cat.models import Cases, User, Team, SalesforceEmails, Product
from flask import current_app
from cat.models import User
from cat import api_utils
from jinja2 import Template
from threading import Thread
import ast

# Asynchronously send email
def send_email_thread(msg):
    from cat import scheduler
    app = scheduler.app
    with app.app_context():
        mail.send(msg)

# Asynchronously send teams notif
def send_teams_notification_thread(teamsMessage):
    from cat import scheduler
    app = scheduler.app
    with app.app_context():
        teamsMessage.send()

def send_email(subject, sender, recipients, text_body, cc=None, attachment=None):
    msg = Message(subject, sender=sender, recipients=recipients, cc=cc)
    if attachment:
        with current_app.open_resource(attachment) as fp:  
            msg.attach(attachment, "text/csv", fp.read()) 
    msg.body = text_body
    email_thr = Thread(target=send_email_thread, args=[msg])
    email_thr.start()
    # mail.send(msg)

# Idea was shared by Nithyananda Velu
def send_teams_notification(MSwebhook, subject, msg):    
    teamsMessage = pymsteams.connectorcard(MSwebhook)
    teamsMessage.text(msg)
    teamsMessage.title(subject)
    teams_thr = Thread(target=send_teams_notification_thread, args=[teamsMessage])
    teams_thr.start()
    # teamsMessage.send()

def send_case_assign_email(d_case, reassign=False):
    try:
        case_id = d_case.get('case_id').strip()
        sf_email_name = d_case.get('sf_email_name')
        case_subject = d_case.get('subject')
        delayed_assignment = d_case.get('delayed_assignment')
        case_schema = Cases.query.filter_by(id=case_id).first().schema()
        assignment_history = case_schema.get('assignment_history')
        assigned_to = case_schema.get("assigned_to")
        caseid = case_schema.get("case_id")
        product = case_schema.get("product")
        priority = case_schema.get("priority")
        mode = case_schema.get("mode")
        comments = case_schema.get("comments")
        sf_account_name = case_schema.get("sf_account_name")
        case_owner = User.query.filter_by(username=assigned_to).first()
        time = case_owner.user_datetime(case_schema.get("time")) + " " + case_owner.timezone
        assigned_by = case_schema.get("assigned_by")
        user_schema = case_owner.schema()
        user_email = user_schema.get("email")
        team_schema = Team.query.filter_by(teamname=user_schema.get('teamname')).first().schema()
        team_email = team_schema.get("email")
        mswebhook = team_schema.get("mswebhook")
        assigned_to_full_name = User.query.filter_by(username=assigned_to).first().full_name
        assigned_by_full_name = User.query.filter_by(username=assigned_by).first().full_name
        assigned_by_email = User.query.filter_by(username=assigned_by).first().email
        if reassign:
            subject = f"{priority} : {mode} : {caseid} : {product} : Reassigned to {assigned_to_full_name}"
            # If reassign find the email of previous user that the case was cat'ed to. cc this user regarding case reassignment.
            assignment_history_list = ast.literal_eval(assignment_history)
            if len(assignment_history_list) >= 2:
                previous_owner_object = User.query.filter_by(username=assignment_history_list[-2]).first()
                if previous_owner_object:
                    previous_owners_email = previous_owner_object.email
        else:
            subject = f"{priority} : {mode} : {caseid} : {product} : Assigned to {assigned_to_full_name}"
            previous_owners_email = None
        # Salesforce IR email
        sf_email_sent = "No"
        if sf_email_name:
            email_object = SalesforceEmails.query.filter_by(email_name=sf_email_name).first()
            if email_object:
                if current_user:
                    sf_sender = current_user.email
                else:
                    # scheduler
                    sf_sender = d_case.get('current_sf_owner_email')
                sf_recipients = [current_app.config['SF_EXTERNAL_EMAIL']]
                sf_subject = case_id + ' ' + email_object.email_subject
                sf_body = Template(email_object.email_body).render(assigned_to=assigned_to, assigned_to_full_name=assigned_to_full_name,
                                                                assigned_by_full_name=assigned_by_full_name, assigned_by=assigned_by,
                                                                assigned_to_email=user_email, assigned_by_email=assigned_by_email)
                current_app.logger.info(f"Sending Salesforce email for case {caseid}")
                send_email(sf_subject, sf_sender, sf_recipients, sf_body, cc=[sf_sender])
                sf_email_sent = "Yes"
            else:
                current_app.logger.info(f"Failed sending Salesforce email for case {caseid}. Reason: Email template {sf_email_name} not found for user.")
        text_body = f'''
        Case : {caseid}
        Product : {product}
        Priority : {priority}
        Mode : {mode}
        Assigned By: {assigned_by_full_name}
        Assigned To: {assigned_to_full_name}
        Comments : {comments}
        Time : {time}
        Account Name : {sf_account_name}
        Synopsis : {case_subject}
        Assignment History : {assignment_history}
        Delayed Assignment : {delayed_assignment}
        Sent Salesforce Initial Email : {sf_email_sent}
'''
        # Email user
        if user_schema.get('email'):
            recipients = [user_email]
            sender = current_app.config.get("MAIL_NO_REPLY_SENDER")
            team_users_email_list = api_utils.team_users_email_list(user_schema.get('teamname'))
            if team_email:
                team_users_email_list = [team_email] + team_users_email_list
            if assigned_by_email:
                team_users_email_list = [assigned_by_email] + team_users_email_list
            if previous_owners_email:
                team_users_email_list = [previous_owners_email] + team_users_email_list
            if recipients:
                send_email(subject, sender, recipients, text_body, cc=team_users_email_list)
        # Teams notification
        if mswebhook:
            send_teams_notification(mswebhook, subject, text_body)
    except Exception as err:
        print(f"Exception caught. {err}")
        current_app.logger.exception(err)

def send_case_unassign_email(case_d):
    try:
        product = case_d.get('product')
        case_id = case_d.get('case_id')
        comments = case_d.get('comments')
        priority = case_d.get('priority')
        assigned_to = case_d.get('assigned_to')
        user_schema = User.query.filter_by(username=case_d.get('assigned_to')).first().schema()
        user_email = user_schema.get("email")
        recipients = [user_email]
        team_schema = Team.query.filter_by(teamname=user_schema.get('teamname')).first().schema()
        team_email = team_schema.get("email")
        mswebhook = team_schema.get("mswebhook")
        subject = f"Case Unassiged {case_id} : {product}"
        sender = current_app.config.get("MAIL_NO_REPLY_SENDER")
        text_body = f'''
        Product: {product}
        Priority: {priority}
        Was Assigned To: {assigned_to}
        Unassigned By: {current_user.username}
        Comments : {comments}
'''
        if user_schema.get('email'):
            team_users_email_list = api_utils.team_users_email_list(user_schema.get('teamname'))
            if team_email:
                team_users_email_list = [team_email] + team_users_email_list
            send_email(subject, sender, recipients, text_body, cc=team_users_email_list)
        if mswebhook:
            send_teams_notification(mswebhook, subject, text_body)
    except Exception as err:
        print(f"Exception caught. {err}")
        current_app.logger.exception(err)
  
def send_add_user_email(username, password):
    try:
        if username in ["admin", "scheduler"]:
            created_by = "admin"
        else:
            created_by = current_user.username
        user_schema = User.query.filter_by(username=username).first().schema()
        team_schema = Team.query.filter_by(teamname=user_schema.get('teamname')).first().schema()
        team_email = team_schema.get("email")
        mswebhook = team_schema.get("mswebhook")
        recipients = [user_schema.get('email')]
        sender = current_app.config.get("MAIL_NO_REPLY_SENDER")
        subject = f"Account created for user {username}"
        text_body = f'''
        Created By : {created_by}
        Username : {username}
        Team : {user_schema.get('teamname')}
        Shift Start : {user_schema.get('shift_start')}
        Shift End: {user_schema.get('shift_end')}
        Timezone : {user_schema.get('timezone')}
        Admin : {user_schema.get('admin')}
        First Name : {user_schema.get('first_name')}
        Last Name : {user_schema.get('last_name')}
'''
        if user_schema.get('email'):
            team_users_email_list = api_utils.team_users_email_list(user_schema.get('teamname'))
            if team_email:
                team_users_email_list = [team_email] + team_users_email_list
            send_email(subject, sender, recipients, text_body, cc=team_users_email_list)
            send_email(subject, sender, recipients, f"Password : {password}")
        if mswebhook:
            send_teams_notification(mswebhook, subject, text_body)
    except Exception as err:
        print(f"Exception caught. {err}")
        current_app.logger.exception(err)

def send_edit_user_email(username, cur_user=None):
    try:
        user_schema = User.query.filter_by(username=username).first().schema()
        team_schema = Team.query.filter_by(teamname=user_schema.get('teamname')).first().schema()
        team_email = team_schema.get("email")
        mswebhook = team_schema.get("mswebhook")
        recipients = [user_schema.get('email')]
        sender = current_app.config.get("MAIL_NO_REPLY_SENDER")
        subject = f"Account updated for user {username}"
        text_body = f'''
        Updated By : {cur_user}
        Username : {username}
        Active : {user_schema.get('active')}
        Team : {user_schema.get('teamname')}
        Shift Start : {user_schema.get('shift_start')}
        Shift End: {user_schema.get('shift_end')}
        Timezone : {user_schema.get('timezone')}
        Admin : {user_schema.get('admin')}
        Team Email Notifications : {user_schema.get('team_email_notifications')}
        Monitor My Bin During Absence : {user_schema.get('monitor_case_updates')}
        First Name : {user_schema.get('first_name')}
        Last Name : {user_schema.get('last_name')}
'''
        if user_schema.get('email'):
            team_users_email_list = api_utils.team_users_email_list(user_schema.get('teamname'))
            if team_email:
                team_users_email_list = [team_email] + team_users_email_list
            send_email(subject, sender, recipients, text_body, cc=team_users_email_list)
        if mswebhook:
            send_teams_notification(mswebhook, subject, text_body)
    except Exception as err:
        print(f"Exception caught. {err}")
        current_app.logger.exception(err)

def send_delete_user_email(user_schema):
    try:
        username = user_schema.get('username')
        team_schema = Team.query.filter_by(teamname=user_schema.get('teamname')).first().schema()
        team_email = team_schema.get("email")
        mswebhook = team_schema.get("mswebhook")
        recipients = [user_schema.get('email')]
        sender = current_app.config.get("MAIL_NO_REPLY_SENDER")
        subject = f"Account deleted for user {username}"
        text_body = f'''
        Deleted By : {current_user.username}
        Username : {username}
        Team : {user_schema.get('teamname')}
'''
        if user_schema.get('email'):
            team_users_email_list = api_utils.team_users_email_list(user_schema.get('teamname'))
            if team_email:
                team_users_email_list = [team_email] + team_users_email_list
            send_email(subject, sender, recipients, text_body, cc=team_users_email_list)
        if mswebhook:
            send_teams_notification(mswebhook, subject, text_body)
    except Exception as err:
        print(f"Exception caught. {err}")
        current_app.logger.exception(err)  

def send_password_reset_email(email, random_string):
    try:
        subject = f"Password reset requested."
        text_body = f"Please use the temporary password to login : {random_string}"
        sender = current_app.config.get("MAIL_NO_REPLY_SENDER")
        recipients = [email]
        send_email(subject, sender, recipients, text_body)
    except Exception as err:
        print(f"Exception caught. {err}")
        current_app.logger.exception(err)

def send_password_change_email(username):
    try:
        user_schema = User.query.filter_by(username=username).first().schema()
        subject = f"Password changed for user {username}"
        text_body = f"This email confirms password changed request for user {username}"
        sender = current_app.config.get("MAIL_NO_REPLY_SENDER")
        recipients = [user_schema.get('email')]
        if user_schema.get('email'):
            send_email(subject, sender, recipients, text_body)
    except Exception as err:
        print(f"Exception caught. {err}")
        current_app.logger.exception(err)

def send_add_user_product_email(d_userproduct, update=False):
    try:
        username = d_userproduct.get('username')
        productname = d_userproduct.get('productname')
        active = d_userproduct.get('active')
        quota = d_userproduct.get('quota')
        user_schema = User.query.filter_by(username=username).first().schema()
        team_schema = Team.query.filter_by(teamname=user_schema.get('teamname')).first().schema()
        team_email = team_schema.get("email")
        mswebhook = team_schema.get("mswebhook")
        recipients = [user_schema.get('email')]
        sender = current_app.config.get("MAIL_NO_REPLY_SENDER")
        text_body = f'''
        Updated By : {current_user.username}
        Username : {username}
        Product : {productname}
        Active : {active}
        Quota: {quota}
'''
        if update:
            subject = f"User {username} and Product {productname} association updated."
        else:
            subject = f"User {username} added to Product {productname}."
        team_users_email_list = api_utils.team_users_email_list(user_schema.get('teamname'))
        if user_schema.get('email'):
            if team_email:
                team_users_email_list = [team_email] + team_users_email_list
            send_email(subject, sender, recipients, text_body, cc=team_users_email_list)
        if mswebhook:
            send_teams_notification(mswebhook, subject, text_body)
    except Exception as err:
        print(f"Exception caught. {err}")
        current_app.logger.exception(err)

def send_delete_user_product_email(username, productname):
    try:
        user_schema = User.query.filter_by(username=username).first().schema()
        team_schema = Team.query.filter_by(teamname=user_schema.get('teamname')).first().schema()
        team_email = team_schema.get("email")
        mswebhook = team_schema.get("mswebhook")
        recipients = [user_schema.get('email')]
        sender = current_app.config.get("MAIL_NO_REPLY_SENDER")
        text_body = f'''
        Updated By : {current_user.username}
        Username : {username}
        Product : {productname}
'''
        subject = f"User {username} removed from product {productname}."
        team_users_email_list = api_utils.team_users_email_list(user_schema.get('teamname'))
        if user_schema.get('email'):
            if team_email:
                team_users_email_list = [team_email] + team_users_email_list
            send_email(subject, sender, recipients, text_body, cc=team_users_email_list)
        if mswebhook:
            send_teams_notification(mswebhook, subject, text_body)
    except Exception as err:
        print(f"Exception caught. {err}")
        current_app.logger.exception(err)
    
def send_job_scheduled_email(username, j_object):
    try:
        user_schema = User.query.filter_by(username=username).first().schema()
        team_schema = Team.query.filter_by(teamname=user_schema.get('teamname')).first().schema()
        team_email = team_schema.get("email")
        submitted_by_user_object = User.query.filter_by(username=username).first()
        time = submitted_by_user_object.user_datetime(j_object.time) + " " + submitted_by_user_object.timezone
        mswebhook = team_schema.get("mswebhook")
        recipients = [user_schema.get('email')]
        sender = current_app.config.get("MAIL_NO_REPLY_SENDER")
        text_body = f'''
        Submitted By : {username}
        Job ID : {j_object.id}
        Status : {j_object.status}
        Created at : {time}
'''
        subject = f"Job : {j_object.job_type} : {j_object.status}"
        team_users_email_list = api_utils.team_users_email_list(user_schema.get('teamname'))
        if user_schema.get('email'):
            if team_email:
                team_users_email_list = [team_email] + team_users_email_list
            send_email(subject, sender, recipients, text_body, cc=team_users_email_list)
        if mswebhook:
            send_teams_notification(mswebhook, subject, text_body)
    except Exception as err:
        print(f"Exception caught. {err}")
        current_app.logger.exception(err)

def send_external_case_update_email(username, case):
    try:
        user_schema = User.query.filter_by(username=username).first().schema()
        team_schema = Team.query.filter_by(teamname=user_schema.get('teamname')).first().schema()
        team_email = team_schema.get("email")
        mswebhook = team_schema.get("mswebhook")
        recipients = [user_schema.get('email')]
        sender = current_app.config.get("MAIL_NO_REPLY_SENDER")
        text_body = f'''
        Case ID : {case.case_id}
        Case Owner : {user_schema.get('full_name')}
        Accout Name : {case.account_name}
        Case Update : {case.last_external_update_note}
        Case Update Email : {case.last_external_update_email}
        Case Update Time(UTC) : {case.last_external_update_utc_time}
'''
        subject = f"External Update On Case : {case.case_id} : {user_schema.get('full_name')} : {case.account_name}"
        team_users_email_list = api_utils.team_users_email_list(user_schema.get('teamname'))
        if user_schema.get('email'):
            if team_email:
                team_users_email_list = [team_email] + team_users_email_list
            send_email(subject, sender, recipients, text_body, cc=team_users_email_list)
        if mswebhook:
            send_teams_notification(mswebhook, subject, text_body)
    except Exception as err:
        print(f"Exception caught. {err}")
        current_app.logger.exception(err)

def send_sf_api_request_summary_report_email(emails, list_requests, days):
    try:
        recipients = emails
        sender = current_app.config.get("MAIL_NO_REPLY_SENDER")
        li = []
        for req in list_requests:
            li.append([req.url, req.details, req.time])
        fields = ['URL', 'Details', f'Time (UTC)'] 
        with open('/tmp/sf_api_details.csv', 'w') as f:
            write = csv.writer(f)
            write.writerow(fields)
            write.writerows(li)
        text_body = f'''
        Api Request details are in the attached csv file.
'''
        subject = f"CAT : Salesforce API requests weekly report - No of days {days} - No of requestes {len(li)}"
        send_email(subject, sender, recipients, text_body, attachment='/tmp/sf_api_details.csv')
    except Exception as err:
        print(f"Exception caught. {err}")
        current_app.logger.exception(err)

def send_case_assigned_failed_email(case, failed_reason=""):
    try:
        product_object = Product.find_product_series(case.product_series, case.mist_product)
        # Incase the product_series is not associated with any product in CAT. Happens only when a case is scheduled to be handoff
        if product_object is None:
            # add the currently assigned owner to supported_list_of_users. This variable is used to determine the team that needs to be notified
            supported_list_of_users = [User.query.filter_by(full_name=case.case_owner).first()]
        else:
            supported_list_of_users = product_object.supported_by
        if supported_list_of_users:
            # find the first user and then trace the team name.
            username = supported_list_of_users[0].username
            user_schema = User.query.filter_by(username=username).first().schema()
            team_schema = Team.query.filter_by(teamname=user_schema.get('teamname')).first().schema()
            team_email = team_schema.get("email")
            mswebhook = team_schema.get("mswebhook")
            recipients = []
            sender = current_app.config.get("MAIL_NO_REPLY_SENDER")
            text_body = f'''
            Case ID : {case.case_id}
            Priority : {case.priority}
            Product : {case.product_series}
            Account Name : {case.account_name}
            Failed Reason : {failed_reason}
            Subject : {case.subject}
    '''
            subject = f"Failed to assign case : {case.case_id} : {case.priority} : {case.product_series}"
            team_users_email_list = api_utils.team_users_email_list(user_schema.get('teamname'))
            if team_email:
                team_users_email_list = [team_email] + team_users_email_list
            if recipients or team_users_email_list:
                send_email(subject, sender, recipients, text_body, cc=team_users_email_list)
            if mswebhook:
                send_teams_notification(mswebhook, subject, text_body)
    except Exception as err:
        print(f"Exception caught. {err}")
        current_app.logger.exception(err)

def send_case_handoffs_summary_email(username, list_of_cated_cases):
    try:
        user_schema = User.query.filter_by(username=username).first().schema()
        team_schema = Team.query.filter_by(teamname=user_schema.get('teamname')).first().schema()
        team_email = team_schema.get("email")
        mswebhook = team_schema.get("mswebhook")
        recipients = [user_schema.get('email')]
        sender = current_app.config.get("MAIL_NO_REPLY_SENDER")
        text_body = ""
        for case in list_of_cated_cases:
            text_body = text_body + f'''
                "case_id": {case.get('case_id')}
                "Cat'ed To": {case.get('cated_to')}
                "Account Name": {case.get('account_name')}
                "Status": {case.get('status')}
                "priority: {case.get('priority')}
                "Current Case Owner": {case.get('case_owner')}
                "Product": {case.get('product_series')}
                "Synopsis": {case.get('subject')}
                "Cat Assignment Failure Reason": {case.get('failed_reason')}
                "Handoff": {case.get('handoffs')}
            '''
        subject = f"CAT Handoff Summary : {user_schema.get('full_name')} : {len(list_of_cated_cases)}"
        team_users_email_list = api_utils.team_users_email_list(user_schema.get('teamname'))
        if user_schema.get('email'):
            if team_email:
                team_users_email_list = [team_email] + team_users_email_list
            send_email(subject, sender, recipients, text_body, cc=team_users_email_list)
        if mswebhook:
            send_teams_notification(mswebhook, subject, text_body)
    except Exception as err:
        print(f"Exception caught. {err}")
        current_app.logger.exception(err)
