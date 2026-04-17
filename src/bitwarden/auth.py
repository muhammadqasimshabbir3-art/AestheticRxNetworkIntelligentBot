"""Bitwarden authentication module.

Handles login and session management for Bitwarden CLI.
"""

import json
import logging
import os
import subprocess
import time

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass


class BitwardenAuth:
    """Handles Bitwarden authentication and session management."""

    def __init__(self):
        """Initialize Bitwarden authentication."""
        self.bw_session: str | None = None
        self.is_authenticated = False

    def login_with_api_key(
        self,
        client_id: str | None = None,
        client_secret: str | None = None,
        master_password: str | None = None,
    ) -> bool:
        """Login to Bitwarden using API key (OAuth 2.0).

        Args:
            client_id: Bitwarden API client ID (or from env: BITWARDEN_CLIENT_ID, BW_CLIENT_ID)
            client_secret: Bitwarden API client secret (or from env: BITWARDEN_CLIENT_SECRET, BW_CLIENT_SECRET)
            master_password: Master password to unlock vault (or from env: BITWARDEN_PASSWORD, BW_PASSWORD)

        Returns:
            bool: True if login successful
        """
        # Get credentials from parameters or environment
        client_id = client_id or os.getenv("BITWARDEN_CLIENT_ID") or os.getenv("BW_CLIENT_ID")
        client_secret = (
            client_secret
            or os.getenv("BITWARDEN_CLIENT_SECRET")
            or os.getenv("BITWARDEN_CLIENT_SECRETE")  # Handle common typo
            or os.getenv("BW_CLIENT_SECRET")
        )
        master_password = (
            master_password
            or os.getenv("BITWARDEN_MASTER_PASSWORD")
            or os.getenv("BITWARDEN_PASSWORD")
            or os.getenv("BW_PASSWORD")
        )

        if not client_id or not client_secret:
            logging.error("Bitwarden API credentials not provided")
            return False

        try:
            # Check current status and logout if needed
            self._logout_if_needed()

            # Set environment variables for bw CLI
            env = os.environ.copy()
            env["BW_CLIENTID"] = client_id
            env["BW_CLIENTSECRET"] = client_secret

            # Login with API key
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
                self.is_authenticated = True
                logging.info("Bitwarden login successful with API key")
                return True

            # Try without --raw flag
            result = subprocess.run(
                ["bw", "login", "--apikey"],
                input=f"{client_id}\n{client_secret}\n",
                capture_output=True,
                text=True,
                env=env,
                check=False,
            )

            if result.returncode == 0:
                time.sleep(1)
                # Check if we need to unlock
                if master_password and self._unlock_vault(master_password):
                    self.is_authenticated = True
                    logging.info("Bitwarden login and unlock successful")
                    return True

            logging.error(f"Bitwarden API key login failed: {result.stderr}")
            return False

        except FileNotFoundError:
            logging.error("Bitwarden CLI not found. Install with: python scripts/install_bitwarden.py")
            return False
        except Exception as e:
            logging.error(f"Bitwarden login failed: {e}")
            return False

    def login_with_password(
        self,
        email: str | None = None,
        password: str | None = None,
    ) -> bool:
        """Login to Bitwarden using email and master password.

        Args:
            email: Bitwarden account email (or from env: BITWARDEN_EMAIL, BW_EMAIL)
            password: Master password (or from env: BITWARDEN_PASSWORD, BW_PASSWORD)

        Returns:
            bool: True if login successful
        """
        email = email or os.getenv("BITWARDEN_EMAIL") or os.getenv("BW_EMAIL")
        password = password or os.getenv("BITWARDEN_PASSWORD") or os.getenv("BW_PASSWORD")

        if not email or not password:
            logging.error("Bitwarden email/password not provided")
            return False

        try:
            self._logout_if_needed()

            result = subprocess.run(
                ["bw", "login", email, password, "--raw"],
                capture_output=True,
                text=True,
                check=False,
            )

            if result.returncode == 0 and result.stdout.strip():
                self.bw_session = result.stdout.strip()
                self.is_authenticated = True
                logging.info("Bitwarden login successful")
                return True

            logging.error(f"Bitwarden login failed: {result.stderr}")
            return False

        except FileNotFoundError:
            logging.error("Bitwarden CLI not found")
            return False
        except Exception as e:
            logging.error(f"Bitwarden login failed: {e}")
            return False

    def unlock(self, master_password: str | None = None) -> bool:
        """Unlock an already logged-in Bitwarden vault.

        Args:
            master_password: Master password (or from env: BITWARDEN_PASSWORD, BW_PASSWORD)

        Returns:
            bool: True if unlock successful
        """
        password = master_password or os.getenv("BITWARDEN_PASSWORD") or os.getenv("BW_PASSWORD")
        return self._unlock_vault(password)

    def _unlock_vault(self, password: str | None) -> bool:
        """Internal method to unlock the vault."""
        if not password:
            logging.error("Master password not provided for unlock")
            return False

        try:
            # First check status
            status = self.get_status()
            if status == "unlocked":
                logging.info("Vault already unlocked")
                return True

            if status == "unauthenticated":
                logging.error("Not logged in, cannot unlock")
                return False

            # Try unlock with password
            result = subprocess.run(
                ["bw", "unlock", "--raw"],
                input=f"{password}\n",
                capture_output=True,
                text=True,
                check=False,
            )

            if result.returncode == 0 and result.stdout.strip():
                self.bw_session = result.stdout.strip()
                logging.info("Vault unlocked successfully")
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
                logging.info("Vault unlocked successfully")
                return True

            logging.error(f"Failed to unlock vault: {result.stderr}")
            return False

        except Exception as e:
            logging.error(f"Unlock failed: {e}")
            return False

    def logout(self) -> bool:
        """Logout from Bitwarden."""
        try:
            subprocess.run(["bw", "logout"], capture_output=True, text=True, check=False)
            self.bw_session = None
            self.is_authenticated = False
            logging.info("Logged out from Bitwarden")
            return True
        except Exception as e:
            logging.error(f"Logout failed: {e}")
            return False

    def _logout_if_needed(self) -> None:
        """Logout if currently logged in."""
        status = self.get_status()
        if status in ["authenticated", "unlocked", "locked"]:
            logging.info("Logging out existing session")
            for _ in range(3):
                result = subprocess.run(["bw", "logout"], capture_output=True, text=True, check=False)
                if result.returncode == 0:
                    break
                time.sleep(0.3)
            time.sleep(0.5)

    def get_status(self) -> str:
        """Get current Bitwarden status.

        Returns:
            str: Status ('unauthenticated', 'locked', 'unlocked')
        """
        try:
            result = subprocess.run(["bw", "status"], capture_output=True, text=True, check=False)
            if result.returncode == 0:
                status_data = json.loads(result.stdout)
                return status_data.get("status", "unauthenticated")
        except Exception:
            pass
        return "unauthenticated"

    def get_session(self) -> str | None:
        """Get the current session token."""
        return self.bw_session


# Global auth instance
_bitwarden_auth: BitwardenAuth | None = None


def get_bitwarden_auth() -> BitwardenAuth:
    """Get the global Bitwarden auth instance."""
    global _bitwarden_auth
    if _bitwarden_auth is None:
        _bitwarden_auth = BitwardenAuth()
    return _bitwarden_auth
