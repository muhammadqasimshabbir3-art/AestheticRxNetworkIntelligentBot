"""Data Loader - CSV loading and parsing for business reports.

This module handles loading CSV files from extracted export data
and provides clean DataFrames to analyzers.
"""

import json
from pathlib import Path
from typing import Any

import pandas as pd

from libraries.logger import logger


class DataLoader:
    """Loads and parses CSV data from exported files."""

    # List of all expected CSV files
    CSV_FILES = [
        "users",
        "doctors",
        "employees",
        "signup_ids",
        "orders",
        "order_statistics",
        "delivery_tracking",
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
        "badges",
        "advertisements",
        "video_advertisements",
        "banner_advertisements",
        "advertisement_applications",
        "advertisement_placements",
        "advertisement_configs",
        "advertisement_pricing_configs",
        "advertisement_rotation_configs",
        "admin_permissions",
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
        "payfast_itn",
    ]

    # Date columns that need parsing
    DATE_COLUMNS = [
        "created_at",
        "updated_at",
        "approved_at",
        "consent_at",
        "completed_at",
        "cancelled_at",
        "payment_date",
        "payment_completed_at",
        "delivery_started_at",
        "delivery_completed_at",
        "start_date",
        "end_date",
        "snapshot_date",
        "used_at",
    ]

    # Numeric columns
    NUMERIC_COLUMNS = [
        "order_total",
        "payment_amount",
        "current_sales",
        "total_cost",
        "paid_amount",
        "price",
        "qty",
        "view_count",
        "upvote_count",
        "impressions",
        "clicks",
        "views",
        "rank",
        "total_doctors",
    ]

    def __init__(self, data_dir: Path) -> None:
        """Initialize the data loader.

        Args:
            data_dir: Path to the directory containing CSV files.
        """
        self.data_dir = data_dir
        self._dataframes: dict[str, pd.DataFrame] = {}
        self._loaded = False

    def load_all(self) -> None:
        """Load all CSV files."""
        logger.info(f"Loading CSV files from {self.data_dir}")

        loaded_count = 0
        for csv_name in self.CSV_FILES:
            csv_path = self.data_dir / f"{csv_name}.csv"
            if csv_path.exists():
                df = self._load_csv(csv_path, csv_name)
                if df is not None and not df.empty:
                    self._dataframes[csv_name] = df
                    loaded_count += 1
                    logger.debug(f"  ✓ {csv_name}: {len(df)} rows")
                else:
                    self._dataframes[csv_name] = pd.DataFrame()
            else:
                logger.debug(f"  ⚠ {csv_name}.csv not found")
                self._dataframes[csv_name] = pd.DataFrame()

        self._loaded = True
        logger.info(f"✓ Loaded {loaded_count} CSV files with data")

    def _load_csv(self, path: Path, name: str) -> pd.DataFrame | None:
        """Load a single CSV file with proper parsing.

        Args:
            path: Path to the CSV file.
            name: Name of the data type.

        Returns:
            DataFrame or None if loading fails.
        """
        try:
            # Read CSV - try standard parsing first
            df = pd.read_csv(path, low_memory=False)

            # Check if parsing produced valid values in key columns
            # Some CSVs have embedded JSON with unescaped commas
            if name == "orders" and not df.empty and "payment_status" in df.columns:
                # Check if payment_status has valid values
                valid_statuses = {"paid", "unpaid", "pending", "success", "failed", "partial"}
                sample_status = str(df["payment_status"].iloc[0]).lower()
                if not any(s in sample_status for s in valid_statuses):
                    logger.warning(f"{name}.csv has malformed rows, attempting regex extraction")
                    regex_df = self._load_csv_with_regex(path, name)
                    if regex_df is not None and not regex_df.empty:
                        return regex_df
                    # Fall back to standard parse if regex fails
                    df = pd.read_csv(path, low_memory=False)

            # Check advertisements CSV for malformed parsing (embedded JSON in doctor column)
            if name == "advertisements" and not df.empty and "status" in df.columns:
                valid_ad_statuses = {"pending", "active", "completed", "rejected", "paused", "expired"}
                sample_status = str(df["status"].iloc[0]).lower()
                if not any(s in sample_status for s in valid_ad_statuses):
                    logger.warning(f"{name}.csv has malformed rows, attempting regex extraction")
                    regex_df = self._load_csv_with_regex(path, name)
                    if regex_df is not None and not regex_df.empty:
                        return regex_df
                    # Fall back to standard parse if regex fails
                    df = pd.read_csv(path, low_memory=False)

            if df.empty:
                return df

            # Remove metadata column if present
            if "_export_metadata" in df.columns:
                df = df.drop(columns=["_export_metadata"])

            # Parse date columns
            for col in self.DATE_COLUMNS:
                if col in df.columns:
                    df[col] = self._parse_date_column(df[col])

            # Parse numeric columns
            for col in self.NUMERIC_COLUMNS:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

            # Parse JSON columns (embedded objects)
            for col in df.columns:
                if col in ["product", "doctor", "google_location"]:
                    df[col] = df[col].apply(self._parse_json_column)

            # Parse boolean columns
            for col in df.columns:
                if col.startswith("is_") or col in ["consent_flag"]:
                    df[col] = df[col].apply(self._parse_bool)

            return df

        except Exception as e:
            logger.warning(f"Failed to load {name}.csv: {e}")
            return None

    def _parse_date_column(self, series: pd.Series) -> pd.Series:
        """Parse a date column, handling various formats."""
        try:
            # Remove extra quotes that might be present
            series = series.astype(str).str.strip('"')
            return pd.to_datetime(series, errors="coerce", utc=True)
        except Exception:
            return series

    def _parse_json_column(self, value: Any) -> Any:
        """Parse a JSON string column."""
        if pd.isna(value) or value == "" or value == "null":
            return None
        if isinstance(value, dict):
            return value
        try:
            return json.loads(str(value))
        except (json.JSONDecodeError, TypeError):
            return value

    def _parse_bool(self, value: Any) -> bool:
        """Parse a boolean value."""
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in ("true", "1", "yes")
        return bool(value)

    def _count_header_columns(self, path: Path) -> int | None:
        """Count the number of columns in the header row."""
        try:
            with open(path, encoding="utf-8") as f:
                header = f.readline().strip()
                return header.count(",") + 1
        except Exception:
            return None

    def _load_csv_with_regex(self, path: Path, name: str) -> pd.DataFrame | None:
        """Load a CSV with embedded JSON using regex extraction.

        This handles malformed CSVs where JSON fields contain unescaped commas.
        It extracts key fields using regex patterns.
        """
        import re

        try:
            with open(path, encoding="utf-8") as f:
                lines = f.readlines()

            if len(lines) < 2:
                return None

            lines[0].strip().split(",")

            # Build records by extracting key values with regex
            records = []

            # Use different extraction logic based on data type
            if name == "advertisements":
                records = self._extract_advertisement_records(lines[1:])
            else:
                # Default extraction for orders and other data
                for line in lines[1:]:
                    if not line.strip():
                        continue

                    record = {}

                    # Extract UUID at the start (id field)
                    id_match = re.search(r'^"([a-f0-9-]{36})"', line)
                    if id_match:
                        record["id"] = id_match.group(1)

                    # Extract order_number
                    order_num_match = re.search(r'"(ORD-\d+)"', line)
                    if order_num_match:
                        record["order_number"] = order_num_match.group(1)

                    # Extract status patterns
                    # First pattern is usually order status, second is delivery status
                    status_matches = re.findall(r'"(completed|pending|accepted|cancelled)"', line.lower())
                    if status_matches:
                        record["status"] = status_matches[0]
                        if len(status_matches) > 1:
                            record["delivery_status"] = status_matches[1]

                    # Extract payment_status
                    payment_status_match = re.search(r'"(paid|unpaid|success|failed|partial)"', line.lower())
                    if payment_status_match:
                        record["payment_status"] = payment_status_match.group(1)

                    # Extract monetary amounts
                    amounts = re.findall(r'"(\d+\.\d{2})"', line)
                    if amounts:
                        # First amount is usually order_total, second is payment_amount
                        record["order_total"] = float(amounts[0])
                        if len(amounts) > 1:
                            record["payment_amount"] = float(amounts[1])
                        else:
                            record["payment_amount"] = float(amounts[0])

                    # Extract payment_method
                    method_match = re.search(r'"(payfast_online|card|cash|bank_transfer|wallet)"', line.lower())
                    if method_match:
                        record["payment_method"] = method_match.group(1)

                    # Extract doctor_id from JSON doctor field
                    doctor_id_match = re.search(r'"doctor_id":(\d+)', line)
                    if doctor_id_match:
                        record["doctor_id"] = int(doctor_id_match.group(1))

                    # Extract doctor_name from doctor JSON
                    doctor_name_match = re.search(r'"doctor_name":"([^"]+)"', line)
                    if doctor_name_match:
                        record["doctor_name"] = doctor_name_match.group(1)

                    # Extract clinic_name from doctor JSON
                    clinic_match = re.search(r'"clinic_name":"([^"]+)"', line)
                    if clinic_match:
                        record["clinic_name"] = clinic_match.group(1)

                    # Extract tier from doctor JSON
                    tier_match = re.search(r'"tier":"([^"]+)"', line)
                    if tier_match:
                        record["tier"] = tier_match.group(1)

                    # Extract product name from product JSON
                    product_name_match = re.search(r'"name":"([^"]+)"', line)
                    if product_name_match:
                        record["product_name"] = product_name_match.group(1)

                    # Extract product_id (UUID after product_id field)
                    product_id_match = re.search(r'"product_id":"([a-f0-9-]{36})"', line)
                    if not product_id_match:
                        # Try alternative format - 4th UUID in the line is usually product_id
                        all_uuids = re.findall(r'"([a-f0-9-]{36})"', line)
                        if len(all_uuids) >= 4:
                            record["product_id"] = all_uuids[3]  # 4th UUID is product_id
                    else:
                        record["product_id"] = product_id_match.group(1)

                    # Extract created_at timestamp
                    created_match = re.search(r'"(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+Z)"', line)
                    if created_match:
                        record["created_at"] = created_match.group(1)

                    # Extract payment_completed_at - looks for timestamp after certain patterns
                    payment_completed_match = re.findall(r'"(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+Z)"', line)
                    if len(payment_completed_match) > 1:
                        # Second timestamp is often payment_completed_at
                        record["payment_completed_at"] = payment_completed_match[1]

                    if record.get("id"):  # Only add if we found an ID
                        records.append(record)

            if not records:
                return None

            df = pd.DataFrame(records)
            logger.info(f"  ✓ Regex extracted {len(df)} records from {name}.csv")

            return df

        except Exception as e:
            logger.warning(f"Regex extraction failed for {name}.csv: {e}")
            return None

    def _extract_advertisement_records(self, lines: list[str]) -> list[dict]:
        """Extract advertisement records from malformed CSV lines.

        Handles embedded JSON in doctor column that causes column shifts.
        """
        import re

        records = []
        for line in lines:
            if not line.strip():
                continue

            record = {}

            # Extract UUID at the start (id field)
            id_match = re.search(r'^"([a-f0-9-]{36})"', line)
            if id_match:
                record["id"] = id_match.group(1)

            # Extract second UUID (doctor_id)
            all_uuids = re.findall(r'"([a-f0-9-]{36})"', line)
            if len(all_uuids) > 1:
                record["doctor_id"] = all_uuids[1]

            # Extract title - usually after doctor_id UUID
            title_match = re.search(r'"[a-f0-9-]{36}","[a-f0-9-]{36}","([^"]*)"', line)
            if title_match:
                record["title"] = title_match.group(1)

            # Extract type (video, image, etc.)
            type_match = re.search(r'"(video|image|banner|slideshow)"', line.lower())
            if type_match:
                record["type"] = type_match.group(1)

            # Extract status - look for ad-specific statuses
            status_match = re.search(r'"(completed|pending|active|rejected|paused|expired)"', line.lower())
            if status_match:
                record["status"] = status_match.group(1)

            # Extract payment_status
            payment_status_match = re.search(r'"(paid|unpaid|pending)"', line.lower())
            if payment_status_match:
                record["payment_status"] = payment_status_match.group(1)

            # Extract payment_method
            method_match = re.search(r'"(cash|card|bank_transfer|payfast_online|wallet)"', line.lower())
            if method_match:
                record["payment_method"] = method_match.group(1)

            # Extract monetary amounts (total_cost, paid_amount)
            amounts = re.findall(r'"(\d+\.\d{2})"', line)
            if amounts:
                record["total_cost"] = float(amounts[0])
                if len(amounts) > 1:
                    record["paid_amount"] = float(amounts[1])
                else:
                    record["paid_amount"] = 0.0

            # Extract impressions, clicks, views (integer values)
            int_values = re.findall(r'"(\d+)"', line)
            # Filter to reasonable ranges for these metrics
            for val in int_values:
                num = int(val)
                if num < 100000:  # Reasonable range for impressions/clicks
                    if "impressions" not in record:
                        record["impressions"] = num
                    elif "clicks" not in record:
                        record["clicks"] = num
                    elif "views" not in record:
                        record["views"] = num

            # Extract doctor_name from embedded JSON
            doctor_name_match = re.search(r'"doctor_name":"([^"]+)"', line)
            if doctor_name_match:
                record["doctor_name"] = doctor_name_match.group(1)

            # Extract timestamps
            timestamps = re.findall(r'"(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+Z)"', line)
            if timestamps:
                record["created_at"] = timestamps[0]
                if len(timestamps) > 1:
                    record["updated_at"] = timestamps[-1]

            if record.get("id"):  # Only add if we found an ID
                records.append(record)

        return records

    def get(self, name: str) -> pd.DataFrame:
        """Get a DataFrame by name.

        Args:
            name: Name of the data type (e.g., "users", "orders").

        Returns:
            DataFrame, empty if not found.
        """
        if not self._loaded:
            raise RuntimeError("Data not loaded. Call load_all() first.")
        return self._dataframes.get(name, pd.DataFrame())

    def __getitem__(self, name: str) -> pd.DataFrame:
        """Get a DataFrame by name using bracket notation."""
        return self.get(name)

    @property
    def data_frames(self) -> dict[str, pd.DataFrame]:
        """Get all DataFrames as a dictionary."""
        if not self._loaded:
            raise RuntimeError("Data not loaded. Call load_all() first.")
        return self._dataframes

    @property
    def users(self) -> pd.DataFrame:
        """Get users DataFrame."""
        return self.get("users")

    @property
    def doctors(self) -> pd.DataFrame:
        """Get doctors DataFrame."""
        return self.get("doctors")

    @property
    def orders(self) -> pd.DataFrame:
        """Get orders DataFrame."""
        return self.get("orders")

    @property
    def products(self) -> pd.DataFrame:
        """Get products DataFrame."""
        return self.get("products")

    @property
    def research_papers(self) -> pd.DataFrame:
        """Get research papers DataFrame."""
        return self.get("research_papers")

    @property
    def advertisements(self) -> pd.DataFrame:
        """Get advertisements DataFrame."""
        return self.get("advertisements")

    @property
    def leaderboard(self) -> pd.DataFrame:
        """Get leaderboard DataFrame."""
        return self.get("leaderboard")

    @property
    def signup_ids(self) -> pd.DataFrame:
        """Get signup IDs DataFrame."""
        return self.get("signup_ids")

    def get_row_counts(self) -> dict[str, int]:
        """Get row counts for all loaded DataFrames."""
        return {name: len(df) for name, df in self._dataframes.items() if not df.empty}

    def get_summary(self) -> dict[str, Any]:
        """Get a summary of loaded data."""
        return {
            "total_files": len(self._dataframes),
            "files_with_data": sum(1 for df in self._dataframes.values() if not df.empty),
            "row_counts": self.get_row_counts(),
        }

