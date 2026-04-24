"""Tests for config module."""

import pytest

from config import CONFIG


class TestAppConfig:
    """Tests for Config class (CONFIG singleton)."""

    @pytest.mark.unit
    def test_config_app_name(self):
        """Test that APP_NAME is set correctly."""
        assert CONFIG.APP_NAME == "AestheticRxNetworkIntelligentBot"

    @pytest.mark.unit
    def test_config_has_google_drive_folder_id(self):
        """Test that GOOGLE_DRIVE_FOLDER_ID is configured."""
        assert hasattr(CONFIG, "GOOGLE_DRIVE_FOLDER_ID")
        assert CONFIG.GOOGLE_DRIVE_FOLDER_ID is not None

    @pytest.mark.unit
    def test_config_has_google_spreadsheet_id(self):
        """Test that GOOGLE_SPREADSHEET_ID is configured."""
        assert hasattr(CONFIG, "GOOGLE_SPREADSHEET_ID")
        assert CONFIG.GOOGLE_SPREADSHEET_ID is not None

    @pytest.mark.unit
    def test_config_has_source_spreadsheet_id(self):
        """Test that SOURCE_SPREADSHEET_ID is configured."""
        assert hasattr(CONFIG, "SOURCE_SPREADSHEET_ID")
        assert CONFIG.SOURCE_SPREADSHEET_ID is not None

    @pytest.mark.unit
    def test_config_has_spreadsheet_name_prefix(self):
        """Test that SPREADSHEET_NAME_PREFIX is configured."""
        assert hasattr(CONFIG, "SPREADSHEET_NAME_PREFIX")
        assert CONFIG.SPREADSHEET_NAME_PREFIX == "AestheticRxNetworkPendingOrder"

    @pytest.mark.unit
    def test_config_has_order_headers(self):
        """Test that ORDER_HEADERS is configured."""
        assert hasattr(CONFIG, "ORDER_HEADERS")
        assert isinstance(CONFIG.ORDER_HEADERS, list)
        assert len(CONFIG.ORDER_HEADERS) > 0
        assert "ID" in CONFIG.ORDER_HEADERS

    @pytest.mark.unit
    def test_config_output_dir_exists(self):
        """Test that OUTPUT_DIR is configured."""
        assert hasattr(CONFIG, "OUTPUT_DIR")
        assert CONFIG.OUTPUT_DIR is not None

    @pytest.mark.unit
    def test_ensure_directories_creates_output_dir(self, tmp_path, monkeypatch):
        """Test that ensure_directories creates the output directory."""
        # Create a temporary config with a temp output dir
        test_output = tmp_path / "test_output"
        monkeypatch.setattr(CONFIG, "OUTPUT_DIR", test_output)

        CONFIG.ensure_directories()

        assert test_output.exists()


class TestConfigConstants:
    """Tests for configuration constants."""

    @pytest.mark.unit
    def test_order_headers_contains_required_fields(self):
        """Test ORDER_HEADERS contains all required fields."""
        required_fields = ["ID", "Order Number", "Payment Status"]
        for field in required_fields:
            assert field in CONFIG.ORDER_HEADERS, f"Missing required field: {field}"

    @pytest.mark.unit
    def test_spreadsheet_prefix_format(self):
        """Test SPREADSHEET_NAME_PREFIX has correct format."""
        assert CONFIG.SPREADSHEET_NAME_PREFIX.startswith("AestheticRxNetwork")
        assert not CONFIG.SPREADSHEET_NAME_PREFIX.endswith("_")
