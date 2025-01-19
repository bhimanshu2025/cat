def login(client):
    return client.post("/login", data={"username": "admin", "password": "admin"}, follow_redirects=True)

def logout(client):
    return client.get("/logout", follow_redirects=True)

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

def test_1_get_products(client):
    initialize_product(client)
    get_products_response = client.get("/products", follow_redirects=True)
    assert b"<title> CAT Products</title>" in get_products_response.data

def test_2_get_products_401(client):
    get_products_response = client.get("/products", follow_redirects=True)
    assert get_products_response.status_code == 401

def test_3_add_product_get(client):
    login_response = login(client)
    add_product_response = client.get("/add_product", follow_redirects=True)
    assert b"<title> CAT Add Product</title>" in add_product_response.data

def test_4_add_product_get_401(client):
    add_product_response = client.get("/add_product", follow_redirects=True)
    assert add_product_response.status_code == 401

# success
def test_5_add_product_post(client):
    login_response = login(client)
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
    add_product_response = client.post("/add_product", data=add_product_data, follow_redirects=True)
    assert b"Product P1 created" in add_product_response.data

# auth failure
def test_6_add_product_post_401(client):
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
            'sf_platform': ""
        }
    add_product_response = client.post("/add_product", data=add_product_data, follow_redirects=True)
    assert add_product_response.status_code == 401

def test_7_edit_product_get(client):
    initialize_product(client)
    edit_product_response = client.get("/edit_product/P1", follow_redirects=True)
    assert b"<title> CAT Edit Product</title>" in edit_product_response.data

def test_8_edit_product_get_401(client):
    initialize_product(client)
    logout(client)
    edit_product_response = client.get("/edit_product/P1", follow_redirects=True)
    assert edit_product_response.status_code == 401

# success
def test_9_edit_product_post(client):
    initialize_product(client)
    edit_product_data = {
            'strategy': "s2",
            'case_regex': "^[0-9]{4}-[0-9]{4}-[0-9]{6}$",
            'max_days_month': 300,
            'max_days': 6
        }
    edit_product_response = client.post("/edit_product/P1", data=edit_product_data, follow_redirects=True)
    assert b"Product P1 updated" in edit_product_response.data

# Product doesnt exist
def test_10_edit_product_post_404(client):
    login(client)
    edit_product_data = {
            'strategy': "s2",
            'case_regex': "^[0-9]{4}-[0-9]{4}-[0-9]{6}$",
            'max_days_month': 300,
            'max_days': 6
        }
    edit_product_response = client.post("/edit_product/P1", data=edit_product_data, follow_redirects=True)
    assert b"Product P1 not found" in edit_product_response.data

def test_11_edit_product_post_401(client):
    edit_product_data = {
            'strategy': "s2",
            'case_regex': "^[0-9]{4}-[0-9]{4}-[0-9]{6}$",
            'max_days_month': 300,
            'max_days': 6
        }
    edit_product_response = client.post("/edit_product/P1", data=edit_product_data, follow_redirects=True)
    assert edit_product_response.status_code == 401

# sf_enabled is try but sf_job_cron is empty
def test_12_edit_product_post_400(client):
    initialize_product(client)
    edit_product_data = {
            'strategy': "s2",
            'case_regex': "^[0-9]{4}-[0-9]{4}-[0-9]{6}$",
            'sf_enabled': True,
            'max_days_month': 300,
            'max_days': 6,
            'sf_job_cron': ""
        }
    edit_product_response = client.post("/edit_product/P1", data=edit_product_data, follow_redirects=True)
    assert b"This field can not be empty if Salesforce is enabled" in edit_product_response.data

def test_13_delete_product(client):
    initialize_product(client)
    delete_product_response = client.post("/delete_product/P1", follow_redirects=True)
    assert b"Product P1 deleted" in delete_product_response.data

# Product doesnt exist
def test_14_delete_product_404(client):
    initialize_product(client)
    delete_product_response = client.post("/delete_product/P2", follow_redirects=True)
    assert b"Product P2 not found" in delete_product_response.data

def test_15_delete_product_401(client):
    delete_product_response = client.post("/delete_product/P1", follow_redirects=True)
    assert delete_product_response.status_code == 401