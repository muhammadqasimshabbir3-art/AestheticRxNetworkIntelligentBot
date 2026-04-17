"""Tests for UserManagement module."""

from unittest.mock import MagicMock, patch

import pytest


class TestUserManagementProcess:
    """Tests for UserManagementProcess class."""

    @pytest.mark.unit
    def test_init_creates_process(self):
        """Test UserManagementProcess initializes correctly."""
        with patch("UserManagement.user_management_process.UserManager"):
            from processes.user.user_management_process import UserManagementProcess

            process = UserManagementProcess()

            assert process is not None
            assert process._user_manager is None

    @pytest.mark.unit
    def test_users_property_empty_before_start(self):
        """Test users property returns empty list before start."""
        with patch("UserManagement.user_management_process.UserManager"):
            from processes.user.user_management_process import UserManagementProcess

            process = UserManagementProcess()

            assert process.users == []

    @pytest.mark.unit
    def test_users_count_zero_before_start(self):
        """Test users_count returns 0 before start."""
        with patch("UserManagement.user_management_process.UserManager"):
            from processes.user.user_management_process import UserManagementProcess

            process = UserManagementProcess()

            assert process.users_count == 0

    @pytest.mark.unit
    def test_new_users_empty_before_start(self):
        """Test new_users returns empty list before start."""
        with patch("UserManagement.user_management_process.UserManager"):
            from processes.user.user_management_process import UserManagementProcess

            process = UserManagementProcess()

            assert process.new_users == []

    @pytest.mark.unit
    def test_updated_users_empty_before_start(self):
        """Test updated_users returns empty list before start."""
        with patch("UserManagement.user_management_process.UserManager"):
            from processes.user.user_management_process import UserManagementProcess

            process = UserManagementProcess()

            assert process.updated_users == []

    @pytest.mark.unit
    def test_status_breakdown_empty_before_start(self):
        """Test status_breakdown returns empty dict before start."""
        with patch("UserManagement.user_management_process.UserManager"):
            from processes.user.user_management_process import UserManagementProcess

            process = UserManagementProcess()

            assert process.status_breakdown == {}

    @pytest.mark.unit
    def test_user_type_breakdown_empty_before_start(self):
        """Test user_type_breakdown returns empty dict before start."""
        with patch("UserManagement.user_management_process.UserManager"):
            from processes.user.user_management_process import UserManagementProcess

            process = UserManagementProcess()

            assert process.user_type_breakdown == {}

    @pytest.mark.unit
    def test_tier_breakdown_empty_before_start(self):
        """Test tier_breakdown returns empty dict before start."""
        with patch("UserManagement.user_management_process.UserManager"):
            from processes.user.user_management_process import UserManagementProcess

            process = UserManagementProcess()

            assert process.tier_breakdown == {}

    @pytest.mark.unit
    def test_admin_count_zero_before_start(self):
        """Test admin_count returns 0 before start."""
        with patch("UserManagement.user_management_process.UserManager"):
            from processes.user.user_management_process import UserManagementProcess

            process = UserManagementProcess()

            assert process.admin_count == 0

    @pytest.mark.unit
    def test_deactivated_count_zero_before_start(self):
        """Test deactivated_count returns 0 before start."""
        with patch("UserManagement.user_management_process.UserManager"):
            from processes.user.user_management_process import UserManagementProcess

            process = UserManagementProcess()

            assert process.deactivated_count == 0

    @pytest.mark.unit
    def test_approved_users_empty_before_start(self):
        """Test approved_users returns empty list before start."""
        with patch("UserManagement.user_management_process.UserManager"):
            from processes.user.user_management_process import UserManagementProcess

            process = UserManagementProcess()

            assert process.approved_users == []

    @pytest.mark.unit
    def test_failed_approvals_empty_before_start(self):
        """Test failed_approvals returns empty list before start."""
        with patch("UserManagement.user_management_process.UserManager"):
            from processes.user.user_management_process import UserManagementProcess

            process = UserManagementProcess()

            assert process.failed_approvals == []


class TestUserManagementProcessStart:
    """Tests for UserManagementProcess.start() method."""

    @pytest.mark.unit
    def test_start_initializes_user_manager(self):
        """Test start() initializes UserManager."""
        mock_manager = MagicMock()
        mock_manager.users = []
        mock_manager.users_count = 0
        mock_manager.new_users = []
        mock_manager.updated_users = []
        mock_manager.status_breakdown = {}

        with patch("UserManagement.user_management_process.UserManager", return_value=mock_manager):
            from processes.user.user_management_process import UserManagementProcess

            process = UserManagementProcess()
            process.start()

            assert process._user_manager is not None
            mock_manager.start.assert_called_once()

    @pytest.mark.unit
    def test_start_handles_exception(self):
        """Test start() handles exceptions gracefully."""
        mock_manager = MagicMock()
        mock_manager.start.side_effect = Exception("Test error")

        with patch("UserManagement.user_management_process.UserManager", return_value=mock_manager):
            from processes.user.user_management_process import UserManagementProcess

            process = UserManagementProcess()

            with pytest.raises(Exception, match="Test error"):
                process.start()


class TestUserManager:
    """Tests for UserManager class."""

    @pytest.fixture
    def mock_api(self):
        """Create mock QWebsiteAPI."""
        mock = MagicMock()
        mock.get_users.return_value = []
        return mock

    @pytest.fixture
    def mock_sheets_api(self):
        """Create mock GoogleSheetsAPI."""
        mock = MagicMock()
        return mock

    @pytest.mark.unit
    def test_init_creates_manager(self, mock_api, mock_sheets_api):
        """Test UserManager initializes correctly."""
        with (
            patch("UserManagement.user_manager.QWebsiteAPI", return_value=mock_api),
            patch("UserManagement.user_manager.GoogleSheetsAPI", return_value=mock_sheets_api),
        ):
            from processes.user.user_manager import UserManager

            manager = UserManager()

            assert manager is not None
            assert manager._users == []
            assert manager._new_users == []
            assert manager._updated_users == []

    @pytest.mark.unit
    def test_users_property(self, mock_api, mock_sheets_api):
        """Test users property."""
        with (
            patch("UserManagement.user_manager.QWebsiteAPI", return_value=mock_api),
            patch("UserManagement.user_manager.GoogleSheetsAPI", return_value=mock_sheets_api),
        ):
            from processes.user.user_manager import UserManager

            manager = UserManager()
            manager._users = [{"id": "1"}, {"id": "2"}]

            assert len(manager.users) == 2

    @pytest.mark.unit
    def test_users_count_property(self, mock_api, mock_sheets_api):
        """Test users_count property."""
        with (
            patch("UserManagement.user_manager.QWebsiteAPI", return_value=mock_api),
            patch("UserManagement.user_manager.GoogleSheetsAPI", return_value=mock_sheets_api),
        ):
            from processes.user.user_manager import UserManager

            manager = UserManager()
            manager._users = [{"id": "1"}, {"id": "2"}, {"id": "3"}]

            assert manager.users_count == 3


class TestUserManagerWorkflow:
    """Tests for UserManager workflow."""

    @pytest.fixture
    def mock_api(self):
        """Create mock QWebsiteAPI."""
        mock = MagicMock()
        return mock

    @pytest.fixture
    def mock_sheets_api(self):
        """Create mock GoogleSheetsAPI."""
        mock = MagicMock()
        return mock

    @pytest.mark.unit
    def test_start_fetches_users(self, mock_api, mock_sheets_api):
        """Test start() fetches users from API."""
        mock_api.get_users.return_value = [
            {"id": "1", "email": "user1@test.com", "status": "active"},
            {"id": "2", "email": "user2@test.com", "status": "pending"},
        ]

        with (
            patch("UserManagement.user_manager.QWebsiteAPI", return_value=mock_api),
            patch("UserManagement.user_manager.GoogleSheetsAPI", return_value=mock_sheets_api),
        ):
            from processes.user.user_manager import UserManager

            manager = UserManager()
            manager.start()

            assert len(manager.users) == 2
            mock_api.get_users.assert_called()

    @pytest.mark.unit
    def test_start_calculates_status_breakdown(self, mock_api, mock_sheets_api):
        """Test start() calculates status breakdown based on approval status."""
        mock_api.get_users.return_value = [
            {"id": "1", "isApproved": True},
            {"id": "2", "isApproved": True},
            {"id": "3", "isApproved": False},
        ]
        mock_api.approve_user.return_value = {"success": True}

        with (
            patch("UserManagement.user_manager.QWebsiteAPI", return_value=mock_api),
            patch("UserManagement.user_manager.GoogleSheetsAPI", return_value=mock_sheets_api),
        ):
            from processes.user.user_manager import UserManager

            manager = UserManager()
            manager.start()

            # Status breakdown is based on approval status
            assert manager.status_breakdown.get("approved") == 2
            assert manager.status_breakdown.get("unapproved") == 1

    @pytest.mark.unit
    def test_start_calculates_user_type_breakdown(self, mock_api, mock_sheets_api):
        """Test start() calculates user type breakdown."""
        mock_api.get_users.return_value = [
            {"id": "1", "user_type": "doctor", "isApproved": True},
            {"id": "2", "user_type": "doctor", "isApproved": True},
            {"id": "3", "user_type": "employee", "isApproved": True},
            {"id": "4", "userType": "regular_user", "isApproved": True},
        ]

        with (
            patch("UserManagement.user_manager.QWebsiteAPI", return_value=mock_api),
            patch("UserManagement.user_manager.GoogleSheetsAPI", return_value=mock_sheets_api),
        ):
            from processes.user.user_manager import UserManager

            manager = UserManager()
            manager.start()

            assert manager.user_type_breakdown.get("doctor") == 2
            assert manager.user_type_breakdown.get("employee") == 1
            assert manager.user_type_breakdown.get("regular_user") == 1

    @pytest.mark.unit
    def test_start_calculates_tier_breakdown(self, mock_api, mock_sheets_api):
        """Test start() calculates tier breakdown."""
        mock_api.get_users.return_value = [
            {"id": "1", "tier": "Diamond Lead", "isApproved": True},
            {"id": "2", "tier": "Diamond Lead", "isApproved": True},
            {"id": "3", "tier": "Platinum Lead", "isApproved": True},
        ]

        with (
            patch("UserManagement.user_manager.QWebsiteAPI", return_value=mock_api),
            patch("UserManagement.user_manager.GoogleSheetsAPI", return_value=mock_sheets_api),
        ):
            from processes.user.user_manager import UserManager

            manager = UserManager()
            manager.start()

            assert manager.tier_breakdown.get("Diamond Lead") == 2
            assert manager.tier_breakdown.get("Platinum Lead") == 1

    @pytest.mark.unit
    def test_start_counts_admins(self, mock_api, mock_sheets_api):
        """Test start() counts admin users."""
        mock_api.get_users.return_value = [
            {"id": "1", "isAdmin": True, "isApproved": True},
            {"id": "2", "is_admin": True, "isApproved": True},
            {"id": "3", "isAdmin": False, "isApproved": True},
        ]

        with (
            patch("UserManagement.user_manager.QWebsiteAPI", return_value=mock_api),
            patch("UserManagement.user_manager.GoogleSheetsAPI", return_value=mock_sheets_api),
        ):
            from processes.user.user_manager import UserManager

            manager = UserManager()
            manager.start()

            assert manager.admin_count == 2

    @pytest.mark.unit
    def test_start_counts_deactivated(self, mock_api, mock_sheets_api):
        """Test start() counts deactivated users."""
        mock_api.get_users.return_value = [
            {"id": "1", "isDeactivated": True, "isApproved": True},
            {"id": "2", "is_deactivated": True, "isApproved": True},
            {"id": "3", "isDeactivated": False, "isApproved": True},
        ]

        with (
            patch("UserManagement.user_manager.QWebsiteAPI", return_value=mock_api),
            patch("UserManagement.user_manager.GoogleSheetsAPI", return_value=mock_sheets_api),
        ):
            from processes.user.user_manager import UserManager

            manager = UserManager()
            manager.start()

            assert manager.deactivated_count == 2

    @pytest.mark.unit
    def test_start_handles_api_error(self, mock_api, mock_sheets_api):
        """Test start() handles API errors gracefully."""
        mock_api.get_users.side_effect = Exception("API Error")

        with (
            patch("UserManagement.user_manager.QWebsiteAPI", return_value=mock_api),
            patch("UserManagement.user_manager.GoogleSheetsAPI", return_value=mock_sheets_api),
        ):
            from processes.user.user_manager import UserManager

            manager = UserManager()
            manager.start()  # Should not raise

            assert manager.users == []

    @pytest.mark.unit
    def test_start_handles_empty_response(self, mock_api, mock_sheets_api):
        """Test start() handles empty API response."""
        mock_api.get_users.return_value = []

        with (
            patch("UserManagement.user_manager.QWebsiteAPI", return_value=mock_api),
            patch("UserManagement.user_manager.GoogleSheetsAPI", return_value=mock_sheets_api),
        ):
            from processes.user.user_manager import UserManager

            manager = UserManager()
            manager.start()

            assert manager.users == []
            assert manager.users_count == 0


class TestUserManagerHeaders:
    """Tests for UserManager headers configuration."""

    @pytest.mark.unit
    def test_user_headers_defined(self):
        """Test USER_HEADERS is defined correctly."""
        from processes.user.user_manager import UserManager

        assert hasattr(UserManager, "USER_HEADERS")
        assert isinstance(UserManager.USER_HEADERS, list)
        assert len(UserManager.USER_HEADERS) > 0

    @pytest.mark.unit
    def test_user_headers_contains_required_fields(self):
        """Test USER_HEADERS contains required fields."""
        from processes.user.user_manager import UserManager

        required = ["ID", "Email", "Name", "Status"]
        for field in required:
            assert field in UserManager.USER_HEADERS


class TestUserManagerApproval:
    """Tests for UserManager approval functionality."""

    @pytest.fixture
    def mock_api(self):
        """Create mock QWebsiteAPI."""
        mock = MagicMock()
        return mock

    @pytest.fixture
    def mock_sheets_api(self):
        """Create mock GoogleSheetsAPI."""
        mock = MagicMock()
        return mock

    @pytest.mark.unit
    def test_approves_unapproved_users(self, mock_api, mock_sheets_api):
        """Test that unapproved users are approved."""
        mock_api.get_users.return_value = [
            {"id": "user-1", "email": "user1@test.com", "isApproved": False},
            {"id": "user-2", "email": "user2@test.com", "isApproved": True},
        ]
        mock_api.approve_user.return_value = {"success": True, "message": "User approved"}

        with (
            patch("UserManagement.user_manager.QWebsiteAPI", return_value=mock_api),
            patch("UserManagement.user_manager.GoogleSheetsAPI", return_value=mock_sheets_api),
        ):
            from processes.user.user_manager import UserManager

            manager = UserManager()
            manager.start()

            # Should only approve user-1 (unapproved)
            mock_api.approve_user.assert_called_once_with("user-1")
            assert "user-1" in manager.approved_users

    @pytest.mark.unit
    def test_tracks_failed_approvals(self, mock_api, mock_sheets_api):
        """Test that failed approvals are tracked."""
        mock_api.get_users.return_value = [
            {"id": "user-1", "email": "user1@test.com", "isApproved": False},
        ]
        mock_api.approve_user.return_value = {"success": False, "message": "Error"}

        with (
            patch("UserManagement.user_manager.QWebsiteAPI", return_value=mock_api),
            patch("UserManagement.user_manager.GoogleSheetsAPI", return_value=mock_sheets_api),
        ):
            from processes.user.user_manager import UserManager

            manager = UserManager()
            manager.start()

            assert "user-1" in manager.failed_approvals
            assert "user-1" not in manager.approved_users

    @pytest.mark.unit
    def test_handles_approval_exception(self, mock_api, mock_sheets_api):
        """Test handling of approval exceptions."""
        mock_api.get_users.return_value = [
            {"id": "user-1", "email": "user1@test.com", "isApproved": False},
        ]
        mock_api.approve_user.side_effect = Exception("API Error")

        with (
            patch("UserManagement.user_manager.QWebsiteAPI", return_value=mock_api),
            patch("UserManagement.user_manager.GoogleSheetsAPI", return_value=mock_sheets_api),
        ):
            from processes.user.user_manager import UserManager

            manager = UserManager()
            manager.start()  # Should not raise

            assert "user-1" in manager.failed_approvals

    @pytest.mark.unit
    def test_no_approval_when_all_approved(self, mock_api, mock_sheets_api):
        """Test no approval calls when all users are approved."""
        mock_api.get_users.return_value = [
            {"id": "user-1", "email": "user1@test.com", "isApproved": True},
            {"id": "user-2", "email": "user2@test.com", "isApproved": True},
        ]

        with (
            patch("UserManagement.user_manager.QWebsiteAPI", return_value=mock_api),
            patch("UserManagement.user_manager.GoogleSheetsAPI", return_value=mock_sheets_api),
        ):
            from processes.user.user_manager import UserManager

            manager = UserManager()
            manager.start()

            mock_api.approve_user.assert_not_called()
            assert len(manager.approved_users) == 0


class TestQWebsiteAPIUserMethods:
    """Tests for QWebsiteAPI user-related methods."""

    @pytest.mark.unit
    def test_approve_user_endpoint(self):
        """Test approve_user calls correct endpoint."""
        with (
            patch("libraries.qwebsite_api._QWebsiteAuth._get_credentials_from_bitwarden"),
            patch("libraries.qwebsite_api._QWebsiteAuth._verify_gmail_connection"),
            patch("libraries.qwebsite_api._QWebsiteAuth._authenticate"),
            patch("requests.request") as mock_request,
        ):
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"success": True, "message": "User approved"}
            mock_request.return_value = mock_response

            from libraries.qwebsite_api import QWebsiteAPI

            api = QWebsiteAPI(auto_authenticate=False)
            api._token = "test-token"

            result = api.approve_user("test-user-id")

            assert result["success"] is True
            # Verify POST was called with correct endpoint
            call_args = mock_request.call_args
            assert "test-user-id/approve" in call_args.kwargs.get("url", call_args[1].get("url", ""))

    @pytest.mark.unit
    def test_get_unapproved_users_filters_correctly(self):
        """Test get_unapproved_users filters out approved users."""
        with (
            patch("libraries.qwebsite_api._QWebsiteAuth._get_credentials_from_bitwarden"),
            patch("libraries.qwebsite_api._QWebsiteAuth._verify_gmail_connection"),
            patch("libraries.qwebsite_api._QWebsiteAuth._authenticate"),
            patch("requests.request") as mock_request,
        ):
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = [
                {"id": "1", "isApproved": True},
                {"id": "2", "isApproved": False},
                {"id": "3", "is_approved": False},
            ]
            mock_request.return_value = mock_response

            from libraries.qwebsite_api import QWebsiteAPI

            api = QWebsiteAPI(auto_authenticate=False)
            api._token = "test-token"

            unapproved = api.get_unapproved_users()

            # Should return users 2 and 3 (unapproved)
            unapproved_ids = [u["id"] for u in unapproved]
            assert "2" in unapproved_ids
            assert "3" in unapproved_ids
            assert "1" not in unapproved_ids
