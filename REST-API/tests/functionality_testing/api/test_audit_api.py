def test_1_get_audit(client):
    response = client.get("/api/audit/1", auth=("admin", "admin"))
    assert response.status_code == 200
    assert response.content_type == "application/json"

def test_2_get_audit_401(client):
    response = client.get("/api/audit/1", auth=("admin", "admin1"))
    assert response.status_code == 401
