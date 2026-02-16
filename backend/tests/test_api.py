from unittest.mock import MagicMock, patch


def test_health_returns_ok(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_hello_returns_message(client):
    response = client.get("/api/v1/hello")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Mapping Business Resilience."


def test_nonexistent_route_returns_404(client):
    response = client.get("/api/v1/nonexistent")
    assert response.status_code == 404


# -- Documents --

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


# -- Prompts --

def test_list_prompts_has_default(client):
    response = client.get("/api/v1/prompts")
    assert response.status_code == 200
    prompts = response.json()["prompts"]
    assert len(prompts) >= 1
    assert "sustainability analyst" in prompts[0]["text"]


def test_create_prompt(client):
    response = client.post("/api/v1/prompts", json={"text": "Test prompt"})
    assert response.status_code == 201
    data = response.json()
    assert data["text"] == "Test prompt"
    assert "id" in data


# -- Runs --

def test_list_runs_empty(client):
    response = client.get("/api/v1/runs")
    assert response.status_code == 200
    assert response.json() == {"runs": []}


def test_get_run_not_found(client):
    response = client.get("/api/v1/runs/nonexistent")
    assert response.status_code == 404


# -- Analyse --

def test_analyse_missing_api_key(client):
    from app.config import settings
    original_key = settings.anthropic_api_key
    settings.anthropic_api_key = ""

    try:
        prompts = client.get("/api/v1/prompts").json()["prompts"]
        client.post(
            "/api/v1/documents",
            files={"file": ("report.txt", b"Some report content", "text/plain")},
        )
        docs = client.get("/api/v1/documents").json()["files"]

        response = client.post("/api/v1/analyse", json={
            "prompt_id": prompts[0]["id"],
            "document_filename": docs[0]["filename"],
        })
        assert response.status_code == 500
        assert "ANTHROPIC_API_KEY" in response.json()["detail"]
    finally:
        settings.anthropic_api_key = original_key


def test_analyse_with_mocked_anthropic(client):
    from app.config import settings
    original_key = settings.anthropic_api_key
    settings.anthropic_api_key = "test-key"

    try:
        prompts = client.get("/api/v1/prompts").json()["prompts"]
        client.post(
            "/api/v1/documents",
            files={"file": ("report.txt", b"ESG report content here", "text/plain")},
        )
        docs = client.get("/api/v1/documents").json()["files"]

        mock_response = MagicMock()
        mock_content = MagicMock()
        mock_content.text = '{"claims": []}'
        mock_response.content = [mock_content]

        with patch("app.routes.anthropic.Anthropic") as mock_cls:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_response
            mock_cls.return_value = mock_client

            response = client.post("/api/v1/analyse", json={
                "prompt_id": prompts[0]["id"],
                "document_filename": docs[0]["filename"],
            })

        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "complete"
        assert data["output"] == '{"claims": []}'
        assert data["duration_ms"] is not None

        # Verify run is persisted
        run_response = client.get(f"/api/v1/runs/{data['id']}")
        assert run_response.status_code == 200
        assert run_response.json()["status"] == "complete"

        # Verify run shows in list
        runs = client.get(f"/api/v1/runs?document_filename={docs[0]['filename']}").json()["runs"]
        assert len(runs) == 1
    finally:
        settings.anthropic_api_key = original_key
