"""Data Analysis Manager - Core logic for data export.

This module handles:
- Starting export jobs
- Polling for job completion
- Downloading export files
- Running Business Report analysis (always runs after successful export)
"""

import time
from pathlib import Path
from typing import TYPE_CHECKING, Optional

from config import CONFIG
from libraries.aestheticrxnetwork_api import AestheticRxNetworkAPI
from libraries.logger import logger

if TYPE_CHECKING:
    from processes.business_report import BusinessReportProcess


class DataAnalysisManager:
    """Manages data export operations."""

    # Polling settings
    MAX_POLL_ATTEMPTS = 24  # Maximum number of poll attempts (2 minutes total)
    POLL_INTERVAL = 5  # Seconds between poll attempts
    INITIAL_WAIT = 30  # Initial wait before first poll (let job start processing)

    def __init__(self) -> None:
        """Initialize the DataAnalysisManager."""
        logger.info("Initializing DataAnalysisManager...")
        self._api = AestheticRxNetworkAPI()

        # Job tracking
        self.job_id: str | None = None
        self.job_status: str = "not_started"
        self.file_path: str | None = None
        self.file_size: int | None = None
        self.download_url: str | None = None
        self.error_message: str | None = None

        # All jobs
        self.export_jobs: list[dict] = []
        self.completed_jobs: list[dict] = []
        self.processing_jobs: list[dict] = []

        # Business Report (always runs after successful export)
        self._business_report: BusinessReportProcess | None = None

        logger.info("DataAnalysisManager initialized")

    def start(self) -> None:
        """Start the data analysis workflow."""
        logger.info("=" * 60)
        logger.info("Starting Data Analysis Workflow")
        logger.info("=" * 60)

        # Step 1: Get existing export jobs
        self._get_export_jobs()

        # Step 2: Start a new export job
        self._start_export_job()

        # Step 3: Poll for completion
        if self.job_id:
            self._poll_for_completion()

        # Step 4: Download the file if completed
        if self.job_status == "completed" and self.job_id:
            self._download_export()

        # Step 5: Log summary
        self._log_summary()

        # Step 6: Run Business Report analysis (always runs after data export)
        if self.file_path:
            self._run_business_report()

        logger.info("=" * 60)
        logger.info("Data Analysis Workflow completed")
        logger.info("=" * 60)

    def _get_export_jobs(self) -> None:
        """Get all export jobs from the API."""
        logger.info("Fetching existing export jobs...")

        try:
            self.export_jobs = self._api.get_export_jobs()
            logger.info(f"✓ Found {len(self.export_jobs)} export jobs")

            # Categorize jobs
            self.completed_jobs = [j for j in self.export_jobs if j.get("status") == "completed"]
            self.processing_jobs = [j for j in self.export_jobs if j.get("status") == "processing"]

            logger.info(f"  - Completed: {len(self.completed_jobs)}")
            logger.info(f"  - Processing: {len(self.processing_jobs)}")

            # Log recent completed jobs
            for job in self.completed_jobs[:3]:
                size = job.get("fileSize", 0)
                size_str = self._format_size(size) if size else "N/A"
                logger.info(f"    📦 {job.get('id')} - {size_str}")

        except Exception as e:
            logger.error(f"✗ Failed to get export jobs: {e}")
            self.error_message = str(e)

    def _start_export_job(self) -> None:
        """Start a new export job."""
        logger.info("=" * 60)
        logger.info("Starting new export job...")
        logger.info("=" * 60)

        try:
            result = self._api.start_export_job()

            if result.get("success"):
                self.job_id = result.get("data", {}).get("jobId")
                self.job_status = "processing"
                logger.info(f"✓ Export job started: {self.job_id}")
            else:
                self.error_message = result.get("message", "Failed to start export job")
                logger.error(f"✗ {self.error_message}")

        except Exception as e:
            logger.error(f"✗ Failed to start export job: {e}")
            self.error_message = str(e)

    def _poll_for_completion(self) -> None:
        """Poll the API until the job is completed."""
        logger.info("=" * 60)
        logger.info(f"Polling for job completion: {self.job_id}")
        logger.info(f"Max attempts: {self.MAX_POLL_ATTEMPTS}, Interval: {self.POLL_INTERVAL}s")
        logger.info("=" * 60)

        # Initial wait to let the job start processing
        logger.info(f"⏳ Waiting {self.INITIAL_WAIT}s for job to process...")
        time.sleep(self.INITIAL_WAIT)

        for attempt in range(1, self.MAX_POLL_ATTEMPTS + 1):
            logger.info(f"Poll attempt {attempt}/{self.MAX_POLL_ATTEMPTS}...")

            try:
                jobs = self._api.get_export_jobs()

                # Find our job
                job = next((j for j in jobs if j.get("id") == self.job_id), None)

                if job:
                    self.job_status = job.get("status", "unknown")
                    self.file_size = job.get("fileSize")

                    logger.info(f"  Status: {self.job_status}")

                    if self.job_status == "completed":
                        logger.info("✓ Job completed!")
                        return
                    elif self.job_status == "failed":
                        logger.error("✗ Job failed!")
                        self.error_message = "Export job failed"
                        return
                else:
                    logger.warning(f"Job {self.job_id} not found in response")

            except Exception as e:
                logger.error(f"✗ Poll error: {e}")

            # Wait before next poll
            if attempt < self.MAX_POLL_ATTEMPTS:
                logger.info(f"  Waiting {self.POLL_INTERVAL}s...")
                time.sleep(self.POLL_INTERVAL)

        # Timeout
        logger.warning(f"⚠ Polling timeout after {self.MAX_POLL_ATTEMPTS} attempts")
        self.job_status = "timeout"
        self.error_message = "Export job polling timeout"

    def _download_export(self) -> None:
        """Download the exported file."""
        logger.info("=" * 60)
        logger.info(f"Downloading export: {self.job_id}")
        logger.info("=" * 60)

        try:
            # Ensure output directory exists
            CONFIG.ensure_directories()
            output_dir = CONFIG.OUTPUT_DIR / "exports"
            output_dir.mkdir(exist_ok=True)

            # Download the file
            file_path = self._api.download_export(self.job_id, str(output_dir))

            if file_path:
                self.file_path = file_path
                self.download_url = (
                    f"https://aestheticrxnetwork-production.up.railway.app"
                    f"/api/admin/export-jobs/{self.job_id}/download"
                )

                # Get actual file size
                path = Path(file_path)
                if path.exists():
                    self.file_size = path.stat().st_size

                logger.info(f"✓ Downloaded to: {file_path}")
                logger.info(f"  Size: {self._format_size(self.file_size or 0)}")
            else:
                logger.error("✗ Download failed - no file path returned")
                self.error_message = "Download failed"

        except Exception as e:
            logger.error(f"✗ Download error: {e}")
            self.error_message = str(e)

    def _log_summary(self) -> None:
        """Log summary of the data analysis operation."""
        logger.info("=" * 60)
        logger.info("📊 DATA ANALYSIS SUMMARY")
        logger.info("=" * 60)
        logger.info(f"  📌 Job ID: {self.job_id or 'N/A'}")
        logger.info(f"  📊 Status: {self.job_status}")

        if self.file_path:
            logger.info(f"  📁 File: {self.file_path}")
            logger.info(f"  📦 Size: {self._format_size(self.file_size or 0)}")

        if self.error_message:
            logger.error(f"  ❌ Error: {self.error_message}")

        logger.info(f"  📋 Total Export Jobs: {len(self.export_jobs)}")
        logger.info(f"  ✅ Completed: {len(self.completed_jobs)}")
        logger.info(f"  ⏳ Processing: {len(self.processing_jobs)}")

    def _format_size(self, size: int) -> str:
        """Format file size in human readable format."""
        for unit in ["B", "KB", "MB", "GB"]:
            if size < 1024:
                return f"{size:.2f} {unit}"
            size /= 1024
        return f"{size:.2f} TB"

    def _run_business_report(self) -> None:
        """Run the Business Report analysis.

        This always runs after a successful data export to generate
        comprehensive business intelligence reports.
        """
        logger.info("=" * 60)
        logger.info("📊 Running Business Report Analysis")
        logger.info("=" * 60)

        try:
            # Lazy import to avoid circular dependencies
            from processes.business_report import BusinessReportProcess

            self._business_report = BusinessReportProcess()
            self._business_report.start()

            logger.info("✅ Business Report Analysis completed")

        except Exception as e:
            logger.error(f"❌ Business Report Analysis failed: {e}")
            # Don't raise - this is a secondary process

    @property
    def business_report(self) -> Optional["BusinessReportProcess"]:
        """Get the Business Report process (if run)."""
        return self._business_report
