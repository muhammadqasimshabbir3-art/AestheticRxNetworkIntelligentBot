"""Main task entry point for AestheticRxNetworkIntelligentBot.

Works with both:
- Robocorp (via @task decorator)
- Local execution (via __main__)

Workflow:
1. Load credentials from environment variables
2. Connect to AestheticRxNetwork API (handles OTP via Gmail)
3. Check for existing order file in Google Drive
4. Fetch ALL orders from API (all statuses)
5. Create new spreadsheet with datestamp naming
6. Write ALL orders to Google Sheets
"""

import json
import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Add src to path for module imports
src_path = project_root / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from config import CONFIG  # noqa: E402
from libraries.logger import log_build_info, logger, reconfigure_log_level  # noqa: E402
from libraries.workitems import INPUTS  # noqa: E402
from workflow.process import Process  # noqa: E402

# Try to import robocorp task decorator, fallback for local runs
try:
    from robocorp.tasks import task as robocorp_task

    HAS_ROBOCORP = True
except ImportError:
    HAS_ROBOCORP = False

    # Create a no-op decorator for local runs
    def robocorp_task(func):
        return func


def initialize_process() -> Process:
    """Initialize the process.

    This performs:
    - Environment credential loading
    - Gmail verification (for OTP)
    - AestheticRxNetwork API authentication
    """
    try:
        return Process()
    except Exception as e:
        logger.error(f"Failed to initialize process: {e}")
        raise


def execute_process(process: Process) -> None:
    """Execute the main process workflow.

    This will run (in order):
    1. UpdatePaymentProcess (if RUN_UPDATE_PAYMENT_PROCESS is True)
       - Updates specified payment IDs to 'paid' status in Google Sheet
    2. OrderManagementProcess (if RUN_ORDER_MANAGE_SYSTEM is True)
       - Fetches pending orders from API
       - Compares with Google Sheet
       - Updates API status for matched orders
       - Creates output spreadsheet
    """
    # Process.start() handles both workflows with proper ordering
    process.start()

    # Log results
    logger.info("=" * 60)
    logger.info("📊 Results Summary:")

    # Update Payment results
    if INPUTS.RUN_UPDATE_PAYMENT_PROCESS:
        logger.info(f"  Payments updated to 'paid': {process.update_payment_count}")

    # Order Management results
    if INPUTS.RUN_ORDER_MANAGE_SYSTEM:
        logger.info(f"  Total orders processed: {len(process.orders)}")
        if process.spreadsheet_id:
            logger.info(f"  Spreadsheet ID: {process.spreadsheet_id}")
            logger.info(f"  URL: {process.get_spreadsheet_url()}")

    logger.info("=" * 60)
    logger.info("Automation completed successfully")


def finalize_process(process: Process | None = None) -> None:
    """Finalize the process with proper cleanup."""
    if process:
        process.finish()
        logger.info("Process finalized successfully")
    else:
        logger.info("No process to finalize")


def log_run_configuration() -> None:
    """Log the current run configuration settings."""
    if INPUTS.DEV_SAFE_MODE:
        logger.info("🛡️  Safe-run mode is enabled.")
    else:
        logger.info("⚠️  Safe-run mode is disabled. This run has consequences.")

    # Log Google configuration
    logger.info("=" * 60)
    logger.info("Configuration:")
    logger.info(f"  📁 Google Drive Folder: {CONFIG.GOOGLE_DRIVE_FOLDER_ID}")
    logger.info(f"  📊 Google Spreadsheet: {CONFIG.GOOGLE_SPREADSHEET_ID}")
    logger.info(f"  📝 Spreadsheet Prefix: {CONFIG.SPREADSHEET_NAME_PREFIX}")
    logger.info("")
    logger.info("Workflow Inputs:")
    logger.info(f"  🔄 RUN_UPDATE_PAYMENT_PROCESS: {INPUTS.RUN_UPDATE_PAYMENT_PROCESS}")
    logger.info(f"  📋 PAYMENT_IDS_LIST: {INPUTS.PAYMENT_IDS_LIST}")
    logger.info(f"  🔄 RUN_ORDER_MANAGE_SYSTEM: {INPUTS.RUN_ORDER_MANAGE_SYSTEM}")
    logger.info("=" * 60)


@robocorp_task
def aestheticrxnetwork_automation_task() -> None:
    """Main task entry point for AestheticRxNetworkIntelligentBot.

    This is the Robocorp task entry point. It orchestrates:
        1. Initialize the process (env credentials, Gmail verification, AestheticRxNetwork login)
        2. Execute the workflow (check existing files, fetch orders, create spreadsheet)
        3. Handle any errors appropriately
        4. Ensure proper cleanup
    """
    # Setup logging
    try:
        reconfigure_log_level(INPUTS.LOG_LEVEL)
        message = log_build_info()
        logger.info(message)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to log build info: {e}")

    logger.info("Starting AestheticRxNetworkIntelligentBot")
    log_run_configuration()

    process = None

    try:
        # 1° - Initialize (env credentials, Gmail, AestheticRxNetwork API)
        process = initialize_process()

        # 2° - Execute (check files, fetch orders, create spreadsheet)
        execute_process(process)

    except Exception as e:
        logger.error(f"Error during execution: {e}")
        raise

    finally:
        # 3° - Cleanup
        if process:
            finalize_process(process)

    logger.info("AestheticRxNetworkIntelligentBot task complete")


# For local execution
if __name__ == "__main__":
    aestheticrxnetwork_automation_task()
