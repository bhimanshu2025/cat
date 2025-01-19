import json 

def login(client, username="admin", password="admin"):
    return client.post("/login", data={"username": username, "password": password}, follow_redirects=True)

def logout(client):
    return client.get("/logout", follow_redirects=True)

def initialize_team(client):
    team_data = '''{
  "email": "abc@xyz.com",
  "mswebhook": "",
  "teamname": "T1"
}'''
    create_team_response = client.post("/api/team", data=team_data, auth=("admin", "admin"))

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
    create_user_response = client.post("/api/user", data=user_data, auth=("admin", "admin"))

def initialize_product(client):
    product_data = '''{
  "strategy": "s1",
  "max_days": "7",
  "max_days_month": "300",
  "case_regex": "^[0-9]{4}-[0-9]{4}-[0-9]{6}$",
  "quota_over_days": 1,
  "sf_api": "",
  "sf_enabled": false,
  "sf_job_cron": "* 6-18 * * 1-5",
  "sf_job_timezone": "US/Pacific",
  "sf_job_query_interval": 1,
  "productname": "P1",
  "sf_init_email_name": ""
}'''
    create_product_response = client.post("/api/product", data=product_data, auth=("admin", "admin"))

def initialize_userproduct(client):
    user_product_data = '''{
  "productname": "P1",
  "username": "test_user",
  "active": true,
  "quota": 1
}'''
    user_product_response = client.post("/api/user-product", data=user_product_data, auth=("admin", "admin"))

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

# success
def test_1_add_product(client):
    data = '''{
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
  "sf_init_email_name": ""
}'''
    response = client.post("/api/product", data=data, auth=("admin", "admin"))
    assert response.status_code == 200
    assert response.content_type == "application/json"

# sf_enabled is true and no sf_query_interval given
def test_2_add_product_400(client):
    data = '''{
  "strategy": "s1",
  "max_days": "3",
  "max_days_month": "300",
  "case_regex": "^[0-9]{4}-[0-9]{4}-[0-9]{6}$",
  "quota_over_days": 1,
  "sf_api": "http://salesforce.com",
  "sf_enabled": true,
  "sf_job_timezone": "US/Pacific",
  "productname": "P1",
  "sf_init_email_name": ""
}'''
    response = client.post("/api/product", data=data, auth=("admin", "admin"))
    assert response.status_code == 400

def test_3_add_product_401(client):
    data = '''{
  "strategy": "s1",
  "max_days": "3",
  "max_days_month": "300",
  "case_regex": "^[0-9]{4}-[0-9]{4}-[0-9]{6}$",
  "quota_over_days": 1,
  "sf_api": "http://salesforce.com",
  "sf_job_timezone": "US/Pacific",
  "productname": "P1",
  "sf_init_email_name": ""
}'''
    response = client.post("/api/product", data=data, auth=("admin", "admin1"))
    assert response.status_code == 401

def test_4_get_products(client):
    initialize_product(client)
    get_product_response = client.get("/api/products", auth=("admin", "admin"))
    assert get_product_response.status_code == 200
    assert get_product_response.content_type == "application/json"

def test_5_get_products_401(client):
    response = client.get("/api/products", auth=("admin", "admin1"))
    assert response.status_code == 401

def test_6_get_product(client):
    initialize_product(client)
    get_product_response = client.get("/api/product/P1", auth=("admin", "admin"))
    assert get_product_response.status_code == 200
    assert get_product_response.content_type == "application/json"

def test_7_get_product_401(client):
    response = client.get("/api/product/P1", auth=("admin", "admin1"))
    assert response.status_code == 401

def test_8_get_product_404(client):
    response = client.get("/api/product/P1", auth=("admin", "admin"))
    assert response.status_code == 404

def test_9_edit_product(client):
    initialize_product(client)
    edit_product_data = '''{
  "strategy": "s2"
}'''
    edit_product_response = client.post("/api/product/P1", data=edit_product_data, auth=("admin", "admin"))
    assert edit_product_response.status_code == 200
    assert edit_product_response.content_type == "application/json"

def test_10_edit_product_404(client):
    edit_product_data = '''{
  "strategy": "s2"
}'''
    edit_product_response = client.post("/api/product/P1", data=edit_product_data, auth=("admin", "admin"))
    assert edit_product_response.status_code == 404

def test_11_edit_product_401(client):
    edit_product_data = '''{
  "strategy": "s2"
}'''
    edit_product_response = client.post("/api/product/P1", data=edit_product_data, auth=("admin", "admin1"))
    assert edit_product_response.status_code == 401

# sf_enabled is true, while sf_job_cron is empty
def test_12_edit_product_400(client):
    add_product_data = '''{
  "strategy": "s1",
  "max_days": "3",
  "max_days_month": "300",
  "case_regex": "^[0-9]{4}-[0-9]{4}-[0-9]{6}$",
  "quota_over_days": 1,
  "sf_api": "",
  "sf_job_timezone": "US/Pacific",
  "sf_job_query_interval": 1,
  "productname": "P1",
  "sf_product_series": "PTXX"
}'''
    add_product_response = client.post("/api/product", data=add_product_data, auth=("admin", "admin"))
    edit_product_data = '''{
  "sf_enabled": true
}'''
    edit_product_response = client.post("/api/product/P1", data=edit_product_data, auth=("admin", "admin"))
    assert edit_product_response.status_code == 400

def test_13_delete_product(client):
    initialize_product(client)
    delete_product_response = client.delete("/api/product/P1", auth=("admin", "admin"))
    assert delete_product_response.status_code == 200
    assert delete_product_response.content_type == "application/json"

def test_14_delete_product_401(client):
    delete_product_response = client.delete("/api/product/P1", auth=("admin", "admin1"))
    assert delete_product_response.status_code == 401

def test_15_delete_product_404(client):
    delete_product_response = client.delete("/api/product/P1", auth=("admin", "admin"))
    assert delete_product_response.status_code == 404

def test_16_get_users_of_product(client):
    initialize_team(client)
    initialize_product(client)
    initialize_user(client)
    initialize_userproduct(client)
    response = client.get("api/users-of-product/P1", auth=("admin", "admin"))
    assert response.status_code == 200

def test_17_get_users_of_product_401(client):
    initialize_team(client)
    initialize_product(client)
    initialize_user(client)
    initialize_userproduct(client)
    response = client.get("api/users-of-product/P1", auth=("admin", "admin1"))
    assert response.status_code == 401

def test_18_get_users_of_product_404(client):
    response = client.get("api/users-of-product/P1", auth=("admin", "admin"))
    assert response.status_code == 404

# success
def test_19_schedule_sf_integration(client):
    initialize_product(client)
    data = '''{
  "datetime": "2025/10/19 13:12",
  "timezone": "US/Pacific",
  "sf_enabled": true
}'''
    response = client.post("/api/product/schedule-sf-integration/P1", data=data, auth=("admin", "admin"))
    assert response.status_code == 200
    assert response.content_type == "application/json"

def test_20_schedule_sf_integration_401(client):
    initialize_product(client)
    data = '''{
  "datetime": "2025/10/19 13:12",
  "timezone": "US/Pacific",
  "sf_enabled": true
}'''
    response = client.post("/api/product/schedule-sf-integration/P1", data=data, auth=("admin", "admin1"))
    assert response.status_code == 401

# Product doesnt exists
def test_21_schedule_sf_integration_404(client):
    data = '''{
  "datetime": "2025/10/19 13:12",
  "timezone": "US/Pacific",
  "sf_enabled": true
}'''
    response = client.post("/api/product/schedule-sf-integration/P1", data=data, auth=("admin", "admin"))
    assert response.status_code == 404

# mandatory argument missing
def test_22_schedule_sf_integration_404(client):
    initialize_product(client)
    data = '''{
  "datetime": "2025/10/19 13:12",
  "timezone": "US/Pacific"
}'''
    response = client.post("/api/product/schedule-sf-integration/P1", data=data, auth=("admin", "admin"))
    assert response.status_code == 404

# success
def test_23_delete_product_job(client):
    initialize_product(client)
    data = '''{
  "datetime": "2025/10/19 13:12",
  "timezone": "US/Pacific",
  "sf_enabled": true
}'''
    create_job_response = client.post("/api/product/schedule-sf-integration/P1", data=data, auth=("admin", "admin"))
    delete_product_job_response = client.delete(f"/api/product/delete-job/{create_job_response.json}", auth=("admin", "admin"))
    assert delete_product_job_response.status_code == 200
    assert delete_product_job_response.content_type == "application/json"

# invalid credentials
def test_24_delete_product_job_401(client):
    initialize_product(client)
    data = '''{
  "datetime": "2025/10/19 13:12",
  "timezone": "US/Pacific",
  "sf_enabled": true
}'''
    create_job_response = client.post("/api/product/schedule-sf-integration/P1", data=data, auth=("admin", "admin"))
    delete_product_job_response = client.delete(f"/api/product/delete-job/{create_job_response.json}", auth=("admin", "admin1"))
    assert delete_product_job_response.status_code == 401

# job not found
def test_25_delete_product_job_404(client):
    delete_product_job_response = client.delete(f"/api/product/delete-job/invalid_job", auth=("admin", "admin"))
    assert delete_product_job_response.status_code == 404