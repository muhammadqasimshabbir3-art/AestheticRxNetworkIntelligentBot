"""Utility functions for Google Sheets operations.

Contains shared helper functions used across sheet-related modules.
"""


def column_index_to_letter(index: int) -> str:
    """Convert a 0-based column index to Excel-style column letter(s).

    Handles columns beyond Z (e.g., AA, AB, etc.)

    Args:
        index: 0-based column index (0=A, 25=Z, 26=AA, etc.)

    Returns:
        str: Column letter(s)

    Examples:
        >>> column_index_to_letter(0)
        'A'
        >>> column_index_to_letter(25)
        'Z'
        >>> column_index_to_letter(26)
        'AA'
        >>> column_index_to_letter(27)
        'AB'
    """
    result = ""
    index += 1  # Convert to 1-based
    while index > 0:
        index, remainder = divmod(index - 1, 26)
        result = chr(65 + remainder) + result
    return result


def find_column_index(headers: list[str], possible_names: list[str]) -> int:
    """Find column index by possible header names (case-insensitive).

    Args:
        headers: List of header names from the sheet
        possible_names: List of possible column names to search for

    Returns:
        int: Column index (0-based) or -1 if not found

    Examples:
        >>> find_column_index(["ID", "Name", "Status"], ["id", "ID"])
        0
        >>> find_column_index(["ID", "Name", "Status"], ["payment_status", "Status"])
        2
    """
    for i, header in enumerate(headers):
        header_lower = header.lower().strip()
        for name in possible_names:
            if header_lower == name.lower():
                return i
    return -1


def get_cell_reference(col_index: int, row_number: int) -> str:
    """Get a cell reference like 'A1', 'B2', 'AA100'.

    Args:
        col_index: 0-based column index
        row_number: 1-based row number

    Returns:
        str: Cell reference (e.g., 'A1', 'AA100')
    """
    return f"{column_index_to_letter(col_index)}{row_number}"
