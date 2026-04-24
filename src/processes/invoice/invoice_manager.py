"""Invoice Manager - downloads source files, fetches unpaid orders, and generates invoices."""

from __future__ import annotations

import json
import time
from datetime import datetime
from typing import TYPE_CHECKING

import pandas as pd
from company_challan.generate_challan import generate_invoice_files

from config import CONFIG
from libraries.google_drive import GoogleDriveAPI
from libraries.logger import logger
from processes.order.api_handler import APIHandler

if TYPE_CHECKING:
    from pathlib import Path


class InvoiceManager:
    """Coordinates invoice generation workflow."""

    def __init__(self) -> None:
        CONFIG.ensure_directories()
        self._drive = GoogleDriveAPI(auto_authenticate=True)
        self._api_handler = APIHandler()

        self.pending_orders_df = pd.DataFrame()
        self.advertisement_df = pd.DataFrame()

        self.generated_invoices: list[dict] = []
        self.skipped_orders: list[str] = []
        self.failed_orders: list[dict] = []

        self._cache_manifest_path = CONFIG.DRIVE_CACHE_DIR / "drive_cache_manifest.json"
        self._processed_log_path = CONFIG.INVOICE_PROCESSED_LOG

    def _with_retry(self, action_name: str, fn, retries: int = 3):
        """Retry helper for transient network operations."""
        last_error = None
        for attempt in range(1, retries + 1):
            try:
                return fn()
            except Exception as e:
                last_error = e
                logger.warning(f"{action_name} failed (attempt {attempt}/{retries}): {e}")
                if attempt < retries:
                    time.sleep(2 ** (attempt - 1))
        raise RuntimeError(f"{action_name} failed after {retries} attempts: {last_error}")

    def _read_cache_manifest(self) -> dict:
        if self._cache_manifest_path.exists():
            with open(self._cache_manifest_path) as f:
                return json.load(f)
        return {}

    def _write_cache_manifest(self, manifest: dict) -> None:
        with open(self._cache_manifest_path, "w") as f:
            json.dump(manifest, f, indent=2)

    def download_drive_file(self, file_id: str) -> Path:
        """Download a Drive file by file ID with local cache support."""
        metadata = self._with_retry(
            f"Fetching Drive metadata for {file_id}",
            lambda: self._drive.get_file(file_id, fields="id,name,modifiedTime,size"),
        )

        file_name = metadata.get("name") or f"{file_id}.bin"
        modified_time = metadata.get("modifiedTime", "")
        size = str(metadata.get("size", ""))

        target_path = CONFIG.DRIVE_CACHE_DIR / file_name
        manifest = self._read_cache_manifest()
        cached = manifest.get(file_id, {})

        if target_path.exists() and cached.get("modifiedTime") == modified_time and cached.get("size") == size:
            logger.info(f"Using cached Drive file: {target_path}")
            return target_path

        self._with_retry(
            f"Downloading Drive file {file_id}",
            lambda: self._drive.download_file(file_id, local_path=target_path),
        )

        manifest[file_id] = {
            "path": str(target_path),
            "modifiedTime": modified_time,
            "size": size,
            "downloadedAt": datetime.now().isoformat(),
        }
        self._write_cache_manifest(manifest)
        return target_path

    def _normalize_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        normalized = df.copy()
        normalized.columns = [str(col).strip().lower().replace(" ", "_") for col in normalized.columns]
        return normalized

    def load_source_excels(self) -> None:
        """Download and parse both source Excel files."""
        pending_path = self.download_drive_file(CONFIG.PENDING_ORDERS_FILE_ID)
        advertisement_path = self.download_drive_file(CONFIG.ADVERTISEMENT_FILE_ID)

        self.pending_orders_df = self._normalize_dataframe(pd.read_excel(pending_path))
        self.advertisement_df = self._normalize_dataframe(pd.read_excel(advertisement_path))

        logger.info(f"Loaded pending orders rows: {len(self.pending_orders_df)}")
        logger.info(f"Loaded advertisement rows: {len(self.advertisement_df)}")

    def fetch_unpaid_orders(self) -> list[dict]:
        """Fetch orders that are not paid yet."""
        return self._with_retry(
            "Fetching unpaid orders from API",
            self._api_handler.fetch_unpaid_orders,
        )

    def _load_processed_orders(self) -> dict[str, dict]:
        if self._processed_log_path.exists():
            with open(self._processed_log_path) as f:
                return json.load(f)
        return {}

    def _save_processed_orders(self, payload: dict[str, dict]) -> None:
        with open(self._processed_log_path, "w") as f:
            json.dump(payload, f, indent=2)

    def _match_pending_row(self, order: dict) -> dict:
        if self.pending_orders_df.empty:
            return {}

        order_id = str(order.get("id") or order.get("order_id") or "").strip()
        order_number = str(order.get("order_number") or order.get("orderNumber") or "").strip()

        id_columns = ["id", "order_id"]
        number_columns = ["order_number", "ordernumber"]

        for col in id_columns:
            if col in self.pending_orders_df.columns:
                matched = self.pending_orders_df[self.pending_orders_df[col].astype(str) == order_id]
                if not matched.empty:
                    return matched.iloc[0].to_dict()

        for col in number_columns:
            if col in self.pending_orders_df.columns:
                matched = self.pending_orders_df[self.pending_orders_df[col].astype(str) == order_number]
                if not matched.empty:
                    return matched.iloc[0].to_dict()

        return {}

    def _safe_float(self, value, default: float = 0.0) -> float:
        try:
            if value is None or (isinstance(value, float) and pd.isna(value)):
                return default
            return float(value)
        except (TypeError, ValueError):
            return default

    def _build_items(self, order: dict, pending_row: dict) -> list[tuple[float, str, str, float, float]]:
        qty = self._safe_float(
            pending_row.get("qty") or pending_row.get("quantity") or order.get("qty") or order.get("quantity") or 1,
            default=1.0,
        )
        unit_price = self._safe_float(
            pending_row.get("product_price")
            or pending_row.get("unit_price")
            or order.get("product_price")
            or order.get("productPrice")
            or 0,
        )

        if unit_price <= 0:
            total = self._safe_float(order.get("order_total") or order.get("orderTotal") or 0)
            if total > 0 and qty > 0:
                unit_price = total / qty

        product_name = str(
            pending_row.get("product_name")
            or pending_row.get("description")
            or order.get("product_name")
            or order.get("productName")
            or "Service"
        )

        item_code = str(
            pending_row.get("product_id") or order.get("product_id") or order.get("productId") or product_name
        )

        line_total = round(qty * unit_price, 2)
        return [(qty, item_code, product_name, unit_price, line_total)]

    def process_order(self, order: dict) -> dict | None:
        """Generate invoice files for one unpaid order."""
        order_id = str(order.get("id") or order.get("order_id") or "").strip()
        if not order_id:
            logger.warning("Skipping order with missing ID")
            return None

        processed_orders = self._load_processed_orders()
        if order_id in processed_orders:
            logger.info(f"Skipping already processed order: {order_id}")
            self.skipped_orders.append(order_id)
            return None

        pending_row = self._match_pending_row(order)
        invoice_no = str(order.get("order_number") or order.get("orderNumber") or f"INV-{order_id[:8]}")
        bill_to = str(
            pending_row.get("doctor_name") or order.get("doctor_name") or order.get("doctorName") or "Customer"
        )
        doctor_email = str(
            pending_row.get("doctor_email") or order.get("doctor_email") or order.get("doctorEmail") or ""
        )

        items = self._build_items(order, pending_row)

        paths = generate_invoice_files(
            output_dir=str(CONFIG.INVOICE_OUTPUT_DIR),
            invoice_no=invoice_no,
            bill_to=bill_to,
            items=items,
            email=doctor_email,
        )

        processed_orders[order_id] = {
            "order_id": order_id,
            "invoice_no": invoice_no,
            "pdf": paths["pdf"],
            "excel": paths["excel"],
            "processed_at": datetime.now().isoformat(),
        }
        self._save_processed_orders(processed_orders)

        self.generated_invoices.append(processed_orders[order_id])
        logger.info(f"Generated invoice for order {order_id}: {paths['pdf']}")
        return processed_orders[order_id]

    def start(self) -> None:
        """Execute full invoice generation workflow."""
        logger.info("=" * 60)
        logger.info("Starting Invoice Generation Workflow")
        logger.info("=" * 60)

        self.load_source_excels()
        unpaid_orders = self.fetch_unpaid_orders()

        if not unpaid_orders:
            logger.info("No unpaid orders found. Invoice generation skipped.")
            return

        for order in unpaid_orders:
            order_id = str(order.get("id") or order.get("order_id") or "")
            try:
                self.process_order(order)
            except Exception as e:
                logger.error(f"Failed to process order {order_id}: {e}")
                self.failed_orders.append({"order_id": order_id, "error": str(e)})

        if self.failed_orders:
            raise RuntimeError(f"Invoice generation failed for {len(self.failed_orders)} order(s)")


def download_drive_file(file_id: str) -> str:
    """Reusable helper: download a Drive file by file ID."""
    manager = InvoiceManager()
    return manager.download_drive_file(file_id)


def fetch_unpaid_orders() -> list[dict]:
    """Reusable helper: fetch unpaid orders from API."""
    manager = InvoiceManager()
    return manager.fetch_unpaid_orders()


def process_order(order: dict) -> dict | None:
    """Reusable helper: process a single order into invoice files."""
    manager = InvoiceManager()
    manager.load_source_excels()
    return manager.process_order(order)
