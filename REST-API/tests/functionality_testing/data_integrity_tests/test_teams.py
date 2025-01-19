import json

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
  "sf_platform": "PL1"
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

def test_1_add_team(client):
    initialize_team(client)
    initialize_user(client)
    get_team_response = client.get("/api/team/T1", auth=("admin", "admin"))
    team_schema = get_team_response.json
    assert team_schema.get('teamname') == "T1" and \
           team_schema.get('mswebhook') == "" and \
           team_schema.get('email') == "abc@xyz.com" and \
           team_schema.get('users') == ['test_user']

# Change all possible editable fields and validate
def test_2_edit_team(client):
    initialize_team(client)
    initialize_user(client)
    edit_team_data = '''{
  "email": "cde@xyz.com",
  "mswebhook": "htts://xyz.com"
}'''
    # First delete the user so the team 'user' field is modified
    delete_user_response = client.delete("/api/user/test_user", auth=("admin", "admin"))
    edit_team_response = client.post("/api/team/T1", data=edit_team_data, auth=("admin", "admin"))
    team_schema = edit_team_response.json
    assert team_schema.get('teamname') == "T1" and \
           team_schema.get('mswebhook') == "htts://xyz.com" and \
           team_schema.get('email') == "cde@xyz.com" and \
           team_schema.get('users') == []

def test_3_delete_team(client):
    initialize_team(client)
    delete_team_response = client.delete("/api/team/T1", auth=("admin", "admin"))
    get_team_response = client.get("/api/team/T1", auth=("admin", "admin"))
    assert get_team_response.status_code == 404