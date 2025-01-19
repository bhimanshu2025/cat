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
  "sf_job_cron": "* 6-18 * * 1-5",
  "sf_job_timezone": "US/Pacific",
  "sf_job_query_interval": 1,
  "productname": "P1"
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

def initialize_all(client):
    initialize_team(client)
    initialize_user(client)
    initialize_product(client)
    initialize_userproduct(client)

def test_1_add_userproducts(client):
    initialize_team(client)
    initialize_product(client)
    initialize_user(client)
    user_product_data = '''{
  "productname": "P1",
  "username": "test_user",
  "active": true,
  "quota": 1
}'''
    user_product_response = client.post("/api/user-product", data=user_product_data, auth=("admin", "admin"))
    assert user_product_response.status_code == 200
    assert user_product_response.content_type == "application/json"

def test_2_add_userproducts_401(client):
    user_product_data = '''{
  "productname": "P1",
  "username": "test_user",
  "active": true,
  "quota": 1
}'''
    user_product_response = client.post("/api/user-product", data=user_product_data, auth=("admin", "admin1"))
    assert user_product_response.status_code == 401

def test_3_add_userproducts_400(client):
    user_product_data = '''{
  "username": "test_user",
  "active": true,
  "quota": 1
}'''
    user_product_response = client.post("/api/user-product", data=user_product_data, auth=("admin", "admin"))
    assert user_product_response.status_code == 400

def test_4_add_userproducts_404(client):
    user_product_data = '''{
  "productname": "P1",
  "username": "test_user",
  "active": true,
  "quota": 1
}'''
    user_product_response = client.post("/api/user-product", data=user_product_data, auth=("admin", "admin"))
    assert user_product_response.status_code == 404

def test_5_get_userproducts(client):
    initialize_all(client)
    response = client.get("/api/all-user-product", auth=("admin", "admin"))
    assert response.status_code == 200
    assert response.content_type == "application/json"

def test_6_get_userproducts_401(client):
    response = client.get("/api/all-user-product", auth=("admin", "admin1"))
    assert response.status_code == 401

def test_7_edit_userproducts(client):
    initialize_all(client)
    edit_userproduct_data = '''{
  "productname": "P1",
  "username": "test_user",
  "quota": 2
}'''
    edit_userproduct_response = client.post("/api/user-product", data=edit_userproduct_data, auth=("admin", "admin"))
    assert edit_userproduct_response.status_code == 200
    assert edit_userproduct_response.content_type == "application/json"

def test_8_edit_userproducts_401(client):
    edit_userproduct_data = '''{
  "productname": "P1",
  "username": "test_user",
  "quota": 2
}'''
    edit_userproduct_response = client.post("/api/user-product", data=edit_userproduct_data, auth=("admin", "admin1"))
    assert edit_userproduct_response.status_code == 401

def test_9_edit_userproducts_400(client):
    edit_userproduct_data = '''{
  "productname": "P1",
  "quota": 2
}'''
    edit_userproduct_response = client.post("/api/user-product", data=edit_userproduct_data, auth=("admin", "admin"))
    assert edit_userproduct_response.status_code == 400

def test_10_edit_userproducts_404(client):
    edit_userproduct_data = '''{
  "productname": "P1",
  "username": "test_user",
  "quota": 2
}'''
    edit_userproduct_response = client.post("/api/user-product", data=edit_userproduct_data, auth=("admin", "admin"))
    assert edit_userproduct_response.status_code == 404

def test_11_delete_userproducts(client):
    initialize_all(client)
    delete_userproduct_response = client.delete("/api/user-product/test_user/P1", auth=("admin", "admin"))
    assert delete_userproduct_response.status_code == 200
    assert delete_userproduct_response.content_type == "application/json"

def test_12_delete_userproducts_401(client):
    edit_userproduct_response = client.delete("/api/user-product/test_user/P1", auth=("admin", "admin1"))
    assert edit_userproduct_response.status_code == 401

def test_13_delete_userproducts_404(client):
    edit_userproduct_response = client.delete("/api/user-product/test_user/P1", auth=("admin", "admin"))
    assert edit_userproduct_response.status_code == 404

def test_14_get_userproduct(client):
    initialize_all(client)
    user_product_response = client.get("/api/user-product/test_user/P1", auth=("admin", "admin"))
    assert user_product_response.status_code == 200
    assert user_product_response.content_type == "application/json"

def test_15_get_userproduct_401(client):
    user_product_response = client.get("/api/user-product/test_user/P1", auth=("admin", "admin1"))
    assert user_product_response.status_code == 401

def test_16_get_userproduct_404(client):
    user_product_response = client.get("/api/user-product/test_user/P1", auth=("admin", "admin"))
    assert user_product_response.status_code == 404

def test_17_get_userproduct_400(client):
    initialize_team(client)
    initialize_product(client)
    initialize_user(client)
    user_product_response = client.get("/api/user-product/test_user/P1", auth=("admin", "admin"))
    assert user_product_response.status_code == 400