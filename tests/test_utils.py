import io
import os
import pytest
from unittest.mock import patch
from utils import extract_pii_from_image as extract_pii


@patch("utils.AzureOpenAI")  # adjust if using azure.ai or azure.openai SDK
def test_extract_pii_mocked(mock_sdk):
    """Mock Azure OpenAI and check structured return"""
    mock_instance = mock_sdk.return_value
    mock_instance.run.return_value = {
        "choices": [{"message": {"content": '{"name": "Jane", "email": "jane@example.com"}'}}]
    }

    img_data = b"fake image bytes"
    result = extract_pii(img_data)
    assert isinstance(result, dict)
    assert "email" in result


def test_extract_pii_empty_input():
    """Empty image bytes should raise ValueError or similar"""
    with pytest.raises(Exception):
        extract_pii(b"")


@pytest.mark.skipif(
    not os.getenv("AZURE_OPENAI_KEY"),
    reason="AZURE_OPENAI_KEY not set - skipping live Azure test"
)
def test_live_extract_pii():
    """Live Azure call (requires environment variables)"""
    with open("tests/assets/valid_image.jpg", "rb") as img_file:
        result = extract_pii(img_file.read())
    assert isinstance(result, dict)
    assert "data" in result or len(result) > 0
