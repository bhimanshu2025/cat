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
  "productname": "P1"
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

def test_1_assign_case_manual(client):
    initialize_all(client)
    case_data = '''{
  "case_id": "2023-0910-029384",
  "product": "P1",
  "priority": "P2",
  "comments": "this is an example",
  "mode": "manual",
  "user": "test_user",
  "check_in_shift": false
}'''
    assign_case_response = client.post("/api/assign-case", data=case_data, auth=("test_user", "password"))
    assert assign_case_response.status_code == 200
    assert assign_case_response.content_type == "application/json"

# success
def test_2_assign_case_auto(client):
    initialize_all(client)
    case_data = '''{
  "case_id": "2023-0910-029384",
  "product": "P1",
  "priority": "P2",
  "comments": "this is an example",
  "mode": "auto",
  "user": "test_user",
  "check_in_shift": false
}'''
    assign_case_response = client.post("/api/assign-case", data=case_data, auth=("test_user", "password"))
    assert assign_case_response.status_code == 200
    assert assign_case_response.content_type == "application/json"

# delayed assignment, success
def test_3_assign_case_delayed_auto(client):
    initialize_all(client)
    case_data = '''{
  "case_id": "2023-0910-029384",
  "product": "P1",
  "priority": "P2",
  "comments": "this is an example",
  "mode": "auto",
  "user": "test_user",
  "check_in_shift": false,
  "delayed_assignment": "16:00:00"
}'''
    assign_case_response = client.post("/api/assign-case", data=case_data, auth=("test_user", "password"))
    assert assign_case_response.status_code == 200
    assert assign_case_response.content_type == "application/json"

# delayed assignment, failure, no user to assign case at 19:00:00 hours
def test_4_assign_case_delayed_auto(client):
    initialize_all(client)
    case_data = '''{
  "case_id": "2023-0910-029384",
  "product": "P1",
  "priority": "P2",
  "comments": "this is an example",
  "mode": "auto",
  "user": "test_user",
  "check_in_shift": false,
  "delayed_assignment": "19:00:00"
}'''
    assign_case_response = client.post("/api/assign-case", data=case_data, auth=("test_user", "password"))
    assert assign_case_response.status_code == 200
    assert assign_case_response.content_type == "application/json"

# invalid product name
def test_5_assign_case_404(client):
    initialize_all(client)
    case_data = '''{
  "case_id": "2023-0910-029384",
  "product": "P2",
  "priority": "P2",
  "comments": "this is an example",
  "mode": "manual",
  "user": "test_user",
  "check_in_shift": false
}'''
    assign_case_response = client.post("/api/assign-case", data=case_data, auth=("test_user", "password"))
    assert assign_case_response.status_code == 404
  
def test_6_assign_case_400(client):
    initialize_all(client)
    case_data = '''{
  "case_id": "2023-0910-0293840",
  "product": "P1",
  "priority": "P2",
  "comments": "this is an example",
  "mode": "manual",
  "user": "test_user",
  "check_in_shift": false
}'''
    assign_case_response = client.post("/api/assign-case", data=case_data, auth=("test_user", "password"))
    assert assign_case_response.status_code == 400

def test_7_assign_case_401(client):
    initialize_all(client)
    case_data = '''{
  "case_id": "2023-0910-029384",
  "product": "P1",
  "priority": "P2",
  "comments": "this is an example",
  "mode": "manual",
  "user": "test_user",
  "check_in_shift": false
}'''
    assign_case_response = client.post("/api/assign-case", data=case_data, auth=("test_user", "password1"))
    assert assign_case_response.status_code == 401

# Reassign a case in auto mode, fails with 400
def test_8_reassign_case_auto_400(client):
    initialize_all(client)
    case_data = '''{
  "case_id": "2023-0910-029384",
  "product": "P1",
  "priority": "P2",
  "comments": "this is an example",
  "mode": "auto",
  "user": "test_user",
  "check_in_shift": false
}'''
    assign_case_response = client.post("/api/assign-case", data=case_data, auth=("test_user", "password"))
    assign_case2_response = client.post("/api/assign-case", data=case_data, auth=("test_user", "password"))
    assert assign_case2_response.status_code == 400

# No other user exists to auto-reassign the case
def test_9_auto_reassign_case_auto_404(client):
    initialize_all(client)
    case_data = '''{
  "case_id": "2023-0910-029384",
  "product": "P1",
  "priority": "P2",
  "comments": "this is an example",
  "mode": "auto-reassign",
  "user": "test_user",
  "check_in_shift": false
}'''
    assign_case_response = client.post("/api/assign-case", data=case_data, auth=("test_user", "password"))
    assign_case2_response = client.post("/api/assign-case", data=case_data, auth=("test_user", "password"))
    assert assign_case2_response.status_code == 404

# auto-reassign case, success
def test_10_auto_reassign_case_auto_200(client):
    initialize_all(client)
    # create second user
    user2_data = '''{
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
    client.post("/api/user", data=user2_data, auth=("admin", "admin"))
    user2_product_data = '''{
  "productname": "P1",
  "username": "test_user2",
  "active": true,
  "quota": 1
}'''
    client.post("/api/user-product", data=user2_product_data, auth=("admin", "admin"))
    case_data = '''{
  "case_id": "2023-0910-029384",
  "product": "P1",
  "priority": "P2",
  "comments": "this is an example",
  "mode": "auto-reassign",
  "user": "test_user",
  "check_in_shift": false
}'''
    assign_case_response = client.post("/api/assign-case", data=case_data, auth=("test_user", "password"))
    assign_case2_response = client.post("/api/assign-case", data=case_data, auth=("test_user", "password"))
    assert assign_case2_response.status_code == 200
    assert assign_case2_response.content_type == "application/json"

def test_11_reassign_case_manual(client):
    initialize_all(client)
    case_data = '''{
  "case_id": "2023-0910-029384",
  "product": "P1",
  "priority": "P2",
  "comments": "this is an example",
  "mode": "manual",
  "user": "test_user",
  "check_in_shift": false
}'''
    assign_case_response = client.post("/api/assign-case", data=case_data, auth=("test_user", "password"))
    assign_case2_response = client.post("/api/assign-case", data=case_data, auth=("test_user", "password"))
    assert assign_case2_response.status_code == 200

def test_12_unassign_case(client):
    initialize_all(client)
    case_data = '''{
  "case_id": "2023-0910-029384",
  "product": "P1",
  "priority": "P2",
  "comments": "this is an example",
  "mode": "manual",
  "user": "test_user",
  "check_in_shift": false
}'''
    assign_case_response = client.post("/api/assign-case", data=case_data, auth=("test_user", "password"))
    unassign_case_data = '''{
  "comments": "testing"
}'''
    unassign_case_response = client.post("/api/unassign-case/2023-0910-029384", data=unassign_case_data, auth=("test_user", "password"))
    assert unassign_case_response.status_code == 200

def test_13_unassign_case_401(client):
    initialize_all(client)
    case_data = '''{
  "case_id": "2023-0910-029384",
  "product": "P1",
  "priority": "P2",
  "comments": "this is an example",
  "mode": "manual",
  "user": "test_user",
  "check_in_shift": false
}'''
    assign_case_response = client.post("/api/assign-case", data=case_data, auth=("test_user", "password"))
    unassign_case_data = '''{
  "comments": "testing"
}'''
    unassign_case_response = client.post("/api/unassign-case/2023-0910-029384", data=unassign_case_data, auth=("test_user", "password1"))
    assert unassign_case_response.status_code == 401

def test_14_unassign_case_404(client):
    initialize_all(client)
    case_data = '''{
  "case_id": "2023-0910-029384",
  "product": "P1",
  "priority": "P2",
  "comments": "this is an example",
  "mode": "manual",
  "user": "test_user",
  "check_in_shift": false
}'''
    assign_case_response = client.post("/api/assign-case", data=case_data, auth=("test_user", "password"))
    unassign_case_data = '''{
  "comments": "testing"
}'''
    unassign_case_response = client.post("/api/unassign-case/2023-0910-029385", data=unassign_case_data, auth=("test_user", "password"))
    assert unassign_case_response.status_code == 404
  
def test_15_get_cases(client):
    initialize_all(client)
    case_data = '''{
  "case_id": "2023-0910-029384",
  "product": "P1",
  "priority": "P2",
  "comments": "this is an example",
  "mode": "auto",
  "user": "test_user",
  "check_in_shift": false
}'''
    assign_case_response = client.post("/api/assign-case", data=case_data, auth=("test_user", "password"))
    get_cases_response = client.get("/api/cases?page=1", auth=("test_user", "password"))
    assert get_cases_response.status_code == 200
    assert get_cases_response.content_type == "application/json"

def test_16_get_cases_401(client):
    get_cases_response = client.get("/api/cases?page=1", auth=("test_user", "password"))
    assert get_cases_response.status_code == 401

def test_17_get_case(client):
    initialize_all(client)
    case_data = '''{
  "case_id": "2023-0910-029384",
  "product": "P1",
  "priority": "P2",
  "comments": "this is an example",
  "mode": "auto",
  "user": "test_user",
  "check_in_shift": false
}'''
    assign_case_response = client.post("/api/assign-case", data=case_data, auth=("test_user", "password"))
    get_case_response = client.get("/api/case/2023-0910-029384", auth=("test_user", "password"))
    assert get_case_response.status_code == 200
    assert get_case_response.content_type == "application/json"

def test_18_get_case_401(client):
    get_case_response = client.get("/api/case/2023-0910-029384", auth=("test_user", "password"))
    assert get_case_response.status_code == 401

def test_19_get_case_404(client):
    initialize_team(client)
    initialize_product(client)
    initialize_user(client)
    get_case_response = client.get("/api/case/2023-0910-029384", auth=("test_user", "password"))
    assert get_case_response.status_code == 404

def test_20_get_cases_of_product(client):
    initialize_all(client)
    case_data = '''{
  "case_id": "2023-0910-029384",
  "product": "P1",
  "priority": "P2",
  "comments": "this is an example",
  "mode": "auto",
  "user": "test_user",
  "check_in_shift": false
}'''
    assign_case_response = client.post("/api/assign-case", data=case_data, auth=("test_user", "password"))
    get_cases_response = client.get("/api/cases-of-product/P1", auth=("test_user", "password"))
    assert get_cases_response.status_code == 200
    assert get_cases_response.content_type == "application/json"

def test_21_get_cases_of_product_401(client):
    get_case_response = client.get("/api/cases-of-product/P1", auth=("test_user", "password"))
    assert get_case_response.status_code == 401

def test_22_get_cases_of_product_404(client):
    initialize_team(client)
    initialize_product(client)
    initialize_user(client)
    get_case_response = client.get("/api/cases-of-product/P2", auth=("test_user", "password"))
    assert get_case_response.status_code == 404

def test_23_get_cases_of_team(client):
    initialize_all(client)
    case_data = '''{
  "case_id": "2023-0910-029384",
  "product": "P1",
  "priority": "P2",
  "comments": "this is an example",
  "mode": "auto",
  "user": "test_user",
  "check_in_shift": false
}'''
    assign_case_response = client.post("/api/assign-case", data=case_data, auth=("test_user", "password"))
    get_cases_response = client.get("/api/cases-of-team/T1", auth=("test_user", "password"))
    assert get_cases_response.status_code == 200
    assert get_cases_response.content_type == "application/json"

def test_24_get_cases_of_team_401(client):
    get_case_response = client.get("/api/cases-of-team/T1", auth=("test_user", "password"))
    assert get_case_response.status_code == 401

def test_25_get_cases_of_team_404(client):
    initialize_team(client)
    initialize_product(client)
    initialize_user(client)
    get_case_response = client.get("/api/cases-of-team/T2", auth=("test_user", "password"))
    assert get_case_response.status_code == 404

def test_26_get_cases_assigned_by_user(client):
    initialize_all(client)
    case_data = '''{
  "case_id": "2023-0910-029384",
  "product": "P1",
  "priority": "P2",
  "comments": "this is an example",
  "mode": "auto",
  "user": "test_user",
  "check_in_shift": false
}'''
    assign_case_response = client.post("/api/assign-case", data=case_data, auth=("test_user", "password"))
    get_cases_response = client.get("/api/cases-assigned-by-user/test_user", auth=("test_user", "password"))
    assert get_cases_response.status_code == 200
    assert get_cases_response.content_type == "application/json"

def test_27_get_cases_assigned_by_user_401(client):
    get_case_response = client.get("/api/cases-assigned-by-user/test_user", auth=("test_user", "password"))
    assert get_case_response.status_code == 401

def test_28_get_cases_assigned_by_user_404(client):
    initialize_team(client)
    initialize_product(client)
    initialize_user(client)
    get_case_response = client.get("/api/cases-assigned-by-user/test_user1", auth=("test_user", "password"))
    assert get_case_response.status_code == 404

def test_29_get_cases_of_user(client):
    initialize_all(client)
    case_data = '''{
  "case_id": "2023-0910-029384",
  "product": "P1",
  "priority": "P2",
  "comments": "this is an example",
  "mode": "auto",
  "user": "test_user",
  "check_in_shift": false
}'''
    assign_case_response = client.post("/api/assign-case", data=case_data, auth=("test_user", "password"))
    get_cases_response = client.get("/api/cases-of-user/test_user", auth=("test_user", "password"))
    assert get_cases_response.status_code == 200
    assert get_cases_response.content_type == "application/json"

def test_30_get_cases_of_user_401(client):
    get_case_response = client.get("/api/cases-of-user/test_user", auth=("test_user", "password"))
    assert get_case_response.status_code == 401

def test_31_get_of_user_404(client):
    initialize_team(client)
    initialize_product(client)
    initialize_user(client)
    get_case_response = client.get("/api/cases-of-user/test_user1", auth=("test_user", "password"))
    assert get_case_response.status_code == 404

def test_32_get_case_count_users(client):
    initialize_all(client)
    case_data = '''{
  "case_id": "2023-0910-029384",
  "product": "P1",
  "priority": "P2",
  "comments": "this is an example",
  "mode": "auto",
  "user": "test_user",
  "check_in_shift": false
}'''
    assign_case_response = client.post("/api/assign-case", data=case_data, auth=("test_user", "password"))
    query_data = '''{
  "period": 3,
  "interval": 1,
  "productname": "P1",
  "teamname": "T1"
}'''
    get_case_count_response = client.post("/api/case-count-of-all-users", data=query_data, auth=("test_user", "password"))
    assert get_case_count_response.status_code == 200
    assert get_case_count_response.content_type == "application/json"

def test_33_get_case_count_users_401(client):
    query_data = '''{
  "period": 3,
  "interval": 1,
  "productname": "P1",
  "teamname": "T1"
}'''
    get_case_response = client.post("/api/case-count-of-all-users", data=query_data, auth=("test_user", "password"))
    assert get_case_response.status_code == 401

def test_34_get_case_count_users_404(client):
    initialize_team(client)
    initialize_user(client)
    query_data = '''{
  "period": 3,
  "interval": 1,
  "productname": "P1",
  "teamname": "T1"
}'''
    get_case_response = client.post("/api/case-count-of-all-users", data=query_data, auth=("test_user", "password"))
    assert get_case_response.status_code == 404

def test_35_get_case_count_users_400(client):
    initialize_team(client)
    initialize_user(client)
    query_data = '''{
  "period": 3,
  "productname": "P1",
  "teamname": "T1"
}'''
    get_case_response = client.post("/api/case-count-of-all-users", data=query_data, auth=("test_user", "password"))
    assert get_case_response.status_code == 400