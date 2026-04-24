"""AestheticRxNetwork API module.

All classes are structured hierarchically with AestheticRxNetworkAPI as the final class.
Only AestheticRxNetworkAPI should be used externally.

Hierarchy:
    _AestheticRxNetworkConfig     → Configuration settings
    _AestheticRxNetworkAuth       → Authentication logic (inherits Config)
    AestheticRxNetworkAPI         → Final API client (inherits Auth) ← USE THIS
"""

import os
from collections.abc import Callable

try:
    from datetime import UTC, datetime
except ImportError:  # Python < 3.11
    from datetime import datetime

    UTC = UTC
from typing import Any

import requests
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from .credentials import get_aestheticrxnetwork_credentials, get_gmail_credentials
from .logger import logger


class _AestheticRxNetworkConfig(BaseSettings):
    """Configuration for AestheticRxNetwork API.

    Internal class - inherited by _AestheticRxNetworkAuth.
    """

    model_config = SettingsConfigDict(
        env_prefix="AESTHETIC_RX_NETWORK_",
        case_sensitive=False,
        extra="ignore",
    )

    BASE_URL: str = Field(
        default_factory=lambda: os.getenv("API_BASE_URL", "https://aestheticrxnetwork-production.up.railway.app")
    )
    FRONTEND_URL: str = Field(default="https://aestheticrxnetwork.vercel.app")
    LOGIN_ENDPOINT: str = Field(default="/api/auth/login")
    ORDER_MANAGEMENT_ENDPOINT: str = Field(default="/api/order-management")
    ADMIN_USERS_ENDPOINT: str = Field(default="/api/admin/users")
    REQUEST_TIMEOUT: int = Field(default=30)

    @property
    def login_url(self) -> str:
        return f"{self.BASE_URL}{self.LOGIN_ENDPOINT}"

    @property
    def order_management_url(self) -> str:
        return f"{self.BASE_URL}{self.ORDER_MANAGEMENT_ENDPOINT}"

    @property
    def admin_users_url(self) -> str:
        return f"{self.BASE_URL}{self.ADMIN_USERS_ENDPOINT}"

    def get_endpoint_url(self, endpoint: str) -> str:
        if endpoint.startswith("/"):
            return f"{self.BASE_URL}{endpoint}"
        return f"{self.BASE_URL}/{endpoint}"

    def get_headers(self, token: str | None = None) -> dict[str, str]:
        headers = {
            "Accept": "application/json, text/plain, */*",
            "Content-Type": "application/json",
            "Origin": self.FRONTEND_URL,
            "Referer": f"{self.FRONTEND_URL}/",
        }
        if token:
            headers["Authorization"] = f"Bearer {token}"
        return headers


class _AestheticRxNetworkAuth:
    """Authentication handler for AestheticRxNetwork API.

    Internal class - inherited by AestheticRxNetworkAPI.
    Handles:
    - Credential retrieval from Bitwarden
    - Gmail verification for OTP
    - Login and OTP verification
    """

    def __init__(self) -> None:
        """Initialize authentication handler."""
        # Configuration
        self._config = _AestheticRxNetworkConfig()

        # Auth state
        self._token: str | None = None
        self._user_data: dict | None = None
        self._pending_email: str | None = None
        self._pending_password: str | None = None

        # Credentials (from Bitwarden)
        self._credentials: dict | None = None
        self._gmail_creds: dict | None = None
        self._gmail_verified: bool = False

        # Timestamp for OTP email filtering
        self._login_timestamp: datetime | None = None

        # OTP callback (can be set externally)
        self._otp_callback: Callable[[], str | None] | None = None

    def _load_credentials_from_environment(self) -> None:
        """Load AestheticRxNetwork and Gmail credentials from environment."""
        logger.info("Loading credentials from environment variables...")

        self._credentials = get_aestheticrxnetwork_credentials()
        logger.info(f"✓ Got AestheticRxNetwork credentials for: {self._credentials['email']}")

        self._gmail_creds = get_gmail_credentials()
        if self._gmail_creds:
            logger.info(f"✓ Got Gmail credentials for: {self._gmail_creds['email']}")
        else:
            logger.warning("⚠ Gmail credentials not available")

    def _verify_gmail_connection(self) -> None:
        """Verify Gmail IMAP connection for OTP retrieval."""
        if not self._gmail_creds:
            self._gmail_verified = False
            return

        from email_reader import GmailReader

        logger.info("Verifying Gmail IMAP connection...")
        gmail_reader = GmailReader(
            email_address=self._gmail_creds["email"], app_password=self._gmail_creds["app_password"]
        )

        if gmail_reader.connect():
            logger.info("✓ Gmail IMAP connection verified")
            gmail_reader.disconnect()
            self._gmail_verified = True
        else:
            logger.error("✗ Failed to connect to Gmail")
            self._gmail_verified = False

    def _login(self, email: str, password: str) -> dict:
        """Login to AestheticRxNetwork API.

        Returns:
            dict: {"otp_required": True} or {"success": True}
        """
        logger.info(f"Logging in as {email}...")

        headers = self._config.get_headers()
        payload = {"email": email, "password": password}

        response = requests.post(
            self._config.login_url,
            json=payload,
            headers=headers,
            timeout=self._config.REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        data = response.json()

        # Check if OTP required
        if data.get("data", {}).get("otpRequired"):
            self._pending_email = email
            self._pending_password = password
            return {"otp_required": True}

        # Extract token
        token = self._extract_token(data)
        if token:
            self._token = token
            self._user_data = data.get("data", {}).get("user", data)
            return {"success": True}

        raise ValueError(f"Login failed: {data}")

    def _verify_otp(self, otp: str) -> None:
        """Verify OTP code to complete authentication."""
        if not self._pending_email or not self._pending_password:
            raise ValueError("No pending OTP verification")

        logger.info(f"Verifying OTP: {otp}...")

        headers = self._config.get_headers()
        payload = {
            "email": self._pending_email,
            "password": self._pending_password,
            "otpCode": otp,
        }

        response = requests.post(
            self._config.login_url,
            json=payload,
            headers=headers,
            timeout=self._config.REQUEST_TIMEOUT,
        )

        try:
            data = response.json()
        except Exception:
            data = {"raw_text": response.text}

        if not response.ok:
            logger.error(f"OTP verification failed: {data}")
            raise ValueError(f"OTP failed: {data.get('message', response.text)}")

        token = self._extract_token(data)
        if not token:
            raise ValueError(f"No token in response: {data}")

        self._token = token
        self._user_data = data.get("data", {}).get("user", data)
        self._pending_email = None
        self._pending_password = None

    def _extract_token(self, data: dict) -> str | None:
        """Extract token from API response."""
        if "data" in data:
            return data["data"].get("accessToken") or data["data"].get("token")
        return data.get("accessToken") or data.get("token")

    def _get_otp(self) -> str | None:
        """Get OTP code from various sources.

        Priority:
        1. Environment variable (AESTHETIC_RX_NETWORK_OTP)
        2. Custom callback function
        3. Gmail inbox
        4. Manual input
        """
        # Option 1: Environment variable
        otp = os.getenv("AESTHETIC_RX_NETWORK_OTP")
        if otp:
            logger.info("Using OTP from environment variable")
            return otp.strip()

        # Option 2: Custom callback
        if self._otp_callback:
            otp = self._otp_callback()
            if otp:
                return otp

        # Option 3: Gmail
        if self._gmail_creds and self._gmail_verified and self._login_timestamp:
            otp = self._get_otp_from_gmail()
            if otp:
                return otp

        # Option 4: Manual input
        logger.info("Please enter the OTP code manually:")
        try:
            otp = input("OTP: ").strip()
            return otp if otp else None
        except EOFError:
            logger.error("Cannot read OTP (non-interactive mode)")
            return None

    def _get_otp_from_gmail(self) -> str | None:
        """Fetch OTP from Gmail inbox."""
        from email_reader import get_otp_from_gmail

        try:
            logger.info("Fetching OTP from Gmail...")
            logger.info(f"Looking for emails after {self._login_timestamp.strftime('%H:%M:%S')} UTC")
            return get_otp_from_gmail(
                email_address=self._gmail_creds["email"],
                app_password=self._gmail_creds["app_password"],
                received_after=self._login_timestamp,
                sender_filter="aestheticrxnetwork",
                timeout_seconds=120,
                initial_delay=20,
            )
        except Exception as e:
            logger.warning(f"Could not fetch OTP from Gmail: {e}")
            return None

    def _authenticate(self) -> None:
        """Full authentication flow: login + OTP if needed."""
        if not self._credentials:
            raise ValueError("No credentials available. Call _load_credentials_from_environment() first.")

        # Record timestamp for OTP email filtering
        self._login_timestamp = datetime.now(UTC)
        logger.info(f"📍 Timestamp: {self._login_timestamp.strftime('%Y-%m-%d %H:%M:%S')} UTC")

        # Login
        result = self._login(self._credentials["email"], self._credentials["password"])

        # Handle OTP if required
        if result.get("otp_required"):
            logger.info("=" * 50)
            logger.info("OTP VERIFICATION REQUIRED")
            logger.info("=" * 50)

            otp = self._get_otp()
            if otp:
                self._verify_otp(otp)
                logger.info("✓ OTP verification successful!")
            else:
                raise ValueError("Could not obtain OTP code")

        logger.info("✓ Authentication successful!")

    @property
    def is_authenticated(self) -> bool:
        """Check if authenticated."""
        return self._token is not None

    @property
    def token(self) -> str | None:
        """Get authentication token."""
        return self._token

    @property
    def user_data(self) -> dict | None:
        """Get user data."""
        return self._user_data


class AestheticRxNetworkAPI(_AestheticRxNetworkAuth):
    """AestheticRxNetwork API client.

    This is the ONLY class that should be used externally.

    Inherits from:
    - _AestheticRxNetworkAuth (authentication) → _AestheticRxNetworkConfig (configuration)

    Usage:
        api = AestheticRxNetworkAPI()  # Auto-authenticates
        orders = api.get_orders()
    """

    def __init__(
        self,
        auto_authenticate: bool = True,
        otp_callback: Callable[[], str | None] | None = None,
    ) -> None:
        """Initialize AestheticRxNetwork API client.

        Args:
            auto_authenticate: If True, authenticate during initialization.
            otp_callback: Optional function to get OTP code.
        """
        # Initialize parent (auth handler)
        super().__init__()

        logger.info("=" * 50)
        logger.info("Initializing AestheticRxNetworkAPI")
        logger.info("=" * 50)

        # Set OTP callback if provided
        if otp_callback:
            self._otp_callback = otp_callback

        # Load credentials from environment variables
        self._load_credentials_from_environment()

        # Verify Gmail connection
        self._verify_gmail_connection()

        # Authenticate if requested
        if auto_authenticate:
            self._authenticate()

        logger.info("=" * 50)
        logger.info("AestheticRxNetworkAPI ready")
        logger.info("=" * 50)

    # ===================
    # HTTP Methods
    # ===================

    def _request(
        self,
        method: str,
        endpoint: str,
        params: dict | None = None,
        json_data: dict | None = None,
        **kwargs: Any,
    ) -> requests.Response:
        """Make an authenticated HTTP request."""
        if not self._token:
            raise RuntimeError("Not authenticated")

        url = self._config.get_endpoint_url(endpoint)
        headers = self._config.get_headers(self._token)

        logger.info(f"Making {method} request to {url}")

        response = requests.request(
            method=method,
            url=url,
            headers=headers,
            params=params,
            json=json_data,
            timeout=self._config.REQUEST_TIMEOUT,
            **kwargs,
        )
        response.raise_for_status()
        return response

    def get(self, endpoint: str, params: dict | None = None, **kwargs: Any) -> requests.Response:
        """Make a GET request."""
        return self._request("GET", endpoint, params=params, **kwargs)

    def post(self, endpoint: str, json_data: dict | None = None, **kwargs: Any) -> requests.Response:
        """Make a POST request."""
        return self._request("POST", endpoint, json_data=json_data, **kwargs)

    def put(self, endpoint: str, json_data: dict | None = None, **kwargs: Any) -> requests.Response:
        """Make a PUT request."""
        return self._request("PUT", endpoint, json_data=json_data, **kwargs)

    def delete(self, endpoint: str, **kwargs: Any) -> requests.Response:
        """Make a DELETE request."""
        return self._request("DELETE", endpoint, **kwargs)

    # ===================
    # Business API Methods
    # ===================

    def get_orders(self) -> list[dict]:
        """Get all orders from order management."""
        response = self.get(self._config.ORDER_MANAGEMENT_ENDPOINT)
        data = response.json()
        if isinstance(data, dict) and "data" in data:
            return data["data"]
        return data

    def get_order_by_id(self, order_id: str) -> dict:
        """Get a specific order by ID."""
        endpoint = f"{self._config.ORDER_MANAGEMENT_ENDPOINT}/{order_id}"
        response = self.get(endpoint)
        return response.json()

    def update_order_status(
        self,
        order_id: str,
        payment_status: str = "completed",
        payment_amount: str = "",
        notes: str = "Status updated via automation",
    ) -> dict:
        """Update order payment status via API.

        API: PUT /api/order-management/{order_id}/status

        Args:
            order_id: The order ID (UUID)
            payment_status: New payment status (e.g., "completed", "pending")
            payment_amount: Payment amount as string
            notes: Notes for the status change

        Returns:
            dict: API response
        """
        endpoint = f"{self._config.ORDER_MANAGEMENT_ENDPOINT}/{order_id}/status"

        payload = {
            "paymentStatus": payment_status,
            "paymentAmount": payment_amount,
            "notes": notes,
        }

        logger.info(f"Updating order {order_id} status to '{payment_status}'...")

        response = self.put(endpoint, json_data=payload)
        data = response.json()

        logger.info(f"✓ Order {order_id} status updated successfully")
        return data

    # ===================
    # User Management API Methods
    # ===================

    def get_users(self) -> list[dict]:
        """Get all users from admin users endpoint.

        API: GET /api/admin/users

        Returns:
            list[dict]: List of user objects
        """
        logger.info("Fetching users from API...")

        try:
            response = self.get(self._config.ADMIN_USERS_ENDPOINT)
            data = response.json()

            # Handle different response formats
            if isinstance(data, dict):
                if "data" in data:
                    users = data["data"]
                elif "users" in data:
                    users = data["users"]
                else:
                    users = [data]
            elif isinstance(data, list):
                users = data
            else:
                users = []

            logger.info(f"✓ Fetched {len(users)} users from API")
            return users

        except Exception as e:
            logger.error(f"✗ Failed to fetch users: {e}")
            return []

    def get_user_by_id(self, user_id: str) -> dict:
        """Get a specific user by ID.

        API: GET /api/admin/users/{user_id}

        Args:
            user_id: The user ID (UUID)

        Returns:
            dict: User object
        """
        endpoint = f"{self._config.ADMIN_USERS_ENDPOINT}/{user_id}"
        response = self.get(endpoint)
        return response.json()

    def approve_user(self, user_id: str) -> dict:
        """Approve a user via API.

        API: POST /api/admin/users/{user_id}/approve

        Args:
            user_id: The user ID (UUID) to approve

        Returns:
            dict: API response with success status and message
                  {"success": True, "message": "User approved successfully"}
        """
        endpoint = f"{self._config.ADMIN_USERS_ENDPOINT}/{user_id}/approve"

        logger.info(f"Approving user {user_id}...")

        try:
            response = self.post(endpoint)
            data = response.json()

            if data.get("success"):
                logger.info(f"✓ User {user_id} approved successfully")
            else:
                logger.warning(f"⚠ User approval response: {data}")

            return data

        except Exception as e:
            logger.error(f"✗ Failed to approve user {user_id}: {e}")
            return {"success": False, "message": str(e)}

    def get_unapproved_users(self) -> list[dict]:
        """Get all users that are not yet approved.

        Returns:
            list[dict]: List of unapproved user objects
        """
        users = self.get_users()

        # Filter for unapproved users
        unapproved = []
        for user in users:
            # Check various possible field names for approval status
            is_approved = user.get("isApproved") or user.get("is_approved") or user.get("approved") or False
            # Convert string 'false' to boolean
            if isinstance(is_approved, str):
                is_approved = is_approved.lower() == "true"

            if not is_approved:
                unapproved.append(user)

        logger.info(f"Found {len(unapproved)} unapproved users out of {len(users)} total")
        return unapproved

    # ===================
    # Signup ID Management API Methods
    # ===================

    def get_signup_ids(self) -> list[dict]:
        """Get all signup IDs from admin endpoint.

        API: GET /api/admin/signup-ids

        Returns:
            list[dict]: List of signup ID objects with fields:
                - id: UUID
                - signup_id: String ID code
                - is_used: Boolean
                - used_by_email: Email of user who used it (null if unused)
                - used_at: Timestamp when used (null if unused)
                - notes: Optional notes
                - created_at: Creation timestamp
        """
        logger.info("Fetching signup IDs from API...")

        try:
            response = self.get("/api/admin/signup-ids")
            data = response.json()

            # Handle different response formats
            if isinstance(data, dict):
                if "data" in data:
                    signup_ids = data["data"]
                else:
                    signup_ids = [data]
            elif isinstance(data, list):
                signup_ids = data
            else:
                signup_ids = []

            logger.info(f"✓ Fetched {len(signup_ids)} signup IDs from API")
            return signup_ids

        except Exception as e:
            logger.error(f"✗ Failed to fetch signup IDs: {e}")
            return []

    # ===================
    # Advertisement Management API Methods
    # ===================

    def get_advertisements(self) -> list[dict]:
        """Get all advertisements from admin endpoint.

        API: GET /api/video-advertisements/admin/all

        Returns:
            list[dict]: List of advertisement objects
        """
        logger.info("Fetching advertisements from API...")

        try:
            response = self.get("/api/video-advertisements/admin/all")
            data = response.json()

            # Handle different response formats
            if isinstance(data, dict):
                if "data" in data and "advertisements" in data["data"]:
                    advertisements = data["data"]["advertisements"]
                elif "data" in data:
                    advertisements = data["data"]
                elif "advertisements" in data:
                    advertisements = data["advertisements"]
                else:
                    advertisements = [data]
            elif isinstance(data, list):
                advertisements = data
            else:
                advertisements = []

            logger.info(f"✓ Fetched {len(advertisements)} advertisements from API")
            return advertisements

        except Exception as e:
            logger.error(f"✗ Failed to fetch advertisements: {e}")
            return []

    def approve_advertisement(self, advertisement_id: str) -> dict:
        """Approve an advertisement via API.

        API: PUT /api/video-advertisements/admin/{advertisement_id}/approve

        Args:
            advertisement_id: The advertisement ID (UUID) to approve

        Returns:
            dict: API response with success status and message
        """
        endpoint = f"/api/video-advertisements/admin/{advertisement_id}/approve"

        logger.info(f"Approving advertisement {advertisement_id}...")

        try:
            response = self.put(endpoint)
            data = response.json()

            if data.get("success"):
                logger.info(f"✓ Advertisement {advertisement_id} approved successfully")
            else:
                logger.warning(f"⚠ Advertisement approval response: {data}")

            return data

        except Exception as e:
            logger.error(f"✗ Failed to approve advertisement {advertisement_id}: {e}")
            return {"success": False, "message": str(e)}

    # ===================
    # Data Export API Methods
    # ===================

    def start_export_job(
        self,
        time_range: str = "30d",
        data_types: list[str] | None = None,
        format_type: str = "csv",
        include_metadata: bool = True,
    ) -> dict:
        """Start a new data export job.

        API: POST /api/admin/export-data

        Args:
            time_range: Time range for export (e.g., "30d", "7d", "90d")
            data_types: List of data types to export. If None, exports all types.
            format_type: Export format ("csv" or "xlsx")
            include_metadata: Whether to include metadata in export

        Returns:
            dict: Response with job ID
                {
                    "success": True,
                    "message": "Export job started successfully",
                    "data": {"jobId": "export_xxx_xxx"}
                }
        """
        logger.info("Starting data export job...")

        # Default data types - all available types
        if data_types is None:
            data_types = [
                "users",
                "employees",
                "doctors",
                "badges",
                "orders",
                "delivery_tracking",
                "payfast_itn",
                "products",
                "research_papers",
                "research_reports",
                "research_views",
                "research_upvotes",
                "research_benefits",
                "research_benefit_configs",
                "research_reward_eligibility",
                "research_settings",
                "leaderboard",
                "tier_configs",
                "hall_of_pride",
                "certificates",
                "advertisements",
                "video_advertisements",
                "banner_advertisements",
                "advertisement_applications",
                "advertisement_placements",
                "advertisement_configs",
                "advertisement_pricing_configs",
                "advertisement_rotation_configs",
                "admin_permissions",
                "signup_ids",
                "user_wallets",
                "user_wallets_full",
                "debt_management",
                "debt_thresholds",
                "notifications",
                "gmail_messages",
                "email_deliveries",
                "auto_email_configs",
                "otp_codes",
                "otp_configs",
                "teams",
                "team_members",
                "team_invitations",
                "team_tier_configs",
                "award_message_templates",
                "ai_models",
                "api_tokens",
                "analytics",
                "user_activity",
                "order_statistics",
            ]

        payload = {
            "timeRange": time_range,
            "dataTypes": data_types,
            "format": format_type,
            "includeMetadata": include_metadata,
        }

        logger.info(f"Export parameters: timeRange={time_range}, format={format_type}, types={len(data_types)}")

        try:
            response = self.post("/api/admin/export-data", json_data=payload)
            data = response.json()

            if data.get("success"):
                job_id = data.get("data", {}).get("jobId")
                logger.info(f"✓ Export job started: {job_id}")
            else:
                logger.warning(f"⚠ Export job response: {data}")

            return data

        except Exception as e:
            logger.error(f"✗ Failed to start export job: {e}")
            return {"success": False, "message": str(e)}

    def get_export_jobs(self) -> list[dict]:
        """Get all export jobs.

        API: GET /api/admin/export-jobs

        Returns:
            list[dict]: List of export job objects with fields:
                - id: Job ID
                - status: "processing" | "completed" | "failed"
                - createdAt: Timestamp
                - completedAt: Timestamp (if completed)
                - fileSize: Size in bytes (if completed)
        """
        logger.info("Fetching export jobs...")

        try:
            response = self.get("/api/admin/export-jobs")
            data = response.json()

            # Handle different response formats
            if isinstance(data, dict):
                if "data" in data:
                    jobs = data["data"]
                else:
                    jobs = [data]
            elif isinstance(data, list):
                jobs = data
            else:
                jobs = []

            logger.info(f"✓ Fetched {len(jobs)} export jobs")
            return jobs

        except Exception as e:
            logger.error(f"✗ Failed to fetch export jobs: {e}")
            return []

    def download_export(self, job_id: str, output_dir: str) -> str | None:
        """Download an exported file.

        API: GET /api/admin/export-jobs/{job_id}/download

        Args:
            job_id: The export job ID
            output_dir: Directory to save the file

        Returns:
            str | None: Path to the downloaded file, or None if failed
        """
        from pathlib import Path

        logger.info(f"Downloading export {job_id}...")

        try:
            endpoint = f"/api/admin/export-jobs/{job_id}/download"
            response = self._request("GET", endpoint, stream=True)

            # Determine filename from Content-Disposition header or use default
            content_disp = response.headers.get("Content-Disposition", "")
            if "filename=" in content_disp:
                filename = content_disp.split("filename=")[-1].strip("\"'")
            else:
                filename = f"export_{job_id}.xlsx"

            # Save file
            output_path = Path(output_dir) / filename
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            logger.info(f"✓ Downloaded to: {output_path}")
            return str(output_path)

        except Exception as e:
            logger.error(f"✗ Failed to download export {job_id}: {e}")
            return None
