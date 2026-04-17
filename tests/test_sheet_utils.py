"""Tests for sheet_utils module."""

import pytest

from libraries.sheet_utils import column_index_to_letter, find_column_index, get_cell_reference


class TestColumnIndexToLetter:
    """Tests for column_index_to_letter function."""

    @pytest.mark.unit
    def test_single_letter_columns(self):
        """Test single letter column names (A-Z)."""
        assert column_index_to_letter(0) == "A"
        assert column_index_to_letter(1) == "B"
        assert column_index_to_letter(25) == "Z"

    @pytest.mark.unit
    def test_double_letter_columns(self):
        """Test double letter column names (AA-AZ, BA-BZ, etc.)."""
        assert column_index_to_letter(26) == "AA"
        assert column_index_to_letter(27) == "AB"
        assert column_index_to_letter(51) == "AZ"
        assert column_index_to_letter(52) == "BA"

    @pytest.mark.unit
    def test_triple_letter_columns(self):
        """Test triple letter column names."""
        # 26 + 26*26 = 702 is AAA
        assert column_index_to_letter(702) == "AAA"

    @pytest.mark.unit
    def test_common_column_indices(self):
        """Test commonly used column indices."""
        # Column C (index 2)
        assert column_index_to_letter(2) == "C"
        # Column J (index 9)
        assert column_index_to_letter(9) == "J"
        # Column T (index 19)
        assert column_index_to_letter(19) == "T"


class TestFindColumnIndex:
    """Tests for find_column_index function."""

    @pytest.mark.unit
    def test_find_exact_match(self):
        """Test finding column with exact match."""
        headers = ["id", "name", "email", "status"]
        assert find_column_index(headers, ["id"]) == 0
        assert find_column_index(headers, ["name"]) == 1
        assert find_column_index(headers, ["status"]) == 3

    @pytest.mark.unit
    def test_find_case_insensitive(self):
        """Test case-insensitive matching."""
        headers = ["ID", "Name", "Email", "Status"]
        assert find_column_index(headers, ["id"]) == 0
        assert find_column_index(headers, ["name"]) == 1
        assert find_column_index(headers, ["status"]) == 3

    @pytest.mark.unit
    def test_find_with_multiple_possible_names(self):
        """Test finding column with multiple possible names."""
        headers = ["order_id", "orderNumber", "user", "payment_status"]
        assert find_column_index(headers, ["id", "order_id", "ID"]) == 0
        assert find_column_index(headers, ["status", "payment_status"]) == 3

    @pytest.mark.unit
    def test_find_returns_negative_one_when_not_found(self):
        """Test returns -1 when column not found."""
        headers = ["id", "name", "email"]
        assert find_column_index(headers, ["nonexistent"]) == -1
        assert find_column_index(headers, ["status", "state"]) == -1

    @pytest.mark.unit
    def test_find_with_empty_headers(self):
        """Test with empty headers list."""
        assert find_column_index([], ["id"]) == -1

    @pytest.mark.unit
    def test_find_with_empty_possible_names(self):
        """Test with empty possible names list."""
        headers = ["id", "name"]
        assert find_column_index(headers, []) == -1


class TestGetCellReference:
    """Tests for get_cell_reference function."""

    @pytest.mark.unit
    def test_simple_cell_references(self):
        """Test simple cell references (row_number is 1-based)."""
        assert get_cell_reference(0, 1) == "A1"
        assert get_cell_reference(0, 2) == "A2"
        assert get_cell_reference(1, 1) == "B1"
        assert get_cell_reference(1, 2) == "B2"

    @pytest.mark.unit
    def test_double_letter_column_references(self):
        """Test cell references with double letter columns."""
        assert get_cell_reference(26, 1) == "AA1"
        assert get_cell_reference(27, 6) == "AB6"

    @pytest.mark.unit
    def test_large_row_numbers(self):
        """Test cell references with large row numbers."""
        assert get_cell_reference(0, 100) == "A100"
        assert get_cell_reference(0, 1000) == "A1000"

    @pytest.mark.unit
    def test_common_cell_references(self):
        """Test commonly used cell references."""
        # C5
        assert get_cell_reference(2, 5) == "C5"
        # J10
        assert get_cell_reference(9, 10) == "J10"
        # T20
        assert get_cell_reference(19, 20) == "T20"
