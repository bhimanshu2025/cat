from flask import render_template, flash, redirect, url_for, request, current_app, Blueprint
from cat.users.forms import AddUserForm, ReactivateUserForm, AddUserProductForm, LoginForm, AccountForm, ChangePasswordForm, ResetPasswordForm, \
ScheduleShiftChangerForm, AddSalesforceEmailForm, ScheduleHandoffsForm
from cat import ui_utils as utils
from flask import current_app
from cat.utils.users import utils as users_utils
from cat.utils.teams import utils as teams_utils
from cat.utils.cases import utils as cases_utils
from cat.utils.userproduct import utils as userproduct_utils
from flask_login import current_user, login_required, login_user, logout_user
from cat import scheduler

users_b = Blueprint('users_b', __name__)

@users_b.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        muleuser = form.muleuser.data
        d = {
            "username": username,
            "password": password,
            "muleuser": muleuser
        }
        response, res_code = users_utils.login_ui(d)
        if res_code == 200:
            login_user(response, remember=form.remember.data)
            flash(f'Login Successful {current_user.username}', 'success')
            return redirect(url_for('main.home'))
        else:
            flash(response, 'warning')
    return render_template('login.html', title="Login", form=form), 401

@users_b.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('users_b.login'))

@users_b.route("/users")
@login_required
def users():
    d_teams = {}
    if current_user.username == "admin":
        teams = utils.get_team_names(object=True)
    else:
        teams = [utils.get_team(current_user.teamname, object=True)]
    for team in teams:
        teamname = team.get('teamname')
        d_teams[teamname] = []
        for username in team.get('users'):
            user_schema, _ = users_utils.user(username)
            d_teams[teamname].append(user_schema)
    return render_template('users.html', title="Users", d_teams=d_teams)

@users_b.route("/add_user", methods=['GET', 'POST'])
def add_user():
    form = AddUserForm()
    # had to remove the below choices option from forms.py or else the teams choices woudnt get updated when a new team is added until app is restarted.
    form.teamname.choices = utils.get_team_names()
    if form.validate_on_submit():
        d = {
            'username': form.username.data,
            'email': form.email.data,
            'teamname': form.teamname.data,
            'active': form.active.data,
            'admin': form.admin.data,
            'shift_start': form.shift_start.data,
            'shift_end': form.shift_end.data,
            'first_name': form.first_name.data,
            'last_name': form.last_name.data,
            'timezone': form.timezone.data,
            'password': form.password.data,
            'team_email_notifications': form.team_email_notifications.data,
            "monitor_case_updates": form.monitor_case_updates.data
        }
        response, res_code = users_utils.add_user(d)
        if res_code == 200:
            msg = f"Account created for user {form.username.data}"
            flash(msg, 'success')
            if current_user.is_anonymous:
                return redirect(url_for('users_b.login'))
            else:
                return redirect(url_for('users_b.users'))
        else:
            flash(response, 'danger')   
    form.teamname.choices = utils.get_team_names()
    return render_template('add_user.html', form=form, title="Register User", legend="Register User")

@users_b.route("/edit_user/<string:username>", methods=['GET', 'POST'])
@login_required
def edit_user(username):
    if utils.check_user_access(username):
        form = AddUserForm()
        # below is needed or else the form fails to validate
        form.username.data = username
        form.password.data = "***"
        form.confirm_password.data = "***"
        form.teamname.choices = utils.get_team_names()
        if form.validate_on_submit():
            d = {
                'email': form.email.data,
                'teamname': form.teamname.data,
                'active': form.active.data,
                'admin': form.admin.data,
                'shift_start': form.shift_start.data,
                'shift_end': form.shift_end.data,
                'first_name': form.first_name.data,
                'last_name': form.last_name.data,
                'timezone': form.timezone.data,
                'team_email_notifications': form.team_email_notifications.data,
                "monitor_case_updates": form.monitor_case_updates.data
            }
            response, res_code = users_utils.edit_user(username, d)
            if res_code == 200:
                msg = f"User {username} updated"
                flash(msg, 'success')
                return redirect(url_for('users_b.users'))
            else:
                flash(response, 'danger')
        elif request.method == 'GET':
            u_schema = utils.get_user_schema(username)
            form.first_name.data = u_schema.get('first_name')
            form.last_name.data = u_schema.get('last_name')
            form.email.data = u_schema.get('email')
            form.teamname.data = u_schema.get('teamname')
            form.active.data = u_schema.get('active')
            form.admin.data = u_schema.get('admin')
            form.shift_start.data = u_schema.get('shift_start')
            form.shift_end.data = u_schema.get('shift_end')
            form.timezone.data = u_schema.get('timezone')
            form.team_email_notifications.data = u_schema.get('team_email_notifications')
            form.monitor_case_updates.data = u_schema.get('monitor_case_updates')
        form.teamname.choices = utils.get_team_names()
        return render_template('add_user.html', form=form, title="Edit User", username=form.username.data, legend="Edit User")
    else:
        flash("Unauthorized Access", 'warning')
        return redirect(url_for('users_b.users'))

@users_b.route("/account", methods=['GET', 'POST'])
@login_required
def account():
    form = AccountForm()
    if form.validate_on_submit():
        d = {
            'email': form.email.data,
            "timezone": form.timezone.data,
            "active": form.active.data,
            'team_email_notifications': form.team_email_notifications.data,
            "monitor_case_updates": form.monitor_case_updates.data
        }
        response, res_code = users_utils.edit_user(current_user.username, d)
        if res_code == 200:
            current_app.logger.info(response)
            msg = f"User {current_user.username} updated"
            flash(msg, 'success')
        else:
            flash(response, 'danger')
    form.email.data = current_user.email
    form.timezone.data = current_user.timezone
    form.active.data = current_user.active
    form.team_email_notifications.data = current_user.team_email_notifications
    form.monitor_case_updates.data = current_user.monitor_case_updates
    return render_template('account.html', form=form, title="Account")

@users_b.route("/change_password", methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        user_d = {
            'new_password': form.new_password.data,
            'current_password': form.current_password.data
        }
        response, res_code = users_utils.change_password(current_user.username, user_d)
        if res_code == 200:
            current_app.logger.info(response)
            msg = f"User {current_user.username} password changed"
            flash(msg, 'success')
            return redirect(url_for('users_b.account'))
        else:
            flash(response, 'danger')
    return render_template('change_password.html', form=form, title="Change Password")

@users_b.route("/reset_password", methods=['GET', 'POST'])
def reset_password():
    form = ResetPasswordForm()
    if form.validate_on_submit():
        email = form.email.data
        response, res_code = users_utils.reset_password(email)
        if res_code == 200:
            current_app.logger.info("Password reset for user : {email}")
            msg = f"Password reset request submitted. User will recieve an email with temporary password"
            flash(msg, 'success')
            return redirect(url_for('users_b.login'))
        else:
            flash(response, 'danger')
    return render_template('reset_password.html', form=form, title="Reset Password")

@users_b.route("/delete_user/<string:username>", methods=['GET', 'POST'])
@login_required
def delete_user(username):
    if utils.check_user_access(username):
        response, res_code = users_utils.del_user(username)
        if res_code == 200:
            msg = f"User {username} deleted"
            flash(msg, 'success')
        else:
            flash(response, 'danger')          
        return redirect(url_for('users_b.users'))
    else:
        flash("Unauthorized Access", 'warning')
        return redirect(url_for('users_b.users'))
    
@users_b.route("/jobs")
@login_required
def jobs():
    page = request.args.get('page', 1, type=int)
    if current_user.username == "admin":
        jobs= users_utils.jobs(page)
    else:
        jobs= users_utils.jobs(page, teamname=current_user.teamname)
    return render_template('jobs.html', title="Jobs", jobs=jobs)

@users_b.route("/jinja2_variables")
@login_required
def jinja2_variables():
    return render_template('jinja2_variables.html', title="Jinja2 Variables")

@users_b.route("/my_details")
@login_required
def my_details():
    cases, _ = cases_utils.cases_of_user(current_user.username, 1)
    return render_template('my_details.html', cases=cases, title="My Details")

@users_b.route("/reactivate_user", methods=['GET', 'POST'])
@login_required
def reactivate_user():
    form = ReactivateUserForm()
    form.username.choices = utils.get_user_names(object=False, teamname=current_user.teamname)
    if form.validate_on_submit():
        username = form.username.data
        datetime = form.datetime.data
        timezone = form.timezone.data
        active = form.active.data
        d = {
            "username": username,
            "datetime": datetime,
            "timezone": timezone,
            "active": active
        }
        response, res_code = users_utils.reactivate_user(d)
        if res_code == 200:
            flash('Job Submitted', 'success')
            return redirect(url_for('users_b.reactivate_user'))
        else:
            flash(response, 'danger')
    form.username.choices=utils.get_user_names(object=False, teamname=current_user.teamname)
    form.timezone.data = current_user.timezone
    jobs = utils.get_scheduled_jobs(scheduler, True)
    l_usernames, _ = teams_utils.usernames(current_user.teamname)
    return render_template('reactivate_user.html', form=form, title="Reactivate User", jobs=jobs, l_usernames=l_usernames)

@users_b.route("/schedule_shift_change", methods=['GET', 'POST'])
@login_required
def schedule_shift_change():
    form = ScheduleShiftChangerForm()
    form.username.choices = utils.get_user_names(object=False, teamname=current_user.teamname)
    if form.validate_on_submit():
        username = form.username.data
        datetime = form.datetime.data
        timezone = form.timezone.data
        shift_start = form.shift_start.data
        shift_end = form.shift_end.data
        d = {
            "username": username,
            "datetime": datetime,
            "timezone": timezone,
            "shift_start": shift_start,
            "shift_end": shift_end
        }
        response, res_code = users_utils.schedule_shift_change(d)
        if res_code == 200:
            flash('Job Submitted', 'success')
            return redirect(url_for('users_b.schedule_shift_change'))
        else:
            flash(response, 'danger')
    form.username.choices=utils.get_user_names(object=False, teamname=current_user.teamname)
    form.timezone.data = current_user.timezone
    jobs = utils.get_scheduled_jobs(scheduler, True)
    l_usernames, _ = teams_utils.usernames(current_user.teamname)
    return render_template('schedule_shift_change.html', form=form, title="Schedule Shift Change", jobs=jobs, l_usernames=l_usernames)

@users_b.route("/schedule_handoffs", methods=['GET', 'POST'])
@login_required
def schedule_handoffs():
    form = ScheduleHandoffsForm()
    form.username.choices = utils.get_user_names(object=False, teamname=current_user.teamname)
    if form.validate_on_submit():
        username = form.username.data
        datetime = form.datetime.data
        timezone = form.timezone.data
        check_in_shift = form.check_in_shift.data
        d = {
            "username": username,
            "datetime": datetime,
            "timezone": timezone,
            "check_in_shift": check_in_shift
        }
        response, res_code = users_utils.schedule_handoffs(d)
        if res_code == 200:
            flash('Job Submitted', 'success')
            return redirect(url_for('users_b.schedule_handoffs'))
        else:
            flash(response, 'danger')
    form.username.choices=utils.get_user_names(object=False, teamname=current_user.teamname)
    form.timezone.data = current_user.timezone
    jobs = utils.get_scheduled_jobs(scheduler, True)
    l_usernames, _ = teams_utils.usernames(current_user.teamname)
    return render_template('schedule_handoffs.html', form=form, title="Schedule Handoffs", jobs=jobs, l_usernames=l_usernames)

@users_b.route("/delete_job/<string:jobid>", methods=['GET', 'POST'])
@login_required
def delete_job(jobid):
    response, res_code = users_utils.del_job(jobid)
    if res_code == 200:
        msg = f"Job {jobid} deleted"
        flash(msg, 'success')
    else:
        flash(response, 'danger')          
    return redirect(url_for('users_b.jobs'))

@users_b.route("/add_user_product", methods=['GET', 'POST'])
@login_required
def add_user_product():
    form = AddUserProductForm()
    form.username.choices = utils.get_user_names(object=False, teamname=current_user.teamname)
    # had to remove choices from forms.py as any new product addition would require app restart for it to show in choices
    form.productname.choices = utils.get_product_names()
    if form.validate_on_submit():
        d = {
            'productname': form.productname.data,
            'username': form.username.data,
            'quota': form.quota.data,
            'active': form.active.data
        }
        response, res_code = userproduct_utils.update_user_product(d)
        if res_code == 200:
            current_app.logger.info(response)
            msg = f"User {form.username.data} supports product {form.productname.data}"
            flash(msg, 'success')
            return redirect(url_for('users_b.user_product'))
        else:
            flash(response, 'danger')
    form.username.choices=utils.get_user_names(object=False, teamname=current_user.teamname)
    form.productname.choices = utils.get_product_names()
    if form.productname.choices == []:
        flash("Please add a product first", "danger")
    return render_template('add_user_product.html', form=form, title="Add User To Product", legend="Add User To Product")

@users_b.route("/edit_user_product/<string:username>/<string:productname>", methods=['GET', 'POST'])
@login_required
def edit_user_product(username, productname):
    if utils.check_user_access(username):
        form = AddUserProductForm()
        # below is needed or else the form fails to validate
        form.username.choices=utils.get_user_names(object=False, teamname=current_user.teamname)
        form.productname.choices = utils.get_product_names()
        form.productname.data = productname
        form.username.data = username
        if form.validate_on_submit():
            d = {
                'username': form.username.data,
                'productname': form.productname.data,
                'quota': form.quota.data,
                'active': form.active.data
            }
            response, res_code = userproduct_utils.update_user_product(d)
            if res_code == 200:
                current_app.logger.info(response)
                msg = f"User {username} and product {productname} association updated"
                flash(msg, 'success')
                return redirect(url_for('users_b.user_product'))
            else:
                flash(response, 'danger')
        elif request.method == 'GET':
            up_schema = utils.get_user_product_schema(username, productname)
            form.username.data = up_schema.get('username')
            form.productname.data = up_schema.get('productname')
            form.quota.data = up_schema.get('quota')
            form.active.data = up_schema.get('active')
        form.username.choices=utils.get_user_names(object=False, teamname=current_user.teamname)
        form.productname.choices = utils.get_product_names()
        return render_template('add_user_product.html', form=form, title="Edit User Product", username=form.username.data, 
                            productname=form.productname.data, legend="Edit User Product")
    else:
        flash("Unauthorized Access", 'warning')
        return redirect(url_for('users_b.user_product'))
    
@users_b.route("/user_product", methods=['GET'])
@login_required
def user_product():
    d = {}
    if current_user.username == "admin":
        products = utils.get_product_names(object=True)
    else:
        products = utils.get_product_names(username=current_user.username, object=True)
    for product in products:
        productname = product.get('productname')
        d[productname] = []
        for username in product.get('supported_by'):
            ups, _ = userproduct_utils.user_product(username, productname)
            d[productname].append({
                'username': ups.get('username'),
                'quota': ups.get('quota'),
                'active': ups.get('active')
            })
    return render_template('user_product.html', title="User Product", dict=d)

@users_b.route("/delete_user_product/<string:username>/<string:productname>", methods=['GET', 'POST'])
@login_required
def delete_user_product(username, productname):
    if utils.check_user_access(username):
        response, res_code = userproduct_utils.del_user_product(username, productname)
        if res_code == 200:
            msg = f"User {username} no longer supports product {productname}"
            flash(msg, 'success')
        else:
            flash(response, 'danger')          
        return redirect(url_for('users_b.user_product'))
    else:
        flash("Unauthorized Access", 'warning')
        return redirect(url_for('users_b.user_product'))

@users_b.route("/salesforce_emails")
@login_required
def salesforce_emails():
    emails, _ = users_utils.salesforce_emails()
    return render_template('salesforce_emails.html', title="Salesforce Emails", emails=emails)

@users_b.route("/add_salesforce_email", methods=['GET', 'POST'])
@login_required
def add_salesforce_email():
    form = AddSalesforceEmailForm()
    if form.validate_on_submit():
        d_sf_email = {
            'email_name': form.email_name.data,
            'email_body': form.email_body.data,
            'email_subject': form.email_subject.data
        }
        response, res_code = users_utils.add_salesforce_email(d_sf_email)
        if res_code == 200:
            current_app.logger.info(response)
            msg = f"Email {form.email_name.data} added"
            flash(msg, 'success')
            return redirect(url_for('users_b.salesforce_emails'))
        else:
            flash(response, 'danger')
    return render_template('add_salesforce_email.html', form=form, title="Add Salesforce Email", legend="Add Salesforce Email")

@users_b.route("/edit_salesforce_email/<string:email_name>", methods=['GET', 'POST'])
@login_required
def edit_salesforce_email(email_name):
    form = AddSalesforceEmailForm()
    if form.validate_on_submit():
        d_sf_email = {
            'email_body': form.email_body.data,
            'email_subject': form.email_subject.data
        }
        response, res_code = users_utils.edit_salesforce_email(email_name, d_sf_email)
        if res_code == 200:
            current_app.logger.info(response)
            msg = f"Email template {email_name} updated"
            flash(msg, 'success')
            return redirect(url_for('users_b.salesforce_emails'))
        else:
            flash(response, 'danger')
    sf_email_schema, _ = users_utils.salesforce_email(email_name)
    form.email_body.data = sf_email_schema.get('email_body')
    form.email_subject.data = sf_email_schema.get('email_subject')
    return render_template('add_salesforce_email.html', form=form, title="Edit Salesforce Email", email_name=email_name, legend="Edit Salesforce Email")

@users_b.route("/delete_salesforce_email/<string:email_name>", methods=['GET', 'POST'])
@login_required
def delete_salesforce_email(email_name):
    response, res_code = users_utils.delete_salesforce_email(email_name)
    if res_code == 200:
        msg = f"Email template {email_name} deleted"
        flash(msg, 'success')
    else:
        flash(response, 'danger')          
    return redirect(url_for('users_b.salesforce_emails'))