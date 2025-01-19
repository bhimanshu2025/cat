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
        'sf_product_series': "P1",
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

def initialize_assign_case(client, mocker_salesforce_case_details_function, mock_sf_case_object):
    initialize_all(client)
    case_data = '''{
        "caseid": "",
        "caseid_text": "2023-0395-203840",
        "product": "P1",
        "comments": "Test",
        "priority": "P2",
        "mode": "auto",
        "check_in_shift": "false"
}'''
    logout(client)
    mocker_salesforce_case_details_function.return_value = mock_sf_case_object, 200
    login(client, username='test_user', password='password')
    return client.post("/", data=json.loads(case_data), follow_redirects=True)

def initialize_all(client):
    initialize_team(client)
    initialize_user(client)
    initialize_product(client)
    initialize_userproduct(client)

def test_1_home(client):
    login(client)
    get_products_response = client.get("/", follow_redirects=True)
    assert b"<title> CAT Home</title>" in get_products_response.data

def test_2_home_401(client):
    get_products_response = client.get("/", follow_redirects=True)
    assert get_products_response.status_code == 401

# Assign case success
def test_3_assign_case(client, mocker_salesforce_case_details_function, mock_sf_case_object):
    initialize_all(client)
    case_data = '''{
        "caseid": "",
        "caseid_text": "2023-0394-203847",
        "product": "P1",
        "comments": "Test",
        "priority": "P2",
        "mode": "auto",
        "check_in_shift": "false",
        "delayed_assignment": "16:00:00"
}'''
    logout(client)
    mocker_salesforce_case_details_function.return_value = mock_sf_case_object, 200
    login(client, username='test_user', password='password')
    assign_case_response = client.post("/", data=json.loads(case_data), follow_redirects=True)
    assert b"Case 2023-0394-203847 assigned to test_user" in assign_case_response.data

# Assign case failed, delayed case assignment when no user in shift. check_in_shift has to be true for this test
def test_4_assign_case_delayed_assignment(client, mocker_salesforce_case_details_function, mock_sf_case_object):
    initialize_all(client)
    case_data = '''{
        "caseid": "",
        "caseid_text": "2023-0394-203847",
        "product": "P1",
        "comments": "Test",
        "priority": "P2",
        "mode": "auto",
        "check_in_shift": "true",
        "delayed_assignment": "19:00:00"
}'''
    logout(client)
    mocker_salesforce_case_details_function.return_value = mock_sf_case_object, 200
    login(client, username='test_user', password='password')
    assign_case_response = client.post("/", data=json.loads(case_data), follow_redirects=True)
    assert b"No user found for P1. This may be due to various reasons like users not in shift or inactive users etc" in assign_case_response.data

def test_5_assign_case_401(client):
    initialize_all(client)
    case_data = '''{
        "caseid": "",
        "caseid_text": "2023-0394-203847",
        "product": "P1",
        "comments": "Test",
        "priority": "P2",
        "mode": "auto",
        "check_in_shift": "false"
}'''
    logout(client)
    login(client, username='test_user', password='password1')
    assign_case_response = client.post("/", data=json.loads(case_data), follow_redirects=True)
    assert assign_case_response.status_code == 401

# Incorect case format
def test_6_assign_case_400(client, mocker_salesforce_case_details_function, mock_sf_case_object):
    initialize_all(client)
    case_data = '''{
        "caseid": "",
        "caseid_text": "2023-0394-2038470",
        "product": "P1",
        "comments": "Test",
        "priority": "P2",
        "mode": "auto",
        "check_in_shift": "false"
}'''
    logout(client)
    mocker_salesforce_case_details_function.return_value = mock_sf_case_object, 200
    login(client, username='test_user', password='password')
    assign_case_response = client.post("/", data=json.loads(case_data), follow_redirects=True)
    assert b"Case id 2023-0394-2038470 format incorrect" in assign_case_response.data

# Current user doesnt support any products
def test_7_assign_case_no_products_supported(client):
    login(client)
    assign_case_response = client.get("/", follow_redirects=True)
    assert b"User admin doesnt support any products" in assign_case_response.data

# mode manual and no user provided
def test_8_assign_case_manual_no_user(client, mocker_salesforce_case_details_function, mock_sf_case_object):
    initialize_all(client)
    case_data = '''{
        "caseid": "",
        "caseid_text": "2023-0394-203847",
        "product": "P1",
        "comments": "Test",
        "priority": "P2",
        "mode": "manual",
        "check_in_shift": "false"
}'''
    logout(client)
    mocker_salesforce_case_details_function.return_value = mock_sf_case_object, 200
    login(client, username='test_user', password='password')
    assign_case_response = client.post("/", data=json.loads(case_data), follow_redirects=True)
    assert b"User is required when mode is manual" in assign_case_response.data

# no user found supporting a product
def test_9_assign_case_no_user_found(client, mocker_salesforce_case_details_function, mock_sf_case_object):
    initialize_team(client)
    initialize_user(client)
    initialize_product(client)
    initialize_userproduct(client, active=False)
    case_data = '''{
        "caseid": "",
        "caseid_text": "2023-0394-203847",
        "product": "P1",
        "comments": "Test",
        "priority": "P2",
        "mode": "auto",
        "check_in_shift": "false"
}'''
    logout(client)
    mocker_salesforce_case_details_function.return_value = mock_sf_case_object, 200
    login(client, username='test_user', password='password')
    assign_case_response = client.post("/", data=json.loads(case_data), follow_redirects=True)
    print(assign_case_response.data)
    assert b"No user found for P1." in assign_case_response.data

# Existing case, successful reassign
def test_10_reassign_case(client, mocker_salesforce_case_details_function, mock_sf_case_object):
    initialize_all(client)
    case1_data = '''{
        "caseid": "",
        "caseid_text": "2023-0394-203847",
        "product": "P1",
        "comments": "Test",
        "priority": "P2",
        "mode": "auto",
        "check_in_shift": "false"
}'''
    logout(client)
    mocker_salesforce_case_details_function.return_value = mock_sf_case_object, 200
    login(client, username='test_user', password='password')
    assign_case1_response = client.post("/", data=json.loads(case1_data), follow_redirects=True)
    case2_data = '''{
        "caseid": "",
        "caseid_text": "2023-0394-203847",
        "product": "P1",
        "comments": "Test",
        "priority": "P2",
        "mode": "manual",
        "check_in_shift": "false",
        "user": "test_user"
}'''
    assign_case2_response = client.post("/", data=json.loads(case2_data), follow_redirects=True)
    assert b"Case 2023-0394-203847 assigned to test_user" in assign_case2_response.data

# Existing case mode auto selected, failure
def test_11_auto_reassign_case_failed(client, mocker_salesforce_case_details_function, mock_sf_case_object):
    initialize_all(client)
    # create a second user
    add_user2_data = {
        "email": "abc@efg.com",
        "teamname": "T1",
        "active": True,
        "admin": True,
        "shift_start": "12:00:00",
        "shift_end": "18:00:00",
        "timezone": "US/Pacific",
        "username": "test_user2",
        "password": "password",
        "confirm_password": "password"
        }
    client.post("/add_user", data=add_user2_data, follow_redirects=True)
    # add the second user to product P1
    add_userproduct2_data = '''{
        "productname": "P1",
        "username": "test_user2",
        "active": "true",
        "quota": 1
    }'''
    client.post("/add_user_product", data=json.loads(add_userproduct2_data), follow_redirects=True)
    # Assign the case and then reassign in auto mode to verify its getting assigned to second user
    case1_data = '''{
        "caseid": "",
        "caseid_text": "2023-0394-203847",
        "product": "P1",
        "comments": "Test",
        "priority": "P2",
        "mode": "auto",
        "check_in_shift": "false"
}'''
    logout(client)
    mocker_salesforce_case_details_function.return_value = mock_sf_case_object, 200
    login(client, username='test_user', password='password')
    assign_case1_response = client.post("/", data=json.loads(case1_data), follow_redirects=True)
    case2_data = '''{
        "caseid": "",
        "caseid_text": "2023-0394-203847",
        "product": "P1",
        "comments": "Test",
        "priority": "P2",
        "mode": "auto",
        "check_in_shift": "false",
        "user": "test_user"
}'''
    assign_case2_response = client.post("/", data=json.loads(case2_data), follow_redirects=True)
    assert b"Mode cannot be auto for case reassignment. Please select mode as auto-reassign. The case 2023-0394-203847 is already assigned to test_user" in assign_case2_response.data

# Existing case mode auto-reassign selected, success
def test_12_auto_reassign_case_success(client, mocker_salesforce_case_details_function, mock_sf_case_object):
    initialize_all(client)
    # create a second user
    add_user2_data = {
        "email": "abc@efg.com",
        "teamname": "T1",
        "active": True,
        "admin": True,
        "shift_start": "12:00:00",
        "shift_end": "18:00:00",
        "timezone": "US/Pacific",
        "username": "test_user2",
        "password": "password",
        "confirm_password": "password"
        }
    client.post("/add_user", data=add_user2_data, follow_redirects=True)
    # add the second user to product P1
    add_userproduct2_data = '''{
        "productname": "P1",
        "username": "test_user2",
        "active": "true",
        "quota": 1
    }'''
    client.post("/add_user_product", data=json.loads(add_userproduct2_data), follow_redirects=True)
    # Assign the case and then reassign in auto mode to verify its getting assigned to second user
    case1_data = '''{
        "caseid": "",
        "caseid_text": "2023-0394-203847",
        "product": "P1",
        "comments": "Test",
        "priority": "P2",
        "mode": "auto",
        "check_in_shift": "false"
}'''
    logout(client)
    mocker_salesforce_case_details_function.return_value = mock_sf_case_object, 200
    login(client, username='test_user', password='password')
    assign_case1_response = client.post("/", data=json.loads(case1_data), follow_redirects=True)
    case2_data = '''{
        "caseid": "",
        "caseid_text": "2023-0394-203847",
        "product": "P1",
        "comments": "Test",
        "priority": "P2",
        "mode": "auto-reassign",
        "check_in_shift": "false",
        "user": "test_user"
}'''
    assign_case2_response = client.post("/", data=json.loads(case2_data), follow_redirects=True)
    assert b"Case 2023-0394-203847 assigned to test_user2" in assign_case2_response.data

# Existing case mode auto-reassign selected, but no other user exists for case to be reassigned to
def test_13_auto_reassign_case_no_user(client, mocker_salesforce_case_details_function, mock_sf_case_object):
    initialize_all(client)
    case1_data = '''{
        "caseid": "",
        "caseid_text": "2023-0394-203847",
        "product": "P1",
        "comments": "Test",
        "priority": "P2",
        "mode": "auto",
        "check_in_shift": "false"
}'''
    logout(client)
    mocker_salesforce_case_details_function.return_value = mock_sf_case_object, 200
    login(client, username='test_user', password='password')
    assign_case1_response = client.post("/", data=json.loads(case1_data), follow_redirects=True)
    case2_data = '''{
        "caseid": "",
        "caseid_text": "2023-0394-203847",
        "product": "P1",
        "comments": "Test",
        "priority": "P2",
        "mode": "auto-reassign",
        "check_in_shift": "false",
        "user": "test_user"
}'''
    assign_case2_response = client.post("/", data=json.loads(case2_data), follow_redirects=True)
    print(assign_case2_response.data)
    assert b"No user found for P1. This may be due to various reasons like users not in shift or inactive users etc" in assign_case2_response.data

# Existing case, no username provided
def test_14_reassign_case_no_user(client, mocker_salesforce_case_details_function, mock_sf_case_object):
    initialize_all(client)
    case1_data = '''{
        "caseid": "",
        "caseid_text": "2023-0394-203847",
        "product": "P1",
        "comments": "Test",
        "priority": "P2",
        "mode": "auto",
        "check_in_shift": "false"
}'''
    logout(client)
    mocker_salesforce_case_details_function.return_value = mock_sf_case_object, 200
    login(client, username='test_user', password='password')
    assign_case1_response = client.post("/", data=json.loads(case1_data), follow_redirects=True)
    case2_data = '''{
        "caseid": "",
        "caseid_text": "2023-0394-203847",
        "product": "P1",
        "comments": "Test",
        "priority": "P2",
        "mode": "manual",
        "check_in_shift": "false",
        "user": "---"
}'''
    assign_case2_response = client.post("/", data=json.loads(case2_data), follow_redirects=True)
    print(assign_case2_response.data)
    assert b"Please provide a username and select mode as manual for case reassignment" in assign_case2_response.data

# Unassign case get request
def test_15_unassign_case_get(client):
    login(client)
    unassign_case_get_response = client.get("/unassign_case", follow_redirects=True)
    assert b"<title> CAT Unassign Case</title>"  in unassign_case_get_response.data

# Unassign case get request, auth failure
def test_16_unassign_case_get_401(client):
    unassign_case_get_response = client.get("/unassign_case", follow_redirects=True)
    assert unassign_case_get_response.status_code == 401

# Unassign case get request, no cases to unassign
def test_17_unassign_case_get_no_cases(client):
    initialize_all(client)
    unassign_case_get_response = client.get("/unassign_case", follow_redirects=True)
    assert b"No cases found for products supported by test_user." in unassign_case_get_response.data

# Unassign case post, success
def test_18_unassign_case_post(client, mocker_salesforce_case_details_function, mock_sf_case_object):
    initialize_assign_case(client, mocker_salesforce_case_details_function, mock_sf_case_object)
    case_data = '''{
        "caseid": "2023-0395-203840",
        "caseid_text": "",
        "comments": "Test"
}'''
    unassign_case_response = client.post("/unassign_case", data=json.loads(case_data), follow_redirects=True)
    assert b"Case 2023-0395-203840 unassigned from test_user" in unassign_case_response.data

# Unassign case post, auth failure
def test_19_unassign_case_post_401(client, mocker_salesforce_case_details_function, mock_sf_case_object):
    initialize_assign_case(client, mocker_salesforce_case_details_function, mock_sf_case_object)
    logout(client)
    case_data = '''{
        "caseid": "2023-0395-203840",
        "caseid_text": "",
        "comments": "Test"
}'''
    unassign_case_response = client.post("/unassign_case", data=json.loads(case_data), follow_redirects=True)
    assert unassign_case_response.status_code == 401

# About page get request
def test_20_about_get(client):
    about_response = client.get("/about", follow_redirects=True)
    assert b"<title> CAT About</title>"  in about_response.data

# Swagger page get request
def test_21_swagger_get(client):
    swagger_response = client.get("/swagger", follow_redirects=True)
    assert swagger_response.status_code == 200

# Audit page get request
def test_22_audit_get(client):
    login(client)
    audit_response = client.get("/audit", follow_redirects=True)
    assert b"<title> CAT Audit</title>"  in audit_response.data

# Audit page get request, auth failure
def test_23_audit_get_401(client):
    audit_response = client.get("/audit", follow_redirects=True)
    assert audit_response.status_code == 401

# Audit details page get request. Do some activity so audits are created
def test_24_audit_details_get(client):
    initialize_all(client)
    audit_details_response = client.get("/audit_details/1", follow_redirects=True)
    assert b"<title> CAT Audit Details</title>"  in audit_details_response.data

# Audit page get request, auth failure
def test_25_audit_details_get_401(client):
    audit_details_response = client.get("/audit_details/1", follow_redirects=True)
    assert audit_details_response.status_code == 401

# Cases page get request
def test_26_cases_get(client):
    login(client)
    cases_response = client.get("/cases", follow_redirects=True)
    assert b"<title> CAT Cases Assigned</title>"  in cases_response.data

# Cases page get request, auth failure
def test_27_cases_get_401(client):
    cases_response = client.get("/cases", follow_redirects=True)
    assert cases_response.status_code == 401

# Cases of product page get request
def test_28_cases_of_product_get(client, mocker_salesforce_case_details_function, mock_sf_case_object):
    initialize_all(client)
    initialize_assign_case(client, mocker_salesforce_case_details_function, mock_sf_case_object)
    cases_response = client.get("/cases_of_product/P1", follow_redirects=True)
    assert b"<title> CAT Cases Assigned</title>"  in cases_response.data

# Cases of product page, auth failure
def test_29_cases_of_product_get_401(client):
    cases_response = client.get("/cases_of_product/P1", follow_redirects=True)
    assert cases_response.status_code == 401

# Cases of product page, unauthorized flash
def test_30_cases_of_product_get_unauthorized(client, mocker_salesforce_case_details_function, mock_sf_case_object):
    initialize_all(client)
    initialize_assign_case(client, mocker_salesforce_case_details_function, mock_sf_case_object)
    cases_response = client.get("/cases_of_product/P2", follow_redirects=True)
    assert b"Unauthorized Access"  in cases_response.data

# Cases assigned by user page get request
def test_31_cases_assigned_by_user_get(client, mocker_salesforce_case_details_function, mock_sf_case_object):
    initialize_all(client)
    initialize_assign_case(client, mocker_salesforce_case_details_function, mock_sf_case_object)
    cases_response = client.get("/cases_assigned_by_user/test_user", follow_redirects=True)
    assert b"<title> CAT Cases Assigned</title>"  in cases_response.data

# Cases assigned by user page, auth failure
def test_32_cases_assigned_by_user_get_401(client):
    cases_response = client.get("/cases_assigned_by_user/test_user", follow_redirects=True)
    assert cases_response.status_code == 401

# Cases assigned by user page, unauthorized flash
def test_33_cases_assigned_by_user_get_unauthorized(client, mocker_salesforce_case_details_function, mock_sf_case_object):
    initialize_all(client)
    initialize_assign_case(client, mocker_salesforce_case_details_function, mock_sf_case_object)
    logout(client)
    login(client, username='test_user', password='password')
    cases_response = client.get("/cases_assigned_by_user/admin", follow_redirects=True)
    assert b"Unauthorized Access"  in cases_response.data

# Cases of user page get request
def test_34_cases_of_user_get(client, mocker_salesforce_case_details_function, mock_sf_case_object):
    initialize_all(client)
    initialize_assign_case(client, mocker_salesforce_case_details_function, mock_sf_case_object)
    cases_response = client.get("/cases_of_user/test_user", follow_redirects=True)
    assert b"<title> CAT Cases Assigned</title>"  in cases_response.data

# Cases of user page get request, auth failure
def test_35_cases_of_user_get_401(client):
    cases_response = client.get("/cases_of_user/test_user", follow_redirects=True)
    assert cases_response.status_code == 401

# Cases of user page get request, unauthorized flash
def test_36_cases_of_user_get_unauthorized(client, mocker_salesforce_case_details_function, mock_sf_case_object):
    initialize_all(client)
    initialize_assign_case(client, mocker_salesforce_case_details_function, mock_sf_case_object)
    logout(client)
    login(client, username='test_user', password='password')
    cases_response = client.get("/cases_of_user/admin", follow_redirects=True)
    assert b"Unauthorized Access"  in cases_response.data

# Cases assigned by mode page get request
def test_37_cases_assigned_by_mode_get(client, mocker_salesforce_case_details_function, mock_sf_case_object):
    initialize_all(client)
    initialize_assign_case(client, mocker_salesforce_case_details_function, mock_sf_case_object)
    cases_response = client.get("/cases_assigned_by_mode/auto", follow_redirects=True)
    assert b"<title> CAT Cases Assigned</title>"  in cases_response.data

# Cases assigned by mode page, auth failure
def test_38_cases_assigned_by_mode_get_401(client):
    cases_response = client.get("/cases_assigned_by_mode/auto", follow_redirects=True)
    assert cases_response.status_code == 401

# Cases assigned by priority page get request
def test_39_cases_assigned_by_priority_get(client, mocker_salesforce_case_details_function, mock_sf_case_object):
    initialize_all(client)
    initialize_assign_case(client, mocker_salesforce_case_details_function, mock_sf_case_object)
    cases_response = client.get("/cases_assigned_by_priority/P2", follow_redirects=True)
    print(cases_response.data)
    assert b"<title> CAT Cases Assigned</title>"  in cases_response.data

# Cases assigned by priority page, auth failure
def test_40_cases_assigned_by_priority_get_401(client):
    cases_response = client.get("/cases_assigned_by_priority/P2", follow_redirects=True)
    assert cases_response.status_code == 401

# Unassign case post, caseid_text having a valid value, success
def test_41_unassign_case_caseid_text_valid_post(client, mocker_salesforce_case_details_function, mock_sf_case_object):
    initialize_assign_case(client, mocker_salesforce_case_details_function, mock_sf_case_object)
    logout(client)
    mocker_salesforce_case_details_function.return_value = mock_sf_case_object, 200
    login(client, username='test_user', password='password')
    case2_data = '''{
        "caseid": "",
        "caseid_text": "2023-0394-203847",
        "product": "P1",
        "comments": "Test",
        "priority": "P2",
        "mode": "auto",
        "check_in_shift": "false"
}'''
    assign_case2_response = client.post("/", data=json.loads(case2_data), follow_redirects=True)
    case_unassign_data = '''{
        "caseid": "2023-0395-203840",
        "caseid_text": "2023-0394-203847",
        "comments": "Test"
}'''
    unassign_case_response = client.post("/unassign_case", data=json.loads(case_unassign_data), follow_redirects=True)
    assert b"Case 2023-0394-203847 unassigned from test_user" in unassign_case_response.data

# Unassign case post, caseid_text having a invalid value, case id not found
def test_42_unassign_case_caseid_text_invalid_post_404(client, mocker_salesforce_case_details_function, mock_sf_case_object):
    initialize_assign_case(client, mocker_salesforce_case_details_function, mock_sf_case_object)
    logout(client)
    login(client, username='test_user', password='password')
    case_unassign_data = '''{
        "caseid": "2023-0395-203840",
        "caseid_text": "2023-0394-203847",
        "comments": "Test"
}'''
    unassign_case_response = client.post("/unassign_case", data=json.loads(case_unassign_data), follow_redirects=True)
    assert b"Case 2023-0394-203847 not found" in unassign_case_response.data