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
  "sf_platform": "PL1",
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

def test_1_add_userproduct(client):
  initialize_all(client)
  get_user_product_response = client.get("/api/user-product/test_user/P1", auth=("admin", "admin"))
  userproduct_schema = get_user_product_response.json
  assert userproduct_schema.get('productname') == 'P1' and \
          userproduct_schema.get('username') == 'test_user' and \
          userproduct_schema.get('active') == True and \
          userproduct_schema.get('quota') == 1

# Update every modifiable field and validate
def test_2_edit_userproduct(client):
  initialize_all(client)
  edit_userproduct_data = '''{
  "productname": "P1",
  "username": "test_user",
  "quota": 2,
  "active": false
}'''
  edit_userproduct_response = client.post("/api/user-product", data=edit_userproduct_data, auth=("admin", "admin"))
  get_user_product_response = client.get("/api/user-product/test_user/P1", auth=("admin", "admin"))
  userproduct_schema = get_user_product_response.json
  assert userproduct_schema.get('productname') == 'P1' and \
          userproduct_schema.get('username') == 'test_user' and \
          userproduct_schema.get('active') == False and \
          userproduct_schema.get('quota') == 2

def test_3_delete_userproduct(client):
  initialize_all(client)
  delete_userproduct_response = client.delete("/api/user-product/test_user/P1", auth=("admin", "admin"))
  get_user_product_response = client.get("/api/user-product/test_user/P1", auth=("admin", "admin"))
  assert get_user_product_response.status_code == 400