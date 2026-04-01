import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
from urllib.error import URLError
from auto_sdlc.logs.export import export_report_to_dir, export_report_to_http


@pytest.fixture
def sample_report():
    return {
        "user_id": "alice@example.com",
        "summary": {
            "total_sessions": 5
        }
    }


def test_export_to_dir_creates_file(sample_report):
    with tempfile.TemporaryDirectory() as tmpdir:
        result = export_report_to_dir(sample_report, tmpdir)
        assert Path(result).exists()


def test_export_to_dir_valid_json(sample_report):
    with tempfile.TemporaryDirectory() as tmpdir:
        result = export_report_to_dir(sample_report, tmpdir)
        content = Path(result).read_text(encoding="utf-8")
        data = json.loads(content)
        assert data == sample_report


def test_export_to_dir_filename_contains_user_id(sample_report):
    with tempfile.TemporaryDirectory() as tmpdir:
        result = export_report_to_dir(sample_report, tmpdir)
        filename = Path(result).name
        assert "alice_at_example.com" in filename


def test_export_to_dir_creates_parent_dirs(sample_report):
    with tempfile.TemporaryDirectory() as tmpdir:
        nested_dir = Path(tmpdir) / "a" / "b" / "c"
        result = export_report_to_dir(sample_report, str(nested_dir))
        assert Path(result).exists()
        assert nested_dir.exists()


@patch("urllib.request.urlopen")
def test_export_to_http_returns_true_on_200(mock_urlopen, sample_report):
    mock_response = MagicMock()
    mock_response.status = 200
    mock_urlopen.return_value = mock_response

    result = export_report_to_http(sample_report, "http://example.com/api")
    assert result is True


@patch("urllib.request.urlopen")
def test_export_to_http_returns_false_on_connection_error(mock_urlopen, sample_report):
    mock_urlopen.side_effect = URLError("Connection failed")

    result = export_report_to_http(sample_report, "http://example.com/api")
    assert result is False
