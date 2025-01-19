from cat.models import Audit, Team

def audit(page, teamname=None):
    if teamname:
        team = Team.query.filter_by(teamname=teamname).first()
        if team:
            l_usernames = team.get_user_names()
            # append jobs from admin user as admin and scheduler users
            l_usernames.append('admin')
            l_usernames.append('scheduler')
            return Audit.query.filter(Audit.user.in_(l_usernames)).order_by(Audit.time.desc()).paginate(per_page=20, page=page)
        else:
            return []
    else:
        return Audit.query.order_by(Audit.time.desc()).paginate(per_page=20, page=page)

def audit_details(id):
    return Audit.query.filter_by(id=id).first()