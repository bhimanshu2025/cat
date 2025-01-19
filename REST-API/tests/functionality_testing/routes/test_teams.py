def login(client):
    return client.post("/login", data={"username": "admin", "password": "admin"}, follow_redirects=True)

def logout(client):
    return client.get("/logout", follow_redirects=True)

def initializa_team(client):
    login(client)
    add_team_data = {
    'teamname': "T1",
    'email': "T1@abc.xyz",
    'mswebhook': ""
    }
    return client.post("/add_team", data=add_team_data, follow_redirects=True)

def test_1_get_teams(client):
    login_response = login(client)
    get_teams_response = client.get("/teams", follow_redirects=True)
    assert b"<title> CAT Teams</title>" in get_teams_response.data

def test_2_get_teams_401(client):
    get_teams_response = client.get("/teams", follow_redirects=True)
    assert get_teams_response.status_code == 401

def test_3_add_team_get(client):
    login_response = login(client)
    add_team_response = client.get("/add_team", follow_redirects=True)
    assert b"<title> CAT Add Team</title>" in add_team_response.data

def test_4_add_team_get_401(client):
    add_team_response = client.get("/add_team", follow_redirects=True)
    assert add_team_response.status_code == 401

# success
def test_5_add_team_post(client):
    login_response = login(client)
    add_team_data = {
    'teamname': "T1",
    'email': "T1@abc.xyz",
    'mswebhook': ""
    }
    add_team_response = client.post("/add_team", data=add_team_data, follow_redirects=True)
    assert b"Team T1 created" in add_team_response.data

def test_6_add_team_post_401(client):
    add_team_data = {
    'teamname': "T1",
    'email': "T1@abc.xyz",
    'mswebhook': ""
    }
    add_team_response = client.post("/add_team", data=add_team_data, follow_redirects=True)
    assert add_team_response.status_code == 401

def test_7_edit_team_get(client):
    initializa_team(client)
    edit_team_response = client.get("/edit_team/T1", follow_redirects=True)
    assert b"<title> CAT Edit Team</title>" in edit_team_response.data

def test_8_edit_team_get_401(client):
    initializa_team(client)
    logout(client)
    edit_team_response = client.get("/edit_team/T1", follow_redirects=True)
    assert edit_team_response.status_code == 401

# sucess
def test_9_edit_team_post(client):
    initializa_team(client)
    edit_team_data = {
    'email': "T1@cde.xyz",
    'mswebhook': ""
    }
    edit_team_response = client.post("/edit_team/T1", data=edit_team_data, follow_redirects=True)
    assert b"Team T1 updated" in edit_team_response.data

def test_10_edit_team_post_401(client):
    edit_team_data = {
    'email': "T1@cde.xyz",
    'mswebhook': ""
    }
    edit_team_response = client.post("/edit_team/T1", data=edit_team_data, follow_redirects=True)
    assert edit_team_response.status_code == 401

# team not found
def test_11_edit_team_post_404(client):
    initializa_team(client)
    edit_team_data = {
    'email': "T1@cde.xyz",
    'mswebhook': ""
    }
    edit_team_response = client.post("/edit_team/T2", data=edit_team_data, follow_redirects=True)
    assert b"Team T2 not found" in edit_team_response.data

# success
def test_12_delete_team(client):
    initializa_team(client)
    delete_team_response = client.post("/delete_team/T1", follow_redirects=True)
    assert b"Team T1 deleted" in delete_team_response.data

# team not found
def test_13_delete_team_404(client):
    initializa_team(client)
    delete_team_response = client.post("/delete_team/T2", follow_redirects=True)
    assert b"Team T2 not found" in delete_team_response.data

def test_14_delete_team_401(client):
    delete_team_response = client.post("/delete_team/T2", follow_redirects=True)
    assert delete_team_response.status_code == 401