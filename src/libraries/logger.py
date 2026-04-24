"""Logger module for the application."""

import json
import logging
from pathlib import Path

# Configure root logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger("aestheticrxnetwork_intelligent_bot")


def reconfigure_log_level(log_level: str) -> None:
    """Reconfigure the log level for the application.

    Args:
        log_level: The log level to set (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    logger.setLevel(numeric_level)
    logging.getLogger().setLevel(numeric_level)


def log_build_info() -> str:
    """Log build information from commit_info.json if available.

    Returns:
        str: Message about build info status
    """
    commit_info_path = Path("commit_info.json")
    if commit_info_path.exists():
        with open(commit_info_path) as f:
            commit_info = json.load(f)
            logger.info(f"Build Info: {commit_info}")
            return f"Build loaded from commit: {commit_info.get('commit_hash', 'unknown')}"
    return "Running local build (no commit_info.json found)"
