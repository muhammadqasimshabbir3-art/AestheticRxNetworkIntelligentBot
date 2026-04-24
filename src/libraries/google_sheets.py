"""Google Sheets API module.

Provides functionality to create and manage Google Sheets via the API.
Uses service account credentials from Bitwarden.

API References:
- Drive API v3: https://developers.google.com/workspace/drive/api/reference/rest/v3
- Sheets API v4: https://developers.google.com/workspace/sheets/api/reference/rest
"""

import json
from datetime import datetime, timedelta
from typing import Any

import requests

from .credentials import get_google_credentials
from .logger import logger


class GoogleAuthError(Exception):
    """Error during Google authentication."""

    pass


class GoogleAPIError(Exception):
    """Error from Google API."""

    pass


class SheetRowWriter:
    """Context manager for writing rows to Google Sheets with buffering.

    Provides an efficient way to add data row by row with automatic batching.

    Usage:
        sheets = GoogleSheetsAPI()
        spreadsheet_id = sheets.create_spreadsheet("My Data")

        with sheets.row_writer(spreadsheet_id) as writer:
            writer.write_header(["Name", "Age", "City"])
            writer.write_row(["Alice", 30, "NYC"])
            writer.write_row(["Bob", 25, "LA"])
            writer.write_row_from_dict({"Name": "Charlie", "Age": 35, "City": "Chicago"})
        # Data is flushed automatically when exiting context
    """

    def __init__(
        self,
        sheets_api: "GoogleSheetsAPI",
        spreadsheet_id: str,
        sheet_name: str = "Sheet1",
        buffer_size: int = 50,
        headers: list[str] | None = None,
    ) -> None:
        """Initialize the row writer.

        Args:
            sheets_api: GoogleSheetsAPI instance
            spreadsheet_id: Target spreadsheet ID
            sheet_name: Sheet name
            buffer_size: Number of rows to buffer before flushing
            headers: Column headers for dict-to-row conversion
        """
        self._api = sheets_api
        self._spreadsheet_id = spreadsheet_id
        self._sheet_name = sheet_name
        self._buffer_size = buffer_size
        self._headers = headers
        self._buffer: list[list[Any]] = []
        self._total_rows = 0

    def __enter__(self) -> "SheetRowWriter":
        """Enter context manager."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit context manager - flush remaining data."""
        self.flush()

    def write_header(self, headers: list[str]) -> None:
        """Write header row and store headers for dict conversion.

        Args:
            headers: List of column headers
        """
        self._headers = headers
        self._buffer.append(headers)
        self._check_flush()

    def write_row(self, row: list[Any]) -> None:
        """Write a single row of data.

        Args:
            row: List of values
        """
        # Convert values to strings
        processed_row = []
        for value in row:
            if value is None:
                processed_row.append("")
            elif isinstance(value, (dict, list)):
                processed_row.append(json.dumps(value))
            else:
                processed_row.append(str(value))

        self._buffer.append(processed_row)
        self._check_flush()

    def write_row_from_dict(self, row_data: dict[str, Any]) -> None:
        """Write a row from a dictionary using stored headers.

        Args:
            row_data: Dictionary with column names as keys

        Raises:
            ValueError: If headers not set via write_header()
        """
        if not self._headers:
            raise ValueError("Headers not set. Call write_header() first or pass headers in constructor.")

        row = []
        for header in self._headers:
            value = row_data.get(header)
            if value is None:
                row.append("")
            elif isinstance(value, (dict, list)):
                row.append(json.dumps(value))
            else:
                row.append(str(value))

        self._buffer.append(row)
        self._check_flush()

    def write_rows(self, rows: list[list[Any]]) -> None:
        """Write multiple rows at once.

        Args:
            rows: List of rows
        """
        for row in rows:
            self.write_row(row)

    def write_rows_from_dicts(self, rows_data: list[dict[str, Any]]) -> None:
        """Write multiple rows from dictionaries.

        Args:
            rows_data: List of dictionaries
        """
        for row_data in rows_data:
            self.write_row_from_dict(row_data)

    def _check_flush(self) -> None:
        """Check if buffer should be flushed."""
        if len(self._buffer) >= self._buffer_size:
            self.flush()

    def flush(self) -> None:
        """Flush buffered rows to the spreadsheet."""
        if not self._buffer:
            return

        self._api.append_data(self._spreadsheet_id, self._buffer, self._sheet_name)
        self._total_rows += len(self._buffer)
        logger.info(f"Flushed {len(self._buffer)} rows (total: {self._total_rows})")
        self._buffer = []

    @property
    def total_rows_written(self) -> int:
        """Get total number of rows written (including buffered)."""
        return self._total_rows + len(self._buffer)


class _GoogleAuth:
    """Handles Google API authentication using service account.

    Internal class - inherited by GoogleSheetsAPI.
    """

    GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
    SCOPES = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive.file",
    ]

    def __init__(self) -> None:
        """Initialize Google authentication."""
        self._access_token: str | None = None
        self._token_expires_at: datetime | None = None
        self._service_account: dict | None = None

    def _load_service_account(self) -> None:
        """Load service account credentials from environment variables."""
        logger.info("Getting Google credentials from environment variables...")
        creds = get_google_credentials()

        if not creds:
            raise GoogleAuthError("Google credentials not found in environment variables")

        # Credentials can be JSON string or dict
        if isinstance(creds.get("service_account_json"), str):
            self._service_account = json.loads(creds["service_account_json"])
        elif isinstance(creds.get("service_account"), dict):
            self._service_account = creds["service_account"]
        elif "private_key" in creds:
            # Direct service account fields
            self._service_account = creds
        else:
            raise GoogleAuthError(
                "Invalid Google credentials format. Expected 'service_account_json' or 'private_key' field."
            )

        logger.info(f"✓ Loaded Google service account: {self._service_account.get('client_email', 'unknown')}")

    def _create_jwt(self) -> str:
        """Create a signed JWT for service account authentication."""
        import base64
        import time

        try:
            from cryptography.hazmat.backends import default_backend
            from cryptography.hazmat.primitives import hashes, serialization
            from cryptography.hazmat.primitives.asymmetric import padding
        except ImportError:
            raise GoogleAuthError("cryptography package required. Install with: pip install cryptography")

        now = int(time.time())

        # JWT Header
        header = {"alg": "RS256", "typ": "JWT"}
        header_b64 = base64.urlsafe_b64encode(json.dumps(header).encode()).rstrip(b"=").decode()

        # JWT Payload
        payload = {
            "iss": self._service_account["client_email"],
            "scope": " ".join(self.SCOPES),
            "aud": self.GOOGLE_TOKEN_URL,
            "iat": now,
            "exp": now + 3600,  # 1 hour
        }
        payload_b64 = base64.urlsafe_b64encode(json.dumps(payload).encode()).rstrip(b"=").decode()

        # Sign with private key
        message = f"{header_b64}.{payload_b64}".encode()
        # Handle escaped newlines from JSON stored in environment variables
        private_key_str = self._service_account["private_key"]
        if "\\n" in private_key_str:
            private_key_str = private_key_str.replace("\\n", "\n")
        private_key_pem = private_key_str.encode()
        private_key = serialization.load_pem_private_key(private_key_pem, password=None, backend=default_backend())

        signature = private_key.sign(message, padding.PKCS1v15(), hashes.SHA256())
        signature_b64 = base64.urlsafe_b64encode(signature).rstrip(b"=").decode()

        return f"{header_b64}.{payload_b64}.{signature_b64}"

    def _get_access_token(self) -> str:
        """Get or refresh access token."""
        # Check if token is still valid
        if self._access_token and self._token_expires_at and datetime.now() < self._token_expires_at:
            return self._access_token

        if not self._service_account:
            self._load_service_account()

        logger.info("Getting Google API access token...")
        jwt = self._create_jwt()

        response = requests.post(
            self.GOOGLE_TOKEN_URL,
            data={
                "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
                "assertion": jwt,
            },
        )

        if not response.ok:
            raise GoogleAuthError(f"Failed to get access token: {response.text}")

        data = response.json()
        self._access_token = data["access_token"]
        # Token expires in X seconds, subtract 60 for safety margin
        expires_in = data.get("expires_in", 3600) - 60
        self._token_expires_at = datetime.now() + timedelta(seconds=expires_in)

        logger.info("✓ Got Google API access token")
        return self._access_token

    def _get_headers(self) -> dict[str, str]:
        """Get headers with authentication."""
        token = self._get_access_token()
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }


class _GoogleDrive(_GoogleAuth):
    """Google Drive API operations.

    Internal class - inherited by GoogleSheetsAPI.

    API Reference: https://developers.google.com/workspace/drive/api/reference/rest/v3
    """

    DRIVE_API_BASE = "https://www.googleapis.com/drive/v3"

    def create_folder(self, name: str, parent_id: str | None = None) -> str:
        """Create a folder in Google Drive.

        Args:
            name: Folder name
            parent_id: Parent folder ID (None for root)

        Returns:
            str: Created folder ID
        """
        logger.info(f"Creating folder: {name}")

        metadata = {
            "name": name,
            "mimeType": "application/vnd.google-apps.folder",
        }
        if parent_id:
            metadata["parents"] = [parent_id]

        response = requests.post(
            f"{self.DRIVE_API_BASE}/files",
            headers=self._get_headers(),
            json=metadata,
        )

        if not response.ok:
            raise GoogleAPIError(f"Failed to create folder: {response.text}")

        folder_id = response.json()["id"]
        logger.info(f"✓ Created folder: {folder_id}")
        return folder_id

    def list_files(
        self,
        query: str | None = None,
        folder_id: str | None = None,
        page_size: int = 100,
    ) -> list[dict]:
        """List files in Google Drive.

        Args:
            query: Search query (e.g., "name contains 'report'")
            folder_id: List files in specific folder
            page_size: Number of results per page

        Returns:
            list[dict]: List of file metadata
        """
        params = {
            "pageSize": page_size,
            "fields": "files(id, name, mimeType, createdTime, modifiedTime)",
        }

        if query:
            params["q"] = query
        elif folder_id:
            params["q"] = f"'{folder_id}' in parents"

        response = requests.get(
            f"{self.DRIVE_API_BASE}/files",
            headers=self._get_headers(),
            params=params,
        )

        if not response.ok:
            raise GoogleAPIError(f"Failed to list files: {response.text}")

        return response.json().get("files", [])

    def get_file(self, file_id: str) -> dict:
        """Get file metadata.

        Args:
            file_id: File ID

        Returns:
            dict: File metadata
        """
        response = requests.get(
            f"{self.DRIVE_API_BASE}/files/{file_id}",
            headers=self._get_headers(),
            params={"fields": "id, name, mimeType, webViewLink, createdTime, modifiedTime"},
        )

        if not response.ok:
            raise GoogleAPIError(f"Failed to get file: {response.text}")

        return response.json()

    def delete_file(self, file_id: str) -> None:
        """Delete a file.

        Args:
            file_id: File ID to delete
        """
        logger.info(f"Deleting file: {file_id}")

        response = requests.delete(
            f"{self.DRIVE_API_BASE}/files/{file_id}",
            headers=self._get_headers(),
        )

        if not response.ok:
            raise GoogleAPIError(f"Failed to delete file: {response.text}")

        logger.info(f"✓ Deleted file: {file_id}")

    def share_file(
        self,
        file_id: str,
        email: str,
        role: str = "reader",
        notify: bool = False,
    ) -> None:
        """Share a file with a user.

        Args:
            file_id: File ID
            email: Email to share with
            role: Permission role (reader, writer, commenter)
            notify: Send notification email
        """
        logger.info(f"Sharing file {file_id} with {email}")

        response = requests.post(
            f"{self.DRIVE_API_BASE}/files/{file_id}/permissions",
            headers=self._get_headers(),
            params={"sendNotificationEmail": str(notify).lower()},
            json={
                "type": "user",
                "role": role,
                "emailAddress": email,
            },
        )

        if not response.ok:
            raise GoogleAPIError(f"Failed to share file: {response.text}")

        logger.info(f"✓ Shared file with {email}")


class GoogleSheetsAPI(_GoogleDrive):
    """Google Sheets API client.

    This is the ONLY class that should be used externally.

    Inherits from:
    - _GoogleDrive (drive operations) → _GoogleAuth (authentication)

    API Reference: https://developers.google.com/workspace/sheets/api/reference/rest

    Usage:
        sheets = GoogleSheetsAPI()
        sheet_id = sheets.create_spreadsheet("My Report")
        sheets.write_data(sheet_id, data)
    """

    SHEETS_API_BASE = "https://sheets.googleapis.com/v4/spreadsheets"

    def __init__(self, auto_authenticate: bool = True) -> None:
        """Initialize Google Sheets API client.

        Args:
            auto_authenticate: If True, authenticate during initialization
        """
        super().__init__()

        logger.info("=" * 50)
        logger.info("Initializing GoogleSheetsAPI")
        logger.info("=" * 50)

        if auto_authenticate:
            self._load_service_account()
            self._get_access_token()

        logger.info("=" * 50)
        logger.info("GoogleSheetsAPI ready")
        logger.info("=" * 50)

    # ===================
    # Spreadsheet Operations
    # ===================

    def create_spreadsheet(
        self,
        title: str,
        sheet_names: list[str] | None = None,
        folder_id: str | None = None,
    ) -> str:
        """Create a new Google Spreadsheet.

        Args:
            title: Spreadsheet title
            sheet_names: Names of sheets to create (default: ["Sheet1"])
            folder_id: Parent folder ID (None for root)

        Returns:
            str: Spreadsheet ID
        """
        logger.info(f"Creating spreadsheet: {title}")

        sheets = []
        for i, name in enumerate(sheet_names or ["Sheet1"]):
            sheets.append(
                {
                    "properties": {
                        "sheetId": i,
                        "title": name,
                    }
                }
            )

        body = {
            "properties": {"title": title},
            "sheets": sheets,
        }

        response = requests.post(
            self.SHEETS_API_BASE,
            headers=self._get_headers(),
            json=body,
        )

        if not response.ok:
            raise GoogleAPIError(f"Failed to create spreadsheet: {response.text}")

        data = response.json()
        spreadsheet_id = data["spreadsheetId"]

        # Move to folder if specified
        if folder_id:
            self._move_to_folder(spreadsheet_id, folder_id)

        logger.info(f"✓ Created spreadsheet: {spreadsheet_id}")
        logger.info(f"  URL: https://docs.google.com/spreadsheets/d/{spreadsheet_id}")

        return spreadsheet_id

    def _move_to_folder(self, file_id: str, folder_id: str) -> None:
        """Move a file to a folder."""
        # Get current parents
        response = requests.get(
            f"{self.DRIVE_API_BASE}/files/{file_id}",
            headers=self._get_headers(),
            params={"fields": "parents"},
        )

        if response.ok:
            current_parents = response.json().get("parents", [])

            # Update parents
            requests.patch(
                f"{self.DRIVE_API_BASE}/files/{file_id}",
                headers=self._get_headers(),
                params={
                    "addParents": folder_id,
                    "removeParents": ",".join(current_parents),
                },
            )

    def get_spreadsheet(self, spreadsheet_id: str) -> dict:
        """Get spreadsheet metadata.

        Args:
            spreadsheet_id: Spreadsheet ID

        Returns:
            dict: Spreadsheet metadata
        """
        response = requests.get(
            f"{self.SHEETS_API_BASE}/{spreadsheet_id}",
            headers=self._get_headers(),
        )

        if not response.ok:
            raise GoogleAPIError(f"Failed to get spreadsheet: {response.text}")

        return response.json()

    # ===================
    # Data Operations
    # ===================

    def write_data(
        self,
        spreadsheet_id: str,
        data: list[list[Any]],
        sheet_name: str = "Sheet1",
        start_cell: str = "A1",
    ) -> dict:
        """Write data to a spreadsheet.

        Args:
            spreadsheet_id: Spreadsheet ID
            data: 2D list of values [[row1], [row2], ...]
            sheet_name: Sheet name
            start_cell: Starting cell (e.g., "A1")

        Returns:
            dict: API response
        """
        logger.info(f"Writing {len(data)} rows to {sheet_name}")

        range_name = f"{sheet_name}!{start_cell}"

        response = requests.put(
            f"{self.SHEETS_API_BASE}/{spreadsheet_id}/values/{range_name}",
            headers=self._get_headers(),
            params={"valueInputOption": "USER_ENTERED"},
            json={"values": data},
        )

        if not response.ok:
            raise GoogleAPIError(f"Failed to write data: {response.text}")

        result = response.json()
        logger.info(f"✓ Updated {result.get('updatedCells', 0)} cells")
        return result

    def append_data(
        self,
        spreadsheet_id: str,
        data: list[list[Any]],
        sheet_name: str = "Sheet1",
    ) -> dict:
        """Append data to a spreadsheet.

        Args:
            spreadsheet_id: Spreadsheet ID
            data: 2D list of values to append
            sheet_name: Sheet name

        Returns:
            dict: API response
        """
        logger.info(f"Appending {len(data)} rows to {sheet_name}")

        range_name = f"{sheet_name}!A:Z"

        response = requests.post(
            f"{self.SHEETS_API_BASE}/{spreadsheet_id}/values/{range_name}:append",
            headers=self._get_headers(),
            params={
                "valueInputOption": "USER_ENTERED",
                "insertDataOption": "INSERT_ROWS",
            },
            json={"values": data},
        )

        if not response.ok:
            raise GoogleAPIError(f"Failed to append data: {response.text}")

        result = response.json()
        logger.info(f"✓ Appended {len(data)} rows")
        return result

    def add_row(
        self,
        spreadsheet_id: str,
        row: list[Any],
        sheet_name: str = "Sheet1",
    ) -> dict:
        """Add a single row to the end of the spreadsheet.

        Args:
            spreadsheet_id: Spreadsheet ID
            row: List of values for the row
            sheet_name: Sheet name

        Returns:
            dict: API response
        """
        return self.append_data(spreadsheet_id, [row], sheet_name)

    def add_rows_batch(
        self,
        spreadsheet_id: str,
        rows: list[list[Any]],
        sheet_name: str = "Sheet1",
        batch_size: int = 100,
    ) -> int:
        """Add multiple rows in batches for better performance.

        Useful for large datasets - processes rows in configurable batch sizes.

        Args:
            spreadsheet_id: Spreadsheet ID
            rows: List of rows to add
            sheet_name: Sheet name
            batch_size: Number of rows per batch (default: 100)

        Returns:
            int: Total number of rows added
        """
        total_rows = len(rows)
        added = 0

        logger.info(f"Adding {total_rows} rows in batches of {batch_size}")

        for i in range(0, total_rows, batch_size):
            batch = rows[i : i + batch_size]
            self.append_data(spreadsheet_id, batch, sheet_name)
            added += len(batch)
            logger.info(f"  Progress: {added}/{total_rows} rows")

        logger.info(f"✓ Added {added} rows total")
        return added

    def add_row_from_dict(
        self,
        spreadsheet_id: str,
        row_data: dict[str, Any],
        headers: list[str] | None = None,
        sheet_name: str = "Sheet1",
    ) -> dict:
        """Add a row from a dictionary, matching keys to column headers.

        Args:
            spreadsheet_id: Spreadsheet ID
            row_data: Dictionary with column names as keys
            headers: Column headers (if None, uses dict keys in order)
            sheet_name: Sheet name

        Returns:
            dict: API response
        """
        if headers is None:
            headers = list(row_data.keys())

        row = []
        for header in headers:
            value = row_data.get(header)
            if value is None:
                row.append("")
            elif isinstance(value, (dict, list)):
                import json

                row.append(json.dumps(value))
            else:
                row.append(str(value))

        return self.add_row(spreadsheet_id, row, sheet_name)

    def add_rows_from_dicts(
        self,
        spreadsheet_id: str,
        rows_data: list[dict[str, Any]],
        headers: list[str] | None = None,
        sheet_name: str = "Sheet1",
        include_headers: bool = False,
        batch_size: int = 100,
    ) -> int:
        """Add multiple rows from a list of dictionaries.

        Args:
            spreadsheet_id: Spreadsheet ID
            rows_data: List of dictionaries
            headers: Column headers (if None, uses keys from first dict)
            sheet_name: Sheet name
            include_headers: If True, write headers as first row
            batch_size: Rows per batch for performance

        Returns:
            int: Number of rows added
        """
        if not rows_data:
            return 0

        # Get headers from first row if not provided
        if headers is None:
            headers = list(rows_data[0].keys())

        # Convert dicts to rows
        rows = []

        # Optionally add header row first
        if include_headers:
            rows.append(headers)

        for row_data in rows_data:
            row = []
            for header in headers:
                value = row_data.get(header)
                if value is None:
                    row.append("")
                elif isinstance(value, (dict, list)):
                    import json

                    row.append(json.dumps(value))
                else:
                    row.append(str(value))
            rows.append(row)

        return self.add_rows_batch(spreadsheet_id, rows, sheet_name, batch_size)

    def row_writer(
        self,
        spreadsheet_id: str,
        sheet_name: str = "Sheet1",
        buffer_size: int = 50,
        headers: list[str] | None = None,
    ) -> SheetRowWriter:
        """Create a row writer context manager for streaming row-by-row data.

        Provides efficient buffered writing with automatic flushing.

        Args:
            spreadsheet_id: Target spreadsheet ID
            sheet_name: Sheet name
            buffer_size: Rows to buffer before auto-flushing
            headers: Column headers for dict-to-row conversion

        Returns:
            SheetRowWriter: Context manager for row-by-row writing

        Example:
            sheets = GoogleSheetsAPI()
            spreadsheet_id = sheets.create_spreadsheet("Orders Export")

            with sheets.row_writer(spreadsheet_id) as writer:
                writer.write_header(["ID", "Name", "Amount"])
                for order in orders:
                    writer.write_row([order["id"], order["name"], order["amount"]])

            # Or with dicts:
            with sheets.row_writer(spreadsheet_id, headers=["id", "name", "amount"]) as writer:
                writer.write_header(writer._headers)
                for order in orders:
                    writer.write_row_from_dict(order)
        """
        return SheetRowWriter(
            sheets_api=self,
            spreadsheet_id=spreadsheet_id,
            sheet_name=sheet_name,
            buffer_size=buffer_size,
            headers=headers,
        )

    def read_data(
        self,
        spreadsheet_id: str,
        range_name: str = "Sheet1!A:Z",
    ) -> list[list[Any]]:
        """Read data from a spreadsheet.

        Args:
            spreadsheet_id: Spreadsheet ID
            range_name: Range to read (e.g., "Sheet1!A1:D10")

        Returns:
            list[list]: 2D list of values
        """
        response = requests.get(
            f"{self.SHEETS_API_BASE}/{spreadsheet_id}/values/{range_name}",
            headers=self._get_headers(),
        )

        if not response.ok:
            raise GoogleAPIError(f"Failed to read data: {response.text}")

        return response.json().get("values", [])

    def clear_data(
        self,
        spreadsheet_id: str,
        range_name: str = "Sheet1!A:Z",
    ) -> None:
        """Clear data from a range.

        Args:
            spreadsheet_id: Spreadsheet ID
            range_name: Range to clear
        """
        logger.info(f"Clearing range: {range_name}")

        response = requests.post(
            f"{self.SHEETS_API_BASE}/{spreadsheet_id}/values/{range_name}:clear",
            headers=self._get_headers(),
        )

        if not response.ok:
            raise GoogleAPIError(f"Failed to clear data: {response.text}")

        logger.info("✓ Cleared range")

    # ===================
    # Batch Operations (v4 API)
    # Reference: https://developers.google.com/workspace/sheets/api/reference/rest/v4/spreadsheets.values
    # ===================

    def batch_get(
        self,
        spreadsheet_id: str,
        ranges: list[str],
        major_dimension: str = "ROWS",
        value_render_option: str = "FORMATTED_VALUE",
    ) -> dict[str, list[list[Any]]]:
        """Get values from multiple ranges in one request.

        API: GET /v4/spreadsheets/{spreadsheetId}/values:batchGet

        Args:
            spreadsheet_id: Spreadsheet ID
            ranges: List of A1 notation ranges (e.g., ["Sheet1!A1:B5", "Sheet2!C1:D10"])
            major_dimension: ROWS or COLUMNS
            value_render_option: FORMATTED_VALUE, UNFORMATTED_VALUE, or FORMULA

        Returns:
            dict: Mapping of range to values
        """
        logger.info(f"Batch getting {len(ranges)} ranges")

        params = {
            "ranges": ranges,
            "majorDimension": major_dimension,
            "valueRenderOption": value_render_option,
        }

        response = requests.get(
            f"{self.SHEETS_API_BASE}/{spreadsheet_id}/values:batchGet",
            headers=self._get_headers(),
            params=params,
        )

        if not response.ok:
            raise GoogleAPIError(f"Failed to batch get: {response.text}")

        result = {}
        for value_range in response.json().get("valueRanges", []):
            range_name = value_range.get("range", "")
            result[range_name] = value_range.get("values", [])

        logger.info(f"✓ Retrieved {len(result)} ranges")
        return result

    def batch_update_values(
        self,
        spreadsheet_id: str,
        data: list[dict[str, Any]],
        value_input_option: str = "USER_ENTERED",
    ) -> dict:
        """Update multiple ranges in one request.

        API: POST /v4/spreadsheets/{spreadsheetId}/values:batchUpdate

        Args:
            spreadsheet_id: Spreadsheet ID
            data: List of dicts with 'range' and 'values' keys
                  e.g., [{"range": "Sheet1!A1", "values": [["a", "b"]]}, ...]
            value_input_option: USER_ENTERED or RAW

        Returns:
            dict: API response with update details
        """
        logger.info(f"Batch updating {len(data)} ranges")

        body = {
            "valueInputOption": value_input_option,
            "data": data,
        }

        response = requests.post(
            f"{self.SHEETS_API_BASE}/{spreadsheet_id}/values:batchUpdate",
            headers=self._get_headers(),
            json=body,
        )

        if not response.ok:
            raise GoogleAPIError(f"Failed to batch update: {response.text}")

        result = response.json()
        logger.info(
            f"✓ Updated {result.get('totalUpdatedCells', 0)} cells across {result.get('totalUpdatedSheets', 0)} sheets"
        )
        return result

    def batch_clear(
        self,
        spreadsheet_id: str,
        ranges: list[str],
    ) -> None:
        """Clear multiple ranges in one request.

        API: POST /v4/spreadsheets/{spreadsheetId}/values:batchClear

        Args:
            spreadsheet_id: Spreadsheet ID
            ranges: List of A1 notation ranges to clear
        """
        logger.info(f"Batch clearing {len(ranges)} ranges")

        response = requests.post(
            f"{self.SHEETS_API_BASE}/{spreadsheet_id}/values:batchClear",
            headers=self._get_headers(),
            json={"ranges": ranges},
        )

        if not response.ok:
            raise GoogleAPIError(f"Failed to batch clear: {response.text}")

        logger.info(f"✓ Cleared {len(ranges)} ranges")

    # ===================
    # Sheet Management Operations
    # Reference: https://developers.google.com/workspace/sheets/api/reference/rest/v4/spreadsheets/batchUpdate
    # ===================

    def add_sheet(
        self,
        spreadsheet_id: str,
        title: str,
        rows: int = 1000,
        columns: int = 26,
    ) -> int:
        """Add a new sheet to an existing spreadsheet.

        Args:
            spreadsheet_id: Spreadsheet ID
            title: Name of the new sheet
            rows: Number of rows
            columns: Number of columns

        Returns:
            int: Sheet ID of the new sheet
        """
        logger.info(f"Adding sheet: {title}")

        requests_body = {
            "requests": [
                {
                    "addSheet": {
                        "properties": {
                            "title": title,
                            "gridProperties": {
                                "rowCount": rows,
                                "columnCount": columns,
                            },
                        }
                    }
                }
            ]
        }

        response = requests.post(
            f"{self.SHEETS_API_BASE}/{spreadsheet_id}:batchUpdate",
            headers=self._get_headers(),
            json=requests_body,
        )

        if not response.ok:
            raise GoogleAPIError(f"Failed to add sheet: {response.text}")

        replies = response.json().get("replies", [])
        sheet_id = replies[0]["addSheet"]["properties"]["sheetId"] if replies else 0
        logger.info(f"✓ Added sheet '{title}' with ID: {sheet_id}")
        return sheet_id

    def delete_sheet(
        self,
        spreadsheet_id: str,
        sheet_id: int,
    ) -> None:
        """Delete a sheet from a spreadsheet.

        Args:
            spreadsheet_id: Spreadsheet ID
            sheet_id: Sheet ID to delete
        """
        logger.info(f"Deleting sheet ID: {sheet_id}")

        requests_body = {"requests": [{"deleteSheet": {"sheetId": sheet_id}}]}

        response = requests.post(
            f"{self.SHEETS_API_BASE}/{spreadsheet_id}:batchUpdate",
            headers=self._get_headers(),
            json=requests_body,
        )

        if not response.ok:
            raise GoogleAPIError(f"Failed to delete sheet: {response.text}")

        logger.info(f"✓ Deleted sheet ID: {sheet_id}")

    def rename_sheet(
        self,
        spreadsheet_id: str,
        sheet_id: int,
        new_title: str,
    ) -> None:
        """Rename a sheet.

        Args:
            spreadsheet_id: Spreadsheet ID
            sheet_id: Sheet ID to rename
            new_title: New sheet name
        """
        logger.info(f"Renaming sheet {sheet_id} to: {new_title}")

        requests_body = {
            "requests": [
                {
                    "updateSheetProperties": {
                        "properties": {
                            "sheetId": sheet_id,
                            "title": new_title,
                        },
                        "fields": "title",
                    }
                }
            ]
        }

        response = requests.post(
            f"{self.SHEETS_API_BASE}/{spreadsheet_id}:batchUpdate",
            headers=self._get_headers(),
            json=requests_body,
        )

        if not response.ok:
            raise GoogleAPIError(f"Failed to rename sheet: {response.text}")

        logger.info(f"✓ Renamed sheet to: {new_title}")

    def copy_sheet_to(
        self,
        source_spreadsheet_id: str,
        sheet_id: int,
        destination_spreadsheet_id: str,
    ) -> int:
        """Copy a sheet to another spreadsheet.

        API: POST /v4/spreadsheets/{spreadsheetId}/sheets/{sheetId}:copyTo

        Args:
            source_spreadsheet_id: Source spreadsheet ID
            sheet_id: Sheet ID to copy
            destination_spreadsheet_id: Destination spreadsheet ID

        Returns:
            int: Sheet ID of the copied sheet in the destination
        """
        logger.info(f"Copying sheet {sheet_id} to spreadsheet {destination_spreadsheet_id}")

        response = requests.post(
            f"{self.SHEETS_API_BASE}/{source_spreadsheet_id}/sheets/{sheet_id}:copyTo",
            headers=self._get_headers(),
            json={"destinationSpreadsheetId": destination_spreadsheet_id},
        )

        if not response.ok:
            raise GoogleAPIError(f"Failed to copy sheet: {response.text}")

        new_sheet_id = response.json().get("sheetId", 0)
        logger.info(f"✓ Copied sheet to new ID: {new_sheet_id}")
        return new_sheet_id

    def get_sheet_info(
        self,
        spreadsheet_id: str,
    ) -> list[dict]:
        """Get information about all sheets in a spreadsheet.

        Args:
            spreadsheet_id: Spreadsheet ID

        Returns:
            list: List of sheet info dicts with id, title, rowCount, columnCount
        """
        data = self.get_spreadsheet(spreadsheet_id)
        sheets = []
        for sheet in data.get("sheets", []):
            props = sheet.get("properties", {})
            grid = props.get("gridProperties", {})
            sheets.append(
                {
                    "sheetId": props.get("sheetId"),
                    "title": props.get("title"),
                    "index": props.get("index"),
                    "rowCount": grid.get("rowCount"),
                    "columnCount": grid.get("columnCount"),
                }
            )
        return sheets

    # ===================
    # Advanced Data Operations
    # ===================

    def find_and_replace(
        self,
        spreadsheet_id: str,
        find: str,
        replacement: str,
        sheet_id: int | None = None,
        match_case: bool = False,
        match_entire_cell: bool = False,
        search_by_regex: bool = False,
    ) -> int:
        """Find and replace text in the spreadsheet.

        Args:
            spreadsheet_id: Spreadsheet ID
            find: Text to find
            replacement: Replacement text
            sheet_id: Specific sheet (None for all sheets)
            match_case: Case-sensitive search
            match_entire_cell: Match entire cell contents
            search_by_regex: Treat 'find' as regex pattern

        Returns:
            int: Number of occurrences replaced
        """
        logger.info(f"Find and replace: '{find}' -> '{replacement}'")

        find_replace = {
            "find": find,
            "replacement": replacement,
            "matchCase": match_case,
            "matchEntireCell": match_entire_cell,
            "searchByRegex": search_by_regex,
            "allSheets": sheet_id is None,
        }

        if sheet_id is not None:
            find_replace["sheetId"] = sheet_id

        requests_body = {"requests": [{"findReplace": find_replace}]}

        response = requests.post(
            f"{self.SHEETS_API_BASE}/{spreadsheet_id}:batchUpdate",
            headers=self._get_headers(),
            json=requests_body,
        )

        if not response.ok:
            raise GoogleAPIError(f"Failed to find and replace: {response.text}")

        replies = response.json().get("replies", [{}])
        occurrences = replies[0].get("findReplace", {}).get("occurrencesChanged", 0)
        logger.info(f"✓ Replaced {occurrences} occurrences")
        return occurrences

    def insert_rows(
        self,
        spreadsheet_id: str,
        sheet_id: int,
        start_index: int,
        num_rows: int,
    ) -> None:
        """Insert empty rows at a specific position.

        Args:
            spreadsheet_id: Spreadsheet ID
            sheet_id: Sheet ID
            start_index: Row index to insert at (0-based)
            num_rows: Number of rows to insert
        """
        logger.info(f"Inserting {num_rows} rows at index {start_index}")

        requests_body = {
            "requests": [
                {
                    "insertDimension": {
                        "range": {
                            "sheetId": sheet_id,
                            "dimension": "ROWS",
                            "startIndex": start_index,
                            "endIndex": start_index + num_rows,
                        },
                        "inheritFromBefore": start_index > 0,
                    }
                }
            ]
        }

        response = requests.post(
            f"{self.SHEETS_API_BASE}/{spreadsheet_id}:batchUpdate",
            headers=self._get_headers(),
            json=requests_body,
        )

        if not response.ok:
            raise GoogleAPIError(f"Failed to insert rows: {response.text}")

        logger.info(f"✓ Inserted {num_rows} rows")

    def delete_rows(
        self,
        spreadsheet_id: str,
        sheet_id: int,
        start_index: int,
        num_rows: int,
    ) -> None:
        """Delete rows from a sheet.

        Args:
            spreadsheet_id: Spreadsheet ID
            sheet_id: Sheet ID
            start_index: Starting row index (0-based)
            num_rows: Number of rows to delete
        """
        logger.info(f"Deleting {num_rows} rows starting at index {start_index}")

        requests_body = {
            "requests": [
                {
                    "deleteDimension": {
                        "range": {
                            "sheetId": sheet_id,
                            "dimension": "ROWS",
                            "startIndex": start_index,
                            "endIndex": start_index + num_rows,
                        }
                    }
                }
            ]
        }

        response = requests.post(
            f"{self.SHEETS_API_BASE}/{spreadsheet_id}:batchUpdate",
            headers=self._get_headers(),
            json=requests_body,
        )

        if not response.ok:
            raise GoogleAPIError(f"Failed to delete rows: {response.text}")

        logger.info(f"✓ Deleted {num_rows} rows")

    def sort_range(
        self,
        spreadsheet_id: str,
        sheet_id: int,
        start_row: int,
        end_row: int,
        start_col: int,
        end_col: int,
        sort_column: int,
        ascending: bool = True,
    ) -> None:
        """Sort a range by a specific column.

        Args:
            spreadsheet_id: Spreadsheet ID
            sheet_id: Sheet ID
            start_row: Start row index (0-based)
            end_row: End row index (exclusive)
            start_col: Start column index (0-based)
            end_col: End column index (exclusive)
            sort_column: Column index to sort by (0-based)
            ascending: Sort order
        """
        logger.info(f"Sorting range by column {sort_column}")

        requests_body = {
            "requests": [
                {
                    "sortRange": {
                        "range": {
                            "sheetId": sheet_id,
                            "startRowIndex": start_row,
                            "endRowIndex": end_row,
                            "startColumnIndex": start_col,
                            "endColumnIndex": end_col,
                        },
                        "sortSpecs": [
                            {
                                "dimensionIndex": sort_column,
                                "sortOrder": "ASCENDING" if ascending else "DESCENDING",
                            }
                        ],
                    }
                }
            ]
        }

        response = requests.post(
            f"{self.SHEETS_API_BASE}/{spreadsheet_id}:batchUpdate",
            headers=self._get_headers(),
            json=requests_body,
        )

        if not response.ok:
            raise GoogleAPIError(f"Failed to sort range: {response.text}")

        logger.info("✓ Sorted range")

    # ===================
    # Formatting Operations
    # ===================

    def format_header_row(
        self,
        spreadsheet_id: str,
        sheet_id: int = 0,
        bold: bool = True,
        background_color: tuple[float, float, float] = (0.9, 0.9, 0.9),
    ) -> None:
        """Format the header row (first row).

        Args:
            spreadsheet_id: Spreadsheet ID
            sheet_id: Sheet ID (0 for first sheet)
            bold: Make text bold
            background_color: RGB tuple (0-1 range)
        """
        logger.info("Formatting header row")

        requests_body = {
            "requests": [
                {
                    "repeatCell": {
                        "range": {
                            "sheetId": sheet_id,
                            "startRowIndex": 0,
                            "endRowIndex": 1,
                        },
                        "cell": {
                            "userEnteredFormat": {
                                "backgroundColor": {
                                    "red": background_color[0],
                                    "green": background_color[1],
                                    "blue": background_color[2],
                                },
                                "textFormat": {"bold": bold},
                            }
                        },
                        "fields": "userEnteredFormat(backgroundColor,textFormat)",
                    }
                },
                {
                    "updateSheetProperties": {
                        "properties": {
                            "sheetId": sheet_id,
                            "gridProperties": {"frozenRowCount": 1},
                        },
                        "fields": "gridProperties.frozenRowCount",
                    }
                },
            ]
        }

        response = requests.post(
            f"{self.SHEETS_API_BASE}/{spreadsheet_id}:batchUpdate",
            headers=self._get_headers(),
            json=requests_body,
        )

        if not response.ok:
            raise GoogleAPIError(f"Failed to format header: {response.text}")

        logger.info("✓ Formatted header row")

    def auto_resize_columns(
        self,
        spreadsheet_id: str,
        sheet_id: int = 0,
    ) -> None:
        """Auto-resize all columns to fit content.

        Args:
            spreadsheet_id: Spreadsheet ID
            sheet_id: Sheet ID
        """
        logger.info("Auto-resizing columns")

        requests_body = {
            "requests": [
                {
                    "autoResizeDimensions": {
                        "dimensions": {
                            "sheetId": sheet_id,
                            "dimension": "COLUMNS",
                            "startIndex": 0,
                            "endIndex": 50,  # Resize first 50 columns
                        }
                    }
                }
            ]
        }

        response = requests.post(
            f"{self.SHEETS_API_BASE}/{spreadsheet_id}:batchUpdate",
            headers=self._get_headers(),
            json=requests_body,
        )

        if not response.ok:
            raise GoogleAPIError(f"Failed to resize columns: {response.text}")

        logger.info("✓ Auto-resized columns")

    # ===================
    # Convenience Methods
    # ===================

    def write_orders_to_sheet(
        self,
        orders: list[dict],
        title: str | None = None,
        spreadsheet_id: str | None = None,
    ) -> str:
        """Write order data to a Google Sheet.

        Creates a new spreadsheet or updates existing one.

        Args:
            orders: List of order dictionaries
            title: Spreadsheet title (for new sheet)
            spreadsheet_id: Existing spreadsheet ID (creates new if None)

        Returns:
            str: Spreadsheet ID
        """
        if not orders:
            raise ValueError("No orders to write")

        # Get column headers from first order
        headers = list(orders[0].keys())

        # Create rows
        rows = [headers]  # Header row
        for order in orders:
            row = []
            for key in headers:
                value = order.get(key)
                # Convert to string for sheets
                if value is None:
                    row.append("")
                elif isinstance(value, (dict, list)):
                    row.append(json.dumps(value))
                else:
                    row.append(str(value))
            rows.append(row)

        # Create or use existing spreadsheet
        if spreadsheet_id is None:
            if title is None:
                title = f"Orders Export - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            spreadsheet_id = self.create_spreadsheet(title)

        # Write data
        self.write_data(spreadsheet_id, rows)

        # Format
        self.format_header_row(spreadsheet_id)
        self.auto_resize_columns(spreadsheet_id)

        logger.info(f"✓ Wrote {len(orders)} orders to spreadsheet")
        logger.info(f"  URL: https://docs.google.com/spreadsheets/d/{spreadsheet_id}")

        return spreadsheet_id
