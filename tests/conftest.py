"""Pytest configuration and shared fixtures."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add project root to path (for workflow module)
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Add src to path (for src modules)
src_path = project_root / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))


# ============================================================================
# Environment Fixtures
# ============================================================================


@pytest.fixture(autouse=True)
def mock_environment(monkeypatch):
    """Set up mock environment variables for all tests."""
    monkeypatch.setenv("BITWARDEN_CLIENT_ID", "test-client-id")
    monkeypatch.setenv("BITWARDEN_CLIENT_SECRETE", "test-client-secret")
    monkeypatch.setenv("BITWARDEN_MASTER_PASSWORD", "test-master-password")
    monkeypatch.setenv("RUN_UPDATE_PAYMENT_PROCESS", "False")
    monkeypatch.setenv("RUN_ORDER_MANAGE_SYSTEM", "True")
    monkeypatch.setenv("PAYMENT_IDS_LIST", "")


@pytest.fixture
def temp_output_dir(tmp_path):
    """Create a temporary output directory."""
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    return output_dir


# ============================================================================
# Mock Data Fixtures
# ============================================================================


@pytest.fixture
def sample_order():
    """Sample order data."""
    return {
        "id": "test-order-123",
        "orderNumber": "ORD-001",
        "userId": "user-456",
        "payment_status": "pending",
        "totalAmount": 100.00,
        "createdAt": "2026-01-22T10:00:00Z",
    }


@pytest.fixture
def sample_orders():
    """List of sample orders."""
    return [
        {
            "id": "order-1",
            "orderNumber": "ORD-001",
            "userId": "user-1",
            "payment_status": "pending",
            "totalAmount": 100.00,
        },
        {
            "id": "order-2",
            "orderNumber": "ORD-002",
            "userId": "user-2",
            "payment_status": "paid",
            "totalAmount": 200.00,
        },
        {
            "id": "order-3",
            "orderNumber": "ORD-003",
            "userId": "user-3",
            "payment_status": "completed",
            "totalAmount": 300.00,
        },
    ]


@pytest.fixture
def sample_sheet_data():
    """Sample Google Sheet data with headers."""
    return [
        ["id", "orderNumber", "userId", "payment_status", "totalAmount"],
        ["order-1", "ORD-001", "user-1", "pending", "100.00"],
        ["order-2", "ORD-002", "user-2", "paid", "200.00"],
        ["order-3", "ORD-003", "user-3", "completed", "300.00"],
    ]


@pytest.fixture
def sample_api_response():
    """Sample API response."""
    return {
        "success": True,
        "data": [
            {"id": "order-1", "orderNumber": "ORD-001", "payment_status": "pending"},
            {"id": "order-4", "orderNumber": "ORD-004", "payment_status": "pending"},
        ],
    }


@pytest.fixture
def sample_credentials():
    """Sample credentials dictionary."""
    return {
        "email": "test@example.com",
        "password": "test-password",
        "app_password": "test-app-password",
    }


@pytest.fixture
def sample_service_account():
    """Sample Google service account JSON."""
    return {
        "type": "service_account",
        "project_id": "test-project",
        "private_key_id": "key-123",
        "private_key": "-----BEGIN RSA PRIVATE KEY-----\nMIIE...\n-----END RSA PRIVATE KEY-----\n",
        "client_email": "test@test-project.iam.gserviceaccount.com",
        "client_id": "123456789",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
    }


# ============================================================================
# Mock Service Fixtures
# ============================================================================


@pytest.fixture
def mock_bitwarden():
    """Mock Bitwarden client."""
    with patch("bitwarden.auth.BitwardenAuth") as mock:
        mock_instance = MagicMock()
        mock_instance.is_logged_in.return_value = True
        mock_instance.login.return_value = True
        mock.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_google_sheets_api():
    """Mock Google Sheets API."""
    with patch("libraries.google_sheets.GoogleSheetsAPI") as mock:
        mock_instance = MagicMock()
        mock_instance.read_data.return_value = []
        mock_instance.write_data.return_value = True
        mock_instance.get_sheet_info.return_value = [{"title": "Sheet1", "sheetId": 0}]
        mock.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_google_drive_api():
    """Mock Google Drive API."""
    with patch("libraries.google_drive.GoogleDriveAPI") as mock:
        mock_instance = MagicMock()
        mock_instance.create_spreadsheet.return_value = "new-spreadsheet-id"
        mock_instance.get_file.return_value = {"id": "file-id", "name": "test-file"}
        mock.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_qwebsite_api():
    """Mock QWebsite API."""
    with patch("libraries.qwebsite_api.QWebsiteAPI") as mock:
        mock_instance = MagicMock()
        mock_instance.authenticate.return_value = True
        mock_instance.get_orders.return_value = []
        mock_instance.update_order_status.return_value = {"status": 200}
        mock.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_requests():
    """Mock requests library."""
    with patch("requests.request") as mock:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"success": True}
        mock.return_value = mock_response
        yield mock
