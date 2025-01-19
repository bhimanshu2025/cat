import json

def initialize_salesforce_email_create(client):
    email_data = '''{
    "email_name": "email1",
    "email_body": "This is a test email body",
    "email_subject": "Test Subject"
}'''
    return client.post("/api/add-salesforce-email", data=email_data, auth=("admin", "admin"))

def login(client, username="admin", password="admin"):
    return client.post("/login", data={"username": username, "password": password}, follow_redirects=True)

def logout(client):
    return client.get("/logout", follow_redirects=True)

def initialize_team(client):
    login(client)
    add_team_data = {
        'teamname': "T1",
        'email': "T1@abc.xyz",
        'mswebhook': ""
    }
    return client.post("/add_team", data=add_team_data, follow_redirects=True)

def initialize_product(client):
    login(client)
    add_product_data = {
            'productname': "P1",
            'strategy': "s1",
            'case_regex': "^[0-9]{4}-[0-9]{4}-[0-9]{6}$",
            'max_days_month': 300,
            'max_days': 7,
            'quota_over_days': 1,
            'sf_job_cron': "",
            'sf_job_timezone': "",
            'sf_api': "",
            'sf_job_query_interval': 1,
            'sf_product_series': "",
            'sf_platform': "",
            "sf_init_email_name": ""
        }
    return client.post("/add_product", data=add_product_data, follow_redirects=True)

def initialize_user(client):
    add_user_data = {
        "email": "abc@efg.com",
        "teamname": "T1",
        "active": True,
        "admin": True,
        "shift_start": "12:00:00",
        "shift_end": "18:00:00",
        "timezone": "US/Pacific",
        "username": "test_user",
        "password": "password",
        "confirm_password": "password"
        }
    return client.post("/add_user", data=add_user_data, follow_redirects=True)

def initialize_userproduct(client, active=True):
    logout(client)
    login(client, username='test_user', password='password')
    if active:
        add_userproduct_data = '''{
        "productname": "P1",
        "username": "test_user",
        "active": "true",
        "quota": 1
    }'''
    else:
        add_userproduct_data = '''{
        "productname": "P1",
        "username": "test_user",
        "active": "false",
        "quota": 1
    }'''
    return client.post("/add_user_product", data=json.loads(add_userproduct_data), follow_redirects=True)

def initialize_assign_case(client):
    initialize_all(client)
    case_data = '''{
        "caseid": "2023-0395-203840",
        "product": "P1",
        "comments": "Test",
        "priority": "P2",
        "mode": "auto",
        "check_in_shift": "false"
}'''
    logout(client)
    login(client, username='test_user', password='password')
    return client.post("/", data=json.loads(case_data), follow_redirects=True)

def initialize_salesfoce_email(client):
    initialize_team(client)
    initialize_user(client)
    logout(client)
    login(client, username='test_user', password='password')
    add_sf_email_data = '''{
            "email_name": "email1",
            "email_body": "This is a test email body",
            "email_subject": "This is a test subject"
        }'''
    return client.post("/add_salesforce_email", data=json.loads(add_sf_email_data), follow_redirects=True)

def initialize_all(client):
    initialize_team(client)
    initialize_user(client)
    initialize_product(client)
    initialize_userproduct(client)

def test_1_add_user(client):
    initialize_team(client)
    data = '''{
  "email": "abc@efg.com",
  "teamname": "T1",
  "active": true,
  "admin": true,
  "shift_start": "09:00:00",
  "shift_end": "18:00:00",
  "timezone": "US/Pacific",
  "username": "test_user",
  "password": "string"
}'''
    client.post("/api/user", data=data, auth=("admin", "admin"))
    response = client.get("/api/user/test_user", auth=("admin", "admin"))
    assert response.json.get('username') == "test_user"

# Every possible modifiable field is changed, not able to test with   "timezone": "US\Eastern" as json string fails
# to parse the backslash. If i try to have double backslash it passes the double backslahed value to pytz and then pytz fails
def test_2_edit_user(client):
    initialize_all(client)
    users_old_schema = client.get("/api/user/test_user", auth=("admin", "admin")).json
    data = '''{
  "email": "cde@juniper.net",
  "teamname": "Global",
  "active": false,
  "shift_start": "09:00:01",
  "shift_end": "18:00:01",
  "admin": false,
  "first_name": "Tom",
  "last_name": "Kumar",
  "team_email_notifications": true,
  "monitor_case_updates": true
}'''
    response = client.post("/api/user/test_user", data=data, auth=("admin", "admin"))
    users_new_schema = client.get("/api/user/test_user", auth=("admin", "admin")).json
    assert users_new_schema.get('email') != users_old_schema.get('email') and \
            users_new_schema.get('active') != users_old_schema.get('active') and \
            users_new_schema.get('shift_start') != users_old_schema.get('shift_start') and \
            users_new_schema.get('shift_end') != users_old_schema.get('shift_end') and \
            users_new_schema.get('admin') != users_old_schema.get('admin') and \
            users_new_schema.get('first_name') != users_old_schema.get('first_name') and \
            users_new_schema.get('last_name') != users_old_schema.get('last_name') and \
            users_new_schema.get('team_email_notifications') != users_old_schema.get('team_email_notifications') and \
            users_new_schema.get('monitor_case_updates') != users_old_schema.get('monitor_case_updates') and \
            users_new_schema.get('teamname') != users_old_schema.get('teamname')
    
def test_3_delete_user(client):
    initialize_team(client)
    initialize_user(client)
    delete_response = client.delete("/api/user/test_user", auth=("admin", "admin"))
    get_user_response = client.get("/api/user/test_user", auth=("admin", "admin"))
    assert get_user_response.status_code == 404

def test_4_change_password(client):
    data = '''{
  "current_password": "admin",
  "new_password": "admin123"
}'''
    change_password_response = client.post("/api/user/change-password/admin", data=data, auth=("admin", "admin"))
    get_user_response_200 = client.get("/api/user/admin", auth=("admin", "admin123"))
    get_user_response_401 = client.get("/api/user/admin", auth=("admin", "admin"))
    assert get_user_response_200.status_code == 200
    assert get_user_response_401.status_code == 401

# reset password and the next login should fail with old pwd
def test_5_reset_password(client):
    initialize_team(client)
    initialize_user(client)
    reset_password_response = client.post("/api/user/reset-password/abc@efg.com")
    get_user_response_401 = client.get("/api/user/test_user", auth=("test_user", "password"))
    assert get_user_response_401.status_code == 401

def test_6_reactivate_user(client):
    initialize_team(client)
    initialize_user(client)
    reactivate_data = '''{
    "datetime": "2030/10/19 13:12",
    "timezone": "US/Pacific",
    "active": true
    }'''
    reactivate_user_response = client.post("/api/user/reactivate/admin", auth=("admin", "admin"), data=reactivate_data)
    get_jobs_response = client.get("/api/jobs/1", auth=("admin", "admin"))
    # assert "activate_user_test_user" == get_jobs_response.json[0]['job_id']
    assert b"activate_user_admin" == bytes(get_jobs_response.json[0]['job_id'], encoding='utf-8')

def test_7_schedule_shift_change(client):
    initialize_team(client)
    initialize_user(client)
    shift_change_data = '''{
    "datetime": "2030/10/19 13:12",
    "timezone": "US/Pacific",
    "shift_start": "09:00:00",
    "shift_end": "18:00:00"
}'''
    schedule_shift_change_response = client.post("/api/user/schedule-shift-change/test_user", auth=("admin", "admin"), data=shift_change_data)
    get_jobs_response = client.get("/api/jobs/1", auth=("admin", "admin"))
    assert bytes(get_jobs_response.json[0]['job_id'], encoding='utf-8') == schedule_shift_change_response.data
    assert get_jobs_response.json[0]['status'] == "Scheduled"

# I ran into the issue once again where data from one of previous test persisted. In this case it was a job to activate admin user
# already existed. Need to research on this more to run each test case with a clean db without any data persisting across tests.
def test_8_delete_job(client):
    initialize_team(client)
    initialize_user(client)
    reactivate_data = '''{
    "datetime": "2030/10/19 13:12",
    "timezone": "US/Pacific",
    "active": false
    }'''
    reactivate_user_response = client.post("/api/user/reactivate/admin", auth=("admin", "admin"), data=reactivate_data)
    delete_job_response = client.delete("/api/delete-job/deactivate_user_admin", auth=("admin", "admin"))
    get_job_response = client.get("/api/job/deactivate_user_admin", auth=("admin", "admin"))
    assert get_job_response.json['status'] == "Deleted"

def test_9_add_salesforce_email(client):
    email_data = {
    "id": 1,
    "user": "admin",
    "email_name": "email1",
    "email_body": "This is a test email body",
    "email_subject": "Test Subject"
}
    initialize_salesforce_email_create(client)
    response = client.get("/api/salesforce-email/email1", auth=("admin", "admin"))
    assert response.json == email_data

# Edit every possible field to test update object
def test_10_edit_salesforce_email(client):
    updated_email_data = {
    "id": 1,
    "user": "admin",
    "email_name": "email1",
    "email_body": "This is updated test email body",
    "email_subject": "Test Subject updated"
}
    initialize_salesforce_email_create(client)
    update_email_data = '''{
    "email_body": "This is updated test email body",
    "email_subject": "Test Subject updated"
}'''
    update_email_response = client.post("/api/salesforce-email/email1", data=update_email_data, auth=("admin", "admin"))
    get_email_response = client.get("/api/salesforce-email/email1", auth=("admin", "admin"))
    assert get_email_response.json == updated_email_data

def test_11_delete_salesforce_email(client):
    initialize_salesforce_email_create(client)
    delete_response = client.delete("/api/salesforce-email/email1", auth=("admin", "admin"))
    get_email_response = client.get("/api/salesforce-email/email1", auth=("admin", "admin"))
    assert get_email_response.status_code == 404

def test_12_schedule_handoffs(client):
    initialize_team(client)
    initialize_user(client)
    shift_change_data = '''{
    "datetime": "2030/10/19 13:12",
    "timezone": "US/Pacific",
    "check_in_shift": false
}'''
    schedule_handoffs_response = client.post("/api/user/schedule-handoffs/test_user", auth=("admin", "admin"), data=shift_change_data)
    get_jobs_response = client.get("/api/jobs/1", auth=("admin", "admin"))
    assert bytes(get_jobs_response.json[0]['job_id'], encoding='utf-8') == schedule_handoffs_response.data
    assert get_jobs_response.json[0]['status'] == "Scheduled"