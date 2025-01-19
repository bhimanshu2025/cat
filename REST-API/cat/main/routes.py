from flask import render_template, flash, redirect, request, current_app, Blueprint
from cat.main.forms import CaseIdForm, CaseUnassignForm
import json
from flask import current_app, url_for, abort
from cat.utils.cases import utils as cases_utils
from cat.utils.audit import utils as audit_utils
from cat.utils.users import utils as users_utils
from cat import ui_utils as ui_utils
from flask_login import login_required, current_user

main = Blueprint('main', __name__)

@main.route("/", methods=['GET', 'POST'])
@login_required
def home():
    form = CaseIdForm()
    form.product.choices = current_user.product_names() + ['---']  
    form.user.choices = ui_utils.get_user_names(object=False, teamname=current_user.teamname) + ['---']  
    form.sf_email_name.choices = current_user.sf_email_names() + ['---'] 
    # Get list of uncat'ed cases.
    uncated_cases_object_list = ui_utils.get_uncated_cases_list(object=True, days=0)
    uncated_case_list = []
    for uncated_case in uncated_cases_object_list:
        uncated_case_list.append(f"{uncated_case.case_id}({uncated_case.product})")
    form.caseid.choices = uncated_case_list + ['']
    if form.validate_on_submit():
        if len(form.caseid_text.data) > 0:
            caseid = form.caseid_text.data
        else:
            caseid = form.caseid.data.split('(')[0]
        if form.user.data == "---":
            form.user.data = None
        if form.sf_email_name.data == "---":
            form.sf_email_name.data = None
        if form.delayed_assignment.data == "---":
            form.delayed_assignment.data = None
        if form.product.data == "---":
            form.product.data = None
        d_case = {
            "case_id": caseid,
            "product": form.product.data,
            "comments": form.comments.data,
            "mode": form.mode.data,
            "user": form.user.data,
            "check_in_shift": form.check_in_shift.data,
            "sf_email_name": form.sf_email_name.data,
            "delayed_assignment": form.delayed_assignment.data
        }
        response, res_code = cases_utils.assign_case(d_case)
        if res_code == 200:
            case_assigned_to = response.get('assigned_to')
            msg = f"Case {caseid} assigned to {case_assigned_to}."
            form.caseid.data = ""
            flash(msg, 'success')
        else:
            flash(response, 'danger')
        return redirect(url_for('main.home'))   
    form.product.choices=current_user.product_names() + ['---']  
    # form.product.data = current_user.most_product_cases()
    form.user.choices=ui_utils.get_user_names(object=False, teamname=current_user.teamname) + ['---']  
    form.sf_email_name.choices = current_user.sf_email_names() + ['---'] 
    # Get list of uncat'ed cases.
    uncated_cases_object_list = ui_utils.get_uncated_cases_list(object=True, days=0)
    uncated_case_list = []
    for uncated_case in uncated_cases_object_list:
        uncated_case_list.append(f"{uncated_case.case_id}({uncated_case.product})")
    form.caseid.choices = uncated_case_list + ['']
    if len(current_user.product_names()) == 0:
        flash(f"User {current_user.username} doesnt support any products. Please associate user to products to be able to assign cases.", "danger")
    return render_template('home.html', title="Home", form=form)

@main.route("/unassign_case", methods=['GET', 'POST'])
@login_required
def unassign_case():
    per_page = 30
    form = CaseUnassignForm()
    form.caseid.choices=ui_utils.get_cases_list(per_page=per_page)  
    if form.validate_on_submit():
        if len(form.caseid_text.data) > 0:
            case_id = form.caseid_text.data
        else:
            case_id = form.caseid.data

        d = {
            "comments": form.comments.data
        }
        response, res_code = cases_utils.unassign_case(d, case_id)
        if res_code == 200:
            msg = f"Case {case_id} unassigned from {response.get('assigned_to')}."
            flash(msg, 'success')
            form.comments.data = ""
            return redirect(url_for('main.unassign_case'))
        else:
            flash(response, 'danger')      
    form.caseid.choices=ui_utils.get_cases_list(per_page=per_page)    
    if len(ui_utils.get_cases_list()) == 0:
        flash(f"No cases found for products supported by { current_user.username }.", "danger")
    return render_template('unassign_case.html', title="Unassign Case", form=form)

@main.route("/about")
def about():
    return render_template('about.html', title="About")

@main.route("/swagger")
@login_required
def swagger():
    return redirect(current_app.config['SWAGGER'])

@main.route("/audit")
@login_required
def audit():
    page = request.args.get('page', 1, type=int)
    if current_user.username == "admin":
        audits = audit_utils.audit(page)
    else:
        audits = audit_utils.audit(page, teamname=current_user.teamname)
    return render_template('audit.html', title="Audit", audits=audits)

@main.route("/audit_details/<int:id>")
@login_required
def audit_details(id):
    audit = audit_utils.audit_details(id)
    return render_template('audit_details.html', audit=audit, title="Audit Details")

@main.route("/cases")
@login_required
def cases():
    page = request.args.get('page', 1, type=int)
    cases, _ = cases_utils.cases(page)
    return render_template('cases.html', title="Cases Assigned", cases=cases)

@main.route("/cases_of_product/<string:productname>")
@login_required
def cases_of_product(productname):
    if productname in current_user.product_names() or current_user.username == "admin":
        page = request.args.get('page', 1, type=int)
        cases, status_code = cases_utils.cases_of_product(productname, page)
        if status_code != 200:
            return render_template(f'/errors/{status_code}.html'), status_code
        return render_template('cases_of_product.html', productname=productname, title="Cases Assigned", cases=cases)
    else:
        flash("Unauthorized Access", "warning")
        return redirect(url_for('main.cases'))

@main.route("/cases_of_user/<string:username>")
@login_required
def cases_of_user(username):
    user_schema, status_code = users_utils.user(username)
    if status_code != 200:
        return render_template(f'/errors/{status_code}.html'), status_code
    if current_user.teamname == user_schema.get("teamname") or current_user.username == "admin":
        page = request.args.get('page', 1, type=int)
        cases, _ = cases_utils.cases_of_user(username, page)
        return render_template('cases_of_user.html', username=username, title="Cases Assigned", cases=cases)
    else:
        flash("Unauthorized Access", "warning")
        return redirect(url_for('main.cases'))

@main.route("/cases_assigned_by_user/<string:username>")
@login_required
def cases_assigned_by_user(username):
    user_schema, status_code = users_utils.user(username)
    if status_code != 200:
        return render_template(f'/errors/{status_code}.html'), status_code
    if current_user.teamname == user_schema.get("teamname") or current_user.username == "admin":
        page = request.args.get('page', 1, type=int)
        cases, _  = cases_utils.cases_assigned_by_user(username, page)
        return render_template('cases_assigned_by_user.html', username=username, title="Cases Assigned", cases=cases)
    else:
        flash("Unauthorized Access", "warning")
        return redirect(url_for('main.cases'))

@main.route("/cases_assigned_by_mode/<string:mode>")
@login_required
def cases_assigned_by_mode(mode):
    page = request.args.get('page', 1, type=int)
    cases, status_code = cases_utils.cases_assigned_by_mode(mode, page)
    if status_code != 200:
        return render_template(f'/errors/{status_code}.html'), status_code
    return render_template('cases_assigned_by_mode.html', mode=mode, title="Cases Assigned", cases=cases)

@main.route("/cases_assigned_by_priority/<string:priority>")
@login_required
def cases_assigned_by_priority(priority):
    page = request.args.get('page', 1, type=int)
    cases, status_code = cases_utils.cases_assigned_by_priority(priority, page)
    if status_code != 200:
        return render_template(f'/errors/{status_code}.html'), status_code
    return render_template('cases_assigned_by_priority.html', title="Cases Assigned", cases=cases, priority=priority)

@main.route("/salesforce_case_details/<string:case_id>")
@login_required
def salesforce_case_details(case_id):
    response, response_code = cases_utils.salesforce_case_details(case_id)
    if response_code == 200:
        case = response
        res, res_code = cases_utils.salesforce_open_cases_of_accounts(case.account_name)
        if res_code == 200:
            cases_list = res
        else:
            cases_list = None
        cat_case_schema_response, cat_case_schema_status = cases_utils.case_details(case_id)
        if cat_case_schema_status == 200:
            cat_case_schema = cat_case_schema_response
        return render_template('salesforce_case_details.html', title="Salesforce Case Details", cat_case_schema=cat_case_schema, case=case, cases_list=cases_list)
    else:
        flash(response, "warning")
        return redirect(url_for('main.cases'))