import json

def initialize_salesforce_email_create(client):
    email_data = '''{
    "email_name": "email1",
    "email_body": "This is a test email body",
    "email_subject": "Test Subject"
}'''
    return client.post("/api/add-salesforce-email", data=email_data, auth=("admin", "admin"))

def test_1_login_success(client):
    data = '{"username": "admin", "password": "admin"}'
    response = client.post("/api/login", data=data)
    assert response.status_code == 200
    assert response.content_type == "application/json"

def test_2_login_401(client):
    data = '{"username": "admin", "password": "admin1"}'
    response = client.post("/api/login", data=data)
    assert response.status_code == 401

# no password
def test_3_login_400(client):
    data = '{"username": "admin"}'
    response = client.post("/api/login", data=data)
    assert response.status_code == 400

# no username
def test_4_login_400(client):
    data = '{"password": "admin1"}'
    response = client.post("/api/login", data=data)
    assert response.status_code == 400

def test_5_get_users(client):
    response = client.get("/api/users", auth=("admin", "admin"))
    assert response.status_code == 200
    assert response.content_type == "application/json"

# make sure scheduler and admin user exists at boot
def test_6_count_users(client):
    response = client.get("/api/users", auth=("admin", "admin"))
    assert len(json.loads(response.data)) == 2

def test_7_get_user(client):
    response = client.get("/api/user/admin", auth=("admin", "admin"))
    assert response.status_code == 200
    assert response.content_type == "application/json"

def test_8_get_user_404(client):
    response = client.get("/api/user/admin1", auth=("admin", "admin"))
    assert response.status_code == 404

def test_9_add_user(client):
    data = '''{
  "email": "abc@efg.com",
  "teamname": "global",
  "active": true,
  "admin": true,
  "shift_start": "09:00:00",
  "shift_end": "18:00:00",
  "timezone": "US/Pacific",
  "username": "test_user",
  "password": "string"
}'''
    response = client.post("/api/user", data=data, auth=("admin", "admin"))
    assert response.status_code == 200
    assert response.content_type == "application/json"

# user doesnt exists
def test_10_add_user_404(client):
    data = '''{
  "email": "abc@efg.com",
  "teamname": "global1",
  "active": true,
  "admin": true,
  "shift_start": "09:00:00",
  "shift_end": "18:00:00",
  "timezone": "US/Pacific",
  "username": "test_user",
  "password": "string"
}'''
    response = client.post("/api/user", data=data, auth=("admin", "admin"))
    assert response.status_code == 404

# no username provided
def test_11_add_user_400(client):
    data = '''{
  "email": "abc@efg.com",
  "teamname": "global",
  "active": true,
  "admin": true,
  "shift_start": "09:00:00",
  "shift_end": "18:00:00",
  "timezone": "US/Pacific",
  "password": "string"
}'''
    response = client.post("/api/user", data=data, auth=("admin", "admin"))
    assert response.status_code == 400

def test_12_update_user(client):
    data = '{"email": "abc@efg.com"}'
    response = client.post("/api/user/admin", data=data, auth=("admin", "admin"))
    assert response.status_code == 200
    assert response.content_type == "application/json"

# invalid credentials
def test_13_update_user_401(client):
    data = '{"email": "abc@efg.com"}'
    response = client.post("/api/user/admin", data=data, auth=("admin", "admin1"))
    assert response.status_code == 401

def test_14_change_password(client):
    data = '''{
  "current_password": "admin",
  "new_password": "admin123"
}'''
    response = client.post("/api/user/change-password/admin", data=data, auth=("admin", "admin"))
    assert response.status_code == 200
    assert response.content_type == "application/json"

def test_15_change_password_401(client):
    data = '''{
  "current_password": "admin",
  "new_password": "admin123"
}'''
    response = client.post("/api/user/change-password/admin", data=data, auth=("admin", "admin1"))
    assert response.status_code == 401

def test_16_change_password_404(client):
    data = '''{
  "current_password": "admin",
  "new_password": "admin123"
}'''
    response = client.post("/api/user/change-password/admin1", data=data, auth=("admin", "admin"))
    assert response.status_code == 404

def test_17_delete_user(client):
    data = '''{
  "email": "abc@efg.com",
  "teamname": "global",
  "active": true,
  "admin": true,
  "shift_start": "09:00:00",
  "shift_end": "18:00:00",
  "timezone": "US/Pacific",
  "username": "test_user",
  "password": "string"
}'''
    create_response = client.post("/api/user", data=data, auth=("admin", "admin"))
    delete_response = client.delete("/api/user/test_user", auth=("admin", "admin"))
    assert delete_response.status_code == 200
    assert delete_response.content_type == "application/json"

# User doesnt exist
def test_18_delete_user_1_401(client):
    data = '''{
  "email": "abc@efg.com",
  "teamname": "global",
  "active": true,
  "admin": true,
  "shift_start": "09:00:00",
  "shift_end": "18:00:00",
  "timezone": "US/Pacific",
  "username": "test_user",
  "password": "string"
}'''
    create_response = client.post("/api/user", data=data, auth=("admin", "admin"))
    delete_response = client.delete("/api/user/test_user1", auth=("admin", "admin"))
    assert delete_response.status_code == 401

# User exists, but invalid credentials
def test_19_delete_user_2_401(client):
    data = '''{
  "email": "abc@efg.com",
  "teamname": "global",
  "active": true,
  "admin": true,
  "shift_start": "09:00:00",
  "shift_end": "18:00:00",
  "timezone": "US/Pacific",
  "username": "test_user",
  "password": "string"
}'''
    create_response = client.post("/api/user", data=data, auth=("admin", "admin"))
    delete_response = client.delete("/api/user/test_user1", auth=("admin", "admin1"))
    assert delete_response.status_code == 401

def test_20_reset_password(client):
    data = '''{
  "email": "abc@efg.com",
  "teamname": "global",
  "active": true,
  "admin": true,
  "shift_start": "09:00:00",
  "shift_end": "18:00:00",
  "timezone": "US/Pacific",
  "username": "test_user",
  "password": "string"
}'''
    create_response = client.post("/api/user", data=data, auth=("admin", "admin"))
    reset_password_response = client.post("/api/user/reset-password/abc@efg.com")
    assert reset_password_response.status_code == 200
    assert reset_password_response.content_type == "application/json"

def test_21_reset_password_404(client):
    reset_password_response = client.post("/api/user/reset-password/abc@efg.com")
    assert reset_password_response.status_code == 404

def test_22_schedule_shift_change(client):
    user_data = '''{
  "email": "abc@efg.com",
  "teamname": "global",
  "active": true,
  "admin": true,
  "shift_start": "09:00:00",
  "shift_end": "18:00:00",
  "timezone": "US/Pacific",
  "username": "test_user",
  "password": "string"
}'''
    create_response = client.post("/api/user", data=user_data, auth=("admin", "admin"))
    # schedule_datetime = (datetime.now(pytz.timezone('US/Pacific')) + timedelta(hours=1)).strftime('%Y/%m/%d %H:%M')
    shift_change_data = '''{
  "datetime": "2030/10/19 13:12",
  "timezone": "US/Pacific",
  "shift_start": "09:00:00",
  "shift_end": "18:00:00"
}'''
    schedule_shift_change_response = client.post("/api/user/schedule-shift-change/test_user", auth=("admin", "admin"), data=shift_change_data)
    assert schedule_shift_change_response.status_code == 200

def test_23_schedule_shift_change_400(client):
    user_data = '''{
  "email": "abc@efg.com",
  "teamname": "global",
  "active": true,
  "admin": true,
  "shift_start": "09:00:00",
  "shift_end": "18:00:00",
  "timezone": "US/Pacific",
  "username": "test_user",
  "password": "string"
}'''
    create_response = client.post("/api/user", data=user_data, auth=("admin", "admin"))
    # schedule_datetime = (datetime.now(pytz.timezone('US/Pacific')) + timedelta(hours=1)).strftime('%Y/%m/%d %H:%M')
    shift_change_data = '''{
  "timezone": "US/Pacific",
  "shift_start": "09:00:00",
  "shift_end": "18:00:00"
}'''
    schedule_shift_change_response = client.post("/api/user/schedule-shift-change/test_user", auth=("admin", "admin"), data=shift_change_data)
    assert schedule_shift_change_response.status_code == 400

def test_24_schedule_reactivate_user(client):
    user_data = '''{
  "email": "abc@efg.com",
  "teamname": "global",
  "active": true,
  "admin": true,
  "shift_start": "09:00:00",
  "shift_end": "18:00:00",
  "timezone": "US/Pacific",
  "username": "test_user",
  "password": "string"
}'''
    create_response = client.post("/api/user", data=user_data, auth=("admin", "admin"))
    # schedule_datetime = (datetime.now(pytz.timezone('US/Pacific')) + timedelta(hours=1)).strftime('%Y/%m/%d %H:%M')
    reactivate_data = '''{
  "datetime": "2030/10/19 13:12",
  "timezone": "US/Pacific",
  "active": true
}'''
    reactivate_user_response = client.post("/api/user/reactivate/test_user", auth=("admin", "admin"), data=reactivate_data)
    assert reactivate_user_response.status_code == 200

def test_25_schedule_reactivate_user_400(client):
    user_data = '''{
  "email": "abc@efg.com",
  "teamname": "global",
  "active": true,
  "admin": true,
  "shift_start": "09:00:00",
  "shift_end": "18:00:00",
  "timezone": "US/Pacific",
  "username": "test_user",
  "password": "string"
}'''
    create_response = client.post("/api/user", data=user_data, auth=("admin", "admin"))
    # schedule_datetime = (datetime.now(pytz.timezone('US/Pacific')) + timedelta(hours=1)).strftime('%Y/%m/%d %H:%M')
    reactivate_data = '''{
  "timezone": "US/Pacific",
  "active": true
}'''
    reactivate_user_response = client.post("/api/user/reactivate/test_user", auth=("admin", "admin"), data=reactivate_data)
    assert reactivate_user_response.status_code == 400

def test_26_get_jobs(client):
    response = client.get("/api/jobs/1", auth=("admin", "admin"))
    assert response.status_code == 200
    assert response.content_type == "application/json"

# Invalid credentials
def test_27_get_jobs_401(client):
    response = client.get("/api/jobs/1", auth=("admin", "admin1"))
    assert response.status_code == 401

# Not found
def test_28_get_jobs_404(client):
    response = client.get("/api/jobs/4", auth=("admin", "admin"))
    assert response.status_code == 404

# Use admin user here instead. If test_user is used it coincides with the job created in test_24_schedule_reactivate_user
def test_29_delete_job(client):
    # schedule_datetime = (datetime.now(pytz.timezone('US/Pacific')) + timedelta(hours=1)).strftime('%Y/%m/%d %H:%M')
    reactivate_data = '''{
  "datetime": "2030/10/19 13:12",
  "timezone": "US/Pacific",
  "active": true
}'''
    reactivate_user_response = client.post("/api/user/reactivate/admin", auth=("admin", "admin"), data=reactivate_data)
    assert reactivate_user_response.status_code == 200
    delete_job_response = client.delete("/api/delete-job/activate_user_admin", auth=("admin", "admin"))
    assert delete_job_response.status_code == 200

# use admin user and deactivate the job. Any job created in previous test cases persists test cases when test cases are run together but 
# if run individually then we dont see any persistent data from previous test cases
def test_30_delete_job_404(client):
    delete_job_response = client.delete("/api/delete-job/deactivate_user_admin", auth=("admin", "admin"))
    assert delete_job_response.status_code == 404

def test_31_add_salesforce_email(client):
    email_data = '''{
    "email_name": "email1",
    "email_body": "This is a test email body",
    "email_subject": "Test Subject"
}'''
    response = client.post("/api/add-salesforce-email", data=email_data, auth=("admin", "admin"))
    assert response.status_code == 200
    assert response.content_type == "application/json"

def test_32_add_salesforce_email_401(client):
    email_data = '''{
    "email_name": "email1",
    "email_body": "This is a test email body",
    "email_subject": "Test Subject"
}'''
    response = client.post("/api/add-salesforce-email", data=email_data)
    assert response.status_code == 401
    assert response.content_type == "application/json"

# No email name provided
def test_33_add_salesforce_email_400(client):
    email_data = '''{
    "email_body": "This is a test email body",
    "email_subject": "Test Subject"
}'''
    response = client.post("/api/add-salesforce-email", data=email_data, auth=("admin", "admin"))
    assert response.status_code == 400

def test_34_get_salesforce_emails(client):
    initialize_salesforce_email_create(client)
    response = client.get("/api/salesforce-emails", auth=("admin", "admin"))
    assert response.status_code == 200
    assert response.content_type == "application/json"

# Invalid credentials
def test_35_get_salesforce_emails_401(client):
    response = client.get("/api/salesforce-emails", auth=("admin", "admin1"))
    assert response.status_code == 401

def test_36_get_salesforce_email(client):
    initialize_salesforce_email_create(client)
    response = client.get("/api/salesforce-email/email1", auth=("admin", "admin"))
    assert response.status_code == 200
    assert response.content_type == "application/json"

# Invalid credentials
def test_37_get_salesforce_email_401(client):
    response = client.get("/api/salesforce-emails", auth=("admin", "admin1"))
    assert response.status_code == 401

def test_38_update_salesforce_email(client):
    initialize_salesforce_email_create(client)
    email_data = '''{
    "email_subject": "Test Subject 2"
}'''
    response = client.post("/api/salesforce-email/email1", data=email_data, auth=("admin", "admin"))
    assert response.status_code == 200
    assert response.content_type == "application/json"

# No user password 
def test_39_update_salesforce_email_1_401(client):
    email_data = '''{
    "email_subject": "Test Subject 2"
}'''
    response = client.post("/api/salesforce-email/email1", data=email_data)
    assert response.status_code == 401
    assert response.content_type == "application/json"

# No email object found
def test_40_update_salesforce_email_2_401(client):
    email_data = '''{
    "email_subject": "Test Subject 2"
}'''
    response = client.post("/api/salesforce-email/email1", data=email_data, auth=("admin", "admin"))
    assert response.status_code == 401

def test_41_delete_salesforce_email(client):
    initialize_salesforce_email_create(client)
    response = client.delete("/api/salesforce-email/email1", auth=("admin", "admin"))
    assert response.status_code == 200
    assert response.content_type == "application/json"

# No user password 
def test_42_delete_salesforce_email_401(client):
    initialize_salesforce_email_create(client)
    response = client.delete("/api/salesforce-email/email1")
    assert response.status_code == 401

# No email object found
def test_43_delete_salesforce_email_404(client):
    response = client.delete("/api/salesforce-email/email1", auth=("admin", "admin"))
    assert response.status_code == 404

# Get j2 variables, success
def test_44_get_jinja2_variables(client):
    initialize_salesforce_email_create(client)
    response = client.get("/api/jinja2_variables", auth=("admin", "admin"))
    assert response.status_code == 200
    assert response.content_type == "application/json"

# Invalid credentials
def test_45_get_jinja2_variables_401(client):
    response = client.get("/api/jinja2_variables", auth=("admin", "admin1"))
    assert response.status_code == 401

# Success
def test_46_schedule_handoffs(client):
    user_data = '''{
  "email": "abc@efg.com",
  "teamname": "global",
  "active": true,
  "admin": true,
  "shift_start": "09:00:00",
  "shift_end": "18:00:00",
  "timezone": "US/Pacific",
  "username": "test_user",
  "password": "string"
}'''
    create_response = client.post("/api/user", data=user_data, auth=("admin", "admin"))
    # schedule_datetime = (datetime.now(pytz.timezone('US/Pacific')) + timedelta(hours=1)).strftime('%Y/%m/%d %H:%M')
    handoffs_data = '''{
  "datetime": "2030/10/19 13:12",
  "timezone": "US/Pacific"
}'''
    schedule_handoffs_response = client.post("/api/user/schedule-handoffs/test_user", auth=("admin", "admin"), data=handoffs_data)
    assert schedule_handoffs_response.status_code == 200

# Invalid input, no timezone provided
def test_47_schedule_handoffs_400(client):
    user_data = '''{
  "email": "abc@efg.com",
  "teamname": "global",
  "active": true,
  "admin": true,
  "shift_start": "09:00:00",
  "shift_end": "18:00:00",
  "timezone": "US/Pacific",
  "username": "test_user",
  "password": "string"
}'''
    create_response = client.post("/api/user", data=user_data, auth=("admin", "admin"))
    # schedule_datetime = (datetime.now(pytz.timezone('US/Pacific')) + timedelta(hours=1)).strftime('%Y/%m/%d %H:%M')
    handoffs_data = '''{
  "datetime": "2030/10/19 13:12"
}'''
    schedule_handoffs_response = client.post("/api/user/schedule-handoffs/test_user", auth=("admin", "admin"), data=handoffs_data)
    assert schedule_handoffs_response.status_code == 400
