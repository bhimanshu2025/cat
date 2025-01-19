from cat.utils.audit import utils
from flask import Blueprint, jsonify
from cat.api.users.auth import basic_auth
from flask_login import logout_user

auditing = Blueprint('audit', __name__)

@auditing.route("/api/audit/<int:page>", methods=['GET'])
@basic_auth.login_required
def audit(page):
    audits = utils.audit(page)
    l_audits = []
    for audit in audits.items:
        l_audits.append(audit.schema())
    logout_user()
    return jsonify(l_audits)
