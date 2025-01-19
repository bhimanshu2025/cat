import json

# Note: any boolean variable passed into form data returns true irrespective of the value passed through the client. The w/a is to use json.loads
# I had to do it in below test cases as check_in_shift always was returning True.

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
        "sf_mist_product": "",
        'sf_platform': "",
        "sf_init_email_name": "---"
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

def test_1_login_get(client):
    get_login_response = client.get("/login", follow_redirects=True)
    assert b"<title> CAT Login</title>" in get_login_response.data

def test_2_login_post(client):
    post_login_response = client.post("/login", data={"username": "admin", "password": "admin"}, follow_redirects=True)
    assert b"<title> CAT Home</title>" in post_login_response.data

# Incorrect login
def test_3_login_post_401(client):
    post_login_response = client.post("/login", data={"username": "admin", "password": "admin1"}, follow_redirects=True)
    assert b"Login Failed" in post_login_response.data

def test_4_logout(client):
    login(client)
    logout_response = client.get("/logout", follow_redirects=True)
    assert b"<title> CAT Login</title>" in logout_response.data

def test_5_users_get(client):
    login(client)
    get_users_response = client.get("/users", follow_redirects=True)
    assert b"<title> CAT Users</title>" in get_users_response.data

def test_6_users_get_401(client):
    get_users_response = client.get("/users", follow_redirects=True)
    assert get_users_response.status_code == 401

def test_7_add_user_get(client):
    add_user_response = client.get("/add_user", follow_redirects=True)
    assert b"<title> CAT Register User</title>" in add_user_response.data

# Add user, when no user logged in
def test_9_add_user_1_post(client):
    initialize_team(client)
    logout(client)
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
    add_user_response = client.post("/add_user", data=add_user_data, follow_redirects=True)
    print(add_user_response.data)
    assert b"Account created for user test_user" in add_user_response.data

# Add user, when user logged in
def test_10_add_user_2_post(client):
    initialize_team(client)
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
    add_user_response = client.post("/add_user", data=add_user_data, follow_redirects=True)
    print(add_user_response.data)
    assert b"Account created for user test_user" in add_user_response.data

def test_11_edit_user_get(client):
    initialize_all(client)
    edit_users_response = client.get("/edit_user/test_user", follow_redirects=True)
    assert b"<title> CAT Edit User</title>" in edit_users_response.data

def test_12_edit_user_get_401(client):
    edit_users_response = client.get("/edit_user/test_user", follow_redirects=True)
    assert edit_users_response.status_code == 401

# update email, success. Note: if teamname wasnt provided, form failed to validate
def test_13_edit_user_post(client):
    initialize_all(client)
    edit_user_data = {
        "email": "cde@efg.com",
        "teamname": "T1"
        }
    edit_users_response = client.post("/edit_user/test_user", data=edit_user_data, follow_redirects=True)
    assert b"User test_user updated" in edit_users_response.data

# auth failure
def test_14_edit_user_post_1_401(client):
    edit_user_data = {
        "email": "cde@efg.com",
        "teamname": "T1"
        }
    edit_users_response = client.post("/edit_user/test_user", data=edit_user_data, follow_redirects=True)
    assert edit_users_response.status_code == 401

# auth failure, editing other teams user
def test_15_edit_user_post_2_401(client):
    initialize_all(client)
    edit_user_data = {
        "email": "cde@efg.com",
        "teamname": "global"
        }
    logout(client)
    login(client, username="test_user", password="password")
    edit_users_response = client.post("/edit_user/admin", data=edit_user_data, follow_redirects=True)
    assert b"Unauthorized Access" in edit_users_response.data

# Get request for account page
def test_16_account_get(client):
    login(client)
    account_response = client.get("/account", follow_redirects=True)
    assert b"<title> CAT Account</title>" in account_response.data

# get request for account page, auth failure
def test_17_account_get_401(client):
    account_response = client.get("/account", follow_redirects=True)
    assert account_response.status_code == 401

# update email, success.
def test_18_account_post(client):
    initialize_all(client)
    account_data = {
        "email": "cde@efg.com"
        }
    logout(client)
    login(client, username="test_user", password="password")
    account_response = client.post("/account", data=account_data, follow_redirects=True)
    assert b"User test_user updated" in account_response.data

# auth failure
def test_19_edit_user_post_401(client):
    initialize_all(client)
    account_data = {
        "email": "cde@efg.com"
        }
    logout(client)
    account_response = client.post("/account", data=account_data, follow_redirects=True)
    assert account_response.status_code == 401

# Get request for change password page
def test_20_change_password_get(client):
    login(client)
    change_password_response = client.get("/change_password", follow_redirects=True)
    assert b"<title> CAT Change Password</title>" in change_password_response.data

# Get request for change password page, auth failure
def test_21_change_password_get_401(client):
    account_response = client.get("/change_password", follow_redirects=True)
    assert account_response.status_code == 401

# update password, success.
def test_22_change_password_post(client):
    initialize_all(client)
    password_data = {
            'new_password': "new_pass",
            'current_password': "password",
            'confirm_new_password': "new_pass"
        }
    logout(client)
    login(client, username="test_user", password="password")
    change_password_response = client.post("/change_password", data=password_data, follow_redirects=True)
    assert b"User test_user password changed" in change_password_response.data

# auth failure
def test_23_change_password_post_1_401(client):
    initialize_all(client)
    password_data = {
            'new_password': "new_pass",
            'current_password': "password",
            'confirm_new_password': "new_pass"
        }
    logout(client)
    account_data = {
        "email": "cde@efg.com"
        }
    logout(client)
    change_password_response = client.post("/change_password", data=password_data, follow_redirects=True)
    assert change_password_response.status_code == 401

# auth failure, incorrect current password
def test_24_change_password_post_2_401(client):
    initialize_all(client)
    password_data = {
            'new_password': "new_pass",
            'current_password': "password1",
            'confirm_new_password': "new_pass"
        }
    logout(client)
    account_data = {
        "email": "cde@efg.com"
        }
    logout(client)
    login(client, username="test_user", password="password")
    change_password_response = client.post("/change_password", data=password_data, follow_redirects=True)
    assert b"Invalid Password" in change_password_response.data
    
# Get request for reset password page
def test_25_reset_password_get(client):
    reset_password_response = client.get("/reset_password", follow_redirects=True)
    assert b"<title> CAT Reset Password</title>" in reset_password_response.data

# Post request for reset password page
def test_26_reset_password_post(client):
    initialize_all(client)
    logout(client)
    email_data = {
        "email": "abc@efg.com"
        }
    reset_password_response = client.post("/reset_password", data=email_data, follow_redirects=True)
    assert b"Password reset request submitted. User will recieve an email with temporary password" in reset_password_response.data

# Post request for reset password page, incorrect email
def test_26_reset_password_incorrect_email_post(client):
    email_data = {
        "email": "abcd@efg.com"
        }
    reset_password_response = client.post("/reset_password", data=email_data, follow_redirects=True)
    assert b"User with email abcd@efg.com not found" in reset_password_response.data

# Post request for delete user page, success
def test_27_delete_user_post(client):
    initialize_all(client)
    delete_user_response = client.post("/delete_user/test_user", follow_redirects=True)
    assert b"User test_user deleted" in delete_user_response.data

# Post request for delete user page, auth failure
def test_28_delete_user_post_1_401(client):
    delete_user_response = client.post("/delete_user/test_user", follow_redirects=True)
    assert delete_user_response.status_code == 401

# Post request for delete user page, unauthorized access
def test_29_delete_user_post_2_401(client):
    login(client)
    delete_user_response = client.post("/delete_user/test_user", follow_redirects=True)
    assert b"Unauthorized Access" in delete_user_response.data

# Get request for jobs page
def test_30_jobs_get(client):
    login(client)
    jobs_response = client.get("/jobs", follow_redirects=True)
    assert b"<title> CAT Jobs</title>" in jobs_response.data

# get request for jobs page, auth failure
def test_31_jobs_get_401(client):
    jobs_response = client.get("/jobs", follow_redirects=True)
    assert jobs_response.status_code == 401

# Get request for reactivate user page
def test_32_reactivate_user_get(client):
    login(client)
    reactivate_user_response = client.get("/reactivate_user", follow_redirects=True)
    assert b"<title> CAT Reactivate User</title>" in reactivate_user_response.data

# Get request for reactivate user page, auth failure
def test_33_reactivate_user_get_401(client):
    reactivate_user_response = client.get("/reactivate_user", follow_redirects=True)
    assert reactivate_user_response.status_code == 401

# Post request for reactivate user page, success. Note: json.loads is needed or else the active variable is always evaluated as True
def test_34_reactivate_user_post(client):
    initialize_all(client)
    logout(client)
    login(client, username="test_user", password="password")
    user_data = '''{
            "username": "test_user",
            "datetime": "2030-10-10T12:10",
            "timezone": "US/Pacific",
            "active": "false"
        }'''
    reactivate_user_response = client.post("/reactivate_user", data=json.loads(user_data), follow_redirects=True)
    assert b"Job Submitted" in reactivate_user_response.data

# Post request for reactivate user page, auth failure
def test_35_reactivate_user_post_401(client):
    initialize_all(client)
    logout(client)
    user_data = '''{
            "username": "test_user",
            "datetime": "2030-10-10T12:10",
            "timezone": "US/Pacific",
            "active": "false"
        }'''
    reactivate_user_response = client.post("/reactivate_user", data=json.loads(user_data), follow_redirects=True)
    assert reactivate_user_response.status_code == 401

# Post request for reactivate user page, date provided is a past date
def test_36_reactivate_user_post_1_400(client):
    initialize_all(client)
    logout(client)
    login(client, username="test_user", password="password")
    user_data = '''{
            "username": "test_user",
            "datetime": "2010-10-10T12:10",
            "timezone": "US/Pacific",
            "active": "false"
        }'''
    reactivate_user_response = client.post("/reactivate_user", data=json.loads(user_data), follow_redirects=True)
    assert b"Datetime has to be a time in future" in reactivate_user_response.data

# Post request for reactivate user page, already a job running
def test_37_reactivate_user_post_2_400(client):
    initialize_all(client)
    logout(client)
    login(client, username="test_user", password="password")
    user_data = '''{
            "username": "test_user",
            "datetime": "2030-10-10T12:10",
            "timezone": "US/Pacific",
            "active": "false"
        }'''
    reactivate_user_response1 = client.post("/reactivate_user", data=json.loads(user_data), follow_redirects=True)
    reactivate_user_response2 = client.post("/reactivate_user", data=json.loads(user_data), follow_redirects=True)
    assert b"There is already a job of this type scheduled for user test_user" in reactivate_user_response2.data

# Get request for schedule shift change page
def test_38_schedule_shift_change_get(client):
    login(client)
    schedule_shift_change_response = client.get("/schedule_shift_change", follow_redirects=True)
    assert b"<title> CAT Schedule Shift Change</title>" in schedule_shift_change_response.data

# Get request for reactivate user page, auth failure
def test_39_schedule_shift_change_get_401(client):
    schedule_shift_change_response = client.get("/schedule_shift_change", follow_redirects=True)
    assert schedule_shift_change_response.status_code == 401

# Post request for schedule shift change page, success.
def test_40_schedule_shift_change_post_1(client):
    initialize_all(client)
    logout(client)
    login(client, username="test_user", password="password")
    user_data = '''{
            "username": "test_user",
            "datetime": "2030-10-10T12:10",
            "timezone": "US/Pacific",
            "shift_start": "09:00:00",
            "shift_end": "14:00:00"
        }'''
    schedule_shift_change_response = client.post("/schedule_shift_change", data=json.loads(user_data), follow_redirects=True)
    assert b"Job Submitted" in schedule_shift_change_response.data

# Post request for schedule shift change page, already a job running, success
def test_41_schedule_shift_change_post_2(client):
    initialize_all(client)
    logout(client)
    login(client, username="test_user", password="password")
    user_data1 = '''{
            "username": "test_user",
            "datetime": "2030-10-10T12:10",
            "timezone": "US/Pacific",
            "shift_start": "09:00:00",
            "shift_end": "14:00:00"
        }'''
    user_data2 = '''{
            "username": "test_user",
            "datetime": "2030-11-10T12:10",
            "timezone": "US/Pacific",
            "shift_start": "09:00:00",
            "shift_end": "14:00:00"
        }'''
    schedule_shift_change_response1 = client.post("/schedule_shift_change", data=json.loads(user_data1), follow_redirects=True)
    schedule_shift_change_response2 = client.post("/schedule_shift_change", data=json.loads(user_data2), follow_redirects=True)
    assert b"Job Submitted" in schedule_shift_change_response2.data

# Post request for schedule shift change page, auth failure
def test_42_schedule_shift_change_401(client):
    initialize_all(client)
    logout(client)
    user_data = '''{
            "username": "test_user",
            "datetime": "2030-10-10T12:10",
            "timezone": "US/Pacific",
            "shift_start": "09:00:00",
            "shift_end": "14:00:00"
        }'''
    schedule_shift_change_response = client.post("/schedule_shift_change", data=json.loads(user_data), follow_redirects=True)
    assert schedule_shift_change_response.status_code == 401

# Post request for schedule shift change page, date provided is a past date
def test_43_schedule_shift_change_post_400(client):
    initialize_all(client)
    logout(client)
    login(client, username="test_user", password="password")
    user_data = '''{
            "username": "test_user",
            "datetime": "2010-10-10T12:10",
            "timezone": "US/Pacific",
            "shift_start": "09:00:00",
            "shift_end": "14:00:00"
        }'''
    schedule_shift_change_response = client.post("/schedule_shift_change", data=json.loads(user_data), follow_redirects=True)
    assert b"Datetime has to be a time in future" in schedule_shift_change_response.data

# Post request for deleting a job, success.
def test_44_delete_job_post(client):
    initialize_all(client)
    logout(client)
    login(client, username="test_user", password="password")
    user_data = '''{
            "username": "test_user",
            "datetime": "2030-10-10T12:10",
            "timezone": "US/Pacific",
            "active": "false"
        }'''
    reactivate_user_response = client.post("/reactivate_user", data=json.loads(user_data), follow_redirects=True)
    delete_job_response = client.post("delete_job/deactivate_user_test_user", follow_redirects=True)
    assert b"Job deactivate_user_test_user deleted" in delete_job_response.data

# Post request for deleting a job, job id not found
def test_45_delete_job_post_404(client):
    initialize_all(client)
    logout(client)
    login(client, username="test_user", password="password")
    delete_job_response = client.post("delete_job/deactivate_user_test_user", follow_redirects=True)
    assert b"Job deactivate_user_test_user not found" in delete_job_response.data

# Post request for deleting a job, auth failure
def test_46_delete_job_post_401(client):
    initialize_all(client)
    logout(client)
    delete_job_response = client.post("delete_job/deactivate_user_test_user", follow_redirects=True)
    assert delete_job_response.status_code == 401

# Get request for user product page
def test_47_user_product_get(client):
    login(client)
    user_product_response = client.get("/user_product", follow_redirects=True)
    assert b"<title> CAT User Product</title>" in user_product_response.data

# Get request for user product page, auth failure
def test_48_user_product_get_401(client):
    user_product_response = client.get("/user_product", follow_redirects=True)
    assert user_product_response.status_code == 401

# Get request for add user product page
def test_49_add_user_product_get(client):
    login(client)
    add_user_product_response = client.get("/add_user_product", follow_redirects=True)
    assert b"<title> CAT Add User To Product</title>" in add_user_product_response.data

# Get request for add user product page, auth failure
def test_50_add_user_product_get_401(client):
    add_user_product_response = client.get("/add_user_product", follow_redirects=True)
    assert add_user_product_response.status_code == 401

# Add user to product post request, success. Note: json.loads is needed or else active variable is always evaluated as True
def test_51_add_user_product_post(client):
    initialize_team(client)
    initialize_product(client)
    initialize_user(client)
    logout(client)
    login(client, username='test_user', password='password')
    add_userproduct_data = '''{
        "productname": "P1",
        "username": "test_user",
        "active": "true",
        "quota": 1
    }'''
    add_user_product_response = client.post("/add_user_product", data=json.loads(add_userproduct_data), follow_redirects=True)
    assert b"User test_user supports product P1" in add_user_product_response.data

# Add user to product post request, auth failure
def test_52_add_user_product_post_401(client):
    add_userproduct_data = '''{
        "productname": "P1",
        "username": "test_user",
        "active": "true",
        "quota": 1
    }'''
    add_user_product_response = client.post("/add_user_product", data=json.loads(add_userproduct_data), follow_redirects=True)
    assert add_user_product_response.status_code == 401

# Get request for edit user product page
def test_53_edit_user_product_get(client):
    initialize_all(client)
    logout(client)
    login(client, username='test_user', password='password')
    edit_user_product_response = client.get("/edit_user_product/test_user/P1", follow_redirects=True)
    assert b"<title> CAT Edit User Product</title>" in edit_user_product_response.data

# Get request for edit user product page, auth failure
def test_54_edit_user_product_get_401(client):
    edit_user_product_response = client.get("/edit_user_product/test_user/P1", follow_redirects=True)
    assert edit_user_product_response.status_code == 401

# Edit user to product post request, success. Note: json.loads is needed or else active variable is always evaluated as True
def test_55_edit_user_product_post(client):
    initialize_all(client)
    logout(client)
    login(client, username='test_user', password='password')
    edit_userproduct_data = '''{
        "productname": "P1",
        "username": "test_user",
        "active": "true",
        "quota": 2
    }'''
    edit_user_product_response = client.post("/edit_user_product/test_user/P1", data=json.loads(edit_userproduct_data), follow_redirects=True)
    assert b"User test_user and product P1 association updated" in edit_user_product_response.data

# Edit user to product post request, auth failure
def test_56_edit_user_product_post_1_401(client):
    edit_userproduct_data = '''{
        "productname": "P1",
        "username": "test_user",
        "active": "true",
        "quota": 1
    }'''
    edit_user_product_response = client.post("/edit_user_product/test_user/P1", data=json.loads(edit_userproduct_data), follow_redirects=True)
    assert edit_user_product_response.status_code == 401

# Edit user to product post request, auth failure editing other users association
def test_57_edit_user_product_post_2_401(client):
    initialize_all(client)
    logout(client)
    login(client, username='test_user', password='password')
    edit_userproduct_data = '''{
        "productname": "P1",
        "username": "test_user",
        "active": "true",
        "quota": 1
    }'''
    edit_user_product_response = client.post("/edit_user_product/admin/P1", data=json.loads(edit_userproduct_data), follow_redirects=True)
    assert b"Unauthorized Access" in edit_user_product_response.data

# Post request for deleting a user product association, success
def test_58_delete_user_product_post(client):
    initialize_all(client)
    logout(client)
    login(client, username="test_user", password="password")
    delete_user_product_response = client.post("delete_user_product/test_user/P1", follow_redirects=True)
    assert b"User test_user no longer supports product P1" in delete_user_product_response.data

# Post request for deleting a user product association, auth failure
def test_59_delete_user_product_post_1_401(client):
    delete_user_product_response = client.post("delete_user_product/test_user/P1", follow_redirects=True)
    assert delete_user_product_response.status_code == 401

# Post request for deleting a user product association, auth failure deleting other users association
def test_60_delete_user_product_post_2_401(client):
    initialize_all(client)
    logout(client)
    login(client, username="test_user", password="password")
    delete_user_product_response = client.post("delete_user_product/admin/P1", follow_redirects=True)
    assert b"Unauthorized Access" in delete_user_product_response.data

# Get request for salesforce emails
def test_61_user_product_get(client):
    login(client)
    sf_emails_response = client.get("/salesforce_emails", follow_redirects=True)
    assert b"<title> CAT Salesforce Emails</title>" in sf_emails_response.data

# Get request for salesforce emails, auth failure
def test_62_user_product_get_401(client):
    sf_emails_response = client.get("/salesforce_emails", follow_redirects=True)
    assert sf_emails_response.status_code == 401

# Add salesforce emails, success.
def test_63_add_salesfoce_email_post(client):
    initialize_team(client)
    initialize_user(client)
    logout(client)
    login(client, username='test_user', password='password')
    add_sf_email_data = '''{
            "email_name": "email1",
            "email_body": "This is a test email body",
            "email_subject": "This is a test subject"
        }'''
    add_sf_email_response = client.post("/add_salesforce_email", data=json.loads(add_sf_email_data), follow_redirects=True)
    assert b"Email email1 added" in add_sf_email_response.data

# Add salesforce emails, auth failure.
def test_64_add_salesfoce_email_post_401(client):
    initialize_team(client)
    initialize_user(client)
    logout(client)
    add_sf_email_data = '''{
            "email_name": "email1",
            "email_body": "This is a test email body",
            "email_subject": "This is a test subject"
        }'''
    add_sf_email_response = client.post("/add_salesforce_email", data=json.loads(add_sf_email_data), follow_redirects=True)
    assert add_sf_email_response.status_code == 401

# Add salesforce emails, invalid data, email_name not provided.
def test_65_add_salesfoce_email_post_400(client):
    initialize_team(client)
    initialize_user(client)
    logout(client)
    login(client, username='test_user', password='password')
    add_sf_email_data = '''{
            "email_body": "This is a test email body",
            "email_subject": "This is a test subject"
        }'''
    add_sf_email_response = client.post("/add_salesforce_email", data=json.loads(add_sf_email_data), follow_redirects=True)
    assert b"No name provided for the email template" in add_sf_email_response.data

# Edit salesforce emails, success.
def test_66_edit_salesfoce_email_post(client):
    initialize_salesfoce_email(client)
    logout(client)
    login(client, username='test_user', password='password')
    edit_sf_email_data = '''{
            "email_subject": "This is a test subject 2"
        }'''
    edit_sf_email_response = client.post("/edit_salesforce_email/email1", data=json.loads(edit_sf_email_data), follow_redirects=True)
    assert b"Email template email1 updated" in edit_sf_email_response.data

# Edit salesforce emails, Auth failure.
def test_67_edit_salesfoce_email_post_1_401(client):
    initialize_salesfoce_email(client)
    logout(client)
    edit_sf_email_data = '''{
            "email_subject": "This is a test subject 2"
        }'''
    edit_sf_email_response = client.post("/edit_salesforce_email/email1", data=json.loads(edit_sf_email_data), follow_redirects=True)
    assert edit_sf_email_response.status_code == 401

# Edit salesforce emails, Auth failure for email template not found or it belongs to some other user.
def test_68_edit_salesfoce_email_post_2_401(client):
    initialize_salesfoce_email(client)
    logout(client)
    login(client, username='test_user', password='password')
    edit_sf_email_data = '''{
            "email_subject": "This is a test subject 2"
        }'''
    edit_sf_email_response = client.post("/edit_salesforce_email/email2", data=json.loads(edit_sf_email_data), follow_redirects=True)
    assert b"Unauthorized Access" in edit_sf_email_response.data

# delete salesforce emails, success.
def test_69_delete_salesfoce_email_post(client):
    initialize_salesfoce_email(client)
    logout(client)
    login(client, username='test_user', password='password')
    delete_sf_email_response = client.post("/delete_salesforce_email/email1", follow_redirects=True)
    assert b"Email template email1 deleted" in delete_sf_email_response.data

# delete salesforce emails, Auth failure.
def test_70_delete_salesfoce_email_post_401(client):
    initialize_salesfoce_email(client)
    logout(client)
    delete_sf_email_response = client.post("/delete_salesforce_email/email1", follow_redirects=True)
    assert delete_sf_email_response.status_code == 401

# delete salesforce emails, email template not found.
def test_71_delete_salesfoce_email_post_404(client):
    initialize_salesfoce_email(client)
    logout(client)
    login(client, username='test_user', password='password')
    delete_sf_email_response = client.post("/delete_salesforce_email/email2", follow_redirects=True)
    assert b"Email template email2 not found" in delete_sf_email_response.data

# Get request for salesforce emails
def test_72_jinja2_variables_get(client):
    login(client)
    response = client.get("/jinja2_variables", follow_redirects=True)
    assert b"<title> CAT Jinja2 Variables</title>" in response.data

# Get request for salesforce emails, auth failure
def test_73_jinja2_variables_get_401(client):
    response = client.get("/jinja2_variables", follow_redirects=True)
    assert response.status_code == 401

# Get request for my details
def test_74_my_details_get(client):
    login(client)
    response = client.get("/my_details", follow_redirects=True)
    assert b"<title> CAT My Details</title>" in response.data

# Get request for my details, auth failure
def test_75_my_details_get_401(client):
    response = client.get("/my_details", follow_redirects=True)
    assert response.status_code == 401

# Get request for jinja2 variables
def test_76_jinja2_variables_get(client):
    login(client)
    response = client.get("/jinja2_variables", follow_redirects=True)
    assert b"<title> CAT Jinja2 Variables</title>" in response.data

# Get request for jinja2 variables, auth failure
def test_77_jinja2_variables_401(client):
    response = client.get("/jinja2_variables", follow_redirects=True)
    assert response.status_code == 401

# Get request for schedule handoffs page
def test_78_schedule_handoffs_get(client):
    login(client)
    schedule_handoffs_response = client.get("/schedule_handoffs", follow_redirects=True)
    assert b"<title> CAT Schedule Handoffs</title>" in schedule_handoffs_response.data

# Get request for schedule handoffs user page, auth failure
def test_79_schedule_handoffs_get_401(client):
    schedule_handoffs_response = client.get("/schedule_handoffs", follow_redirects=True)
    assert schedule_handoffs_response.status_code == 401

# Post request for schedule handoffs page, success.
def test_80_schedule_handoffs_post_1(client):
    initialize_all(client)
    logout(client)
    login(client, username="test_user", password="password")
    user_data = '''{
            "username": "test_user",
            "datetime": "2030-10-10T12:10",
            "timezone": "US/Pacific"
        }'''
    schedule_handoffs_response = client.post("/schedule_handoffs", data=json.loads(user_data), follow_redirects=True)
    assert b"Job Submitted" in schedule_handoffs_response.data

# Post request for schedule handoffs page, already a job running, success
def test_81_schedule_handoffs_post_2(client):
    initialize_all(client)
    logout(client)
    login(client, username="test_user", password="password")
    user_data1 = '''{
            "username": "test_user",
            "datetime": "2030-10-10T12:10",
            "timezone": "US/Pacific",
            "check_in_shift": "false"
        }'''
    user_data2 = '''{
            "username": "test_user",
            "datetime": "2030-11-10T12:10",
            "timezone": "US/Pacific",
            "check_in_shift": "true"
        }'''
    schedule_handoffs_response1 = client.post("/schedule_handoffs", data=json.loads(user_data1), follow_redirects=True)
    schedule_handoffs_response2 = client.post("/schedule_handoffs", data=json.loads(user_data2), follow_redirects=True)
    assert b"Job Submitted" in schedule_handoffs_response2.data

# Post request for schedule shift change page, auth failure
def test_82_schedule_handoffs_401(client):
    initialize_all(client)
    logout(client)
    user_data = '''{
            "username": "test_user",
            "datetime": "2030-11-10T12:10",
            "timezone": "US/Pacific",
            "check_in_shift": "true"
        }'''
    schedule_handoffs_response = client.post("/schedule_handoffs", data=json.loads(user_data), follow_redirects=True)
    assert schedule_handoffs_response.status_code == 401

# Post request for schedule handoffs page, date provided is a past date
def test_83_schedule_handoffs_post_400(client):
    initialize_all(client)
    logout(client)
    login(client, username="test_user", password="password")
    user_data = '''{
            "username": "test_user",
            "datetime": "2010-10-10T12:10",
            "timezone": "US/Pacific"
        }'''
    schedule_handoffs_response = client.post("/schedule_handoffs", data=json.loads(user_data), follow_redirects=True)
    assert b"Datetime has to be a time in future" in schedule_handoffs_response.data
