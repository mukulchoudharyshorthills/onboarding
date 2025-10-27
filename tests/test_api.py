import io
import os
import pytest
from unittest.mock import patch

# Mocked tests first
@patch("utils.extract_pii")
def test_upload_valid_image(mock_extract, client):
    """Test successful image upload and mocked PII extraction"""
    mock_extract.return_value = {
        "name": "John Doe",
        "email": "john@example.com"
    }

    img = io.BytesIO(b"fake image data")
    response = client.post(
        "/upload",
        data={"file": (img, "valid_image.jpg")},
        content_type="multipart/form-data"
    )

    assert response.status_code == 200
    json_data = response.get_json()
    assert "data" in json_data
    assert json_data["data"]["name"] == "John Doe"


def test_upload_no_file(client):
    """Ensure API returns error if no file uploaded"""
    response = client.post("/upload", data={}, content_type="multipart/form-data")
    assert response.status_code == 400


def test_upload_invalid_file_type(client):
    """Rejects unsupported file types"""
    fake_file = io.BytesIO(b"not an image")
    response = client.post(
        "/upload",
        data={"file": (fake_file, "test.txt")},
        content_type="multipart/form-data"
    )
    assert response.status_code in (400, 415)


@patch("utils.extract_pii", side_effect=Exception("Azure API failure"))
def test_azure_failure(mock_extract, client):
    """Handles Azure errors gracefully"""
    img = io.BytesIO(b"fake image data")
    response = client.post(
        "/upload",
        data={"file": (img, "valid_image.jpg")},
        content_type="multipart/form-data"
    )
    assert response.status_code >= 400
    json_data = response.get_json()
    assert "error" in json_data


# ---------- Optional LIVE Azure Test ----------
@pytest.mark.skipif(
    not os.getenv("AZURE_OPENAI_KEY"),
    reason="AZURE_OPENAI_KEY not set - skipping live Azure test"
)
def test_live_upload(client):
    """Test full pipeline with live Azure call (requires API key)"""
    with open("tests/assets/valid_image.jpg", "rb") as img_file:
        response = client.post(
            "/upload",
            data={"file": (img_file, "valid_image.jpg")},
            content_type="multipart/form-data"
        )
    assert response.status_code == 200
    json_data = response.get_json()
    assert "data" in json_data
