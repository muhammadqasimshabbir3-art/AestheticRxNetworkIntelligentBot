"""Credential manager that reads credentials from environment variables."""

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


class CredentialManager:
    """Centralized credential manager that fetches credentials from environment variables."""

    def __init__(self):
        """Initialize the credential manager cache."""
        self.credentials = {}

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

        if item_name not in self.credentials:
            item_data = self._get_from_environment(item_name)
            if item_data:
                self.credentials[item_name] = item_data

        if item_name in self.credentials:
            login_data = self.credentials[item_name]
            if key:
                return login_data.get(key)
            return login_data

        # Fallback to environment variables
        return self._get_from_environment(item_name, key)

    def get_all_credentials(self) -> dict[str, dict]:
        """Get all cached credentials loaded from environment variables."""
        return self.credentials

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


def get_aestheticrxnetwork_credentials() -> dict[str, str]:
    """Get AestheticRxNetwork credentials from environment variables.

    Preferred names:
    - AESTHETIC_RX_NETWORK_EMAIL
    - AESTHETIC_RX_NETWORK_PASSWORD
    Compatibility names:
    - AESTHETICRXNETWORKLOGIN_EMAIL
    - AESTHETICRXNETWORKLOGIN_PASSWORD
    Or environment variables:
    - AESTHETIC_RX_NETWORK_EMAIL / AESTHETICRXNETWORKLOGIN_EMAIL
    - AESTHETIC_RX_NETWORK_PASSWORD / AESTHETICRXNETWORKLOGIN_PASSWORD

    Returns:
        dict: Credentials with 'email' and 'password' keys
    """
    # Read directly from environment variables.
    email = os.getenv("AESTHETIC_RX_NETWORK_EMAIL") or os.getenv("AESTHETICRXNETWORKLOGIN_EMAIL") or ""
    password = os.getenv("AESTHETIC_RX_NETWORK_PASSWORD") or os.getenv("AESTHETICRXNETWORKLOGIN_PASSWORD") or ""

    if not email or not password:
        raise ValueError(
            "AestheticRxNetwork credentials not found. "
            "Set AESTHETIC_RX_NETWORK_EMAIL and AESTHETIC_RX_NETWORK_PASSWORD environment variables."
        )

    return {"email": email, "password": password}


def get_gmail_credentials() -> dict[str, str] | None:
    """Get Gmail credentials for IMAP access from environment variables.

    Preferred names:
    - GMAIL_EMAIL
    - GMAIL_APP_PASSWORD
    Compatibility names:
    - GMAIL_USER
    - GMAIL_PASSWORD

    Returns:
        dict: Credentials with 'email' and 'app_password' keys, or None
    """
    email = os.getenv("GMAIL_EMAIL") or os.getenv("GMAIL_USER", "")
    app_password = (os.getenv("GMAIL_APP_PASSWORD") or os.getenv("GMAIL_PASSWORD", "")).replace(" ", "")

    if email and app_password:
        return {"email": email, "app_password": app_password}

    return None


def get_google_credentials() -> dict | None:
    """Get Google credentials from environment variables.

    Supported sources:
    - GOOGLE_SERVICE_ACCOUNT_JSON (full JSON string)
    - GOOGLE_SERVICE_ACCOUNT_EMAIL + GOOGLE_SERVICE_ACCOUNT_PRIVATE_KEY
    - GOOGLE_CREDENTIALS_FILE / GOOGLE_APPLICATION_CREDENTIALS (path to JSON)
    - GOOGLE_API_KEY (limited public access)

    Returns:
        dict: Service account credentials or None
    """
    import json

    # Full service account JSON as one secret.
    service_json = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
    if service_json:
        return {"service_account_json": service_json}

    # Service account as split secrets.
    client_email = os.getenv("GOOGLE_SERVICE_ACCOUNT_EMAIL", "")
    private_key = os.getenv("GOOGLE_SERVICE_ACCOUNT_PRIVATE_KEY", "")
    if client_email and private_key:
        project_id = os.getenv("GOOGLE_PROJECT_ID", "")
        service_account = {
            "type": "service_account",
            "client_email": client_email,
            "private_key": private_key,
            "project_id": project_id,
        }
        return {"service_account_json": json.dumps(service_account)}

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
