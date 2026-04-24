"""Module providing functionality related to work items and variables.

This module handles input loading from:
1. Robocorp Work Items (when running in Robocorp Cloud/Assistant)
2. Environment variables (for local development)
3. Default values (fallback)

Priority order: Robocorp Work Items > Environment Variables > Defaults
"""

import os
import uuid
from pprint import pformat
from typing import Any

from pydantic import BaseModel, Field

from libraries.logger import logger


class Inputs(BaseModel):
    """Input parameters for the automation run.

    These inputs can be provided via:
    - Robocorp Work Items JSON (payload)
    - Environment variables
    - Default values defined here
    """

    # ============================================
    # RUNTIME CONFIGURATION
    # ============================================
    # IN_PRODUCTION: Flag that indicates which environment the workflow is running in
    IN_PRODUCTION: bool = False

    # DEV_SAFE_MODE: Flag indicating whether the bot should run in safe mode
    DEV_SAFE_MODE: bool = True

    # LOG_LEVEL: Logging level for the application
    LOG_LEVEL: str = "INFO"

    # RUN_ID: Unique identifier for this run
    RUN_ID: str = ""

    # ============================================
    # ORDER MANAGEMENT INPUTS
    # ============================================
    # RUN_ORDER_MANAGE_SYSTEM: Flag to enable/disable order management system workflow
    RUN_ORDER_MANAGE_SYSTEM: bool = True

    # ============================================
    # UPDATE PAYMENT SHEET INPUTS
    # ============================================
    # RUN_UPDATE_PAYMENT_PROCESS: Flag to enable/disable update payment process
    RUN_UPDATE_PAYMENT_PROCESS: bool = False

    # PAYMENT_IDS_LIST: List of payment IDs to update status to 'paid'
    PAYMENT_IDS_LIST: list[str] = Field(default_factory=list)

    # ============================================
    # USER MANAGEMENT INPUTS
    # ============================================
    # RUN_USER_MANAGEMENT_PROCESS: Flag to enable/disable user management process
    RUN_USER_MANAGEMENT_PROCESS: bool = True

    # ============================================
    # ADVERTISEMENT MANAGEMENT INPUTS
    # ============================================
    # RUN_ADVERTISEMENT_MANAGEMENT_PROCESS: Flag to enable/disable advertisement management
    RUN_ADVERTISEMENT_MANAGEMENT_PROCESS: bool = True

    # ADVERTISEMENT_PAID_IDS_LIST: List of advertisement IDs to mark as 'paid'
    ADVERTISEMENT_PAID_IDS_LIST: list[str] = Field(default_factory=list)

    # ============================================
    # SIGNUP ID MANAGEMENT INPUTS
    # ============================================
    # RUN_SIGNUP_ID_MANAGEMENT_PROCESS: Flag to enable/disable signup ID management
    RUN_SIGNUP_ID_MANAGEMENT_PROCESS: bool = True

    # ============================================
    # DATA ANALYSIS PROCESS INPUTS
    # ============================================
    # RUN_DATA_ANALYSIS_PROCESS: Flag to enable/disable data export/analysis process
    # Note: BusinessReport runs automatically inside DataAnalysis
    RUN_DATA_ANALYSIS_PROCESS: bool = True

    # ============================================
    # BUSINESS REPORT PROCESS INPUTS
    # ============================================
    # RUN_BUSINESS_REPORT_PROCESS: Flag to enable/disable standalone business report
    # Note: If RUN_DATA_ANALYSIS_PROCESS is True, BusinessReport runs automatically
    RUN_BUSINESS_REPORT_PROCESS: bool = True

    # ============================================
    # INVOICE GENERATION PROCESS INPUTS
    # ============================================
    RUN_INVOICE_GENERATION_PROCESS: bool = False


def _parse_bool(value: Any, default: bool = False) -> bool:
    """Parse a value to boolean.

    Args:
        value: Value to parse (str, bool, int, or None)
        default: Default value if parsing fails

    Returns:
        bool: Parsed boolean value
    """
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return value != 0
    if isinstance(value, str):
        return value.lower() in ("true", "1", "yes", "on")
    return default


def _parse_list(value: Any, default: list | None = None) -> list[str]:
    """Parse a value to list of strings.

    Args:
        value: Value to parse (list, str, or None)
        default: Default value if parsing fails

    Returns:
        list[str]: Parsed list of strings
    """
    if default is None:
        default = []
    if value is None:
        return default
    if isinstance(value, list):
        return [str(item).strip() for item in value if item]
    if isinstance(value, str):
        return [item.strip() for item in value.split(",") if item.strip()]
    return default


def _get_robocorp_workitem() -> dict[str, Any] | None:
    """Get work item payload from Robocorp.

    Returns:
        dict: Work item payload or None if not running in Robocorp
    """
    try:
        from robocorp import workitems

        # Get current input work item
        item = workitems.inputs.current
        if item and item.payload:
            logger.info("📥 Loading inputs from Robocorp Work Item")
            return item.payload
    except ImportError:
        logger.debug("robocorp.workitems not available - using environment/defaults")
    except Exception as e:
        logger.warning(f"Failed to get Robocorp work item: {e}")

    return None


def _get_env_variables() -> dict[str, Any]:
    """Get input variables from environment.

    Returns:
        dict: Environment variables as input dict
    """
    logger.info("📥 Loading inputs from environment variables")

    return {
        "environment": os.getenv("ENVIRONMENT", "local"),
        "dev_safe_mode": os.getenv("DEV_SAFE_MODE", "True"),
        "log_level": os.getenv("LOG_LEVEL", "INFO"),
        # Order Management (default: True)
        "run_order_manage_system": os.getenv("RUN_ORDER_MANAGE_SYSTEM", "True"),
        # Payment Update (default: False)
        "run_update_payment_process": os.getenv("RUN_UPDATE_PAYMENT_PROCESS", "False"),
        "payment_ids_list": os.getenv("PAYMENT_IDS_LIST", ""),
        # User Management (default: True)
        "run_user_management_process": os.getenv("RUN_USER_MANAGEMENT_PROCESS", "True"),
        # Advertisement Management (default: True)
        "run_advertisement_management_process": os.getenv("RUN_ADVERTISEMENT_MANAGEMENT_PROCESS", "True"),
        "advertisement_paid_ids_list": os.getenv("ADVERTISEMENT_PAID_IDS_LIST", ""),
        # Signup ID Management (default: True)
        "run_signup_id_management_process": os.getenv("RUN_SIGNUP_ID_MANAGEMENT_PROCESS", "True"),
        # Data Analysis (default: True)
        "run_data_analysis_process": os.getenv("RUN_DATA_ANALYSIS_PROCESS", "True"),
        # Business Report (default: True)
        "run_business_report_process": os.getenv("RUN_BUSINESS_REPORT_PROCESS", "True"),
        # Invoice Generation (default: False)
        "run_invoice_generation_process": os.getenv("RUN_INVOICE_GENERATION_PROCESS", "False"),
    }


def get_workitem_data() -> tuple[dict[str, Any], dict[str, Any]]:
    """Get workitem variables from Robocorp or environment.

    Priority:
    1. Robocorp Work Items (if running in Robocorp)
    2. Environment variables
    3. Default values

    Returns:
        tuple: (variables, metadata) dictionaries
    """
    # Try Robocorp work items first
    robocorp_payload = _get_robocorp_workitem()

    if robocorp_payload:
        variables = robocorp_payload
        source = "Robocorp Work Item"
    else:
        variables = _get_env_variables()
        source = "Environment Variables"

    # Generate metadata
    metadata = {
        "processRunId": os.getenv("RC_PROCESS_RUN_ID") or f"local-run-id-{uuid.uuid4().hex[:8]}",
        "source": source,
    }

    logger.info(f"Work item data ({source}):\nVariables: {pformat(variables)}\nMetadata: {pformat(metadata)}")
    return variables, metadata


def load_work_items(variables: dict[str, Any], metadata: dict[str, Any]) -> Inputs:
    """Load work items and create Inputs object.

    Args:
        variables: Input variables dict
        metadata: Metadata dict

    Returns:
        Inputs: Validated input object
    """
    # Parse boolean flags with defaults
    dev_safe_mode = _parse_bool(variables.get("dev_safe_mode"), default=True)
    environment = str(variables.get("environment", "local"))
    is_production = environment == "production" and not dev_safe_mode

    # Parse log level
    log_level = str(variables.get("log_level", "INFO")).upper()
    if log_level not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
        log_level = "INFO"

    # Parse process flags (all default to True for full workflow)
    run_order_manage_system = _parse_bool(variables.get("run_order_manage_system"), default=True)
    run_update_payment_process = _parse_bool(variables.get("run_update_payment_process"), default=False)
    run_user_management_process = _parse_bool(variables.get("run_user_management_process"), default=True)
    run_advertisement_management_process = _parse_bool(
        variables.get("run_advertisement_management_process"), default=True
    )
    run_signup_id_management_process = _parse_bool(variables.get("run_signup_id_management_process"), default=True)
    run_data_analysis_process = _parse_bool(variables.get("run_data_analysis_process"), default=True)
    run_business_report_process = _parse_bool(variables.get("run_business_report_process"), default=True)
    run_invoice_generation_process = _parse_bool(variables.get("run_invoice_generation_process"), default=False)

    # Parse ID lists
    payment_ids_list = _parse_list(variables.get("payment_ids_list"))
    advertisement_paid_ids_list = _parse_list(variables.get("advertisement_paid_ids_list"))

    return Inputs(
        IN_PRODUCTION=is_production,
        DEV_SAFE_MODE=dev_safe_mode,
        LOG_LEVEL=log_level,
        RUN_ID=str(metadata.get("processRunId", "")),
        RUN_ORDER_MANAGE_SYSTEM=run_order_manage_system,
        RUN_UPDATE_PAYMENT_PROCESS=run_update_payment_process,
        PAYMENT_IDS_LIST=payment_ids_list,
        RUN_USER_MANAGEMENT_PROCESS=run_user_management_process,
        RUN_ADVERTISEMENT_MANAGEMENT_PROCESS=run_advertisement_management_process,
        ADVERTISEMENT_PAID_IDS_LIST=advertisement_paid_ids_list,
        RUN_SIGNUP_ID_MANAGEMENT_PROCESS=run_signup_id_management_process,
        RUN_DATA_ANALYSIS_PROCESS=run_data_analysis_process,
        RUN_BUSINESS_REPORT_PROCESS=run_business_report_process,
        RUN_INVOICE_GENERATION_PROCESS=run_invoice_generation_process,
    )


# ============================================
# MODULE-LEVEL INITIALIZATION
# ============================================
# Load inputs on module import
variables, metadata = get_workitem_data()
INPUTS = load_work_items(variables, metadata)
