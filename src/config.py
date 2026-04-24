"""Configuration for AestheticRxNetwork."""

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    """Application configuration.

    Values are loaded from:
    1. Environment variables (highest priority)
    2. .env file (if exists)
    3. Default values
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # Application
    APP_NAME: str = "AestheticRxNetworkIntelligentBot"
    DEBUG: bool = Field(default=False)

    # Directories
    OUTPUT_DIR: Path = Field(default_factory=lambda: Path.cwd() / "output")
    TEMP_DIR: Path = Field(default_factory=lambda: Path.cwd() / "temp")

    # ===================
    # Google Drive Configuration
    # ===================

    # Google Drive folder ID where spreadsheets are stored
    # Folder URL: https://drive.google.com/drive/folders/1oF2l_zLXVGPZthOvRwiwb5gwIxGcm-SJ
    GOOGLE_DRIVE_FOLDER_ID: str = Field(
        default="1oF2l_zLXVGPZthOvRwiwb5gwIxGcm-SJ",
        description="Google Drive folder ID for storing order files",
    )

    # ===================
    # Google Sheets Configuration
    # ===================

    # Source spreadsheet ID - the main Google Sheet to read from and update
    # Spreadsheet URL: https://docs.google.com/spreadsheets/d/1wNrE75TQzg4Qkyj0enRvdKw1QSFq1NhU3ZGqbhnzX1E
    SOURCE_SPREADSHEET_ID: str = Field(
        default="1wNrE75TQzg4Qkyj0enRvdKw1QSFq1NhU3ZGqbhnzX1E",
        description="Source Google Sheet ID to read orders from and update payment status",
    )

    # Legacy alias for backward compatibility
    GOOGLE_SPREADSHEET_ID: str = Field(
        default="1wNrE75TQzg4Qkyj0enRvdKw1QSFq1NhU3ZGqbhnzX1E",
        description="Google Spreadsheet ID (alias for SOURCE_SPREADSHEET_ID)",
    )

    # Spreadsheet naming convention
    SPREADSHEET_NAME_PREFIX: str = Field(
        default="AestheticRxNetworkPendingOrder",
        description="Prefix for spreadsheet names (followed by date)",
    )

    # Advertisement Management Spreadsheet
    # Spreadsheet URL: https://docs.google.com/spreadsheets/d/1E9eA0XrEv7BqvYUgvLQOlaqw9walZUmC7p8atgh2D_s
    ADVERTISEMENT_SPREADSHEET_ID: str = Field(
        default="1E9eA0XrEv7BqvYUgvLQOlaqw9walZUmC7p8atgh2D_s",
        description="Google Sheet ID for advertisement management",
    )

    # Google Drive file IDs for invoice generation workflow
    PENDING_ORDERS_FILE_ID: str = Field(
        default="1wRQcrgotbeWsz6s5hJQ4xv_5g_fjhQiM",
        description="Google Drive file ID for pending orders Excel",
    )
    ADVERTISEMENT_FILE_ID: str = Field(
        default="1BOucirkN3GmY84IsS9dK3wjFwjavoZaQ",
        description="Google Drive file ID for advertisement Excel",
    )

    INVOICE_OUTPUT_DIR: Path = Field(default_factory=lambda: Path.cwd() / "output" / "invoices")
    INVOICE_PROCESSED_LOG: Path = Field(default_factory=lambda: Path.cwd() / "output" / "processed_invoices.json")
    DRIVE_CACHE_DIR: Path = Field(default_factory=lambda: Path.cwd() / "temp" / "drive_cache")

    # ===================
    # Financial Tracking Configuration
    # ===================

    # Financial Tracking Spreadsheet - for manual business KPI entry
    # This sheet will be created by financial_sheet_setup.py if not exists
    # Contains 95-column structure for comprehensive financial tracking
    # Spreadsheet URL: https://docs.google.com/spreadsheets/d/1C4W-25vnzHHROsM-pBIEurK3wGc3HQJGCsPtdM9_-gg
    FINANCIAL_TRACKING_SPREADSHEET_ID: str = Field(
        default="1C4W-25vnzHHROsM-pBIEurK3wGc3HQJGCsPtdM9_-gg",
        description="Google Sheet ID for financial tracking data (manual entry)",
    )

    # ===================
    # Order Headers (column names in spreadsheet)
    # ===================

    ORDER_HEADERS: list[str] = Field(
        default=[
            "ID",
            "Order Number",
            "Doctor ID",
            "Doctor Name",
            "Doctor Email",
            "Product ID",
            "Product Name",
            "Product Price",
            "Qty",
            "Order Total",
            "Payment Amount",
            "Remaining Amount",
            "Payment Status",
            "Payment Method",
            "Order Date",
            "Payment Date",
            "Notes",
            "Status",
            "Created At",
            "Updated At",
        ],
        description="Column headers for the orders spreadsheet",
    )

    def ensure_directories(self) -> None:
        """Create output and temp directories if they don't exist."""
        self.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        self.TEMP_DIR.mkdir(parents=True, exist_ok=True)
        self.INVOICE_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        self.DRIVE_CACHE_DIR.mkdir(parents=True, exist_ok=True)

    @property
    def spreadsheet_url(self) -> str:
        """Get the full URL of the Google Spreadsheet."""
        return f"https://docs.google.com/spreadsheets/d/{self.GOOGLE_SPREADSHEET_ID}"

    @property
    def drive_folder_url(self) -> str:
        """Get the full URL of the Google Drive folder."""
        return f"https://drive.google.com/drive/folders/{self.GOOGLE_DRIVE_FOLDER_ID}"

    @property
    def advertisement_spreadsheet_url(self) -> str:
        """Get the full URL of the Advertisement Google Spreadsheet."""
        return f"https://docs.google.com/spreadsheets/d/{self.ADVERTISEMENT_SPREADSHEET_ID}"

    @property
    def financial_tracking_spreadsheet_url(self) -> str:
        """Get the full URL of the Financial Tracking Google Spreadsheet."""
        if self.FINANCIAL_TRACKING_SPREADSHEET_ID:
            return f"https://docs.google.com/spreadsheets/d/{self.FINANCIAL_TRACKING_SPREADSHEET_ID}"
        return ""


CONFIG = Config()
