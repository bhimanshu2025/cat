from flask import render_template, flash, redirect, url_for, request, current_app, Blueprint
from cat.teams.forms import AddTeamForm
from flask_login import login_required
from cat import ui_utils as utils
from flask import current_app
from cat.utils.teams import utils as teams_utils
from flask_login import current_user

teams_b = Blueprint('teams_b', __name__)

@teams_b.route("/teams")
@login_required
def teams():
    teams, _ = teams_utils.teams()
    return render_template('teams.html', title="Teams", teams=teams)

@teams_b.route("/add_team", methods=['GET', 'POST'])
@login_required
def add_team():
    form = AddTeamForm()
    if form.validate_on_submit():
        d = {
            'teamname': form.teamname.data,
            'email': form.email.data,
            'mswebhook': form.mswebhook.data
        }
        response, res_code = teams_utils.add_team(d)
        if res_code == 200:
            msg = f"Team {form.teamname.data} created"
            flash(msg, 'success')
            return redirect(url_for('teams_b.teams'))
        else:
            flash(response, 'danger')   
    return render_template('add_team.html', form=form, title="Add Team", legend="Add Team")

@teams_b.route("/edit_team/<string:teamname>", methods=['GET', 'POST'])
@login_required
def edit_team(teamname):
    if (current_user.teamname == teamname and current_user.admin) or current_user.username == "admin":
        form = AddTeamForm()
        # below is needed or else the form fails to validate
        form.teamname.data = teamname
        if form.validate_on_submit():
            d = {
                'email': form.email.data,
                'mswebhook': form.mswebhook.data
            }
            response, res_code = teams_utils.edit_team(teamname, d)
            if res_code == 200:
                current_app.logger.info(response)
                msg = f"Team {teamname} updated"
                flash(msg, 'success')
                return redirect(url_for('teams_b.teams'))
            else:
                flash(response, 'danger')
        elif request.method == 'GET':
            t_schema = utils.get_team_schema(teamname)
            form.email.data = t_schema.get('email')
            form.mswebhook.data = t_schema.get('mswebhook')
            form.teamname.data = teamname
        return render_template('add_team.html', form=form, title="Edit Team", teamname=form.teamname.data, legend="Edit Team")
    else:
        flash("Unauthorized Access", 'warning')
        return redirect(url_for('teams_b.teams'))
    
@teams_b.route("/delete_team/<string:teamname>", methods=['GET', 'POST'])
@login_required
def delete_team(teamname):
    if (current_user.teamname == teamname and current_user.admin) or current_user.username == "admin":
        respose, res_code = teams_utils.del_team(teamname)
        if res_code == 200:
            msg = f"Team {teamname} deleted"
            flash(msg, 'success')
        else:
            flash(respose, 'danger')          
        return redirect(url_for('teams_b.teams'))
    else:
        flash("Unauthorized Access", 'warning')
        return redirect(url_for('teams_b.teams'))
