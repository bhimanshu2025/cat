from flask import current_app
import cat.api_utils as utils
from cat.models import Product, Audit, User, Jobs, SalesforceEmails
from flask_login import current_user
from datetime import datetime 
import json 
from cat import scheduler_sf
from cat.email import email

def products(username=None):
    li_products = []
    if not username: 
        products = Product.query.all()
    else:
        products = User.query.filter_by(username=username).first().products
    for product in products:
        li_products.append(product.schema())
    return li_products, 200

def product(productname):
    product = Product.query.filter_by(productname=productname).first()
    if product == None:
        return f"Product {productname} not found", 404
    else:
        return product.schema(), 200
    
def del_product(productname):
    if current_user.admin or current_user.username == "admin":
        product = Product.query.filter_by(productname=productname).first()
        if product == None:
            return f"Product {productname} not found", 404
        else:
            if len(product.supported_by) !=0:
                l_users = utils.get_user_names(product.supported_by)
                return f"Product {productname} still has users that support it: {l_users}. Remove all users from supporting this product first.", 400
            p = product.schema()
            a = Audit(user=current_user.username, task_type="DELETE PRODUCT", task=str(product.schema()))
            utils.add_all([a])
            utils.delete_all([product])
            utils.delete_sf_jobs(productname)
            current_app.logger.info(f"Product {productname} deleted successfully")
            return p, 200
    else:
        return "Unauthorized Access", 401
    
def edit_product(productname, d_product, cur_user=None):
    '''
    productname is users product name that needs to be edited
    cur_user is the user name who is making the change.
    user_d is a dict object containing the key value mappings to update product properties
    '''
    from cat import scheduler
    app = scheduler.app
    with app.app_context():
        if cur_user is None:
            cur_user = current_user.username
            if current_user.admin or current_user.username == "admin":
                pass
            else:
                return "Unauthorized Access", 401
        product = Product.query.filter_by(productname=productname).first()
        if product == None:
            return f"Product {productname} not found", 404
        else:
            if d_product.get('sf_init_email_name'):
                sf_email = SalesforceEmails.query.filter_by(email_name=d_product.get('sf_init_email_name')).first()
                if sf_email is None:
                    return f"Email {d_product.get('sf_init_email_name')} does not exist.", 400
            if d_product.get('sf_enabled') and \
                    (d_product.get('sf_product_series') is None and not product.sf_product_series) or \
                    (d_product.get('sf_job_cron') is None and not product.sf_job_cron) or \
                    (d_product.get('sf_job_timezone') is None and not product.sf_job_timezone) or \
                    (d_product.get('sf_job_query_interval') is None and not product.sf_job_query_interval):
                return f"sf_job_cron, sf_product_series, sf_job_query_interval or sf_job_timezone can not be none if sf_enabled is true", 400
            a = Audit(user=cur_user, task_type="UPDATE PRODUCT", task=str([d_product, product.schema()]))
            product.update(d_product)
            utils.add_all([product, a])
            utils.schedule_sf_jobs(l_productnames=[productname])
            current_app.logger.info(f"Product {productname} updated successfully")
            return product.schema(), 200
            
def add_product(d):
    if d.get('productname') == None:
        return f"No productname provided", 400
    temp = Product.query.filter_by(productname=d.get('productname')).first()
    if d.get('sf_init_email_name'):
        sf_email = SalesforceEmails.query.filter_by(email_name=d.get('sf_init_email_name')).first()
        if sf_email is None:
            return f"Email {d.get('sf_init_email_name')} does not exist.", 400
    if temp != None:
        return f"Product {d.get('productname')} already exists", 400
    if d.get('sf_enabled') and (d.get('sf_product_series') is None or \
        d.get('sf_job_cron') is None or d.get('sf_job_timezone') is None or\
            d.get('sf_job_query_interval') is None):
        return f"sf_job_cron, sf_product_series, sf_job_query_interval or sf_job_timezone can not be none if sf_enabled is true", 400
    p = Product(productname=d.get('productname'), strategy=d.get('strategy'), max_days=d.get('max_days'), case_regex=d.get('case_regex'),
                max_days_month=d.get('max_days_month'), quota_over_days=d.get('quota_over_days'), sf_api=d.get('sf_api'),
                sf_job_cron=d.get('sf_job_cron'), sf_job_timezone=d.get('sf_job_timezone'), sf_job_query_interval=d.get('sf_job_query_interval'),
                sf_product_series=d.get('sf_product_series'), sf_platform=d.get('sf_platform'), sf_enabled=d.get('sf_enabled'),
                sf_init_email_name=d.get('sf_init_email_name'), sf_mist_product=d.get('sf_mist_product'))
    a = Audit(user=current_user.username, task_type="ADD PRODUCT", task=str(p.schema()))
    utils.add_all([p, a])
    utils.schedule_sf_jobs()
    current_app.logger.info(f"Product {d.get('productname')} added successfully")
    return p.schema(), 200    

def users(productname):
    l = []
    product = Product.query.filter_by(productname=productname).first()
    if product is None:
        return f"Product {productname} not found", 404
    users = product.supported_by
    for user in users:
        l.append(user.schema())
    return l, 200

def schedule_sf_integration(d, reschedule=False):
    '''
    username is the username whose shift change needs to be  scheduled
    d = {
        "productname": <P1>,
        "datetime": <datetime>,
        "timezone": <tz>,
        "sf_enabled": True,
        "holiday_list": {...}
    }
    productname is products name whose SF integration(for polling new cases) needs to be disabled or enabled
    datetime is a tz unaware datetime object
    timezone is a tz object from datetime class in string format eg : "US/Pacific". this is for the datetime object
    sf_enabled is whether to enable or disable the sf integration for polling new cases
    holiday_list is a json formated list of holidays to deactivate the sf integration
    '''
    holiday_list = d.get('holiday_list')
    if holiday_list:
        return schedule_sf_integration_holidays(d)
    productname = d.get("productname")
    dt = d.get("datetime")
    dt_zone = d.get("timezone")
    sf_enabled = d.get("sf_enabled")
    if productname is None or dt is None or dt_zone is None or sf_enabled is None:
        return f"Missing mandatory arguments", 404
    product_obj = Product.query.filter_by(productname=productname).first()
    if product_obj is None:
        return f"Product {productname} not found", 404
    if reschedule:
        job_status = "Rescheduled"
    else:
        job_status =  "Scheduled"
    if current_user and not current_user.is_anonymous:
        logged_user = current_user.username
    else:
        # system restart reschedules the jobs reading from database
        logged_user = "admin"
    datetime_str = utils.convert_to_local_dt(dt, dt_zone)
    if datetime_str < datetime.now().astimezone():
        return "Datetime has to be a time in future", 400
    year, month, day, hour, minute = datetime_str.year, datetime_str.month, datetime_str.day, \
                                datetime_str.hour, datetime_str.minute
    schema = {
        "productname": productname,
        "time": str(dt) + " " + str(dt_zone),
        "sf_enabled": sf_enabled
    }
    if sf_enabled:
        job_id = f"enable_sf_integration_{datetime.utcnow()}_{productname}"
    else:
        job_id = f"disable_sf_integration_{datetime.utcnow()}_{productname}"
    a = Audit(user=logged_user, task_type="SCHEDULE SF INTEGRATION", task=str(schema))
    j_object = Jobs(id=job_id, username=logged_user, job_type="sf_integration", details=json.dumps(d, default=str), status=job_status)
    utils.add_all([a, j_object])
    r = scheduler_sf.add_job(id=job_id, func=utils.schedule_sf_integration, args=[productname, sf_enabled, j_object.number],
                        trigger='cron', year=year, month=month, day=day, hour=hour, minute=minute)
    current_app.logger.info(f"Schedule SF Integration job submitted successfully for user {logged_user}, job_status is {job_status} \
                            job_id is {job_id}")
    email.send_job_scheduled_email(logged_user, j_object)
    return job_id, 200

def schedule_sf_integration_holidays(d):
    current_app.logger.info(f"Runnig Schedlule SF Integration job for list of holidays : {d.get('holiday_list')}")
    holiday_list = d.get('holiday_list')
    productname = d.get("productname")
    dt_zone = d.get("timezone") or current_user.timezone
    try:
        d_holiday_list = json.loads(holiday_list)
    except json.decoder.JSONDecodeError as error:
        current_app.logger.exception(error)
        return f"Failed to load the request json data. Error: {error}", 400
    else:
        for _, date in d_holiday_list.items():
            # Deactivate Job
            dt = datetime.strptime(date + " " + "00:00", "%Y-%m-%d %H:%M")
            d_deactivate = {
                "productname": productname,
                "datetime": dt,
                "timezone": dt_zone,
                "sf_enabled": False
            }
            response, response_code = schedule_sf_integration(d_deactivate)
            if response_code == 200:
                current_app.logger.info(f"Scheduled job {response}")
            else: 
                current_app.logger.info(f"Failed to schedule job with reason : {response} : {response_code}")
            # Activate Job
            dt = datetime.strptime(date + " " + "23:59", "%Y-%m-%d %H:%M")
            d_activate = {
                "productname": productname,
                "datetime": dt,
                "timezone": dt_zone,
                "sf_enabled": True
            }
            response, response_code = schedule_sf_integration(d_activate)
            if response_code == 200:
                current_app.logger.info(f"Scheduled job {response}")
            else: 
                current_app.logger.info(f"Failed to schedule job with reason : {response} : {response_code}")
        return utils.get_scheduled_jobs(scheduler=scheduler_sf), 200

def del_job(jobid):
    '''
    deletes job with id jobid from scheduler
    '''
    job = scheduler_sf.get_job(id=jobid)
    if job:
        scheduler_sf.delete_job(id=jobid)
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
        return utils.get_scheduled_jobs(scheduler=scheduler_sf), 200
    else:
        current_app.logger.info(f"Delete job failed for job id {jobid}. Job id not found")
        return f"Job {jobid} not found", 404

# Returns list of all available email names to a user
def sf_all_available_email_names():
    return SalesforceEmails.sf_all_available_email_names()

# Returns name of the product defined in CAT that has "product_series" in its list of sf_product_series
def find_product_series(product_series, sf_mist_product):
    return Product.find_product_series(product_series, sf_mist_product)

# Returns list of all product names
def product_names():
    return Product.product_names(), 200