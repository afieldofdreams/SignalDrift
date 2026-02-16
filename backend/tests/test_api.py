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
    assert data["message"] == "Mapping Business Resilience."


def test_nonexistent_route_returns_404(client):
    response = client.get("/api/v1/nonexistent")
    assert response.status_code == 404


def test_list_documents_empty(client):
    response = client.get("/api/v1/documents")
    assert response.status_code == 200
    assert response.json() == {"files": []}


def test_upload_valid_document(client):
    response = client.post(
        "/api/v1/documents",
        files={"file": ("test.pdf", b"fake pdf content", "application/pdf")},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["original_name"] == "test.pdf"
    assert data["size"] == len(b"fake pdf content")
    assert "filename" in data


def test_upload_rejected_extension(client):
    response = client.post(
        "/api/v1/documents",
        files={"file": ("malware.exe", b"bad stuff", "application/octet-stream")},
    )
    assert response.status_code == 400
    assert "not allowed" in response.json()["detail"]


def test_list_documents_after_upload(client):
    client.post(
        "/api/v1/documents",
        files={"file": ("notes.txt", b"hello world", "text/plain")},
    )
    response = client.get("/api/v1/documents")
    assert response.status_code == 200
    files = response.json()["files"]
    assert len(files) == 1
    assert files[0]["size"] == len(b"hello world")
    assert "notes.txt" in files[0]["filename"]


def test_delete_document(client):
    upload = client.post(
        "/api/v1/documents",
        files={"file": ("to_delete.txt", b"bye", "text/plain")},
    )
    filename = upload.json()["filename"]

    response = client.delete(f"/api/v1/documents/{filename}")
    assert response.status_code == 200
    assert response.json() == {"deleted": filename}

    listing = client.get("/api/v1/documents")
    assert listing.json() == {"files": []}


def test_delete_nonexistent_returns_404(client):
    response = client.delete("/api/v1/documents/nonexistent.txt")
    assert response.status_code == 404
