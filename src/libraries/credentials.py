"""Credential manager that integrates Bitwarden with environment variables."""

import os
from pathlib import Path

from dotenv import load_dotenv

# Load from .env file if it exists
project_root = Path(__file__).parent.parent.parent
env_file = project_root / ".env"
if env_file.exists():
    load_dotenv(env_file, override=False)
else:
    load_dotenv(override=False)

try:
    from bitwarden.credentials import BitwardenCredentialManagement
except ImportError:
    try:
        from src.bitwarden.credentials import BitwardenCredentialManagement
    except ImportError:
        BitwardenCredentialManagement = None


class CredentialManager:
    """Centralized credential manager that fetches credentials from Bitwarden or environment."""

    def __init__(self):
        """Initialize the credential manager."""
        self.bitwarden = None
        self.credentials = {}

        # Try to initialize Bitwarden if available
        if BitwardenCredentialManagement:
            try:
                self.bitwarden = BitwardenCredentialManagement()
            except Exception as e:
                print(f"Warning: Could not initialize Bitwarden: {e}")
                print("Continuing with environment variables...")

    def get_credential(self, item_name: str | None = None, key: str | None = None) -> dict | None:
        """Get a credential from Bitwarden or environment.

        Args:
            item_name: Name of the credential item. If None, returns all credentials.
            key: Optional specific key to return (e.g., 'username', 'password')

        Returns:
            Dict with credential data, or all credentials if item_name is None
        """
        # If no item_name provided, get all credentials
        if item_name is None:
            return self.get_all_credentials()

        # Try Bitwarden first
        if self.bitwarden and item_name not in self.credentials:
            item_data = self.bitwarden.get_credential(item_name)
            if item_data and isinstance(item_data, dict):
                if "login" in item_data:
                    self.credentials[item_name] = item_data.get("login", {})
                else:
                    self.credentials[item_name] = item_data

        if item_name in self.credentials:
            login_data = self.credentials[item_name]
            if key:
                return login_data.get(key)
            return login_data

        # Fallback to environment variables
        return self._get_from_environment(item_name, key)

    def get_all_credentials(self) -> dict[str, dict]:
        """Get all credentials from Bitwarden.

        Returns:
            Dict mapping item names to credential data
        """
        if self.bitwarden:
            all_creds = self.bitwarden.get_credential(None)
            if all_creds:
                return all_creds
        return {}

    def _get_from_environment(self, item_name: str, key: str | None = None) -> dict | None:
        """Get credentials from environment variables."""
        prefix = item_name.upper().replace(" ", "_").replace("-", "_")

        username = os.getenv(f"{prefix}_USERNAME") or os.getenv(f"{prefix}_EMAIL") or os.getenv(f"{prefix}_USER")
        password = os.getenv(f"{prefix}_PASSWORD") or os.getenv(f"{prefix}_PASS")

        if username or password:
            creds = {"username": username or "", "password": password or "", "email": username or ""}
            if key:
                return creds.get(key)
            return creds

        return None


# Global credential manager instance
_credential_manager = None


def get_credential_manager() -> CredentialManager:
    """Get the global credential manager instance."""
    global _credential_manager
    if _credential_manager is None:
        _credential_manager = CredentialManager()
    return _credential_manager


def get_qwebsite_credentials() -> dict[str, str]:
    """Get Q Website credentials from Bitwarden or environment.

    Bitwarden item name: "qwebsitelogin"
    Or environment variables:
    - QWEBSITE_EMAIL / QWEBSITELOGIN_EMAIL
    - QWEBSITE_PASSWORD / QWEBSITELOGIN_PASSWORD

    Returns:
        dict: Credentials with 'email' and 'password' keys
    """
    manager = get_credential_manager()

    # Try Bitwarden item name "qwebsitelogin"
    creds = manager.get_credential("qwebsitelogin")
    if creds:
        return {
            "email": creds.get("username") or creds.get("email") or "",
            "password": creds.get("password") or "",
        }

    # Fallback to direct environment variables
    email = os.getenv("QWEBSITE_EMAIL") or os.getenv("QWEBSITELOGIN_EMAIL", "")
    password = os.getenv("QWEBSITE_PASSWORD") or os.getenv("QWEBSITELOGIN_PASSWORD", "")

    if not email or not password:
        raise ValueError(
            "Q Website credentials not found. Either:\n"
            "1. Set up Bitwarden with an item named 'qwebsitelogin'\n"
            "2. Set QWEBSITE_EMAIL and QWEBSITE_PASSWORD environment variables"
        )

    return {"email": email, "password": password}


def get_gmail_credentials() -> dict[str, str] | None:
    """Get Gmail credentials for IMAP access.

    Bitwarden item names tried: "Gmail", "Google Credential", "gmail"
    Or environment variables:
    - GMAIL_EMAIL
    - GMAIL_APP_PASSWORD

    Returns:
        dict: Credentials with 'email' and 'app_password' keys, or None
    """
    manager = get_credential_manager()

    # Try various Bitwarden item names
    for item_name in ["Google Credential", "Gmail", "gmail", "google"]:
        creds = manager.get_credential(item_name)
        if creds:
            # Get email - check multiple possible field names
            email = creds.get("username") or creds.get("email") or creds.get("Email") or creds.get("Gmail") or ""

            # App password might be in custom field 'Gmail App Password' or standard 'password'
            app_password = (
                creds.get("Gmail App Password")
                or creds.get("gmail app password")
                or creds.get("app_password")
                or creds.get("App Password")
                or creds.get("password")
                or ""
            )

            # Remove spaces from app password (Google format: xxxx xxxx xxxx xxxx)
            app_password = app_password.replace(" ", "")

            if app_password:
                # If no email in Google Credential, use the Q Website email
                if not email:
                    try:
                        qw_creds = get_qwebsite_credentials()
                        email = qw_creds.get("email", "")
                    except Exception:
                        pass

                if email and app_password:
                    return {"email": email, "app_password": app_password}

    # Fallback to environment variables
    email = os.getenv("GMAIL_EMAIL", "")
    app_password = os.getenv("GMAIL_APP_PASSWORD", "").replace(" ", "")

    if email and app_password:
        return {"email": email, "app_password": app_password}

    return None


def get_google_credentials() -> dict | None:
    """Get Google service account credentials for API access.

    Bitwarden item names tried: "Google Service Account", "google-service-account", "GoogleDrive"
    The item should contain the service account JSON either as:
    - A custom field named 'service_account_json' containing the full JSON
    - The JSON fields directly (private_key, client_email, etc.)
    - Password field containing the full JSON or private key

    Or environment variables:
    - GOOGLE_SERVICE_ACCOUNT_JSON (full JSON string)
    - GOOGLE_CREDENTIALS_FILE (path to JSON file)
    - GOOGLE_API_KEY (for limited public access)

    Returns:
        dict: Service account credentials or None
    """
    import json

    manager = get_credential_manager()

    # Try various Bitwarden item names
    for item_name in [
        "google_service_account",
        "Google Service Account",
        "google-service-account",
        "GoogleDrive",
        "Google Drive",
        "google api key",
    ]:
        creds = manager.get_credential(item_name)
        if creds:
            # Check for service account JSON in various fields
            service_json = (
                creds.get("service_account_json")
                or creds.get("Service Account JSON")
                or creds.get("service_account")
                or creds.get("notes")  # Sometimes stored in notes field
                or creds.get("password")  # Might store JSON in password field
            )

            # Try to parse as JSON if it's a string
            if service_json and isinstance(service_json, str):
                # Check if it looks like JSON
                if service_json.strip().startswith("{"):
                    try:
                        parsed = json.loads(service_json)
                        if "private_key" in parsed:
                            return {"service_account_json": service_json}
                    except json.JSONDecodeError:
                        pass
                # Check if it's a private key directly
                elif "BEGIN PRIVATE KEY" in service_json:
                    client_email = creds.get("client_email") or creds.get("username") or creds.get("email") or ""
                    if client_email:
                        return {
                            "private_key": service_json,
                            "client_email": client_email,
                            "type": "service_account",
                        }

            # Check if fields are directly available
            private_key = creds.get("private_key") or creds.get("Private Key")
            client_email = (
                creds.get("client_email") or creds.get("Client Email") or creds.get("username") or creds.get("email")
            )

            if private_key and client_email:
                return {
                    "private_key": private_key,
                    "client_email": client_email,
                    "project_id": creds.get("project_id", ""),
                    "type": "service_account",
                }

            # Check for API key (limited functionality)
            api_key = (
                creds.get("api_key") or creds.get("API Key") or creds.get("password")  # Might store API key in password
            )
            if api_key and not api_key.strip().startswith("{"):
                return {
                    "api_key": api_key,
                    "client_email": client_email or creds.get("username", ""),
                    "type": "api_key",
                }

    # Fallback to environment variables
    service_json = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
    if service_json:
        return {"service_account_json": service_json}

    # Check for file path
    creds_file = os.getenv("GOOGLE_CREDENTIALS_FILE") or os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if creds_file and Path(creds_file).exists():
        with open(creds_file) as f:
            return {"service_account_json": f.read()}

    # Check for API key
    api_key = os.getenv("GOOGLE_API_KEY")
    if api_key:
        return {"api_key": api_key, "type": "api_key"}

    return None


def get_credentials(item_name: str | None = None) -> dict:
    """Get credentials by name or all credentials if no name given.

    Args:
        item_name: Name of the Bitwarden item. If None, returns all credentials.

    Returns:
        Dict with credential(s)
    """
    manager = get_credential_manager()
    return manager.get_credential(item_name)
