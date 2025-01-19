def test_1_get_teams(client):
    response = client.get("/api/teams", auth=("admin", "admin"))
    assert response.status_code == 200
    assert response.content_type == "application/json"

def test_2_get_teams_401(client):
    response = client.get("/api/teams", auth=("admin", "admin1"))
    assert response.status_code == 401

def test_3_get_users_of_team(client):
    response = client.get("/api/users-of-team/global", auth=("admin", "admin"))
    assert response.status_code == 200
    assert response.content_type == "application/json"

def test_4_get_users_of_team_404(client):
    response = client.get("/api/users-of-team/global1", auth=("admin", "admin"))
    assert response.status_code == 404

def test_5_get_team(client):
    response = client.get("/api/team/global", auth=("admin", "admin"))
    assert response.status_code == 200
    assert response.content_type == "application/json"

def test_6_get_team_401(client):
    response = client.get("/api/team/global1", auth=("admin", "admin"))
    assert response.status_code == 404

def test_7_add_team(client):
    data = '''{
  "email": "abc@xyz.com",
  "mswebhook": "",
  "teamname": "T1"
}'''
    response = client.post("/api/team", data=data, auth=("admin", "admin"))
    assert response.status_code == 200
    assert response.content_type == "application/json"

def test_8_add_team_400(client):
    data = '''{
  "email": "abc@xyz.com",
  "mswebhook": ""
}'''
    response = client.post("/api/team", data=data, auth=("admin", "admin"))
    assert response.status_code == 400

def test_9_edit_team(client):
    add_team_data = '''{
  "email": "abc@xyz.com",
  "mswebhook": "",
  "teamname": "T1"
}'''
    add_team_response = client.post("/api/team", data=add_team_data, auth=("admin", "admin"))
    edit_team_data = '''{
  "email": "cde@xyz.com"
}'''
    edit_team_response = client.post("/api/team/T1", data=edit_team_data, auth=("admin", "admin"))
    assert edit_team_response.status_code == 200
    assert edit_team_response.content_type == "application/json"

def test_10_edit_team_404(client):
    edit_team_data = '''{
  "email": "cde@xyz.com"
}'''
    edit_team_response = client.post("/api/team/T2", data=edit_team_data, auth=("admin", "admin"))
    assert edit_team_response.status_code == 404

def test_11_edit_team_400(client):
    edit_team_data = '''{
  "email": "cde@xyz.com",
}'''
    edit_team_response = client.post("/api/team/T2", data=edit_team_data, auth=("admin", "admin"))
    assert edit_team_response.status_code == 400

def test_12_delete_team(client):
    add_team_data = '''{
  "email": "abc@xyz.com",
  "mswebhook": "",
  "teamname": "T1"
}'''
    add_team_response = client.post("/api/team", data=add_team_data, auth=("admin", "admin"))
    delete_team_response = client.delete("/api/team/T1", auth=("admin", "admin"))
    assert delete_team_response.status_code == 200
    assert delete_team_response.content_type == "application/json"

def test_13_delete_team_404(client):
    delete_team_response = client.delete("/api/team/T1", auth=("admin", "admin"))
    assert delete_team_response.status_code == 404
