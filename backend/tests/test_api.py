def test_health_returns_ok(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data == {"status": "ok"}


def test_hello_returns_message(client):
    response = client.get("/api/v1/hello")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert data["message"] == "Hello, World!"


def test_nonexistent_route_returns_404(client):
    response = client.get("/api/v1/nonexistent")
    assert response.status_code == 404
