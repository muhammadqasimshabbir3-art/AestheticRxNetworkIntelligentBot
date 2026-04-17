"""Signup ID Management Process - Entry point for signup ID management workflow.

This module provides the public interface for the signup ID management functionality.
"""

from libraries.logger import logger
from processes.signup.signup_id_manager import SignupIDManager


class SignupIDManagementProcess:
    """Public entry point for the Signup ID Management workflow."""

    def __init__(self) -> None:
        """Initialize the SignupIDManagementProcess."""
        logger.info("=" * 60)
        logger.info("Initializing Signup ID Management Process")
        logger.info("=" * 60)
        self._signup_id_manager = SignupIDManager()
        logger.info("Signup ID Management Process initialized")

    def start(self) -> None:
        """Start the signup ID management workflow."""
        logger.info("=" * 60)
        logger.info("Starting Signup ID Management Workflow")
        logger.info("=" * 60)
        self._signup_id_manager.start()
        logger.info("=" * 60)
        logger.info("✅ SIGNUP ID MANAGEMENT WORKFLOW COMPLETED!")
        logger.info("=" * 60)
        logger.info(f"Total signup IDs: {self.total_count}")
        logger.info(f"Used: {self.used_count}")
        logger.info(f"Unused (Available): {self.unused_count}")
        logger.info(f"Usage percentage: {self.usage_percentage:.1f}%")
        if self.is_emergency:
            logger.warning(f"⚠️ EMERGENCY: Only {self.unused_count} signup IDs remaining!")

    @property
    def signup_ids(self) -> list[dict]:
        """Get all signup IDs."""
        return self._signup_id_manager.signup_ids

    @property
    def total_count(self) -> int:
        """Get total count of signup IDs."""
        return self._signup_id_manager.total_count

    @property
    def used_count(self) -> int:
        """Get count of used signup IDs."""
        return self._signup_id_manager.used_count

    @property
    def unused_count(self) -> int:
        """Get count of unused signup IDs."""
        return self._signup_id_manager.unused_count

    @property
    def usage_percentage(self) -> float:
        """Get usage percentage."""
        return self._signup_id_manager.usage_percentage

    @property
    def is_emergency(self) -> bool:
        """Check if signup IDs are critically low."""
        return self._signup_id_manager.is_emergency

    @property
    def used_signup_ids(self) -> list[dict]:
        """Get list of used signup IDs."""
        return self._signup_id_manager.used_signup_ids

    @property
    def unused_signup_ids(self) -> list[dict]:
        """Get list of unused signup IDs."""
        return self._signup_id_manager.unused_signup_ids

    @property
    def recent_signups(self) -> list[dict]:
        """Get recently used signup IDs (sorted by used_at)."""
        return self._signup_id_manager.recent_signups

    @property
    def emergency_threshold(self) -> int:
        """Get the emergency threshold."""
        return self._signup_id_manager.emergency_threshold

