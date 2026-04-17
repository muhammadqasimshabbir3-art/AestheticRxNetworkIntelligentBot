"""Data Analysis Process - Entry point for data export workflow.

This module provides the public interface for the data analysis/export functionality.
"""


from libraries.logger import logger
from processes.data_analysis.data_analysis_manager import DataAnalysisManager


class DataAnalysisProcess:
    """Public entry point for the Data Analysis workflow."""

    def __init__(self) -> None:
        """Initialize the DataAnalysisProcess."""
        logger.info("=" * 60)
        logger.info("Initializing Data Analysis Process")
        logger.info("=" * 60)
        self._manager = DataAnalysisManager()
        logger.info("Data Analysis Process initialized")

    def start(self) -> None:
        """Start the data analysis workflow."""
        logger.info("=" * 60)
        logger.info("Starting Data Analysis Workflow")
        logger.info("=" * 60)
        self._manager.start()
        logger.info("=" * 60)
        logger.info("✅ DATA ANALYSIS WORKFLOW COMPLETED!")
        logger.info("=" * 60)
        logger.info(f"Job ID: {self.job_id}")
        logger.info(f"Job Status: {self.job_status}")
        if self.file_path:
            logger.info(f"Downloaded file: {self.file_path}")
        if self.file_size:
            logger.info(f"File size: {self._format_size(self.file_size)}")

    def _format_size(self, size: int) -> str:
        """Format file size in human readable format."""
        for unit in ["B", "KB", "MB", "GB"]:
            if size < 1024:
                return f"{size:.2f} {unit}"
            size /= 1024
        return f"{size:.2f} TB"

    @property
    def job_id(self) -> str | None:
        """Get the export job ID."""
        return self._manager.job_id

    @property
    def job_status(self) -> str:
        """Get the export job status."""
        return self._manager.job_status

    @property
    def file_path(self) -> str | None:
        """Get the downloaded file path."""
        return self._manager.file_path

    @property
    def file_size(self) -> int | None:
        """Get the file size in bytes."""
        return self._manager.file_size

    @property
    def export_jobs(self) -> list[dict]:
        """Get all export jobs."""
        return self._manager.export_jobs

    @property
    def completed_jobs(self) -> list[dict]:
        """Get completed export jobs."""
        return self._manager.completed_jobs

    @property
    def processing_jobs(self) -> list[dict]:
        """Get processing export jobs."""
        return self._manager.processing_jobs

    @property
    def download_url(self) -> str | None:
        """Get the download URL."""
        return self._manager.download_url

    @property
    def error_message(self) -> str | None:
        """Get error message if any."""
        return self._manager.error_message

    @property
    def business_report(self):
        """Get the Business Report process (always runs inside DataAnalysis)."""
        return self._manager.business_report

