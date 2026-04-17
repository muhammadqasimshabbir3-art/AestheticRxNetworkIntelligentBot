"""Tests for workitems module."""

import pytest


class TestWorkItemInputs:
    """Tests for WorkItemInputs class."""

    @pytest.mark.unit
    def test_default_run_order_manage_system(self, monkeypatch):
        """Test default value for RUN_ORDER_MANAGE_SYSTEM."""
        monkeypatch.delenv("RUN_ORDER_MANAGE_SYSTEM", raising=False)

        # Re-import to get fresh instance
        from importlib import reload

        import libraries.workitems

        reload(libraries.workitems)
        from libraries.workitems import INPUTS

        assert INPUTS.RUN_ORDER_MANAGE_SYSTEM is True

    @pytest.mark.unit
    def test_default_run_update_payment_process(self, monkeypatch):
        """Test default value for RUN_UPDATE_PAYMENT_PROCESS."""
        monkeypatch.delenv("RUN_UPDATE_PAYMENT_PROCESS", raising=False)

        from importlib import reload

        import libraries.workitems

        reload(libraries.workitems)
        from libraries.workitems import INPUTS

        assert INPUTS.RUN_UPDATE_PAYMENT_PROCESS is False

    @pytest.mark.unit
    def test_default_payment_ids_list(self, monkeypatch):
        """Test default value for PAYMENT_IDS_LIST."""
        monkeypatch.delenv("PAYMENT_IDS_LIST", raising=False)

        from importlib import reload

        import libraries.workitems

        reload(libraries.workitems)
        from libraries.workitems import INPUTS

        assert INPUTS.PAYMENT_IDS_LIST == []

    @pytest.mark.unit
    def test_payment_ids_list_from_env(self, monkeypatch):
        """Test PAYMENT_IDS_LIST is parsed from comma-separated env var."""
        monkeypatch.setenv("PAYMENT_IDS_LIST", "id1,id2,id3")

        from importlib import reload

        import libraries.workitems

        reload(libraries.workitems)
        from libraries.workitems import INPUTS

        assert INPUTS.PAYMENT_IDS_LIST == ["id1", "id2", "id3"]

    @pytest.mark.unit
    def test_payment_ids_list_strips_whitespace(self, monkeypatch):
        """Test PAYMENT_IDS_LIST strips whitespace from IDs."""
        monkeypatch.setenv("PAYMENT_IDS_LIST", " id1 , id2 , id3 ")

        from importlib import reload

        import libraries.workitems

        reload(libraries.workitems)
        from libraries.workitems import INPUTS

        assert INPUTS.PAYMENT_IDS_LIST == ["id1", "id2", "id3"]

    @pytest.mark.unit
    def test_run_order_manage_system_true_string(self, monkeypatch):
        """Test RUN_ORDER_MANAGE_SYSTEM parses 'True' string."""
        monkeypatch.setenv("RUN_ORDER_MANAGE_SYSTEM", "True")

        from importlib import reload

        import libraries.workitems

        reload(libraries.workitems)
        from libraries.workitems import INPUTS

        assert INPUTS.RUN_ORDER_MANAGE_SYSTEM is True

    @pytest.mark.unit
    def test_run_order_manage_system_false_string(self, monkeypatch):
        """Test RUN_ORDER_MANAGE_SYSTEM parses 'False' string."""
        monkeypatch.setenv("RUN_ORDER_MANAGE_SYSTEM", "False")

        from importlib import reload

        import libraries.workitems

        reload(libraries.workitems)
        from libraries.workitems import INPUTS

        assert INPUTS.RUN_ORDER_MANAGE_SYSTEM is False

    @pytest.mark.unit
    def test_dev_safe_mode_default(self, monkeypatch):
        """Test DEV_SAFE_MODE defaults to True."""
        monkeypatch.delenv("DEV_SAFE_MODE", raising=False)

        from importlib import reload

        import libraries.workitems

        reload(libraries.workitems)
        from libraries.workitems import INPUTS

        assert INPUTS.DEV_SAFE_MODE is True

    @pytest.mark.unit
    def test_log_level_default(self, monkeypatch):
        """Test LOG_LEVEL defaults to INFO."""
        monkeypatch.delenv("LOG_LEVEL", raising=False)

        from importlib import reload

        import libraries.workitems

        reload(libraries.workitems)
        from libraries.workitems import INPUTS

        assert INPUTS.LOG_LEVEL == "INFO"
