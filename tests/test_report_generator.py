"""Tests for report_generator module."""

from datetime import datetime
from pathlib import Path

import pytest

from libraries.report_generator import ReportGenerator


class TestReportGenerator:
    """Tests for ReportGenerator class."""

    @pytest.fixture
    def report_generator(self):
        """Create a fresh ReportGenerator instance."""
        return ReportGenerator("test_report")

    @pytest.mark.unit
    def test_init_default_name(self):
        """Test initialization with default name."""
        gen = ReportGenerator()
        assert gen.report_name == "workflow_report"

    @pytest.mark.unit
    def test_init_custom_name(self):
        """Test initialization with custom name."""
        gen = ReportGenerator("custom_report")
        assert gen.report_name == "custom_report"

    @pytest.mark.unit
    def test_start_sets_start_time(self, report_generator):
        """Test start() sets start_time."""
        assert report_generator.start_time is None
        report_generator.start()
        assert report_generator.start_time is not None
        assert isinstance(report_generator.start_time, datetime)

    @pytest.mark.unit
    def test_finish_sets_end_time(self, report_generator):
        """Test finish() sets end_time."""
        report_generator.start()
        assert report_generator.end_time is None
        report_generator.finish()
        assert report_generator.end_time is not None
        assert isinstance(report_generator.end_time, datetime)

    @pytest.mark.unit
    def test_set_update_payment_data(self, report_generator):
        """Test set_update_payment_data stores data correctly."""
        report_generator.set_update_payment_data(
            enabled=True,
            payment_ids=["id1", "id2"],
            updated_count=1,
            failed_ids=["id2"],
            not_found_ids=[],
        )

        data = report_generator.data["update_payment"]
        assert data["enabled"] is True
        assert data["payment_ids"] == ["id1", "id2"]
        assert data["updated_count"] == 1
        assert data["failed_ids"] == ["id2"]
        assert data["not_found_ids"] == []

    @pytest.mark.unit
    def test_set_order_management_data(self, report_generator):
        """Test set_order_management_data stores data correctly."""
        report_generator.set_order_management_data(
            enabled=True,
            api_pending_orders=[{"id": "1"}],
            sheet_orders_count=10,
            matching_orders=[{"id": "1"}],
            new_orders=[],
            orders_updated_to_completed=["1"],
            duplicates_removed=["2"],
            status_breakdown={"pending": 5, "paid": 3, "completed": 2},
        )

        data = report_generator.data["order_management"]
        assert data["enabled"] is True
        assert len(data["api_pending_orders"]) == 1
        assert data["sheet_orders_count"] == 10
        assert len(data["matching_orders"]) == 1
        assert data["new_orders"] == []
        assert data["orders_updated_to_completed"] == ["1"]
        assert data["duplicates_removed"] == ["2"]
        assert data["status_breakdown"]["pending"] == 5

    @pytest.mark.unit
    def test_add_error(self, report_generator):
        """Test add_error adds error to data."""
        report_generator.add_error("Test error message")

        assert len(report_generator.data["errors"]) == 1
        assert report_generator.data["errors"][0]["message"] == "Test error message"
        assert "timestamp" in report_generator.data["errors"][0]

    @pytest.mark.unit
    def test_add_warning(self, report_generator):
        """Test add_warning adds warning to data."""
        report_generator.add_warning("Test warning message")

        assert len(report_generator.data["warnings"]) == 1
        assert report_generator.data["warnings"][0]["message"] == "Test warning message"
        assert "timestamp" in report_generator.data["warnings"][0]

    @pytest.mark.unit
    def test_multiple_errors_and_warnings(self, report_generator):
        """Test adding multiple errors and warnings."""
        report_generator.add_error("Error 1")
        report_generator.add_error("Error 2")
        report_generator.add_warning("Warning 1")

        assert len(report_generator.data["errors"]) == 2
        assert len(report_generator.data["warnings"]) == 1


class TestReportGeneration:
    """Tests for HTML report generation."""

    @pytest.fixture
    def report_generator(self, tmp_path, monkeypatch):
        """Create a ReportGenerator with temp output directory."""
        from config import CONFIG

        monkeypatch.setattr(CONFIG, "OUTPUT_DIR", tmp_path)
        return ReportGenerator("test_report")

    @pytest.mark.unit
    def test_generate_report_creates_file(self, report_generator, tmp_path):
        """Test generate_report creates HTML file."""
        report_generator.start()
        report_generator.finish()

        filepath = report_generator.generate_report()

        assert Path(filepath).exists()
        assert filepath.endswith(".html")

    @pytest.mark.unit
    def test_generate_report_filename_format(self, report_generator, tmp_path):
        """Test generated report filename format."""
        report_generator.start()
        report_generator.finish()

        filepath = report_generator.generate_report()
        filename = Path(filepath).name

        assert filename.startswith("test_report_")
        assert filename.endswith(".html")
        # Should contain date format: YYYY-MM-DD_HH-MM-SS
        assert "-" in filename

    @pytest.mark.unit
    def test_generate_report_contains_html_structure(self, report_generator, tmp_path):
        """Test generated report contains proper HTML structure."""
        report_generator.start()
        report_generator.finish()

        filepath = report_generator.generate_report()

        with open(filepath) as f:
            content = f.read()

        assert "<!DOCTYPE html>" in content
        assert "<html" in content
        assert "</html>" in content
        assert "<head>" in content
        assert "<body>" in content
        assert "QwebsiteAutomationBot" in content

    @pytest.mark.unit
    def test_generate_report_contains_update_payment_section(self, report_generator, tmp_path):
        """Test report contains Update Payment section."""
        report_generator.start()
        report_generator.set_update_payment_data(
            enabled=True,
            payment_ids=["test-id"],
            updated_count=1,
            failed_ids=[],
            not_found_ids=[],
        )
        report_generator.finish()

        filepath = report_generator.generate_report()

        with open(filepath) as f:
            content = f.read()

        assert "Update Payment Process" in content
        assert "ENABLED" in content
        assert "test-id" in content

    @pytest.mark.unit
    def test_generate_report_contains_order_management_section(self, report_generator, tmp_path):
        """Test report contains Order Management section."""
        report_generator.start()
        report_generator.set_order_management_data(
            enabled=True,
            api_pending_orders=[{"id": "order-1"}],
            sheet_orders_count=5,
            matching_orders=[],
            new_orders=[],
            orders_updated_to_completed=[],
            duplicates_removed=[],
            status_breakdown={"pending": 3, "paid": 2},
        )
        report_generator.finish()

        filepath = report_generator.generate_report()

        with open(filepath) as f:
            content = f.read()

        assert "Order Management Process" in content
        assert "ENABLED" in content

    @pytest.mark.unit
    def test_generate_report_shows_disabled_sections(self, report_generator, tmp_path):
        """Test report shows DISABLED badge for disabled processes."""
        report_generator.start()
        report_generator.set_update_payment_data(
            enabled=False,
            payment_ids=[],
            updated_count=0,
            failed_ids=[],
            not_found_ids=[],
        )
        report_generator.set_order_management_data(
            enabled=False,
            api_pending_orders=[],
            sheet_orders_count=0,
            matching_orders=[],
            new_orders=[],
            orders_updated_to_completed=[],
            duplicates_removed=[],
            status_breakdown={},
        )
        report_generator.finish()

        filepath = report_generator.generate_report()

        with open(filepath) as f:
            content = f.read()

        assert "DISABLED" in content

    @pytest.mark.unit
    def test_generate_report_shows_errors(self, report_generator, tmp_path):
        """Test report shows errors section."""
        report_generator.start()
        report_generator.add_error("Test error occurred")
        report_generator.finish()

        filepath = report_generator.generate_report()

        with open(filepath) as f:
            content = f.read()

        assert "Test error occurred" in content
        assert "Errors" in content

    @pytest.mark.unit
    def test_generate_report_shows_no_errors_message(self, report_generator, tmp_path):
        """Test report shows 'no errors' message when clean."""
        report_generator.start()
        report_generator.finish()

        filepath = report_generator.generate_report()

        with open(filepath) as f:
            content = f.read()

        assert "No errors or warnings" in content


class TestUserManagementSection:
    """Tests for User Management section in report."""

    @pytest.fixture
    def report_generator(self, tmp_path, monkeypatch):
        """Create a ReportGenerator with temp output directory."""
        from config import CONFIG

        monkeypatch.setattr(CONFIG, "OUTPUT_DIR", tmp_path)
        return ReportGenerator("test_report")

    @pytest.mark.unit
    def test_set_user_management_data(self):
        """Test set_user_management_data stores all fields."""
        gen = ReportGenerator()
        gen.set_user_management_data(
            enabled=True,
            users=[{"id": "1", "email": "test@test.com"}],
            users_count=10,
            new_users=[],
            updated_users=[],
            approved_users=["user-1", "user-2"],
            failed_approvals=["user-3"],
            status_breakdown={"approved": 7, "unapproved": 3},
            user_type_breakdown={"doctor": 5, "employee": 3, "regular_user": 2},
            tier_breakdown={"Diamond Lead": 2, "Platinum Lead": 5, "Unknown": 3},
            admin_count=2,
            deactivated_count=1,
        )

        data = gen.data["user_management"]
        assert data["enabled"] is True
        assert data["users_count"] == 10
        assert len(data["approved_users"]) == 2
        assert len(data["failed_approvals"]) == 1
        assert data["status_breakdown"]["approved"] == 7
        assert data["user_type_breakdown"]["doctor"] == 5
        assert data["tier_breakdown"]["Diamond Lead"] == 2
        assert data["admin_count"] == 2
        assert data["deactivated_count"] == 1

    @pytest.mark.unit
    def test_report_contains_user_management_section(self, report_generator, tmp_path):
        """Test report contains User Management section."""
        report_generator.start()
        report_generator.set_user_management_data(
            enabled=True,
            users=[{"id": "test-user-1", "email": "test@example.com"}],
            users_count=5,
            new_users=[],
            updated_users=[],
            approved_users=["test-user-1"],
            failed_approvals=[],
            status_breakdown={"approved": 4, "unapproved": 1},
            user_type_breakdown={"doctor": 3, "employee": 2},
            tier_breakdown={"Diamond Lead": 2},
            admin_count=1,
            deactivated_count=0,
        )
        report_generator.finish()

        filepath = report_generator.generate_report()

        with open(filepath) as f:
            content = f.read()

        assert "User Management Process" in content
        assert "ENABLED" in content

    @pytest.mark.unit
    def test_report_shows_user_type_breakdown(self, report_generator, tmp_path):
        """Test report displays user type breakdown."""
        report_generator.start()
        report_generator.set_user_management_data(
            enabled=True,
            users=[],
            users_count=10,
            new_users=[],
            updated_users=[],
            approved_users=[],
            failed_approvals=[],
            status_breakdown={"approved": 10},
            user_type_breakdown={"doctor": 6, "employee": 4},
            tier_breakdown={},
            admin_count=0,
            deactivated_count=0,
        )
        report_generator.finish()

        filepath = report_generator.generate_report()

        with open(filepath) as f:
            content = f.read()

        assert "User Types" in content
        assert "doctor" in content
        assert "employee" in content

    @pytest.mark.unit
    def test_report_shows_tier_breakdown(self, report_generator, tmp_path):
        """Test report displays tier breakdown."""
        report_generator.start()
        report_generator.set_user_management_data(
            enabled=True,
            users=[],
            users_count=10,
            new_users=[],
            updated_users=[],
            approved_users=[],
            failed_approvals=[],
            status_breakdown={},
            user_type_breakdown={},
            tier_breakdown={"Diamond Lead": 3, "Platinum Lead": 5},
            admin_count=0,
            deactivated_count=0,
        )
        report_generator.finish()

        filepath = report_generator.generate_report()

        with open(filepath) as f:
            content = f.read()

        assert "Tier Distribution" in content
        assert "Diamond Lead" in content
        assert "Platinum Lead" in content

    @pytest.mark.unit
    def test_report_shows_admin_and_deactivated_counts(self, report_generator, tmp_path):
        """Test report displays admin and deactivated counts."""
        report_generator.start()
        report_generator.set_user_management_data(
            enabled=True,
            users=[],
            users_count=20,
            new_users=[],
            updated_users=[],
            approved_users=[],
            failed_approvals=[],
            status_breakdown={"approved": 15, "unapproved": 5},
            user_type_breakdown={},
            tier_breakdown={},
            admin_count=3,
            deactivated_count=2,
        )
        report_generator.finish()

        filepath = report_generator.generate_report()

        with open(filepath) as f:
            content = f.read()

        assert "Admins" in content
        assert "Deactivated" in content

    @pytest.mark.unit
    def test_report_shows_disabled_user_management(self, report_generator, tmp_path):
        """Test report shows DISABLED for user management when disabled."""
        report_generator.start()
        report_generator.set_user_management_data(
            enabled=False,
            users=[],
            users_count=0,
            new_users=[],
            updated_users=[],
            approved_users=[],
            failed_approvals=[],
            status_breakdown={},
            user_type_breakdown={},
            tier_breakdown={},
            admin_count=0,
            deactivated_count=0,
        )
        report_generator.finish()

        filepath = report_generator.generate_report()

        with open(filepath) as f:
            content = f.read()

        assert "User Management Process" in content
        assert "DISABLED" in content

    @pytest.mark.unit
    def test_report_shows_users_table(self, report_generator, tmp_path):
        """Test report shows users table with data."""
        report_generator.start()
        report_generator.set_user_management_data(
            enabled=True,
            users=[
                {
                    "id": "user-123-abc",
                    "email": "doctor@hospital.com",
                    "doctor_name": "Dr. Smith",
                    "user_type": "doctor",
                    "tier": "Diamond Lead",
                    "is_approved": True,
                    "is_admin": False,
                    "is_deactivated": False,
                }
            ],
            users_count=1,
            new_users=[],
            updated_users=[],
            approved_users=[],
            failed_approvals=[],
            status_breakdown={"approved": 1},
            user_type_breakdown={"doctor": 1},
            tier_breakdown={"Diamond Lead": 1},
            admin_count=0,
            deactivated_count=0,
        )
        report_generator.finish()

        filepath = report_generator.generate_report()

        with open(filepath) as f:
            content = f.read()

        assert "All Users" in content
        assert "doctor@hospital.com" in content
        assert "Dr. Smith" in content


class TestReportGeneratorDuration:
    """Tests for duration calculation."""

    @pytest.mark.unit
    def test_duration_calculation(self):
        """Test duration is calculated correctly."""
        gen = ReportGenerator()
        gen.start_time = datetime(2026, 1, 22, 10, 0, 0)
        gen.end_time = datetime(2026, 1, 22, 10, 1, 30)

        html = gen._generate_html()

        # Duration should be 90 seconds = 90.00 seconds
        assert "90.00 seconds" in html

    @pytest.mark.unit
    def test_duration_na_when_not_finished(self):
        """Test duration shows N/A when not properly timed."""
        gen = ReportGenerator()
        # Don't call start() or finish()

        html = gen._generate_html()

        assert "N/A" in html
