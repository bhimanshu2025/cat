from flask import render_template, flash, redirect, url_for, request, current_app, Blueprint
from cat.products.forms import AddProductForm, SheduleSFIntegrationForm
from flask_login import login_required
from cat import ui_utils as utils
from flask import current_app
from cat.utils.products import utils as products_utils
from flask_login import current_user
from cat import scheduler_sf

products_b = Blueprint('products_b', __name__)

@products_b.route("/products")
@login_required
def products():
    products, _ = products_utils.products()
    return render_template('products.html', title="Products", products=products)

@products_b.route("/add_product", methods=['GET', 'POST'])
@login_required
def add_product():
    form = AddProductForm()
    form.sf_job_timezone.data = current_user.timezone
    form.sf_init_email_name.choices = products_utils.sf_all_available_email_names() + ['---'] 
    if form.validate_on_submit():
        if form.sf_init_email_name.data == '---':
            form.sf_init_email_name.data = None
        d = {
            'productname': form.productname.data,
            'strategy': form.strategy.data,
            'case_regex': form.regex.data,
            'max_days_month': form.max_days_month.data,
            'max_days': form.max_days.data,
            'quota_over_days': form.quota_over_days.data,
            'sf_job_cron': form.sf_job_cron.data,
            'sf_job_timezone': form.sf_job_timezone.data,
            'sf_api': form.sf_api.data,
            'sf_job_query_interval': form.sf_job_query_interval.data,
            'sf_platform': form.sf_platform.data,
            'sf_product_series': form.sf_product_series.data,
            'sf_mist_product': form.sf_mist_product.data,
            'sf_enabled': form.sf_enabled.data,
            'sf_init_email_name': form.sf_init_email_name.data
        }
        response, res_code = products_utils.add_product(d)
        if res_code == 200:
            msg = f"Product {form.productname.data} created"
            flash(msg, 'success')
            form.productname.data = ""
            return redirect(url_for('products_b.products'))
        else:
            flash(response, 'danger')   
    form.sf_init_email_name.choices = products_utils.sf_all_available_email_names() + ['---'] 
    return render_template('add_product.html', form=form, title="Add Product", legend="Add Product")

@products_b.route("/edit_product/<string:productname>", methods=['GET', 'POST'])
@login_required
def edit_product(productname):
    if current_user.admin or current_user.username == "admin":
        form = AddProductForm()
        # below is needed or else the form fails to validate
        form.productname.data = productname
        form.sf_init_email_name.choices = products_utils.sf_all_available_email_names() + ['---'] 
        if form.validate_on_submit():
            if form.sf_init_email_name.data == '---':
                form.sf_init_email_name.data = None
            d = {
                'strategy': form.strategy.data,
                'case_regex': form.regex.data,
                'max_days_month': form.max_days_month.data,
                'max_days': form.max_days.data,
                'quota_over_days': form.quota_over_days.data,
                'sf_job_cron': form.sf_job_cron.data,
                'sf_job_timezone': form.sf_job_timezone.data,
                'sf_api': form.sf_api.data,
                'sf_job_query_interval': form.sf_job_query_interval.data,
                'sf_platform': form.sf_platform.data,
                'sf_product_series': form.sf_product_series.data,
                'sf_mist_product': form.sf_mist_product.data,
                'sf_enabled': form.sf_enabled.data,
                'sf_init_email_name': form.sf_init_email_name.data
            }
            response, res_code = products_utils.edit_product(productname, d)
            if res_code == 200:
                current_app.logger.info(response)
                msg = f"Product {productname} updated"
                flash(msg, 'success')
                return redirect(url_for('products_b.products'))
            else:
                flash(response, 'danger')
        elif request.method == 'GET':
            p_schema = utils.get_product_schema(productname)
            form.strategy.data = p_schema.get('strategy')
            form.regex.data = p_schema.get('case_regex')
            form.max_days_month.data = p_schema.get('max_days_month')
            form.max_days.data = p_schema.get('max_days')
            form.quota_over_days.data = p_schema.get('quota_over_days')
            form.sf_job_cron.data = p_schema.get('sf_job_cron')
            form.sf_api.data = p_schema.get('sf_api')
            form.sf_job_query_interval.data = p_schema.get('sf_job_query_interval')
            form.sf_platform.data = p_schema.get('sf_platform')
            form.sf_product_series.data = p_schema.get('sf_product_series')
            form.sf_mist_product.data = p_schema.get('sf_mist_product')
            form.sf_enabled.data = p_schema.get('sf_enabled')
            form.sf_init_email_name.data = p_schema.get('sf_init_email_name') or '---'
            form.sf_job_timezone.data = p_schema.get('sf_job_timezone')
        form.sf_init_email_name.choices = products_utils.sf_all_available_email_names() + ['---'] 
        return render_template('add_product.html', form=form, title="Edit Product", productname=form.productname.data, legend="Edit Product")
    else:
        flash("Unauthorized Access", 'warning')
        return redirect(url_for('products_b.products'))
    
@products_b.route("/delete_product/<string:productname>", methods=['GET', 'POST'])
@login_required
def delete_product(productname):
    if current_user.admin or current_user.username == "admin":
        response, res_code = products_utils.del_product(productname)
        if res_code == 200:
            msg = f"Product {productname} deleted"
            flash(msg, 'success')
        else:
            flash(response, 'danger')          
        return redirect(url_for('products_b.products'))
    else:
        flash("Unauthorized Access", 'warning')
        return redirect(url_for('products_b.products'))

@products_b.route("/schedule_sf_integration", methods=['GET', 'POST'])
@login_required
def schedule_sf_integration():
    form = SheduleSFIntegrationForm()
    form.productname.choices=utils.get_product_names()
    if form.validate_on_submit():
        productname = form.productname.data
        datetime = form.datetime.data
        timezone = form.timezone.data
        sf_enabled = form.sf_enabled.data
        holiday_list = form.holiday_list.data
        d = {
            "productname": productname,
            "datetime": datetime,
            "timezone": timezone,
            "sf_enabled": sf_enabled,
            "holiday_list": holiday_list
        }
        response, res_code = products_utils.schedule_sf_integration(d)
        if res_code == 200:
            flash('Job Submitted', 'success')
            return redirect(url_for('products_b.schedule_sf_integration'))
        else:
            flash(response, 'danger')
    form.productname.choices=utils.get_product_names()
    form.timezone.data = current_user.timezone
    jobs = utils.get_scheduled_jobs(scheduler=scheduler_sf, object=True)
    return render_template('schedule_sf_integration.html', form=form, title="Schedule SF Integration", jobs=jobs)

@products_b.route("/products_delete_job/<string:jobid>", methods=['GET', 'POST'])
@login_required
def products_delete_job(jobid):
    response, res_code = products_utils.del_job(jobid)
    if res_code == 200:
        msg = f"Job {jobid} deleted"
        flash(msg, 'success')
    else:
        flash(response, 'danger')          
    return redirect(url_for('products_b.schedule_sf_integration'))