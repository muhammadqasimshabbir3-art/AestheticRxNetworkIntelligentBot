"""Google Drive API module.

Provides functionality to manage files and folders in Google Drive via the API.
Uses service account credentials from Bitwarden.

API Reference: https://developers.google.com/workspace/drive/api/reference/rest/v3
"""

import json
import mimetypes
from datetime import datetime, timedelta
from pathlib import Path

import requests

from .credentials import get_google_credentials
from .logger import logger


class GoogleDriveError(Exception):
    """Error from Google Drive API."""

    pass


class _GoogleDriveAuth:
    """Handles Google Drive API authentication using service account.

    Internal class - inherited by GoogleDriveAPI.
    """

    GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
    SCOPES = [
        "https://www.googleapis.com/auth/drive",
        "https://www.googleapis.com/auth/drive.file",
    ]

    def __init__(self) -> None:
        """Initialize Google authentication."""
        self._access_token: str | None = None
        self._token_expires_at: datetime | None = None
        self._service_account: dict | None = None

    def _load_service_account(self) -> None:
        """Load service account credentials from environment variables."""
        logger.info("Getting Google Drive credentials from environment variables...")
        creds = get_google_credentials()

        if not creds:
            raise GoogleDriveError("Google credentials not found in environment variables")

        # Credentials can be JSON string or dict
        if isinstance(creds.get("service_account_json"), str):
            self._service_account = json.loads(creds["service_account_json"])
        elif isinstance(creds.get("service_account"), dict):
            self._service_account = creds["service_account"]
        elif "private_key" in creds:
            self._service_account = creds
        else:
            raise GoogleDriveError(
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
            raise GoogleDriveError("cryptography package required. Install with: pip install cryptography")

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
            "exp": now + 3600,
        }
        payload_b64 = base64.urlsafe_b64encode(json.dumps(payload).encode()).rstrip(b"=").decode()

        # Sign with private key
        message = f"{header_b64}.{payload_b64}".encode()
        # Handle escaped newlines (common when stored in environment variables)
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
        if self._access_token and self._token_expires_at and datetime.now() < self._token_expires_at:
            return self._access_token

        if not self._service_account:
            self._load_service_account()

        logger.info("Getting Google Drive API access token...")
        jwt = self._create_jwt()

        response = requests.post(
            self.GOOGLE_TOKEN_URL,
            data={
                "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
                "assertion": jwt,
            },
        )

        if not response.ok:
            raise GoogleDriveError(f"Failed to get access token: {response.text}")

        data = response.json()
        self._access_token = data["access_token"]
        expires_in = data.get("expires_in", 3600) - 60
        self._token_expires_at = datetime.now() + timedelta(seconds=expires_in)

        logger.info("✓ Got Google Drive API access token")
        return self._access_token

    def _get_headers(self) -> dict[str, str]:
        """Get headers with authentication."""
        token = self._get_access_token()
        return {
            "Authorization": f"Bearer {token}",
        }

    def _get_json_headers(self) -> dict[str, str]:
        """Get headers for JSON requests."""
        headers = self._get_headers()
        headers["Content-Type"] = "application/json"
        return headers


class GoogleDriveAPI(_GoogleDriveAuth):
    """Google Drive API client.

    This is the main class for interacting with Google Drive.

    API Reference: https://developers.google.com/workspace/drive/api/reference/rest/v3

    Usage:
        drive = GoogleDriveAPI()

        # Create a folder
        folder_id = drive.create_folder("My Folder")

        # Upload a file
        file_id = drive.upload_file("report.pdf", folder_id=folder_id)

        # Share with someone
        drive.share_file(file_id, "user@example.com", role="reader")
    """

    DRIVE_API_BASE = "https://www.googleapis.com/drive/v3"
    UPLOAD_API_BASE = "https://www.googleapis.com/upload/drive/v3"

    # Common MIME types
    MIME_TYPES = {
        "folder": "application/vnd.google-apps.folder",
        "spreadsheet": "application/vnd.google-apps.spreadsheet",
        "document": "application/vnd.google-apps.document",
        "presentation": "application/vnd.google-apps.presentation",
        "pdf": "application/pdf",
        "csv": "text/csv",
        "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "json": "application/json",
        "txt": "text/plain",
    }

    def __init__(self, auto_authenticate: bool = True) -> None:
        """Initialize Google Drive API client.

        Args:
            auto_authenticate: If True, authenticate during initialization
        """
        super().__init__()

        logger.info("=" * 50)
        logger.info("Initializing GoogleDriveAPI")
        logger.info("=" * 50)

        if auto_authenticate:
            self._load_service_account()
            self._get_access_token()

        logger.info("=" * 50)
        logger.info("GoogleDriveAPI ready")
        logger.info("=" * 50)

    # ===================
    # File Operations
    # Reference: https://developers.google.com/workspace/drive/api/reference/rest/v3/files
    # ===================

    def get_file(
        self,
        file_id: str,
        fields: str = "id, name, mimeType, size, createdTime, modifiedTime, parents, webViewLink",
    ) -> dict:
        """Get file metadata by ID.

        API: GET /drive/v3/files/{fileId}

        Args:
            file_id: File ID
            fields: Comma-separated list of fields to return

        Returns:
            dict: File metadata
        """
        response = requests.get(
            f"{self.DRIVE_API_BASE}/files/{file_id}",
            headers=self._get_headers(),
            params={"fields": fields},
        )

        if not response.ok:
            raise GoogleDriveError(f"Failed to get file: {response.text}")

        return response.json()

    def list_files(
        self,
        query: str | None = None,
        folder_id: str | None = None,
        page_size: int = 100,
        fields: str = "files(id, name, mimeType, size, createdTime, modifiedTime, parents)",
        order_by: str = "modifiedTime desc",
    ) -> list[dict]:
        """List files in Google Drive.

        API: GET /drive/v3/files

        Args:
            query: Search query (e.g., "name contains 'report'")
            folder_id: List files in specific folder
            page_size: Number of results per page (max 1000)
            fields: Fields to return
            order_by: Sort order

        Returns:
            list[dict]: List of file metadata
        """
        params = {
            "pageSize": min(page_size, 1000),
            "fields": f"nextPageToken, {fields}",
            "orderBy": order_by,
        }

        # Build query
        q_parts = []
        if query:
            q_parts.append(query)
        if folder_id:
            q_parts.append(f"'{folder_id}' in parents")

        if q_parts:
            params["q"] = " and ".join(q_parts)

        all_files = []
        next_page_token = None

        while True:
            if next_page_token:
                params["pageToken"] = next_page_token

            response = requests.get(
                f"{self.DRIVE_API_BASE}/files",
                headers=self._get_headers(),
                params=params,
            )

            if not response.ok:
                raise GoogleDriveError(f"Failed to list files: {response.text}")

            data = response.json()
            all_files.extend(data.get("files", []))

            next_page_token = data.get("nextPageToken")
            if not next_page_token or len(all_files) >= page_size:
                break

        return all_files[:page_size]

    def search_files(
        self,
        name_contains: str | None = None,
        mime_type: str | None = None,
        folder_id: str | None = None,
        trashed: bool = False,
        page_size: int = 100,
    ) -> list[dict]:
        """Search for files with various filters.

        Args:
            name_contains: File name contains this string
            mime_type: Filter by MIME type
            folder_id: Filter by parent folder
            trashed: Include trashed files
            page_size: Max results

        Returns:
            list[dict]: Matching files
        """
        q_parts = [f"trashed = {str(trashed).lower()}"]

        if name_contains:
            q_parts.append(f"name contains '{name_contains}'")
        if mime_type:
            q_parts.append(f"mimeType = '{mime_type}'")
        if folder_id:
            q_parts.append(f"'{folder_id}' in parents")

        query = " and ".join(q_parts)
        return self.list_files(query=query, page_size=page_size)

    def create_file(
        self,
        name: str,
        mime_type: str | None = None,
        parent_id: str | None = None,
        content: bytes | str | None = None,
        description: str | None = None,
    ) -> str:
        """Create a new file in Google Drive.

        API: POST /drive/v3/files

        Args:
            name: File name
            mime_type: MIME type (auto-detected if not provided)
            parent_id: Parent folder ID
            content: File content (bytes or string)
            description: File description

        Returns:
            str: Created file ID
        """
        logger.info(f"Creating file: {name}")

        # Build metadata
        metadata = {"name": name}
        if parent_id:
            metadata["parents"] = [parent_id]
        if description:
            metadata["description"] = description
        if mime_type:
            metadata["mimeType"] = mime_type

        if content is None:
            # Create metadata-only file
            response = requests.post(
                f"{self.DRIVE_API_BASE}/files",
                headers=self._get_json_headers(),
                json=metadata,
            )
        else:
            # Upload with content
            if isinstance(content, str):
                content = content.encode("utf-8")

            # Multipart upload
            boundary = "---boundary---"

            body = (
                (
                    f"--{boundary}\r\n"
                    f"Content-Type: application/json; charset=UTF-8\r\n\r\n"
                    f"{json.dumps(metadata)}\r\n"
                    f"--{boundary}\r\n"
                    f"Content-Type: {mime_type or 'application/octet-stream'}\r\n\r\n"
                ).encode()
                + content
                + f"\r\n--{boundary}--".encode()
            )

            headers = self._get_headers()
            headers["Content-Type"] = f"multipart/related; boundary={boundary}"

            response = requests.post(
                f"{self.UPLOAD_API_BASE}/files?uploadType=multipart",
                headers=headers,
                data=body,
            )

        if not response.ok:
            raise GoogleDriveError(f"Failed to create file: {response.text}")

        file_id = response.json()["id"]
        logger.info(f"✓ Created file: {file_id}")
        return file_id

    def upload_file(
        self,
        local_path: str | Path,
        name: str | None = None,
        parent_id: str | None = None,
        mime_type: str | None = None,
    ) -> str:
        """Upload a local file to Google Drive.

        Args:
            local_path: Path to local file
            name: Name in Drive (defaults to local filename)
            parent_id: Parent folder ID
            mime_type: MIME type (auto-detected if not provided)

        Returns:
            str: Uploaded file ID
        """
        local_path = Path(local_path)

        if not local_path.exists():
            raise GoogleDriveError(f"File not found: {local_path}")

        name = name or local_path.name

        # Auto-detect MIME type
        if mime_type is None:
            mime_type, _ = mimetypes.guess_type(str(local_path))
            mime_type = mime_type or "application/octet-stream"

        logger.info(f"Uploading file: {local_path} as '{name}'")

        with open(local_path, "rb") as f:
            content = f.read()

        return self.create_file(
            name=name,
            mime_type=mime_type,
            parent_id=parent_id,
            content=content,
        )

    def update_file(
        self,
        file_id: str,
        name: str | None = None,
        content: bytes | str | None = None,
        mime_type: str | None = None,
        add_parents: str | None = None,
        remove_parents: str | None = None,
    ) -> dict:
        """Update a file's metadata or content.

        API: PATCH /drive/v3/files/{fileId}

        Args:
            file_id: File ID to update
            name: New name
            content: New content
            mime_type: New MIME type
            add_parents: Comma-separated folder IDs to add
            remove_parents: Comma-separated folder IDs to remove

        Returns:
            dict: Updated file metadata
        """
        logger.info(f"Updating file: {file_id}")

        params = {}
        if add_parents:
            params["addParents"] = add_parents
        if remove_parents:
            params["removeParents"] = remove_parents

        metadata = {}
        if name:
            metadata["name"] = name

        if content is None:
            # Metadata-only update
            response = requests.patch(
                f"{self.DRIVE_API_BASE}/files/{file_id}",
                headers=self._get_json_headers(),
                params=params,
                json=metadata if metadata else None,
            )
        else:
            # Update with new content
            if isinstance(content, str):
                content = content.encode("utf-8")

            boundary = "---boundary---"

            body = (
                (
                    f"--{boundary}\r\n"
                    f"Content-Type: application/json; charset=UTF-8\r\n\r\n"
                    f"{json.dumps(metadata)}\r\n"
                    f"--{boundary}\r\n"
                    f"Content-Type: {mime_type or 'application/octet-stream'}\r\n\r\n"
                ).encode()
                + content
                + f"\r\n--{boundary}--".encode()
            )

            headers = self._get_headers()
            headers["Content-Type"] = f"multipart/related; boundary={boundary}"

            response = requests.patch(
                f"{self.UPLOAD_API_BASE}/files/{file_id}?uploadType=multipart",
                headers=headers,
                params=params,
                data=body,
            )

        if not response.ok:
            raise GoogleDriveError(f"Failed to update file: {response.text}")

        logger.info(f"✓ Updated file: {file_id}")
        return response.json()

    def copy_file(
        self,
        file_id: str,
        name: str | None = None,
        parent_id: str | None = None,
    ) -> str:
        """Create a copy of a file.

        API: POST /drive/v3/files/{fileId}/copy

        Args:
            file_id: Source file ID
            name: Name for the copy
            parent_id: Parent folder for the copy

        Returns:
            str: New file ID
        """
        logger.info(f"Copying file: {file_id}")

        metadata = {}
        if name:
            metadata["name"] = name
        if parent_id:
            metadata["parents"] = [parent_id]

        response = requests.post(
            f"{self.DRIVE_API_BASE}/files/{file_id}/copy",
            headers=self._get_json_headers(),
            json=metadata if metadata else None,
        )

        if not response.ok:
            raise GoogleDriveError(f"Failed to copy file: {response.text}")

        new_id = response.json()["id"]
        logger.info(f"✓ Copied to: {new_id}")
        return new_id

    def delete_file(self, file_id: str) -> None:
        """Permanently delete a file.

        API: DELETE /drive/v3/files/{fileId}

        Args:
            file_id: File ID to delete
        """
        logger.info(f"Deleting file: {file_id}")

        response = requests.delete(
            f"{self.DRIVE_API_BASE}/files/{file_id}",
            headers=self._get_headers(),
        )

        if not response.ok:
            raise GoogleDriveError(f"Failed to delete file: {response.text}")

        logger.info(f"✓ Deleted file: {file_id}")

    def trash_file(self, file_id: str) -> None:
        """Move a file to trash.

        Args:
            file_id: File ID to trash
        """
        logger.info(f"Trashing file: {file_id}")

        response = requests.patch(
            f"{self.DRIVE_API_BASE}/files/{file_id}",
            headers=self._get_json_headers(),
            json={"trashed": True},
        )

        if not response.ok:
            raise GoogleDriveError(f"Failed to trash file: {response.text}")

        logger.info(f"✓ Trashed file: {file_id}")

    def restore_file(self, file_id: str) -> None:
        """Restore a file from trash.

        Args:
            file_id: File ID to restore
        """
        logger.info(f"Restoring file: {file_id}")

        response = requests.patch(
            f"{self.DRIVE_API_BASE}/files/{file_id}",
            headers=self._get_json_headers(),
            json={"trashed": False},
        )

        if not response.ok:
            raise GoogleDriveError(f"Failed to restore file: {response.text}")

        logger.info(f"✓ Restored file: {file_id}")

    def empty_trash(self) -> None:
        """Permanently delete all files in trash.

        API: DELETE /drive/v3/files/trash
        """
        logger.info("Emptying trash...")

        response = requests.delete(
            f"{self.DRIVE_API_BASE}/files/trash",
            headers=self._get_headers(),
        )

        if not response.ok:
            raise GoogleDriveError(f"Failed to empty trash: {response.text}")

        logger.info("✓ Emptied trash")

    # ===================
    # Download & Export
    # ===================

    def download_file(
        self,
        file_id: str,
        local_path: str | Path | None = None,
    ) -> bytes:
        """Download a file's content.

        Args:
            file_id: File ID
            local_path: Save to this path (optional)

        Returns:
            bytes: File content
        """
        logger.info(f"Downloading file: {file_id}")

        response = requests.get(
            f"{self.DRIVE_API_BASE}/files/{file_id}",
            headers=self._get_headers(),
            params={"alt": "media"},
        )

        if not response.ok:
            raise GoogleDriveError(f"Failed to download file: {response.text}")

        content = response.content

        if local_path:
            Path(local_path).write_bytes(content)
            logger.info(f"✓ Downloaded to: {local_path}")
        else:
            logger.info(f"✓ Downloaded {len(content)} bytes")

        return content

    def export_file(
        self,
        file_id: str,
        mime_type: str,
        local_path: str | Path | None = None,
    ) -> bytes:
        """Export a Google Workspace document to a different format.

        API: GET /drive/v3/files/{fileId}/export

        Args:
            file_id: File ID (must be a Google Workspace doc)
            mime_type: Export format (e.g., "application/pdf")
            local_path: Save to this path (optional)

        Returns:
            bytes: Exported content
        """
        logger.info(f"Exporting file {file_id} as {mime_type}")

        response = requests.get(
            f"{self.DRIVE_API_BASE}/files/{file_id}/export",
            headers=self._get_headers(),
            params={"mimeType": mime_type},
        )

        if not response.ok:
            raise GoogleDriveError(f"Failed to export file: {response.text}")

        content = response.content

        if local_path:
            Path(local_path).write_bytes(content)
            logger.info(f"✓ Exported to: {local_path}")
        else:
            logger.info(f"✓ Exported {len(content)} bytes")

        return content

    def export_spreadsheet_as_csv(
        self,
        file_id: str,
        local_path: str | Path | None = None,
    ) -> str:
        """Export a Google Spreadsheet as CSV.

        Args:
            file_id: Spreadsheet file ID
            local_path: Save to this path (optional)

        Returns:
            str: CSV content
        """
        content = self.export_file(file_id, "text/csv", local_path)
        return content.decode("utf-8")

    def export_spreadsheet_as_xlsx(
        self,
        file_id: str,
        local_path: str | Path | None = None,
    ) -> bytes:
        """Export a Google Spreadsheet as Excel.

        Args:
            file_id: Spreadsheet file ID
            local_path: Save to this path (optional)

        Returns:
            bytes: Excel file content
        """
        return self.export_file(
            file_id,
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            local_path,
        )

    # ===================
    # Folder Operations
    # ===================

    def create_folder(
        self,
        name: str,
        parent_id: str | None = None,
        description: str | None = None,
    ) -> str:
        """Create a folder in Google Drive.

        Args:
            name: Folder name
            parent_id: Parent folder ID (None for root)
            description: Folder description

        Returns:
            str: Created folder ID
        """
        logger.info(f"Creating folder: {name}")

        metadata = {
            "name": name,
            "mimeType": self.MIME_TYPES["folder"],
        }
        if parent_id:
            metadata["parents"] = [parent_id]
        if description:
            metadata["description"] = description

        response = requests.post(
            f"{self.DRIVE_API_BASE}/files",
            headers=self._get_json_headers(),
            json=metadata,
        )

        if not response.ok:
            raise GoogleDriveError(f"Failed to create folder: {response.text}")

        folder_id = response.json()["id"]
        logger.info(f"✓ Created folder: {folder_id}")
        return folder_id

    def get_or_create_folder(
        self,
        name: str,
        parent_id: str | None = None,
    ) -> str:
        """Get existing folder or create if not exists.

        Args:
            name: Folder name
            parent_id: Parent folder ID

        Returns:
            str: Folder ID
        """
        # Search for existing folder
        q_parts = [
            f"name = '{name}'",
            f"mimeType = '{self.MIME_TYPES['folder']}'",
            "trashed = false",
        ]
        if parent_id:
            q_parts.append(f"'{parent_id}' in parents")

        files = self.list_files(query=" and ".join(q_parts), page_size=1)

        if files:
            logger.info(f"Found existing folder: {files[0]['id']}")
            return files[0]["id"]

        return self.create_folder(name, parent_id)

    def list_folder(
        self,
        folder_id: str | None = None,
        include_folders: bool = True,
        include_files: bool = True,
    ) -> list[dict]:
        """List contents of a folder.

        Args:
            folder_id: Folder ID (None for root)
            include_folders: Include subfolders
            include_files: Include files

        Returns:
            list[dict]: Folder contents
        """
        q_parts = ["trashed = false"]

        if folder_id:
            q_parts.append(f"'{folder_id}' in parents")
        else:
            q_parts.append("'root' in parents")

        if not include_folders:
            q_parts.append(f"mimeType != '{self.MIME_TYPES['folder']}'")
        if not include_files:
            q_parts.append(f"mimeType = '{self.MIME_TYPES['folder']}'")

        return self.list_files(query=" and ".join(q_parts))

    def get_folder_path(self, file_id: str) -> str:
        """Get full path of a file/folder.

        Args:
            file_id: File or folder ID

        Returns:
            str: Full path (e.g., "/Folder1/Folder2/file.txt")
        """
        path_parts = []
        current_id = file_id

        while current_id:
            file_info = self.get_file(current_id, fields="id, name, parents")
            path_parts.insert(0, file_info.get("name", ""))

            parents = file_info.get("parents", [])
            current_id = parents[0] if parents else None

        return "/" + "/".join(path_parts)

    # ===================
    # Permissions
    # Reference: https://developers.google.com/workspace/drive/api/reference/rest/v3/permissions
    # ===================

    def share_file(
        self,
        file_id: str,
        email: str,
        role: str = "reader",
        send_notification: bool = False,
        message: str | None = None,
    ) -> str:
        """Share a file with a user.

        API: POST /drive/v3/files/{fileId}/permissions

        Args:
            file_id: File ID
            email: Email address to share with
            role: Permission role (reader, writer, commenter, owner)
            send_notification: Send email notification
            message: Custom message for notification

        Returns:
            str: Permission ID
        """
        logger.info(f"Sharing file {file_id} with {email} as {role}")

        params = {
            "sendNotificationEmail": str(send_notification).lower(),
        }
        if message:
            params["emailMessage"] = message

        body = {
            "type": "user",
            "role": role,
            "emailAddress": email,
        }

        response = requests.post(
            f"{self.DRIVE_API_BASE}/files/{file_id}/permissions",
            headers=self._get_json_headers(),
            params=params,
            json=body,
        )

        if not response.ok:
            raise GoogleDriveError(f"Failed to share file: {response.text}")

        permission_id = response.json()["id"]
        logger.info(f"✓ Shared file (permission: {permission_id})")
        return permission_id

    def share_file_with_anyone(
        self,
        file_id: str,
        role: str = "reader",
    ) -> str:
        """Make a file accessible to anyone with the link.

        Args:
            file_id: File ID
            role: Permission role (reader or writer)

        Returns:
            str: Permission ID
        """
        logger.info(f"Making file {file_id} accessible to anyone")

        body = {
            "type": "anyone",
            "role": role,
        }

        response = requests.post(
            f"{self.DRIVE_API_BASE}/files/{file_id}/permissions",
            headers=self._get_json_headers(),
            json=body,
        )

        if not response.ok:
            raise GoogleDriveError(f"Failed to share file: {response.text}")

        permission_id = response.json()["id"]
        logger.info(f"✓ File is now public (permission: {permission_id})")
        return permission_id

    def share_file_with_domain(
        self,
        file_id: str,
        domain: str,
        role: str = "reader",
    ) -> str:
        """Share a file with everyone in a domain.

        Args:
            file_id: File ID
            domain: Domain name (e.g., "example.com")
            role: Permission role

        Returns:
            str: Permission ID
        """
        logger.info(f"Sharing file {file_id} with domain {domain}")

        body = {
            "type": "domain",
            "role": role,
            "domain": domain,
        }

        response = requests.post(
            f"{self.DRIVE_API_BASE}/files/{file_id}/permissions",
            headers=self._get_json_headers(),
            json=body,
        )

        if not response.ok:
            raise GoogleDriveError(f"Failed to share file: {response.text}")

        permission_id = response.json()["id"]
        logger.info(f"✓ Shared with domain (permission: {permission_id})")
        return permission_id

    def list_permissions(self, file_id: str) -> list[dict]:
        """List all permissions on a file.

        API: GET /drive/v3/files/{fileId}/permissions

        Args:
            file_id: File ID

        Returns:
            list[dict]: List of permissions
        """
        response = requests.get(
            f"{self.DRIVE_API_BASE}/files/{file_id}/permissions",
            headers=self._get_headers(),
            params={"fields": "permissions(id, type, role, emailAddress, domain)"},
        )

        if not response.ok:
            raise GoogleDriveError(f"Failed to list permissions: {response.text}")

        return response.json().get("permissions", [])

    def update_permission(
        self,
        file_id: str,
        permission_id: str,
        role: str,
    ) -> None:
        """Update a permission's role.

        API: PATCH /drive/v3/files/{fileId}/permissions/{permissionId}

        Args:
            file_id: File ID
            permission_id: Permission ID
            role: New role
        """
        logger.info(f"Updating permission {permission_id} to role {role}")

        response = requests.patch(
            f"{self.DRIVE_API_BASE}/files/{file_id}/permissions/{permission_id}",
            headers=self._get_json_headers(),
            json={"role": role},
        )

        if not response.ok:
            raise GoogleDriveError(f"Failed to update permission: {response.text}")

        logger.info("✓ Updated permission")

    def delete_permission(self, file_id: str, permission_id: str) -> None:
        """Remove a permission from a file.

        API: DELETE /drive/v3/files/{fileId}/permissions/{permissionId}

        Args:
            file_id: File ID
            permission_id: Permission ID to remove
        """
        logger.info(f"Deleting permission {permission_id}")

        response = requests.delete(
            f"{self.DRIVE_API_BASE}/files/{file_id}/permissions/{permission_id}",
            headers=self._get_headers(),
        )

        if not response.ok:
            raise GoogleDriveError(f"Failed to delete permission: {response.text}")

        logger.info("✓ Deleted permission")

    # ===================
    # Utility Methods
    # ===================

    def get_storage_quota(self) -> dict:
        """Get storage quota information.

        API: GET /drive/v3/about

        Returns:
            dict: Storage quota info (limit, usage, etc.)
        """
        response = requests.get(
            f"{self.DRIVE_API_BASE}/about",
            headers=self._get_headers(),
            params={"fields": "storageQuota"},
        )

        if not response.ok:
            raise GoogleDriveError(f"Failed to get quota: {response.text}")

        return response.json().get("storageQuota", {})

    def get_file_link(self, file_id: str) -> str:
        """Get the web view link for a file.

        Args:
            file_id: File ID

        Returns:
            str: Web view URL
        """
        file_info = self.get_file(file_id, fields="webViewLink")
        return file_info.get("webViewLink", f"https://drive.google.com/file/d/{file_id}/view")

    def move_file(
        self,
        file_id: str,
        new_parent_id: str,
        old_parent_id: str | None = None,
    ) -> None:
        """Move a file to a different folder.

        Args:
            file_id: File ID
            new_parent_id: New parent folder ID
            old_parent_id: Old parent folder ID (auto-detected if not provided)
        """
        logger.info(f"Moving file {file_id} to folder {new_parent_id}")

        if old_parent_id is None:
            file_info = self.get_file(file_id, fields="parents")
            parents = file_info.get("parents", [])
            old_parent_id = parents[0] if parents else None

        self.update_file(
            file_id,
            add_parents=new_parent_id,
            remove_parents=old_parent_id,
        )

        logger.info(f"✓ Moved file to: {new_parent_id}")

    def rename_file(self, file_id: str, new_name: str) -> None:
        """Rename a file.

        Args:
            file_id: File ID
            new_name: New file name
        """
        logger.info(f"Renaming file {file_id} to '{new_name}'")
        self.update_file(file_id, name=new_name)
        logger.info(f"✓ Renamed file to: {new_name}")
