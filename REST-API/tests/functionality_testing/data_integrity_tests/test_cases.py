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
  "max_days": "7",
  "max_days_month": "300",
  "case_regex": "^[0-9]{4}-[0-9]{4}-[0-9]{6}$",
  "quota_over_days": 1,
  "sf_api": "",
  "sf_job_cron": "* 6-18 * * 1-5",
  "sf_job_timezone": "US/Pacific",
  "sf_job_query_interval": 1,
  "productname": "P1",
  "sf_init_email_name": "",
  "sf_mist_product": "",
  "sf_product_series": "P1"
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

def initialize_assign_case(client, mocker_salesforce_case_details_function, mock_sf_case_object):
    initialize_all(client)
    mocker_salesforce_case_details_function.return_value = mock_sf_case_object, 200
    case_data = '''{
  "case_id": "2023-0910-029384",
  "product": "P1",
  "priority": "P2",
  "comments": "this is an example",
  "mode": "auto",
  "user": "test_user",
  "check_in_shift": false,
  "sf_account_name" : "XYZ"
}'''
    return client.post("/api/assign-case", data=case_data, auth=("test_user", "password"))

def test_1_assign_case_auto(client, mocker_salesforce_case_details_function, mock_sf_case_object):
    initialize_all(client)
    assign_case_response = initialize_assign_case(client, mocker_salesforce_case_details_function, mock_sf_case_object)
    assign_case_schema = assign_case_response.json 
    assert assign_case_schema.get('case_id') == "2023-0910-029384" and \
           assign_case_schema.get('product') == "P1" and \
           assign_case_schema.get('priority') == "P2" and \
           assign_case_schema.get('comments') == "this is an example" and \
           assign_case_schema.get('mode') == "auto" and \
           assign_case_schema.get('assigned_to') == "test_user" and \
           assign_case_schema.get('assigned_by') == "test_user" and \
           assign_case_schema.get('sf_account_name') == "XYZ" and \
           assign_case_schema.get('assignment_history') == "['test_user']"

def test_2_assign_case_manual(client, mocker_salesforce_case_details_function, mock_sf_case_object):
    initialize_all(client)
    mocker_salesforce_case_details_function.return_value = mock_sf_case_object, 200
    case_data = '''{
  "case_id": "2023-0910-029385",
  "product": "P1",
  "priority": "P2",
  "comments": "this is an example",
  "mode": "manual",
  "user": "test_user",
  "check_in_shift": false,
  "sf_account_name" : "XYZ"
}'''
    assign_case_response = client.post("/api/assign-case", data=case_data, auth=("test_user", "password"))
    assign_case_schema = assign_case_response.json 
    assert assign_case_schema.get('case_id') == "2023-0910-029385" and \
           assign_case_schema.get('product') == "P1" and \
           assign_case_schema.get('priority') == "P2" and \
           assign_case_schema.get('comments') == "this is an example" and \
           assign_case_schema.get('mode') == "manual" and \
           assign_case_schema.get('assigned_to') == "test_user" and \
           assign_case_schema.get('assigned_by') == "test_user" and \
           assign_case_schema.get('sf_account_name') == "XYZ"

# create 2 users. Reassign case to second user, make some edits to case object values and validate
def test_3_reassign_case(client, mocker_salesforce_case_details_function, mock_sf_case_object):
    initialize_all(client)
    mocker_salesforce_case_details_function.return_value = mock_sf_case_object, 200
    assign_case_response = initialize_assign_case(client, mocker_salesforce_case_details_function, mock_sf_case_object)
    test_user2_data = '''{
  "email": "abc@efg.com",
  "teamname": "T1",
  "active": true,
  "admin": true,
  "shift_start": "09:00:00",
  "shift_end": "18:00:00",
  "timezone": "US/Pacific",
  "username": "test_user2",
  "password": "password"
}'''
    client.post("/api/user", data=test_user2_data, auth=("admin", "admin"))
    test_user2_product_data = '''{
  "productname": "P1",
  "username": "test_user2",
  "active": true,
  "quota": 1
}'''
    add_userproduct_test_user2 = client.post("/api/user-product", data=test_user2_product_data, auth=("admin", "admin"))
    reassign_case_data = '''{
  "case_id": "2023-0910-029384",
  "product": "P1",
  "priority": "P3",
  "comments": "this is an example 2",
  "mode": "manual",
  "user": "test_user2",
  "check_in_shift": false,
  "sf_account_name" : "ABC"
}'''
    # Update the mock object sf_case
    mock_sf_case_object.account_name = "ABC"
    mock_sf_case_object.priority = "P3"
    reassign_case_response = client.post("/api/assign-case", data=reassign_case_data, auth=("test_user2", "password"))
    reassign_case_schema = reassign_case_response.json 
    assert reassign_case_schema.get('case_id') == "2023-0910-029384" and \
           reassign_case_schema.get('product') == "P1" and \
           reassign_case_schema.get('priority') == "P3" and \
           reassign_case_schema.get('comments') == "this is an example 2" and \
           reassign_case_schema.get('mode') == "manual" and \
           reassign_case_schema.get('assigned_to') == "test_user2" and \
           reassign_case_schema.get('assigned_by') == "test_user2" and \
           reassign_case_schema.get('sf_account_name') == "ABC" and \
           reassign_case_schema.get('assignment_history') == "['test_user', 'test_user2']"
    
# After case unassignment, case is removed from cases table.
def test_4_unassign_case(client, mocker_salesforce_case_details_function, mock_sf_case_object):
    initialize_all(client)
    assign_case_response = initialize_assign_case(client, mocker_salesforce_case_details_function, mock_sf_case_object)
    unassign_case_data = '''{
    "comments": "testing"
    }'''
    unassign_case_response = client.post("/api/unassign-case/2023-0910-029384", data=unassign_case_data, auth=("test_user", "password"))
    get_case_response = client.get("/api/case/2023-0910-029384", auth=("test_user", "password"))
    assert get_case_response.status_code == 404

# create two users. assign the case and verify if its getting assigned to intended users based on value defined in delayed_assignment
def test_5_assign_case_delayed_auto(client):
    initialize_all(client)
    test_user2_data = '''{
  "email": "abc@efg.com",
  "teamname": "T1",
  "active": true,
  "admin": true,
  "shift_start": "10:00:00",
  "shift_end": "20:00:00",
  "timezone": "US/Pacific",
  "username": "test_user2",
  "password": "password"
}'''
    client.post("/api/user", data=test_user2_data, auth=("admin", "admin"))
    test_user2_product_data = '''{
  "productname": "P1",
  "username": "test_user2",
  "active": true,
  "quota": 1
}'''
    add_userproduct_test_user2 = client.post("/api/user-product", data=test_user2_product_data, auth=("admin", "admin"))
    assign_case_data = '''{
  "case_id": "2023-0910-029384",
  "product": "P1",
  "priority": "P2",
  "comments": "this is an example",
  "mode": "auto",
  "check_in_shift": true,
  "sf_account_name" : "XYZ",
  "delayed_assignment" : "09:30:00"
}'''
    # this will assign to test_user as only that user is in shift
    assign_case_response = client.post("/api/assign-case", data=assign_case_data, auth=("test_user", "password"))
    assign_case_schema = assign_case_response.json 
    assert assign_case_schema.get('assigned_to') == "test_user" 
    unassign_case_data = '''{
    "comments": "testing"
    }'''
    unassign_case_response = client.post("/api/unassign-case/2023-0910-029384", data=unassign_case_data, auth=("test_user", "password"))
    # add delayed_assignment
    assign_case_data = '''{
  "case_id": "2023-0910-029385",
  "product": "P1",
  "priority": "P2",
  "comments": "this is an example",
  "mode": "auto",
  "check_in_shift": true,
  "sf_account_name" : "XYZ",
  "delayed_assignment" : "19:00:00"
}'''
    # this will assign to test_user2 as only that user is in shift at 19:00:00
    assign_case_response = client.post("/api/assign-case", data=assign_case_data, auth=("test_user", "password"))
    assign_case_schema = assign_case_response.json 
    assert assign_case_schema.get('assigned_to') == "test_user2" 

# create 2 users. auto-reassign case to second user, make some edits to case object values and validate
def test_6_auto_reassign_case(client, mocker_salesforce_case_details_function, mock_sf_case_object):
    initialize_all(client)
    mocker_salesforce_case_details_function.return_value = mock_sf_case_object, 200
    assign_case_response = initialize_assign_case(client, mocker_salesforce_case_details_function, mock_sf_case_object)
    test_user2_data = '''{
  "email": "abc@efg.com",
  "teamname": "T1",
  "active": true,
  "admin": true,
  "shift_start": "09:00:00",
  "shift_end": "18:00:00",
  "timezone": "US/Pacific",
  "username": "test_user2",
  "password": "password"
}'''
    client.post("/api/user", data=test_user2_data, auth=("admin", "admin"))
    test_user2_product_data = '''{
  "productname": "P1",
  "username": "test_user2",
  "active": true,
  "quota": 1
}'''
    add_userproduct_test_user2 = client.post("/api/user-product", data=test_user2_product_data, auth=("admin", "admin"))
    reassign_case_data = '''{
  "case_id": "2023-0910-029384",
  "product": "P1",
  "priority": "P3",
  "comments": "this is an example 2",
  "mode": "auto-reassign",
  "user": "test_user2",
  "check_in_shift": false,
  "sf_account_name" : "ABC"
}'''
    # Update the mock object sf_case
    mock_sf_case_object.account_name = "ABC"
    mock_sf_case_object.priority = "P3"
    reassign_case_response = client.post("/api/assign-case", data=reassign_case_data, auth=("test_user2", "password"))
    reassign_case_schema = reassign_case_response.json 
    assert reassign_case_schema.get('case_id') == "2023-0910-029384" and \
           reassign_case_schema.get('product') == "P1" and \
           reassign_case_schema.get('priority') == "P3" and \
           reassign_case_schema.get('comments') == "this is an example 2" and \
           reassign_case_schema.get('mode') == "auto-reassign" and \
           reassign_case_schema.get('assigned_to') == "test_user2" and \
           reassign_case_schema.get('assigned_by') == "test_user2" and \
           reassign_case_schema.get('sf_account_name') == "ABC" and \
           reassign_case_schema.get('assignment_history') == "['test_user', 'test_user2']"