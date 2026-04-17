"""Financial Tracking Google Sheet Setup.

This module creates a new Google Sheet with the 95-column structure
from the Q_Financial_Tracking.csv template for manual business KPI entry.
"""

from datetime import datetime

from config import CONFIG
from libraries.google_drive import GoogleDriveAPI
from libraries.google_sheets import GoogleSheetsAPI
from libraries.logger import logger

# All 95 column headers from Q_Financial_Tracking.csv
FINANCIAL_TRACKING_HEADERS = [
    "Year",
    "Month",
    "Timestamp",
    "Record_Type",
    "Notes",
    # Sales
    "TS_Target",
    "Medical_Products_Sales_Target",
    "Medical_Products_Sales_Actual",
    "Beauty_Products_Sales_Target",
    "Beauty_Products_Sales_Actual",
    "TS_Calculated",
    # Investment
    "TI_Target",
    "TI_Calculated",
    "Founder_Investment_Target",
    "Founder_Investment_Actual",
    "CoFounder_Investment_Target",
    "CoFounder_Investment_Actual",
    "Investor_Investment_Target",
    "Investor_Investment_Actual",
    "Importer_Investment_Target",
    "Importer_Investment_Actual",
    # Profit & Clients
    "TP_Target",
    "TP_Actual",
    "TNC_Target",
    "TNC_Actual",
    # Contributions
    "CFC_Target",
    "CFC_Actual",
    "PFC_Target",
    "PFC_Actual",
    # Borrowed Products
    "TBPC_Target",
    "TBPC_Actual",
    "TBPP_Target",
    "TBPP_Actual",
    "RBPP_Calculated",
    # Expenses
    "TE_Target",
    "Operating_Expenses_Target",
    "Operating_Expenses_Actual",
    "Marketing_Sales_Expenses_Target",
    "Marketing_Sales_Expenses_Actual",
    "Product_Costs_Target",
    "Product_Costs_Actual",
    "Salaries_Wages_Target",
    "Salaries_Wages_Actual",
    "Delivery_Logistics_Target",
    "Delivery_Logistics_Actual",
    "Regulatory_Compliance_Target",
    "Regulatory_Compliance_Actual",
    "Other_Expenses_Target",
    "Other_Expenses_Actual",
    "TE_Calculated",
    # Doctor Prizes
    "PUPMPD_Target",
    "Doctor_Prizes_Gifts_Target",
    "Doctor_Prizes_Gifts_Actual",
    "Doctor_Prizes_Research_Products_Target",
    "Doctor_Prizes_Research_Products_Actual",
    "PUPMPD_Calculated",
    # Capital
    "TCMC_Target",
    "TCMC_Calculated",
    "TCMCCI_Target",
    "TCMCCI_Actual",
    # Calculated Metrics
    "TNPPM_Calculated",
    "ROI_Percent_Calculated",
    "Profit_Margin_Percent_Calculated",
    "CAC_Calculated",
    "Debt_Ratio_Percent_Calculated",
    "Collection_Efficiency_Percent_Calculated",
    "Sales_Growth_Percent_Calculated",
    "Client_Growth_Percent_Calculated",
    # Previous Month Data
    "NCPMT",
    "NCPMD",
    "TIPM",
    "Founder_Investment_PM",
    "CoFounder_Investment_PM",
    "Investor_Investment_PM",
    "Importer_Investment_PM",
    "CFCPM",
    "PFCPM",
    "TBPCPM",
    "TBPPPM",
    "TPPM",
    "TNPPM",
    "TPMRP",
    "TRPMRP",
    "MSPM",
    "RPUPMPDPM",
    "TEPM",
    "Operating_Expenses_PM",
    "Marketing_Sales_Expenses_PM",
    "Product_Costs_PM",
    "Salaries_Wages_PM",
    "Delivery_Logistics_PM",
    "Regulatory_Compliance_PM",
    "Other_Expenses_PM",
    # Special
    "Legislation_Website_Launch_Status",
    "Special_Notes",
]

# Month names
MONTHS = [
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
]

# Record types per month
RECORD_TYPES = ["Target", "Update", "Month_End"]


def get_month_end_day(year: int, month: int) -> int:
    """Get the last day of a month."""
    if month == 12:
        return 31
    next_month = datetime(year, month + 1, 1)
    last_day = (next_month - datetime.timedelta(days=1)).day
    return last_day


def generate_row_data(year: int, month_idx: int, record_type: str) -> list:
    """Generate a row of data for a given year/month/record_type.

    Args:
        year: The year (e.g., 2025)
        month_idx: 0-based month index (0=January)
        record_type: One of "Target", "Update", "Month_End"

    Returns:
        List of values for the row
    """
    month_name = MONTHS[month_idx]
    month_num = month_idx + 1

    # Determine timestamp based on record type
    if record_type == "Target":
        timestamp = f"{year}-{month_num:02d}-01 00:00:00"
    elif record_type == "Update":
        timestamp = f"{year}-{month_num:02d}-15 12:00:00"
    else:  # Month_End
        # Get last day of month
        if month_num == 12:
            last_day = 31
        elif month_num in [4, 6, 9, 11]:
            last_day = 30
        elif month_num == 2:
            # Leap year check
            if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0):
                last_day = 29
            else:
                last_day = 28
        else:
            last_day = 31
        timestamp = f"{year}-{month_num:02d}-{last_day:02d} 23:59:59"

    # Create row with Year, Month, Timestamp, Record_Type, and empty values for rest
    row = [year, month_name, timestamp, record_type]
    # Add empty values for remaining 91 columns
    row.extend([""] * (len(FINANCIAL_TRACKING_HEADERS) - 4))

    return row


def create_financial_tracking_sheet(
    sheets_api: GoogleSheetsAPI | None = None,
    years: list[int] | None = None,
) -> str:
    """Create a new Financial Tracking Google Sheet.

    Args:
        sheets_api: Optional GoogleSheetsAPI instance (creates new if not provided)
        years: Years to include (default: 2025-2028)

    Returns:
        str: The spreadsheet ID of the created sheet
    """
    logger.info("=" * 60)
    logger.info("Creating Financial Tracking Google Sheet")
    logger.info("=" * 60)

    if sheets_api is None:
        sheets_api = GoogleSheetsAPI()

    if years is None:
        years = [2025, 2026, 2027, 2028]

    # Create the spreadsheet using Drive API (works in shared folders)
    title = f"Q_Financial_Tracking_{datetime.now().strftime('%Y%m%d')}"

    try:
        # Try using Google Drive API to create spreadsheet directly in shared folder
        drive_api = GoogleDriveAPI()
        spreadsheet_id = drive_api.create_file(
            name=title,
            mime_type="application/vnd.google-apps.spreadsheet",
            parent_id=CONFIG.GOOGLE_DRIVE_FOLDER_ID,
        )
        logger.info(f"✓ Created spreadsheet via Drive API: {title}")
    except Exception as drive_error:
        logger.warning(f"Drive API method failed: {drive_error}")
        logger.info("Trying Sheets API method...")
        # Fallback to Sheets API
        spreadsheet_id = sheets_api.create_spreadsheet(
            title=title,
            sheet_names=["Financial_Data"],
            folder_id=CONFIG.GOOGLE_DRIVE_FOLDER_ID,
        )
        logger.info(f"✓ Created spreadsheet via Sheets API: {title}")

    logger.info(f"  ID: {spreadsheet_id}")

    # Get the actual sheet name (might be "Sheet1" if created via Drive API)
    try:
        sheet_info = sheets_api.get_sheet_info(spreadsheet_id)
        if sheet_info and len(sheet_info) > 0:
            sheet_name = sheet_info[0].get("title", "Sheet1")
            logger.info(f"  Sheet name: {sheet_name}")
        else:
            sheet_name = "Sheet1"
    except Exception:
        sheet_name = "Sheet1"

    # Rename sheet to Financial_Data if needed
    if sheet_name != "Financial_Data":
        try:
            sheets_api.rename_sheet(
                spreadsheet_id=spreadsheet_id,
                sheet_id=0,
                new_name="Financial_Data",
            )
            sheet_name = "Financial_Data"
            logger.info(f"  Renamed sheet to: {sheet_name}")
        except Exception as rename_error:
            logger.warning(f"  Could not rename sheet: {rename_error}")

    # Prepare data: headers + rows for each year/month/record_type
    data = [FINANCIAL_TRACKING_HEADERS]

    for year in years:
        for month_idx in range(12):
            for record_type in RECORD_TYPES:
                row = generate_row_data(year, month_idx, record_type)
                data.append(row)

    total_rows = len(data) - 1  # Exclude header
    logger.info(f"  Preparing {total_rows} rows ({len(years)} years × 12 months × 3 record types)")

    # Write data to sheet
    sheets_api.write_data(
        spreadsheet_id=spreadsheet_id,
        data=data,
        sheet_name=sheet_name,
        start_cell="A1",
    )
    logger.info("✓ Written all data to sheet")

    # Format the header row
    sheets_api.format_header_row(
        spreadsheet_id=spreadsheet_id,
        sheet_id=0,
        bold=True,
        background_color=(0.2, 0.4, 0.6),  # Blue header
    )
    logger.info("✓ Formatted header row")

    # Freeze the header row
    try:
        sheets_api.freeze_rows(
            spreadsheet_id=spreadsheet_id,
            sheet_id=0,
            num_rows=1,
        )
        logger.info("✓ Frozen header row")
    except AttributeError:
        # Method might not exist
        logger.info("  (Freeze rows method not available)")

    # Auto-resize columns (first 10 columns for better visibility)
    try:
        sheets_api.auto_resize_columns(
            spreadsheet_id=spreadsheet_id,
            sheet_id=0,
            start_column=0,
            end_column=10,
        )
        logger.info("✓ Auto-resized first 10 columns")
    except Exception as e:
        logger.warning(f"  Could not auto-resize columns: {e}")

    spreadsheet_url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}"

    logger.info("")
    logger.info("=" * 60)
    logger.info("✅ FINANCIAL TRACKING SHEET CREATED!")
    logger.info("=" * 60)
    logger.info(f"Spreadsheet ID: {spreadsheet_id}")
    logger.info(f"URL: {spreadsheet_url}")
    logger.info("")
    logger.info("📝 Next steps:")
    logger.info("1. Update CONFIG.FINANCIAL_TRACKING_SPREADSHEET_ID in src/config.py")
    logger.info(f"   Set it to: {spreadsheet_id}")
    logger.info("2. Open the spreadsheet and start entering your financial data")
    logger.info("3. Run the Business Report to include financial KPIs")
    logger.info("")

    return spreadsheet_id


def setup_financial_tracking() -> dict:
    """One-time setup function to create the Financial Tracking sheet.

    Returns:
        dict with spreadsheet_id and url
    """
    try:
        spreadsheet_id = create_financial_tracking_sheet()
        return {
            "spreadsheet_id": spreadsheet_id,
            "url": f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}",
            "headers_count": len(FINANCIAL_TRACKING_HEADERS),
        }
    except Exception as e:
        logger.error(f"Failed to create spreadsheet: {e}")
        logger.info("")
        logger.info("=" * 60)
        logger.info("⚠️ MANUAL SETUP REQUIRED")
        logger.info("=" * 60)
        logger.info("The service account cannot create new spreadsheets.")
        logger.info("Please create the spreadsheet manually:")
        logger.info("")
        logger.info("1. Open Google Sheets: https://sheets.google.com")
        logger.info("2. Create a new blank spreadsheet")
        logger.info("3. Name it: Q_Financial_Tracking")
        logger.info("4. Share it with: googledrive@qwebsite.iam.gserviceaccount.com")
        logger.info("   (Give Editor access)")
        logger.info("5. Copy the spreadsheet ID from the URL")
        logger.info("   (The ID is in: docs.google.com/spreadsheets/d/[ID_HERE]/edit)")
        logger.info("6. Update src/config.py:")
        logger.info("   FINANCIAL_TRACKING_SPREADSHEET_ID = 'YOUR_ID_HERE'")
        logger.info("")
        logger.info("After sharing, run populate_financial_sheet(spreadsheet_id)")
        logger.info("to populate it with headers and template rows.")
        logger.info("=" * 60)

        return {
            "spreadsheet_id": None,
            "url": None,
            "headers_count": len(FINANCIAL_TRACKING_HEADERS),
            "manual_setup_required": True,
        }


def populate_financial_sheet(
    spreadsheet_id: str,
    years: list[int] | None = None,
) -> bool:
    """Populate an existing Financial Tracking Google Sheet with headers and template rows.

    Use this after manually creating a spreadsheet and sharing it with the service account.

    Args:
        spreadsheet_id: The ID of the spreadsheet to populate
        years: Years to include (default: 2025-2028)

    Returns:
        bool: True if successful
    """
    logger.info("=" * 60)
    logger.info("Populating Financial Tracking Sheet")
    logger.info("=" * 60)

    if years is None:
        years = [2025, 2026, 2027, 2028]

    sheets_api = GoogleSheetsAPI()

    # Get the actual sheet name
    try:
        sheet_info = sheets_api.get_sheet_info(spreadsheet_id)
        if sheet_info and len(sheet_info) > 0:
            sheet_name = sheet_info[0].get("title", "Sheet1")
            logger.info(f"Sheet name: {sheet_name}")
        else:
            sheet_name = "Sheet1"
    except Exception:
        sheet_name = "Sheet1"

    # Prepare data: headers + rows for each year/month/record_type
    data = [FINANCIAL_TRACKING_HEADERS]

    for year in years:
        for month_idx in range(12):
            for record_type in RECORD_TYPES:
                row = generate_row_data(year, month_idx, record_type)
                data.append(row)

    total_rows = len(data) - 1
    logger.info(f"Preparing {total_rows} rows ({len(years)} years × 12 months × 3 record types)")

    # Write data to sheet
    sheets_api.write_data(
        spreadsheet_id=spreadsheet_id,
        data=data,
        sheet_name=sheet_name,
        start_cell="A1",
    )
    logger.info("✓ Written all data to sheet")

    # Format the header row
    sheets_api.format_header_row(
        spreadsheet_id=spreadsheet_id,
        sheet_id=0,
        bold=True,
        background_color=(0.2, 0.4, 0.6),
    )
    logger.info("✓ Formatted header row")

    spreadsheet_url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}"
    logger.info("")
    logger.info("=" * 60)
    logger.info("✅ FINANCIAL TRACKING SHEET POPULATED!")
    logger.info("=" * 60)
    logger.info(f"URL: {spreadsheet_url}")
    logger.info("")
    logger.info("📝 Next steps:")
    logger.info(f"1. Update CONFIG.FINANCIAL_TRACKING_SPREADSHEET_ID = '{spreadsheet_id}'")
    logger.info("2. Open the spreadsheet and start entering your financial data")
    logger.info("")

    return True


def generate_mock_data_row(year: int, month_idx: int, record_type: str) -> list:
    """Generate a row with realistic mock data for testing.

    Args:
        year: The year (e.g., 2025)
        month_idx: 0-based month index (0=January)
        record_type: One of "Target", "Update", "Month_End"

    Returns:
        List of values for the row with mock data
    """
    import random

    month_name = MONTHS[month_idx]
    month_num = month_idx + 1

    # Determine timestamp
    if record_type == "Target":
        timestamp = f"{year}-{month_num:02d}-01 00:00:00"
    elif record_type == "Update":
        timestamp = f"{year}-{month_num:02d}-15 12:00:00"
    else:
        if month_num == 12:
            last_day = 31
        elif month_num in [4, 6, 9, 11]:
            last_day = 30
        elif month_num == 2:
            last_day = 29 if (year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)) else 28
        else:
            last_day = 31
        timestamp = f"{year}-{month_num:02d}-{last_day:02d} 23:59:59"

    # Only generate actual data for Month_End records
    if record_type != "Month_End":
        row = [year, month_name, timestamp, record_type]
        row.extend([""] * (len(FINANCIAL_TRACKING_HEADERS) - 4))
        return row

    # Generate realistic mock data for Month_End
    # Base values that grow over time
    month_factor = (year - 2025) * 12 + month_num
    growth_rate = 1 + (month_factor * 0.05)  # 5% growth per month
    variance = random.uniform(0.9, 1.1)

    # Sales (PKR - Pakistani Rupees)
    medical_sales_target = round(500000 * growth_rate, 2)
    medical_sales_actual = round(medical_sales_target * variance * random.uniform(0.85, 1.15), 2)
    beauty_sales_target = round(300000 * growth_rate, 2)
    beauty_sales_actual = round(beauty_sales_target * variance * random.uniform(0.8, 1.2), 2)
    ts_calculated = round(medical_sales_actual + beauty_sales_actual, 2)

    # Investment
    founder_inv_target = round(100000 * (1 + month_factor * 0.02), 2)
    founder_inv_actual = round(founder_inv_target * random.uniform(0.9, 1.1), 2) if month_factor <= 6 else 0
    cofounder_inv_target = round(50000 * (1 + month_factor * 0.02), 2)
    cofounder_inv_actual = round(cofounder_inv_target * random.uniform(0.9, 1.1), 2) if month_factor <= 6 else 0
    investor_inv_target = round(200000 * (1 + month_factor * 0.03), 2) if month_factor >= 3 else 0
    investor_inv_actual = round(investor_inv_target * random.uniform(0.8, 1.0), 2)
    importer_inv_target = round(150000 * (1 + month_factor * 0.02), 2) if month_factor >= 6 else 0
    importer_inv_actual = round(importer_inv_target * random.uniform(0.7, 1.0), 2)
    ti_calculated = round(founder_inv_actual + cofounder_inv_actual + investor_inv_actual + importer_inv_actual, 2)

    # Expenses
    operating_exp_target = round(80000 * growth_rate, 2)
    operating_exp_actual = round(operating_exp_target * variance * random.uniform(0.9, 1.1), 2)
    marketing_exp_target = round(100000 * growth_rate, 2)
    marketing_exp_actual = round(marketing_exp_target * variance * random.uniform(0.8, 1.2), 2)
    product_costs_target = round(ts_calculated * 0.35, 2)  # ~35% COGS
    product_costs_actual = round(product_costs_target * variance, 2)
    salaries_target = round(150000 * (1 + month_factor * 0.03), 2)
    salaries_actual = round(salaries_target * random.uniform(0.98, 1.02), 2)
    delivery_target = round(ts_calculated * 0.05, 2)  # ~5% of sales
    delivery_actual = round(delivery_target * variance, 2)
    regulatory_target = round(20000 * (1 + month_factor * 0.01), 2)
    regulatory_actual = round(regulatory_target * variance, 2)
    other_exp_target = round(30000 * growth_rate, 2)
    other_exp_actual = round(other_exp_target * variance * random.uniform(0.7, 1.3), 2)
    te_calculated = round(
        operating_exp_actual + marketing_exp_actual + product_costs_actual +
        salaries_actual + delivery_actual + regulatory_actual + other_exp_actual, 2
    )

    # Profit
    tp_target = round(ts_calculated - te_calculated + 50000, 2)  # Target slightly higher
    tp_actual = round(ts_calculated - te_calculated, 2)

    # Clients
    tnc_target = round(10 + month_factor * 2, 0)
    tnc_actual = round(tnc_target * random.uniform(0.8, 1.2), 0)

    # Contributions
    cfc_target = round(50000 * (1 + month_factor * 0.01), 2)
    cfc_actual = round(cfc_target * random.uniform(0.9, 1.0), 2) if month_factor % 3 == 0 else 0
    pfc_target = round(30000 * (1 + month_factor * 0.01), 2)
    pfc_actual = round(pfc_target * random.uniform(0.9, 1.0), 2) if month_factor % 2 == 0 else 0

    # Borrowed Products
    tbpc_target = round(100000 * growth_rate, 2)
    tbpc_actual = round(tbpc_target * variance, 2)
    tbpp_target = round(tbpc_target * 0.8, 2)  # Target 80% payment
    tbpp_actual = round(tbpp_target * random.uniform(0.7, 1.0), 2)
    rbpp_calculated = round(tbpc_actual - tbpp_actual, 2)

    # Doctor Prizes
    prizes_gifts_target = round(20000 * growth_rate, 2)
    prizes_gifts_actual = round(prizes_gifts_target * variance, 2)
    prizes_research_target = round(30000 * growth_rate, 2)
    prizes_research_actual = round(prizes_research_target * variance, 2)
    pupmpd_calculated = round(prizes_gifts_actual + prizes_research_actual, 2)

    # Capital
    tcmc_target = round(ti_calculated + tp_actual, 2)
    tcmc_calculated = round(ti_calculated + tp_actual - pupmpd_calculated - tbpp_actual, 2)
    tcmcci_target = round(tcmc_calculated * 0.5, 2)
    tcmcci_actual = round(tcmcci_target * random.uniform(0.8, 1.0), 2)

    # Calculated Metrics
    tnppm_calculated = round(tp_actual, 2)
    roi_percent = round(((tp_actual - ti_calculated) / ti_calculated * 100) if ti_calculated > 0 else 0, 2)
    profit_margin = round((tp_actual / ts_calculated * 100) if ts_calculated > 0 else 0, 2)
    cac_calculated = round(te_calculated / tnc_actual if tnc_actual > 0 else 0, 2)
    debt_ratio = round((rbpp_calculated / tcmc_calculated * 100) if tcmc_calculated > 0 else 0, 2)
    collection_eff = round(random.uniform(85, 98), 2)
    sales_growth = round((month_factor - 1) * 5 + random.uniform(-2, 5), 2)  # ~5% monthly
    client_growth = round((month_factor - 1) * 3 + random.uniform(-1, 3), 2)  # ~3% monthly

    # Previous Month Data (simplified - use previous month's actuals)
    ncpmt = round(tnc_target * 0.95, 0)
    ncpmd = round(tnc_actual * 0.95, 0)
    tipm = round(ti_calculated * 0.95, 2)
    founder_inv_pm = round(founder_inv_actual * 0.95, 2)
    cofounder_inv_pm = round(cofounder_inv_actual * 0.95, 2)
    investor_inv_pm = round(investor_inv_actual * 0.95, 2)
    importer_inv_pm = round(importer_inv_actual * 0.95, 2)
    cfcpm = round(cfc_actual * 0.9, 2)
    pfcpm = round(pfc_actual * 0.9, 2)
    tbpcpm = round(tbpc_actual * 0.95, 2)
    tbpppm = round(tbpp_actual * 0.95, 2)
    tppm = round(tp_actual * 0.95, 2)
    tnppm_pm = round(tnppm_calculated * 0.95, 2)
    tpmrp = round(ts_calculated * 0.9, 2)  # 90% payment retrieved
    trpmrp = round(ts_calculated * 0.05, 2)  # 5% remaining
    mspm = round(ts_calculated * 0.95, 2)
    rpupmpdpm = round(pupmpd_calculated * 0.9, 2)
    tepm = round(te_calculated * 0.95, 2)
    operating_pm = round(operating_exp_actual * 0.95, 2)
    marketing_pm = round(marketing_exp_actual * 0.95, 2)
    product_costs_pm = round(product_costs_actual * 0.95, 2)
    salaries_pm = round(salaries_actual * 0.95, 2)
    delivery_pm = round(delivery_actual * 0.95, 2)
    regulatory_pm = round(regulatory_actual * 0.95, 2)
    other_pm = round(other_exp_actual * 0.95, 2)

    # Special
    legislation_status = "Active" if month_factor >= 6 else "Pending"
    special_notes = f"Mock data for {month_name} {year}"

    # Build the row in correct column order
    row = [
        year, month_name, timestamp, record_type, special_notes,  # Basic info (5)
        # Sales (6)
        ts_calculated,  # TS_Target (using calculated as target for simplicity)
        medical_sales_target, medical_sales_actual,
        beauty_sales_target, beauty_sales_actual,
        ts_calculated,
        # Investment (10)
        ti_calculated,  # TI_Target
        ti_calculated,  # TI_Calculated
        founder_inv_target, founder_inv_actual,
        cofounder_inv_target, cofounder_inv_actual,
        investor_inv_target, investor_inv_actual,
        importer_inv_target, importer_inv_actual,
        # Profit & Clients (4)
        tp_target, tp_actual,
        tnc_target, tnc_actual,
        # Contributions (4)
        cfc_target, cfc_actual,
        pfc_target, pfc_actual,
        # Borrowed Products (5)
        tbpc_target, tbpc_actual,
        tbpp_target, tbpp_actual,
        rbpp_calculated,
        # Expenses (15)
        te_calculated,  # TE_Target
        operating_exp_target, operating_exp_actual,
        marketing_exp_target, marketing_exp_actual,
        product_costs_target, product_costs_actual,
        salaries_target, salaries_actual,
        delivery_target, delivery_actual,
        regulatory_target, regulatory_actual,
        other_exp_target, other_exp_actual,
        te_calculated,
        # Doctor Prizes (6)
        pupmpd_calculated,  # PUPMPD_Target
        prizes_gifts_target, prizes_gifts_actual,
        prizes_research_target, prizes_research_actual,
        pupmpd_calculated,
        # Capital (4)
        tcmc_target, tcmc_calculated,
        tcmcci_target, tcmcci_actual,
        # Calculated Metrics (8)
        tnppm_calculated,
        roi_percent,
        profit_margin,
        cac_calculated,
        debt_ratio,
        collection_eff,
        sales_growth,
        client_growth,
        # Previous Month Data (20)
        ncpmt, ncpmd,
        tipm,
        founder_inv_pm, cofounder_inv_pm, investor_inv_pm, importer_inv_pm,
        cfcpm, pfcpm,
        tbpcpm, tbpppm,
        tppm, tnppm_pm,
        tpmrp, trpmrp,
        mspm,
        rpupmpdpm,
        tepm,
        operating_pm, marketing_pm, product_costs_pm, salaries_pm, delivery_pm, regulatory_pm, other_pm,
        # Special (2)
        legislation_status, special_notes,
    ]

    return row


def populate_with_mock_data(
    spreadsheet_id: str,
    years: list[int] | None = None,
) -> bool:
    """Populate a Financial Tracking Google Sheet with mock data for testing.

    Args:
        spreadsheet_id: The ID of the spreadsheet to populate
        years: Years to include (default: 2025-2026)

    Returns:
        bool: True if successful
    """
    logger.info("=" * 60)
    logger.info("Populating Financial Tracking Sheet with MOCK DATA")
    logger.info("=" * 60)

    if years is None:
        years = [2025, 2026]

    sheets_api = GoogleSheetsAPI()

    # Get the actual sheet name
    try:
        sheet_info = sheets_api.get_sheet_info(spreadsheet_id)
        if sheet_info and "sheets" in sheet_info:
            sheet_name = sheet_info["sheets"][0]["properties"]["title"]
            logger.info(f"Sheet name: {sheet_name}")
        else:
            sheet_name = "Sheet1"
    except Exception:
        sheet_name = "Sheet1"

    # Prepare data: headers + rows with mock data
    data = [FINANCIAL_TRACKING_HEADERS]

    for year in years:
        for month_idx in range(12):
            for record_type in RECORD_TYPES:
                row = generate_mock_data_row(year, month_idx, record_type)
                data.append(row)

    total_rows = len(data) - 1
    logger.info(f"Preparing {total_rows} rows with mock data")

    # Clear existing data first
    try:
        sheets_api.clear_sheet(spreadsheet_id, f"{sheet_name}!A:ZZ")
        logger.info("✓ Cleared existing data")
    except Exception as e:
        logger.warning(f"Could not clear sheet: {e}")

    # Write data to sheet
    sheets_api.write_data(
        spreadsheet_id=spreadsheet_id,
        data=data,
        sheet_name=sheet_name,
        start_cell="A1",
    )
    logger.info("✓ Written mock data to sheet")

    # Format the header row
    sheets_api.format_header_row(
        spreadsheet_id=spreadsheet_id,
        sheet_id=0,
        bold=True,
        background_color=(0.2, 0.4, 0.6),
    )
    logger.info("✓ Formatted header row")

    spreadsheet_url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}"
    logger.info("")
    logger.info("=" * 60)
    logger.info("✅ MOCK DATA POPULATED!")
    logger.info("=" * 60)
    logger.info(f"URL: {spreadsheet_url}")
    logger.info(f"Years: {years}")
    logger.info(f"Total rows: {total_rows}")
    logger.info("")

    return True


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Financial Tracking Sheet Setup")
    parser.add_argument(
        "--populate",
        type=str,
        help="Spreadsheet ID to populate (use after manual creation)",
    )
    parser.add_argument(
        "--mock",
        type=str,
        help="Spreadsheet ID to populate with mock data for testing",
    )
    parser.add_argument(
        "--years",
        type=str,
        default="2025,2026",
        help="Comma-separated years to include (default: 2025,2026)",
    )
    args = parser.parse_args()

    years = [int(y.strip()) for y in args.years.split(",")]

    if args.mock:
        # Populate with mock data
        success = populate_with_mock_data(args.mock, years)
        if success:
            print("\n✅ Mock data populated successfully!")
            print(f"Update CONFIG.FINANCIAL_TRACKING_SPREADSHEET_ID = '{args.mock}'")
    elif args.populate:
        # Populate existing spreadsheet
        success = populate_financial_sheet(args.populate, years)
        if success:
            print("\n✅ Spreadsheet populated successfully!")
            print(f"Update CONFIG.FINANCIAL_TRACKING_SPREADSHEET_ID = '{args.populate}'")
    else:
        # Try to create new spreadsheet
        result = setup_financial_tracking()
        if result.get("manual_setup_required"):
            print("\n⚠️ Manual setup required - see instructions above")
        else:
            print(f"\n✅ Spreadsheet ID: {result['spreadsheet_id']}")
            print(f"URL: {result['url']}")
            print(f"Total columns: {result['headers_count']}")

