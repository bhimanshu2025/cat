from cat.models import UserProduct, Audit
from flask import request, current_app
import cat.api_utils as utils
from flask_login import current_user
from cat.email import email

def all_user_product():
    l = []
    ups = UserProduct.query.all()
    for up in ups:
        l.append(up.schema())
    return l, 200

def update_user_product(d):
    r, res_code = utils.check_user_product(d)
    if r == 0:
        username = d.get('username')
        productname = d.get('productname')
        if utils.check_user_access(username):
            up = UserProduct.query.filter_by(user_name=username, product_name=productname).first()
            if up == None:  # ADD REQUEST
                up = UserProduct(user_name=username, product_name=productname, 
                                active=d.get('active'), quota=d.get('quota'))
                a = Audit(user=current_user.username, task_type="ADD USER TO PRODUCT", task=str(up.schema()))
                email.send_add_user_product_email(d)
                current_app.logger.info(f"User {username} added to support product {productname}")
            else:  # UPDATE REQUEST
                a = Audit(user=current_user.username, task_type="UPDATE USER TO PRODUCT", task=str([d, up.schema()]))
                up.update(d)
                email.send_add_user_product_email(d, update=True)
                current_app.logger.info(f"User product association updated for user {username} and product {productname}")
            utils.add_all([up, a])
            return up.schema(), 200
        else:
            return "Unauthorized Access", 401
    else:
        return r, res_code
    
def user_product(username, productname):
    d = {}
    d["username"] = username
    d["productname"] = productname
    r, res_code = utils.check_user_product(d)
    if r == 0:
        up = UserProduct.query.filter_by(user_name=d.get('username'), product_name=d.get('productname')).first()
        if up is None:
            return f"User {username} doesnt support product {productname}", 400
        return up.schema(), 200
    else:
        return r, res_code

def del_user_product(username, productname):
    d = {}
    d["username"] = username
    d["productname"] = productname
    r, res_code = utils.check_user_product(d)
    if r == 0:
        if utils.check_user_access(username):
            up = UserProduct.query.filter_by(user_name=d.get('username'), product_name=d.get('productname')).first()
            if up is None:
                return f"User {username} doesnt support product {productname}", 400
            a = Audit(user=current_user.username, task_type="DELETE USER TO PRODUCT", task=str(up.schema()))
            up_schema = up.schema()
            utils.delete_all([up])
            utils.add_all([a])
            email.send_delete_user_product_email(username, productname)
            current_app.logger.info(f"User {username} removed from supporting product {productname}")
            return up_schema, 200
        else:
            return "Unauthorized Access", 401
    else:
        return r, res_code

