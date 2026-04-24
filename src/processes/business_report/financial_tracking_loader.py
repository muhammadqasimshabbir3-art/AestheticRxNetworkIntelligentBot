"""Financial Tracking Data Loader.

This module reads financial tracking data from a Google Sheet
and provides structured data for business KPI analysis.
"""

import contextlib
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from config import CONFIG
from libraries.google_sheets import GoogleSheetsAPI
from libraries.logger import logger


@dataclass
class MonthlyFinancialData:
    """Financial data for a single month."""

    year: int
    month: str
    record_type: str  # Target, Update, Month_End
    timestamp: datetime | None = None

    # Sales
    ts_target: float = 0.0
    medical_products_sales_target: float = 0.0
    medical_products_sales_actual: float = 0.0
    beauty_products_sales_target: float = 0.0
    beauty_products_sales_actual: float = 0.0
    ts_calculated: float = 0.0

    # Investment
    ti_target: float = 0.0
    ti_calculated: float = 0.0
    founder_investment_target: float = 0.0
    founder_investment_actual: float = 0.0
    cofounder_investment_target: float = 0.0
    cofounder_investment_actual: float = 0.0
    investor_investment_target: float = 0.0
    investor_investment_actual: float = 0.0
    importer_investment_target: float = 0.0
    importer_investment_actual: float = 0.0

    # Profit & Clients
    tp_target: float = 0.0
    tp_actual: float = 0.0
    tnc_target: float = 0.0
    tnc_actual: float = 0.0

    # Contributions
    cfc_target: float = 0.0
    cfc_actual: float = 0.0
    pfc_target: float = 0.0
    pfc_actual: float = 0.0

    # Borrowed Products
    tbpc_target: float = 0.0
    tbpc_actual: float = 0.0
    tbpp_target: float = 0.0
    tbpp_actual: float = 0.0
    rbpp_calculated: float = 0.0

    # Expenses
    te_target: float = 0.0
    operating_expenses_target: float = 0.0
    operating_expenses_actual: float = 0.0
    marketing_sales_expenses_target: float = 0.0
    marketing_sales_expenses_actual: float = 0.0
    product_costs_target: float = 0.0
    product_costs_actual: float = 0.0
    salaries_wages_target: float = 0.0
    salaries_wages_actual: float = 0.0
    delivery_logistics_target: float = 0.0
    delivery_logistics_actual: float = 0.0
    regulatory_compliance_target: float = 0.0
    regulatory_compliance_actual: float = 0.0
    other_expenses_target: float = 0.0
    other_expenses_actual: float = 0.0
    te_calculated: float = 0.0

    # Doctor Prizes
    pupmpd_target: float = 0.0
    doctor_prizes_gifts_target: float = 0.0
    doctor_prizes_gifts_actual: float = 0.0
    doctor_prizes_research_products_target: float = 0.0
    doctor_prizes_research_products_actual: float = 0.0
    pupmpd_calculated: float = 0.0

    # Capital
    tcmc_target: float = 0.0
    tcmc_calculated: float = 0.0
    tcmcci_target: float = 0.0
    tcmcci_actual: float = 0.0

    # Calculated Metrics
    tnppm_calculated: float = 0.0
    roi_percent_calculated: float = 0.0
    profit_margin_percent_calculated: float = 0.0
    cac_calculated: float = 0.0
    debt_ratio_percent_calculated: float = 0.0
    collection_efficiency_percent_calculated: float = 0.0
    sales_growth_percent_calculated: float = 0.0
    client_growth_percent_calculated: float = 0.0

    # Previous Month Data
    ncpmt: float = 0.0
    ncpmd: float = 0.0
    tipm: float = 0.0
    tppm: float = 0.0
    tnppm: float = 0.0
    tpmrp: float = 0.0  # Money Received
    trpmrp: float = 0.0  # Outstanding
    mspm: float = 0.0  # Sales Orders
    tepm: float = 0.0

    notes: str = ""
    special_notes: str = ""


@dataclass
class FinancialTrackingData:
    """Complete financial tracking data."""

    records: list[MonthlyFinancialData] = field(default_factory=list)
    loaded_at: datetime | None = None
    source_spreadsheet_id: str = ""

    @property
    def has_data(self) -> bool:
        """Check if any records have actual data."""
        for record in self.records:
            if record.record_type == "Month_End" and (
                record.medical_products_sales_actual > 0
                or record.beauty_products_sales_actual > 0
                or record.tp_actual > 0
                or record.tnc_actual > 0
            ):
                return True
        return False

    def get_month_end_records(self) -> list[MonthlyFinancialData]:
        """Get only Month_End records (final monthly data)."""
        return [r for r in self.records if r.record_type == "Month_End"]

    def get_latest_month_end(self) -> MonthlyFinancialData | None:
        """Get the most recent Month_End record with data."""
        month_ends = self.get_month_end_records()
        for record in reversed(month_ends):
            if (
                record.medical_products_sales_actual > 0
                or record.beauty_products_sales_actual > 0
                or record.tp_actual > 0
            ):
                return record
        return month_ends[-1] if month_ends else None

    def get_records_by_year(self, year: int) -> list[MonthlyFinancialData]:
        """Get all records for a specific year."""
        return [r for r in self.records if r.year == year]


class FinancialTrackingLoader:
    """Loads financial tracking data from Google Sheet."""

    # Column name to index mapping (based on FINANCIAL_TRACKING_HEADERS)
    COLUMN_MAPPING = {
        "Year": 0,
        "Month": 1,
        "Timestamp": 2,
        "Record_Type": 3,
        "Notes": 4,
        "TS_Target": 5,
        "Medical_Products_Sales_Target": 6,
        "Medical_Products_Sales_Actual": 7,
        "Beauty_Products_Sales_Target": 8,
        "Beauty_Products_Sales_Actual": 9,
        "TS_Calculated": 10,
        "TI_Target": 11,
        "TI_Calculated": 12,
        "Founder_Investment_Target": 13,
        "Founder_Investment_Actual": 14,
        "CoFounder_Investment_Target": 15,
        "CoFounder_Investment_Actual": 16,
        "Investor_Investment_Target": 17,
        "Investor_Investment_Actual": 18,
        "Importer_Investment_Target": 19,
        "Importer_Investment_Actual": 20,
        "TP_Target": 21,
        "TP_Actual": 22,
        "TNC_Target": 23,
        "TNC_Actual": 24,
        "CFC_Target": 25,
        "CFC_Actual": 26,
        "PFC_Target": 27,
        "PFC_Actual": 28,
        "TBPC_Target": 29,
        "TBPC_Actual": 30,
        "TBPP_Target": 31,
        "TBPP_Actual": 32,
        "RBPP_Calculated": 33,
        "TE_Target": 34,
        "Operating_Expenses_Target": 35,
        "Operating_Expenses_Actual": 36,
        "Marketing_Sales_Expenses_Target": 37,
        "Marketing_Sales_Expenses_Actual": 38,
        "Product_Costs_Target": 39,
        "Product_Costs_Actual": 40,
        "Salaries_Wages_Target": 41,
        "Salaries_Wages_Actual": 42,
        "Delivery_Logistics_Target": 43,
        "Delivery_Logistics_Actual": 44,
        "Regulatory_Compliance_Target": 45,
        "Regulatory_Compliance_Actual": 46,
        "Other_Expenses_Target": 47,
        "Other_Expenses_Actual": 48,
        "TE_Calculated": 49,
        "PUPMPD_Target": 50,
        "Doctor_Prizes_Gifts_Target": 51,
        "Doctor_Prizes_Gifts_Actual": 52,
        "Doctor_Prizes_Research_Products_Target": 53,
        "Doctor_Prizes_Research_Products_Actual": 54,
        "PUPMPD_Calculated": 55,
        "TCMC_Target": 56,
        "TCMC_Calculated": 57,
        "TCMCCI_Target": 58,
        "TCMCCI_Actual": 59,
        "TNPPM_Calculated": 60,
        "ROI_Percent_Calculated": 61,
        "Profit_Margin_Percent_Calculated": 62,
        "CAC_Calculated": 63,
        "Debt_Ratio_Percent_Calculated": 64,
        "Collection_Efficiency_Percent_Calculated": 65,
        "Sales_Growth_Percent_Calculated": 66,
        "Client_Growth_Percent_Calculated": 67,
        "NCPMT": 68,
        "NCPMD": 69,
        "TIPM": 70,
        "Founder_Investment_PM": 71,
        "CoFounder_Investment_PM": 72,
        "Investor_Investment_PM": 73,
        "Importer_Investment_PM": 74,
        "CFCPM": 75,
        "PFCPM": 76,
        "TBPCPM": 77,
        "TBPPPM": 78,
        "TPPM": 79,
        "TNPPM": 80,
        "TPMRP": 81,
        "TRPMRP": 82,
        "MSPM": 83,
        "RPUPMPDPM": 84,
        "TEPM": 85,
        "Operating_Expenses_PM": 86,
        "Marketing_Sales_Expenses_PM": 87,
        "Product_Costs_PM": 88,
        "Salaries_Wages_PM": 89,
        "Delivery_Logistics_PM": 90,
        "Regulatory_Compliance_PM": 91,
        "Other_Expenses_PM": 92,
        "Legislation_Website_Launch_Status": 93,
        "Special_Notes": 94,
    }

    def __init__(self, spreadsheet_id: str | None = None) -> None:
        """Initialize the loader.

        Args:
            spreadsheet_id: Google Sheet ID. Uses CONFIG if not provided.
        """
        self.spreadsheet_id = spreadsheet_id or CONFIG.FINANCIAL_TRACKING_SPREADSHEET_ID
        self._sheets_api: GoogleSheetsAPI | None = None
        self._data: FinancialTrackingData | None = None

    def _get_sheets_api(self) -> GoogleSheetsAPI:
        """Get or create GoogleSheetsAPI instance."""
        if self._sheets_api is None:
            self._sheets_api = GoogleSheetsAPI()
        return self._sheets_api

    def _safe_float(self, value: Any) -> float:
        """Safely convert value to float."""
        if value is None or value == "":
            return 0.0
        try:
            return float(value)
        except (ValueError, TypeError):
            return 0.0

    def _safe_int(self, value: Any) -> int:
        """Safely convert value to int."""
        if value is None or value == "":
            return 0
        try:
            return int(float(value))
        except (ValueError, TypeError):
            return 0

    def _safe_str(self, value: Any) -> str:
        """Safely convert value to string."""
        if value is None:
            return ""
        return str(value)

    def _get_cell(self, row: list, column_name: str) -> Any:
        """Get cell value from row by column name."""
        idx = self.COLUMN_MAPPING.get(column_name)
        if idx is None or idx >= len(row):
            return None
        return row[idx]

    def _parse_row(self, row: list) -> MonthlyFinancialData | None:
        """Parse a row of data into MonthlyFinancialData."""
        try:
            year = self._safe_int(self._get_cell(row, "Year"))
            month = self._safe_str(self._get_cell(row, "Month"))
            record_type = self._safe_str(self._get_cell(row, "Record_Type"))

            if not year or not month or not record_type:
                return None

            # Parse timestamp
            timestamp_str = self._safe_str(self._get_cell(row, "Timestamp"))
            timestamp = None
            if timestamp_str:
                with contextlib.suppress(ValueError):
                    timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")

            return MonthlyFinancialData(
                year=year,
                month=month,
                record_type=record_type,
                timestamp=timestamp,
                # Sales
                ts_target=self._safe_float(self._get_cell(row, "TS_Target")),
                medical_products_sales_target=self._safe_float(self._get_cell(row, "Medical_Products_Sales_Target")),
                medical_products_sales_actual=self._safe_float(self._get_cell(row, "Medical_Products_Sales_Actual")),
                beauty_products_sales_target=self._safe_float(self._get_cell(row, "Beauty_Products_Sales_Target")),
                beauty_products_sales_actual=self._safe_float(self._get_cell(row, "Beauty_Products_Sales_Actual")),
                ts_calculated=self._safe_float(self._get_cell(row, "TS_Calculated")),
                # Investment
                ti_target=self._safe_float(self._get_cell(row, "TI_Target")),
                ti_calculated=self._safe_float(self._get_cell(row, "TI_Calculated")),
                founder_investment_target=self._safe_float(self._get_cell(row, "Founder_Investment_Target")),
                founder_investment_actual=self._safe_float(self._get_cell(row, "Founder_Investment_Actual")),
                cofounder_investment_target=self._safe_float(self._get_cell(row, "CoFounder_Investment_Target")),
                cofounder_investment_actual=self._safe_float(self._get_cell(row, "CoFounder_Investment_Actual")),
                investor_investment_target=self._safe_float(self._get_cell(row, "Investor_Investment_Target")),
                investor_investment_actual=self._safe_float(self._get_cell(row, "Investor_Investment_Actual")),
                importer_investment_target=self._safe_float(self._get_cell(row, "Importer_Investment_Target")),
                importer_investment_actual=self._safe_float(self._get_cell(row, "Importer_Investment_Actual")),
                # Profit & Clients
                tp_target=self._safe_float(self._get_cell(row, "TP_Target")),
                tp_actual=self._safe_float(self._get_cell(row, "TP_Actual")),
                tnc_target=self._safe_float(self._get_cell(row, "TNC_Target")),
                tnc_actual=self._safe_float(self._get_cell(row, "TNC_Actual")),
                # Contributions
                cfc_target=self._safe_float(self._get_cell(row, "CFC_Target")),
                cfc_actual=self._safe_float(self._get_cell(row, "CFC_Actual")),
                pfc_target=self._safe_float(self._get_cell(row, "PFC_Target")),
                pfc_actual=self._safe_float(self._get_cell(row, "PFC_Actual")),
                # Borrowed Products
                tbpc_target=self._safe_float(self._get_cell(row, "TBPC_Target")),
                tbpc_actual=self._safe_float(self._get_cell(row, "TBPC_Actual")),
                tbpp_target=self._safe_float(self._get_cell(row, "TBPP_Target")),
                tbpp_actual=self._safe_float(self._get_cell(row, "TBPP_Actual")),
                rbpp_calculated=self._safe_float(self._get_cell(row, "RBPP_Calculated")),
                # Expenses
                te_target=self._safe_float(self._get_cell(row, "TE_Target")),
                operating_expenses_target=self._safe_float(self._get_cell(row, "Operating_Expenses_Target")),
                operating_expenses_actual=self._safe_float(self._get_cell(row, "Operating_Expenses_Actual")),
                marketing_sales_expenses_target=self._safe_float(
                    self._get_cell(row, "Marketing_Sales_Expenses_Target")
                ),
                marketing_sales_expenses_actual=self._safe_float(
                    self._get_cell(row, "Marketing_Sales_Expenses_Actual")
                ),
                product_costs_target=self._safe_float(self._get_cell(row, "Product_Costs_Target")),
                product_costs_actual=self._safe_float(self._get_cell(row, "Product_Costs_Actual")),
                salaries_wages_target=self._safe_float(self._get_cell(row, "Salaries_Wages_Target")),
                salaries_wages_actual=self._safe_float(self._get_cell(row, "Salaries_Wages_Actual")),
                delivery_logistics_target=self._safe_float(self._get_cell(row, "Delivery_Logistics_Target")),
                delivery_logistics_actual=self._safe_float(self._get_cell(row, "Delivery_Logistics_Actual")),
                regulatory_compliance_target=self._safe_float(self._get_cell(row, "Regulatory_Compliance_Target")),
                regulatory_compliance_actual=self._safe_float(self._get_cell(row, "Regulatory_Compliance_Actual")),
                other_expenses_target=self._safe_float(self._get_cell(row, "Other_Expenses_Target")),
                other_expenses_actual=self._safe_float(self._get_cell(row, "Other_Expenses_Actual")),
                te_calculated=self._safe_float(self._get_cell(row, "TE_Calculated")),
                # Doctor Prizes
                pupmpd_target=self._safe_float(self._get_cell(row, "PUPMPD_Target")),
                doctor_prizes_gifts_target=self._safe_float(self._get_cell(row, "Doctor_Prizes_Gifts_Target")),
                doctor_prizes_gifts_actual=self._safe_float(self._get_cell(row, "Doctor_Prizes_Gifts_Actual")),
                doctor_prizes_research_products_target=self._safe_float(
                    self._get_cell(row, "Doctor_Prizes_Research_Products_Target")
                ),
                doctor_prizes_research_products_actual=self._safe_float(
                    self._get_cell(row, "Doctor_Prizes_Research_Products_Actual")
                ),
                pupmpd_calculated=self._safe_float(self._get_cell(row, "PUPMPD_Calculated")),
                # Capital
                tcmc_target=self._safe_float(self._get_cell(row, "TCMC_Target")),
                tcmc_calculated=self._safe_float(self._get_cell(row, "TCMC_Calculated")),
                tcmcci_target=self._safe_float(self._get_cell(row, "TCMCCI_Target")),
                tcmcci_actual=self._safe_float(self._get_cell(row, "TCMCCI_Actual")),
                # Calculated Metrics
                tnppm_calculated=self._safe_float(self._get_cell(row, "TNPPM_Calculated")),
                roi_percent_calculated=self._safe_float(self._get_cell(row, "ROI_Percent_Calculated")),
                profit_margin_percent_calculated=self._safe_float(
                    self._get_cell(row, "Profit_Margin_Percent_Calculated")
                ),
                cac_calculated=self._safe_float(self._get_cell(row, "CAC_Calculated")),
                debt_ratio_percent_calculated=self._safe_float(self._get_cell(row, "Debt_Ratio_Percent_Calculated")),
                collection_efficiency_percent_calculated=self._safe_float(
                    self._get_cell(row, "Collection_Efficiency_Percent_Calculated")
                ),
                sales_growth_percent_calculated=self._safe_float(
                    self._get_cell(row, "Sales_Growth_Percent_Calculated")
                ),
                client_growth_percent_calculated=self._safe_float(
                    self._get_cell(row, "Client_Growth_Percent_Calculated")
                ),
                # Previous Month
                ncpmt=self._safe_float(self._get_cell(row, "NCPMT")),
                ncpmd=self._safe_float(self._get_cell(row, "NCPMD")),
                tipm=self._safe_float(self._get_cell(row, "TIPM")),
                tppm=self._safe_float(self._get_cell(row, "TPPM")),
                tnppm=self._safe_float(self._get_cell(row, "TNPPM")),
                tpmrp=self._safe_float(self._get_cell(row, "TPMRP")),
                trpmrp=self._safe_float(self._get_cell(row, "TRPMRP")),
                mspm=self._safe_float(self._get_cell(row, "MSPM")),
                tepm=self._safe_float(self._get_cell(row, "TEPM")),
                notes=self._safe_str(self._get_cell(row, "Notes")),
                special_notes=self._safe_str(self._get_cell(row, "Special_Notes")),
            )
        except Exception as e:
            logger.warning(f"Failed to parse row: {e}")
            return None

    def load(self) -> FinancialTrackingData:
        """Load financial tracking data from Google Sheet.

        Returns:
            FinancialTrackingData with all records
        """
        logger.info("Loading financial tracking data...")

        if not self.spreadsheet_id:
            logger.warning("No Financial Tracking Spreadsheet ID configured")
            return FinancialTrackingData(
                records=[],
                loaded_at=datetime.now(),
                source_spreadsheet_id="",
            )

        try:
            sheets_api = self._get_sheets_api()

            # Read all data from the sheet
            # Try common sheet names
            data = None
            for sheet_name in ["Financial_Data", "Sheet1", "financial_data"]:
                try:
                    range_name = f"{sheet_name}!A:CQ"  # Up to column 95
                    data = sheets_api.read_data(
                        spreadsheet_id=self.spreadsheet_id,
                        range_name=range_name,
                    )
                    if data and len(data) > 1:
                        logger.info(f"  Found data in sheet: {sheet_name}")
                        break
                except Exception:
                    continue

            if not data or len(data) <= 1:
                logger.warning("No data found in Financial Tracking sheet")
                return FinancialTrackingData(
                    records=[],
                    loaded_at=datetime.now(),
                    source_spreadsheet_id=self.spreadsheet_id,
                )

            # Skip header row
            records = []
            for row in data[1:]:
                record = self._parse_row(row)
                if record:
                    records.append(record)

            logger.info(f"✓ Loaded {len(records)} financial tracking records")

            self._data = FinancialTrackingData(
                records=records,
                loaded_at=datetime.now(),
                source_spreadsheet_id=self.spreadsheet_id,
            )

            if self._data.has_data:
                logger.info("  Financial data has actual entries")
            else:
                logger.info("  Financial data is empty (no actual values entered yet)")

            return self._data

        except Exception as e:
            logger.error(f"Failed to load financial tracking data: {e}")
            return FinancialTrackingData(
                records=[],
                loaded_at=datetime.now(),
                source_spreadsheet_id=self.spreadsheet_id,
            )

    def calculate_derived_metrics(self, record: MonthlyFinancialData) -> MonthlyFinancialData:
        """Calculate derived metrics for a record.

        Updates the *_Calculated fields based on actual values.
        """
        # Total Sales = Medical + Beauty
        record.ts_calculated = record.medical_products_sales_actual + record.beauty_products_sales_actual

        # Total Investment = All sources
        record.ti_calculated = (
            record.founder_investment_actual
            + record.cofounder_investment_actual
            + record.investor_investment_actual
            + record.importer_investment_actual
        )

        # Total Expenses = All categories
        record.te_calculated = (
            record.operating_expenses_actual
            + record.marketing_sales_expenses_actual
            + record.product_costs_actual
            + record.salaries_wages_actual
            + record.delivery_logistics_actual
            + record.regulatory_compliance_actual
            + record.other_expenses_actual
        )

        # Doctor Prizes = Gifts + Research Products
        record.pupmpd_calculated = record.doctor_prizes_gifts_actual + record.doctor_prizes_research_products_actual

        # Remaining Borrowed Product
        record.rbpp_calculated = record.tbpc_actual - record.tbpp_actual

        # Total Capital = Investment + Profit - Prizes - Borrowed Paid
        # Note: TP is already Net Profit (TS - TE)
        record.tcmc_calculated = record.ti_calculated + record.tp_actual - record.pupmpd_calculated - record.tbpp_actual

        # ROI (Payment Received Rate) = Money Received / Sales Orders * 100
        if record.mspm > 0:
            record.roi_percent_calculated = (record.tpmrp / record.mspm) * 100

        # Profit Margin = Net Profit / Sales * 100
        if record.ts_calculated > 0:
            record.profit_margin_percent_calculated = (record.tp_actual / record.ts_calculated) * 100

        # Client Acquisition Cost = Total Expenses / Clients
        if record.tnc_actual > 0:
            record.cac_calculated = record.te_calculated / record.tnc_actual

        # Debt Ratio = Remaining Borrowed / Total Capital * 100
        if record.tcmc_calculated > 0:
            record.debt_ratio_percent_calculated = (record.rbpp_calculated / record.tcmc_calculated) * 100

        # Collection Efficiency = Money Received / Total Sales Orders * 100
        total_sales_orders = record.tpmrp + record.trpmrp
        if total_sales_orders > 0:
            record.collection_efficiency_percent_calculated = (record.tpmrp / total_sales_orders) * 100

        return record

    @property
    def data(self) -> FinancialTrackingData | None:
        """Get the loaded data (None if not loaded yet)."""
        return self._data
