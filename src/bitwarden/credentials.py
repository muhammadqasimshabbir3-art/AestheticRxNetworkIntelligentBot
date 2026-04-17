"""Bitwarden credential retrieval module.

Handles fetching credentials from Bitwarden vault.
"""

import json
import logging
import os
import subprocess

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass


class BitwardenCredentialManagement:
    """Manage credentials from Bitwarden vault."""

    def __init__(self, auto_login: bool = True):
        """Initialize Bitwarden credential management.

        Args:
            auto_login: If True, automatically attempt to login/unlock
        """
        self.bw_session: str | None = None
        self.is_robocorp = self._detect_robocorp_environment()

        if auto_login and not self.is_robocorp:
            self._auto_authenticate()

    def _detect_robocorp_environment(self) -> bool:
        """Detect if running in Robocorp environment."""
        return (
            os.getenv("RPA_SECRET_MANAGER") == "Robocorp.Vault.FileSecrets"
            or os.getenv("RC_ENVIRONMENT") is not None
            or os.path.exists("/tmp/robocorp-temp")
        )

    def _auto_authenticate(self) -> bool:
        """Automatically authenticate using available credentials."""
        # First check if already unlocked
        status = self._get_status()
        if status == "unlocked":
            self.bw_session = self._get_session_from_status()
            if self.bw_session:
                logging.info("Bitwarden already unlocked")
                return True

        # Try API key login
        client_id = os.getenv("BITWARDEN_CLIENT_ID") or os.getenv("BW_CLIENT_ID")
        client_secret = (
            os.getenv("BITWARDEN_CLIENT_SECRET")
            or os.getenv("BITWARDEN_CLIENT_SECRETE")  # Handle common typo
            or os.getenv("BW_CLIENT_SECRET")
        )

        if client_id and client_secret and self._login_with_api_key(client_id, client_secret):
            return True

        # Try password unlock if already logged in
        if status == "locked":
            password = (
                os.getenv("BITWARDEN_MASTER_PASSWORD") or os.getenv("BITWARDEN_PASSWORD") or os.getenv("BW_PASSWORD")
            )
            if password and self._unlock_vault(password):
                return True

        return False

    def _get_status(self) -> str:
        """Get Bitwarden status."""
        try:
            result = subprocess.run(["bw", "status"], capture_output=True, text=True, check=False)
            if result.returncode == 0:
                status_data = json.loads(result.stdout)
                return status_data.get("status", "unauthenticated")
        except Exception:
            pass
        return "unauthenticated"

    def _get_session_from_status(self) -> str | None:
        """Get session token from status."""
        try:
            result = subprocess.run(["bw", "status"], capture_output=True, text=True, check=False)
            if result.returncode == 0:
                status_data = json.loads(result.stdout)
                return status_data.get("session")
        except Exception:
            pass
        return None

    def _login_with_api_key(self, client_id: str, client_secret: str) -> bool:
        """Login with API key."""
        try:
            import time

            # Logout first if needed
            status = self._get_status()
            if status in ["authenticated", "unlocked", "locked"]:
                subprocess.run(["bw", "logout"], capture_output=True, text=True, check=False)
                time.sleep(0.5)

            env = os.environ.copy()
            env["BW_CLIENTID"] = client_id
            env["BW_CLIENTSECRET"] = client_secret

            result = subprocess.run(
                ["bw", "login", "--apikey", "--raw"],
                input=f"{client_id}\n{client_secret}\n",
                capture_output=True,
                text=True,
                env=env,
                check=False,
            )

            if result.returncode == 0 and result.stdout.strip():
                self.bw_session = result.stdout.strip()
                logging.info("Bitwarden API key login successful")
                return True

            # Try unlocking after login
            password = (
                os.getenv("BITWARDEN_MASTER_PASSWORD") or os.getenv("BITWARDEN_PASSWORD") or os.getenv("BW_PASSWORD")
            )
            if password:
                return self._unlock_vault(password)

            return False
        except Exception as e:
            logging.warning(f"API key login failed: {e}")
            return False

    def _unlock_vault(self, password: str) -> bool:
        """Unlock the vault with master password."""
        try:
            result = subprocess.run(
                ["bw", "unlock", "--raw"],
                input=f"{password}\n",
                capture_output=True,
                text=True,
                check=False,
            )

            if result.returncode == 0 and result.stdout.strip():
                self.bw_session = result.stdout.strip()
                logging.info("Bitwarden vault unlocked")
                return True

            # Try with passwordenv
            os.environ["BITWARDEN_PASSWORD"] = password
            result = subprocess.run(
                ["bw", "unlock", "--passwordenv", "BITWARDEN_PASSWORD", "--raw"],
                capture_output=True,
                text=True,
                check=False,
            )

            if result.returncode == 0 and result.stdout.strip():
                self.bw_session = result.stdout.strip()
                logging.info("Bitwarden vault unlocked")
                return True

            return False
        except Exception as e:
            logging.warning(f"Vault unlock failed: {e}")
            return False

    def get_credential(self, item_name: str | None = None) -> dict | None:
        """Get a credential by name from Bitwarden.

        Args:
            item_name: Name of the credential item. If None, returns all items.

        Returns:
            Dict with credential data or None if not found
        """
        if not self.bw_session:
            logging.error("Bitwarden not unlocked")
            return self._get_from_environment(item_name) if item_name else None

        try:
            if item_name is None:
                # Get all items
                result = subprocess.run(
                    ["bw", "list", "items", "--session", self.bw_session],
                    capture_output=True,
                    text=True,
                    check=True,
                )
                items = json.loads(result.stdout)
                all_credentials = {}

                for item in items:
                    name = item.get("name", f"item_{item.get('id', 'unknown')}")
                    all_credentials[name] = self._extract_credential(item)

                return all_credentials

            # Search for specific item
            result = subprocess.run(
                ["bw", "list", "items", "--search", item_name, "--session", self.bw_session],
                capture_output=True,
                text=True,
                check=True,
            )
            items = json.loads(result.stdout)

            if not items:
                logging.warning(f"Item '{item_name}' not found in Bitwarden")
                return self._get_from_environment(item_name)

            return self._extract_credential(items[0])

        except subprocess.CalledProcessError as e:
            logging.error(f"Error retrieving from Bitwarden: {e.stderr}")
            return self._get_from_environment(item_name) if item_name else None
        except json.JSONDecodeError as e:
            logging.error(f"Error parsing Bitwarden response: {e}")
            return self._get_from_environment(item_name) if item_name else None

    def _extract_credential(self, item: dict) -> dict:
        """Extract credential data from a Bitwarden item."""
        credential = {}

        # Extract login credentials
        if "login" in item:
            login = item["login"]
            credential["username"] = login.get("username", "")
            credential["password"] = login.get("password", "")
            credential["email"] = login.get("username", "")  # Often email is stored as username

        # Extract custom fields
        if "fields" in item:
            for field in item["fields"]:
                field_name = field.get("name", "")
                if field_name:
                    credential[field_name] = field.get("value", "")

        # Extract notes
        if item.get("notes"):
            credential["notes"] = item["notes"]

        return credential

    def _get_from_environment(self, item_name: str) -> dict | None:
        """Fallback to get credentials from environment variables."""
        prefix = item_name.upper().replace(" ", "_").replace("-", "_")

        username = os.getenv(f"{prefix}_USERNAME") or os.getenv(f"{prefix}_EMAIL") or os.getenv(f"{prefix}_USER")
        password = os.getenv(f"{prefix}_PASSWORD") or os.getenv(f"{prefix}_PASS")

        if username or password:
            logging.info(f"Retrieved {item_name} from environment variables")
            return {
                "username": username or "",
                "password": password or "",
                "email": username or "",
            }

        return None

    def get_credentials(self, item_names: list[str]) -> dict[str, dict]:
        """Get multiple credentials by name.

        Args:
            item_names: List of credential item names

        Returns:
            Dict mapping item names to credential data
        """
        credentials = {}
        for name in item_names:
            cred = self.get_credential(name)
            if cred:
                credentials[name] = cred
            else:
                logging.warning(f"Could not retrieve credential: {name}")
        return credentials


# Global instance
_credential_manager: BitwardenCredentialManagement | None = None


def get_bitwarden_credentials() -> BitwardenCredentialManagement:
    """Get the global Bitwarden credential manager."""
    global _credential_manager
    if _credential_manager is None:
        _credential_manager = BitwardenCredentialManagement()
    return _credential_manager
