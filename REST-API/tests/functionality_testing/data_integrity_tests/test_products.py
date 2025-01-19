import json

def initialize_salesforce_email_create(client):
    email_data = '''{
    "email_name": "email1",
    "email_body": "This is a test email body",
    "email_subject": "Test Subject"
}'''
    return client.post("/api/add-salesforce-email", data=email_data, auth=("admin", "admin"))

def initialize_team(client):
    team_data = '''{
  "email": "abc@xyz.com",
  "mswebhook": "",
  "teamname": "T1"
}'''
    return client.post("/api/team", data=team_data, auth=("admin", "admin"))

def initialize_user(client):
    user_data = '''{
  "email": "abc@efg.com",
  "teamname": "T1",
  "active": true,
  "admin": true,
  "shift_start": "09:00:00",
  "shift_end": "18:00:00",
  "timezone": "US/Pacific",
  "username": "test_user",
  "password": "password"
}'''
    return client.post("/api/user", data=user_data, auth=("admin", "admin"))

def initialize_product(client):
    product_data = '''{
  "strategy": "s1",
  "max_days": "3",
  "max_days_month": "300",
  "case_regex": "^[0-9]{4}-[0-9]{4}-[0-9]{6}$",
  "quota_over_days": 1,
  "sf_api": "",
  "sf_job_cron": "* 6-18 * * 1-5",
  "sf_job_timezone": "US/Pacific",
  "sf_job_query_interval": 1,
  "productname": "P1",
  "sf_enabled": true,
  "sf_product_series": "PS1",
  "sf_platform": "PL1",
  "sf_mist_product": "M1",
  "sf_init_email_name": ""
}'''
    return client.post("/api/product", data=product_data, auth=("admin", "admin"))

def initialize_userproduct(client):
    user_product_data = '''{
  "productname": "P1",
  "username": "test_user",
  "active": true,
  "quota": 1
}'''
    return client.post("/api/user-product", data=user_product_data, auth=("admin", "admin"))

def initialize_all(client):
    initialize_team(client)
    initialize_user(client)
    initialize_product(client)
    initialize_userproduct(client)

def test_1_add_product(client):
    initialize_product(client)
    get_product_response = client.get("/api/product/P1", auth=("admin", "admin"))
    product_schema = get_product_response.json
    assert product_schema.get('strategy') == "s1" and \
           product_schema.get('max_days') == 3 and \
           product_schema.get('max_days_month') == 300 and \
           product_schema.get('case_regex') == "^[0-9]{4}-[0-9]{4}-[0-9]{6}$" and \
           product_schema.get('quota_over_days') == 1 and \
           product_schema.get('sf_api') == "" and \
           product_schema.get('sf_job_cron') == "* 6-18 * * 1-5" and \
           product_schema.get('sf_job_timezone') == "US/Pacific" and \
           product_schema.get('sf_job_query_interval') == 1 and \
           product_schema.get('productname') == "P1" and \
           product_schema.get('sf_enabled') == True and \
           product_schema.get('sf_product_series') == "PS1" and \
           product_schema.get('sf_platform') == "PL1" and \
           product_schema.get('sf_mist_product') == "M1" and \
           product_schema.get('sf_init_email_name') == ""

# Edit every editable field and validate
def test_2_edit_product(client):
    initialize_product(client)
    initialize_salesforce_email_create(client)
    edit_product_data = '''{
  "strategy": "s2",
  "max_days": "4",
  "max_days_month": "400",
  "case_regex": "^[A-Z]{4}-[0-9]{4}-[0-9]{4}-[0-9]{6}$",
  "quota_over_days": 2,
  "sf_api": "http://xyz.com",
  "sf_job_cron": "* 6-18 * * 1-4",
  "sf_job_timezone": "US/Eastern",
  "sf_job_query_interval": 2,
  "productname": "P2",
  "sf_enabled": false,
  "sf_product_series": "PS2",
  "sf_platform": "PL2",
  "sf_init_email_name": "email1",
  "sf_mist_product": "M2"
}'''
    edit_product_response = client.post("/api/product/P1", data=edit_product_data, auth=("admin", "admin"))
    get_product_response = client.get("/api/product/P1", auth=("admin", "admin"))
    product_schema = get_product_response.json
    assert product_schema.get('strategy') == "s2" and \
           product_schema.get('max_days') == 4 and \
           product_schema.get('max_days_month') == 400 and \
           product_schema.get('case_regex') == "^[A-Z]{4}-[0-9]{4}-[0-9]{4}-[0-9]{6}$" and \
           product_schema.get('quota_over_days') == 2 and \
           product_schema.get('sf_api') == "http://xyz.com" and \
           product_schema.get('sf_job_cron') == "* 6-18 * * 1-4" and \
           product_schema.get('sf_job_timezone') == "US/Eastern" and \
           product_schema.get('sf_job_query_interval') == 2 and \
           product_schema.get('productname') == "P1" and \
           product_schema.get('sf_enabled') == False and \
           product_schema.get('sf_product_series') == "PS2" and \
           product_schema.get('sf_platform') == "PL2" and \
           product_schema.get('sf_mist_product') == "M2" and \
           product_schema.get('sf_init_email_name') == "email1"
    
def test_3_delete_product(client):
    initialize_product(client)
    delete_product_response = client.delete("/api/product/P1", auth=("admin", "admin"))
    get_product_response = client.get("/api/product/P1", auth=("admin", "admin"))
    get_product_response.status_code == 404

def test_4_schedule_sf_integration(client):
    initialize_product(client)
    data = '''{
  "datetime": "2025/10/19 13:12",
  "timezone": "US/Pacific",
  "sf_enabled": true
}'''
    schedule_sf_integration_response = client.post("/api/product/schedule-sf-integration/P1", data=data, auth=("admin", "admin"))
    get_jobs_response = client.get("/api/jobs/1", auth=("admin", "admin"))
    assert get_jobs_response.json[0]['job_id'] == schedule_sf_integration_response.json
    assert get_jobs_response.json[0]['status'] == "Scheduled"

def test_5_delete_product_job(client):
    initialize_product(client)
    data = '''{
  "datetime": "2025/10/19 13:12",
  "timezone": "US/Pacific",
  "sf_enabled": true
}'''
    create_job_response = client.post("/api/product/schedule-sf-integration/P1", data=data, auth=("admin", "admin"))
    delete_product_job_response = client.delete(f"/api/product/delete-job/{create_job_response.json}", auth=("admin", "admin"))
    assert create_job_response.json not in delete_product_job_response.json