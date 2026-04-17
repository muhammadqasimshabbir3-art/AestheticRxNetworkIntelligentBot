"""Main Process - Entry point for QwebsiteAutomationBot.

This module handles:
- Bitwarden authentication setup
- Environment configuration
- Running UpdatePaymentProcess (if enabled) FIRST
- Calling OrderManagementProcess.start()
- Generating HTML report

Usage:
    from workflow.process import Process

    process = Process()
    process.start()
"""


from config import CONFIG
from libraries.logger import logger
from libraries.report_generator import ReportGenerator
from libraries.workitems import INPUTS
from processes.advertisement import AdvertisementManagementProcess
from processes.business_report import BusinessReportProcess
from processes.data_analysis import DataAnalysisProcess
from processes.order import OrderManagementProcess
from processes.payment import UpdatePaymentProcess
from processes.signup import SignupIDManagementProcess
from processes.user import UserManagementProcess


class Process:
    """Main Process class for QwebsiteAutomationBot.

    This class handles:
    1. Initialization and configuration logging
    2. Update Payment Process (if RUN_UPDATE_PAYMENT_PROCESS is True) - RUNS FIRST
    3. Order Management Process (if RUN_ORDER_MANAGE_SYSTEM is True)
    4. User Management Process (if RUN_USER_MANAGEMENT_PROCESS is True)
    5. Advertisement Management Process (if RUN_ADVERTISEMENT_MANAGEMENT_PROCESS is True)
    6. Signup ID Management Process (if RUN_SIGNUP_ID_MANAGEMENT_PROCESS is True)
    7. Data Analysis Process (if RUN_DATA_ANALYSIS_PROCESS is True)
    8. Business Report Process (if RUN_BUSINESS_REPORT_PROCESS is True)

    Execution Order:
    1. UpdatePaymentProcess.start() - Updates sheet status from pending to paid
    2. OrderManagementProcess.start() - Order management workflow
    3. UserManagementProcess.start() - User management workflow
    4. AdvertisementManagementProcess.start() - Advertisement management workflow
    5. SignupIDManagementProcess.start() - Signup ID management workflow
    6. DataAnalysisProcess.start() - Data export and analysis workflow
    7. BusinessReportProcess.start() - Business intelligence report generation
    """

    def __init__(self) -> None:
        """Initialize the Process.

        This sets up configuration and prepares all processes.
        """
        logger.info("=" * 60)
        logger.info("Initializing QwebsiteAutomationBot Process")
        logger.info("=" * 60)

        # Log configuration
        self._log_configuration()

        # Initialize process holders
        self._update_payment_process: UpdatePaymentProcess | None = None
        self._order_process: OrderManagementProcess | None = None
        self._user_process: UserManagementProcess | None = None
        self._advertisement_process: AdvertisementManagementProcess | None = None
        self._signup_id_process: SignupIDManagementProcess | None = None
        self._data_analysis_process: DataAnalysisProcess | None = None
        self._business_report_process: BusinessReportProcess | None = None

        # Initialize report generator
        self._report = ReportGenerator()
        self._report_path: str | None = None

        logger.info("=" * 60)
        logger.info("Process initialized - Ready to execute")
        logger.info("=" * 60)

    def _log_configuration(self) -> None:
        """Log current configuration."""
        logger.info("Configuration:")
        logger.info(f"  App Name: {CONFIG.APP_NAME}")
        logger.info(f"  Google Drive Folder: {CONFIG.GOOGLE_DRIVE_FOLDER_ID}")
        logger.info(f"  Google Spreadsheet: {CONFIG.GOOGLE_SPREADSHEET_ID}")
        logger.info(f"  Spreadsheet Prefix: {CONFIG.SPREADSHEET_NAME_PREFIX}")
        logger.info("")
        logger.info("Workflow Flags:")
        logger.info(f"  RUN_UPDATE_PAYMENT_PROCESS: {INPUTS.RUN_UPDATE_PAYMENT_PROCESS}")
        logger.info(f"  PAYMENT_IDS_LIST: {INPUTS.PAYMENT_IDS_LIST}")
        logger.info(f"  RUN_ORDER_MANAGE_SYSTEM: {INPUTS.RUN_ORDER_MANAGE_SYSTEM}")
        logger.info(f"  RUN_USER_MANAGEMENT_PROCESS: {INPUTS.RUN_USER_MANAGEMENT_PROCESS}")
        logger.info(f"  RUN_ADVERTISEMENT_MANAGEMENT_PROCESS: {INPUTS.RUN_ADVERTISEMENT_MANAGEMENT_PROCESS}")
        logger.info(f"  RUN_SIGNUP_ID_MANAGEMENT_PROCESS: {INPUTS.RUN_SIGNUP_ID_MANAGEMENT_PROCESS}")
        logger.info(f"  RUN_DATA_ANALYSIS_PROCESS: {INPUTS.RUN_DATA_ANALYSIS_PROCESS}")
        logger.info(f"  RUN_BUSINESS_REPORT_PROCESS: {INPUTS.RUN_BUSINESS_REPORT_PROCESS}")

    def start(self) -> None:
        """Start the main workflow.

        Execution order:
        1. FIRST: Run UpdatePaymentProcess if RUN_UPDATE_PAYMENT_PROCESS is True
        2. THEN: Run OrderManagementProcess if RUN_ORDER_MANAGE_SYSTEM is True
        3. Generate HTML report
        """
        logger.info("=" * 60)
        logger.info("Starting QwebsiteAutomationBot Workflow")
        logger.info("=" * 60)

        # Start report tracking
        self._report.start()

        errors: list[str] = []

        # ============================================
        # STEP 1: Update Payment Process (RUNS FIRST)
        # ============================================
        if INPUTS.RUN_UPDATE_PAYMENT_PROCESS:
            logger.info("=" * 60)
            logger.info("🔄 RUN_UPDATE_PAYMENT_PROCESS is enabled")
            logger.info("=" * 60)

            self._report.step_start("payment_update")

            if INPUTS.PAYMENT_IDS_LIST:
                try:
                    logger.info(f"Processing {len(INPUTS.PAYMENT_IDS_LIST)} payment IDs...")
                    self._update_payment_process = UpdatePaymentProcess(payment_ids=INPUTS.PAYMENT_IDS_LIST)
                    self._update_payment_process.start()

                    # Update report data
                    self._report.set_update_payment_data(
                        enabled=True,
                        payment_ids=INPUTS.PAYMENT_IDS_LIST,
                        updated_count=self._update_payment_process.updated_count,
                        failed_ids=self._update_payment_process.failed_ids,
                        not_found_ids=self._update_payment_process.not_found_ids,
                    )

                    # Mark step passed
                    self._report.step_passed("payment_update", {
                        "IDs Processed": len(INPUTS.PAYMENT_IDS_LIST),
                        "Updated": self._update_payment_process.updated_count,
                        "Failed": len(self._update_payment_process.failed_ids),
                    })
                except Exception as e:
                    error_msg = f"Update Payment Process failed: {e}"
                    logger.error(f"❌ {error_msg}")
                    errors.append(error_msg)
                    self._report.add_error(error_msg)
                    self._report.step_failed("payment_update", str(e))
            else:
                logger.warning("⚠ PAYMENT_IDS_LIST is empty - nothing to update")
                self._report.add_warning("PAYMENT_IDS_LIST is empty - nothing to update")
                self._report.step_passed("payment_update", {"Note": "No IDs to process"})
        else:
            logger.info("⏸ RUN_UPDATE_PAYMENT_PROCESS is disabled - skipping")
            self._report.step_skipped("payment_update", "Disabled in config")
            self._report.set_update_payment_data(
                enabled=False,
                payment_ids=[],
                updated_count=0,
                failed_ids=[],
                not_found_ids=[],
            )

        # ============================================
        # STEP 2: Order Management Process
        # ============================================
        if INPUTS.RUN_ORDER_MANAGE_SYSTEM:
            logger.info("=" * 60)
            logger.info("🔄 RUN_ORDER_MANAGE_SYSTEM is enabled")
            logger.info("=" * 60)

            self._report.step_start("order_management")

            try:
                self._order_process = OrderManagementProcess()
                self._order_process.start()

                # Update report data from order manager
                order_manager = self._order_process._order_manager
                if order_manager:
                    self._report.set_order_management_data(
                        enabled=True,
                        api_pending_orders=order_manager.payment_to_process,
                        sheet_orders_count=len(order_manager.sheet_payments),
                        matching_orders=order_manager.filtered_payment_data,
                        new_orders=order_manager.new_orders,
                        orders_updated_to_completed=order_manager.updated_order_ids,
                        duplicates_removed=getattr(order_manager, "duplicates_removed", []),
                        status_breakdown=getattr(order_manager, "status_breakdown", {}),
                        doctor_debts=getattr(order_manager, "doctor_debts", []),
                    )

                    # Mark step passed
                    self._report.step_passed("order_management", {
                        "Orders": len(order_manager.payment_to_process),
                        "Updated": len(order_manager.updated_order_ids),
                        "New": len(order_manager.new_orders),
                    })
            except Exception as e:
                error_msg = f"Order Management Process failed: {e}"
                logger.error(f"❌ {error_msg}")
                errors.append(error_msg)
                self._report.add_error(error_msg)
                self._report.step_failed("order_management", str(e))
        else:
            logger.info("⏸ RUN_ORDER_MANAGE_SYSTEM is disabled - skipping")
            self._report.step_skipped("order_management", "Disabled in config")
            self._report.set_order_management_data(
                enabled=False,
                api_pending_orders=[],
                sheet_orders_count=0,
                matching_orders=[],
                new_orders=[],
                orders_updated_to_completed=[],
                duplicates_removed=[],
                status_breakdown={},
                doctor_debts=[],
            )

        # ============================================
        # STEP 3: User Management Process
        # ============================================
        if INPUTS.RUN_USER_MANAGEMENT_PROCESS:
            logger.info("=" * 60)
            logger.info("🔄 RUN_USER_MANAGEMENT_PROCESS is enabled")
            logger.info("=" * 60)

            self._report.step_start("user_management")

            try:
                self._user_process = UserManagementProcess()
                self._user_process.start()

                # Update report data
                self._report.set_user_management_data(
                    enabled=True,
                    users=self._user_process.users,
                    users_count=self._user_process.users_count,
                    new_users=self._user_process.new_users,
                    updated_users=self._user_process.updated_users,
                    approved_users=self._user_process.approved_users,
                    failed_approvals=self._user_process.failed_approvals,
                    status_breakdown=self._user_process.status_breakdown,
                    user_type_breakdown=self._user_process.user_type_breakdown,
                    tier_breakdown=self._user_process.tier_breakdown,
                    admin_count=self._user_process.admin_count,
                    deactivated_count=self._user_process.deactivated_count,
                )

                # Mark step passed
                self._report.step_passed("user_management", {
                    "Users": self._user_process.users_count,
                    "Approved": len(self._user_process.approved_users),
                })
            except Exception as e:
                error_msg = f"User Management Process failed: {e}"
                logger.error(f"❌ {error_msg}")
                errors.append(error_msg)
                self._report.add_error(error_msg)
                self._report.step_failed("user_management", str(e))
        else:
            logger.info("⏸ RUN_USER_MANAGEMENT_PROCESS is disabled - skipping")
            self._report.step_skipped("user_management", "Disabled in config")
            self._report.set_user_management_data(
                enabled=False,
                users=[],
                users_count=0,
                new_users=[],
                updated_users=[],
                approved_users=[],
                failed_approvals=[],
                status_breakdown={},
                user_type_breakdown={},
                tier_breakdown={},
                admin_count=0,
                deactivated_count=0,
            )

        # ============================================
        # STEP 4: Advertisement Management Process
        # ============================================
        if INPUTS.RUN_ADVERTISEMENT_MANAGEMENT_PROCESS:
            logger.info("=" * 60)
            logger.info("🔄 RUN_ADVERTISEMENT_MANAGEMENT_PROCESS is enabled")
            logger.info("=" * 60)

            self._report.step_start("advertisement_management")

            try:
                # Pass paid IDs list to the process
                self._advertisement_process = AdvertisementManagementProcess(
                    paid_ids_list=INPUTS.ADVERTISEMENT_PAID_IDS_LIST
                )
                self._advertisement_process.start()

                # Update report data
                self._report.set_advertisement_management_data(
                    enabled=True,
                    advertisements=self._advertisement_process.advertisements,
                    total_count=self._advertisement_process.total_count,
                    status_breakdown=self._advertisement_process.status_breakdown,
                    type_breakdown=self._advertisement_process.type_breakdown,
                    payment_status_breakdown=self._advertisement_process.payment_status_breakdown,
                    pending_count=len(self._advertisement_process.pending_advertisements),
                    approved_count=len(self._advertisement_process.approved_advertisements),
                    approved_ads=self._advertisement_process.approved_advertisements,
                    failed_approvals=self._advertisement_process.failed_approvals,
                    payment_updated_ids=self._advertisement_process.payment_updated_ids,
                    payment_update_failed_ids=self._advertisement_process.payment_update_failed_ids,
                    status_updated_ids=self._advertisement_process.status_updated_ids,
                )

                # Mark step passed
                self._report.step_passed("advertisement_management", {
                    "Ads": self._advertisement_process.total_count,
                    "Approved": len(self._advertisement_process.approved_advertisements),
                })
            except Exception as e:
                error_msg = f"Advertisement Management Process failed: {e}"
                logger.error(f"❌ {error_msg}")
                errors.append(error_msg)
                self._report.add_error(error_msg)
                self._report.step_failed("advertisement_management", str(e))
        else:
            logger.info("⏸ RUN_ADVERTISEMENT_MANAGEMENT_PROCESS is disabled - skipping")
            self._report.step_skipped("advertisement_management", "Disabled in config")
            self._report.set_advertisement_management_data(
                enabled=False,
                advertisements=[],
                total_count=0,
                status_breakdown={},
                type_breakdown={},
                payment_status_breakdown={},
                pending_count=0,
                approved_count=0,
                approved_ads=[],
                failed_approvals=[],
                payment_updated_ids=[],
                payment_update_failed_ids=[],
                status_updated_ids=[],
            )

        # ============================================
        # STEP 5: Signup ID Management Process
        # ============================================
        if INPUTS.RUN_SIGNUP_ID_MANAGEMENT_PROCESS:
            logger.info("=" * 60)
            logger.info("🔄 RUN_SIGNUP_ID_MANAGEMENT_PROCESS is enabled")
            logger.info("=" * 60)

            self._report.step_start("signup_id_management")

            try:
                self._signup_id_process = SignupIDManagementProcess()
                self._signup_id_process.start()

                # Update report data
                self._report.set_signup_id_management_data(
                    enabled=True,
                    signup_ids=self._signup_id_process.signup_ids,
                    total_count=self._signup_id_process.total_count,
                    used_count=self._signup_id_process.used_count,
                    unused_count=self._signup_id_process.unused_count,
                    usage_percentage=self._signup_id_process.usage_percentage,
                    is_emergency=self._signup_id_process.is_emergency,
                    emergency_threshold=self._signup_id_process.emergency_threshold,
                    used_signup_ids=self._signup_id_process.used_signup_ids,
                    unused_signup_ids=self._signup_id_process.unused_signup_ids,
                    recent_signups=self._signup_id_process.recent_signups,
                )

                # Mark step passed
                self._report.step_passed("signup_id_management", {
                    "Total": self._signup_id_process.total_count,
                    "Available": self._signup_id_process.unused_count,
                })
            except Exception as e:
                error_msg = f"Signup ID Management Process failed: {e}"
                logger.error(f"❌ {error_msg}")
                errors.append(error_msg)
                self._report.add_error(error_msg)
                self._report.step_failed("signup_id_management", str(e))
        else:
            logger.info("⏸ RUN_SIGNUP_ID_MANAGEMENT_PROCESS is disabled - skipping")
            self._report.step_skipped("signup_id_management", "Disabled in config")
            self._report.set_signup_id_management_data(
                enabled=False,
                signup_ids=[],
                total_count=0,
                used_count=0,
                unused_count=0,
                usage_percentage=0.0,
                is_emergency=False,
                emergency_threshold=20,
                used_signup_ids=[],
                unused_signup_ids=[],
                recent_signups=[],
            )

        # ============================================
        # STEP 6: Data Analysis Process
        # ============================================
        if INPUTS.RUN_DATA_ANALYSIS_PROCESS:
            logger.info("=" * 60)
            logger.info("🔄 RUN_DATA_ANALYSIS_PROCESS is enabled")
            logger.info("=" * 60)

            self._report.step_start("data_analysis")

            try:
                self._data_analysis_process = DataAnalysisProcess()
                self._data_analysis_process.start()

                # Update report data
                self._report.set_data_analysis_data(
                    enabled=True,
                    job_id=self._data_analysis_process.job_id,
                    job_status=self._data_analysis_process.job_status,
                    file_path=self._data_analysis_process.file_path,
                    file_size=self._data_analysis_process.file_size,
                    export_jobs=self._data_analysis_process.export_jobs,
                    completed_jobs=self._data_analysis_process.completed_jobs,
                    processing_jobs=self._data_analysis_process.processing_jobs,
                    download_url=self._data_analysis_process.download_url,
                    error_message=self._data_analysis_process.error_message,
                )

                # Mark step passed
                self._report.step_passed("data_analysis", {
                    "Status": self._data_analysis_process.job_status,
                    "Jobs": len(self._data_analysis_process.completed_jobs),
                })
            except Exception as e:
                error_msg = f"Data Analysis Process failed: {e}"
                logger.error(f"❌ {error_msg}")
                errors.append(error_msg)
                self._report.add_error(error_msg)
                self._report.step_failed("data_analysis", str(e))
        else:
            logger.info("⏸ RUN_DATA_ANALYSIS_PROCESS is disabled - skipping")
            self._report.step_skipped("data_analysis", "Disabled in config")
            self._report.set_data_analysis_data(
                enabled=False,
                job_id=None,
                job_status="not_started",
                file_path=None,
                file_size=None,
                export_jobs=[],
                completed_jobs=[],
                processing_jobs=[],
                download_url=None,
                error_message=None,
            )

        # ============================================
        # STEP 7: Business Report Process
        # NOTE: Business Report now runs automatically inside DataAnalysisProcess
        # This separate step only runs if DataAnalysis was disabled but you still want a report
        # ============================================
        if INPUTS.RUN_BUSINESS_REPORT_PROCESS:
            # Check if BusinessReport already ran inside DataAnalysis
            if (
                self._data_analysis_process
                and self._data_analysis_process.business_report
            ):
                logger.info("=" * 60)
                logger.info("📊 Business Report already ran inside Data Analysis Process")
                logger.info("=" * 60)
                self._business_report_process = self._data_analysis_process.business_report
                if self._business_report_process and self._business_report_process.report_path:
                    logger.info(f"📊 Business Report: {self._business_report_process.report_path}")
                    self._report.step_passed("business_report", {
                        "Source": "DataAnalysis",
                        "Report": "Generated",
                    })
            else:
                # Run standalone Business Report
                logger.info("=" * 60)
                logger.info("🔄 RUN_BUSINESS_REPORT_PROCESS is enabled (standalone)")
                logger.info("=" * 60)

                self._report.step_start("business_report")

                try:
                    self._business_report_process = BusinessReportProcess()
                    self._business_report_process.start()
                    logger.info(f"📊 Business Report: {self._business_report_process.report_path}")

                    self._report.step_passed("business_report", {
                        "Source": "Standalone",
                        "Report": "Generated",
                    })
                except Exception as e:
                    error_msg = f"Business Report Process failed: {e}"
                    logger.error(f"❌ {error_msg}")
                    errors.append(error_msg)
                    self._report.add_error(error_msg)
                    self._report.step_failed("business_report", str(e))
        else:
            logger.info("⏸ RUN_BUSINESS_REPORT_PROCESS is disabled - skipping")
            self._report.step_skipped("business_report", "Disabled in config")

        # Finish report and generate
        self._report.finish()

        # Log final status
        logger.info("=" * 60)
        if errors:
            logger.error(f"⚠ Workflow completed with {len(errors)} error(s):")
            for err in errors:
                logger.error(f"  - {err}")
            logger.info("=" * 60)
            # Generate report before raising error
            self._generate_report()
            raise RuntimeError(f"Workflow failed with {len(errors)} error(s)")
        else:
            logger.info("✅ All workflows completed successfully")
            logger.info("=" * 60)
            # Generate report
            self._generate_report()

    @property
    def orders(self) -> list[dict]:
        """Get orders from order management process."""
        if self._order_process:
            return self._order_process.orders
        return []

    @property
    def spreadsheet_id(self) -> str | None:
        """Get spreadsheet ID from order management process."""
        if self._order_process:
            return self._order_process.spreadsheet_id
        return None

    @property
    def update_payment_count(self) -> int:
        """Get count of updated payments."""
        if self._update_payment_process:
            return self._update_payment_process.updated_count
        return 0

    def get_orders(self) -> list[dict]:
        """Get the processed orders."""
        return self.orders

    def get_spreadsheet_url(self) -> str | None:
        """Get the URL of the created Google Sheet."""
        if self._order_process:
            return self._order_process.spreadsheet_url
        return None

    def get_report_path(self) -> str | None:
        """Get the path to the generated report."""
        return self._report_path

    def _generate_report(self) -> None:
        """Generate the HTML report."""
        try:
            self._report_path = self._report.generate_report()
            logger.info(f"📊 Report generated: {self._report_path}")
        except Exception as e:
            logger.error(f"Failed to generate report: {e}")

    def finish(self) -> None:
        """Finalize the process."""
        logger.info("Finalizing Process...")

        # Log update payment results
        if self._update_payment_process:
            logger.info(f"Payments updated to 'paid': {self._update_payment_process.updated_count}")

        # Log order management results
        if self._order_process:
            logger.info(f"Total orders: {len(self.orders)}")
            if self.spreadsheet_id:
                logger.info(f"Spreadsheet: {self.get_spreadsheet_url()}")

        # Log user management results
        if self._user_process:
            logger.info(f"Total users: {self._user_process.users_count}")
            logger.info(f"New users: {len(self._user_process.new_users)}")

        # Log advertisement management results
        if self._advertisement_process:
            logger.info(f"Total advertisements: {self._advertisement_process.total_count}")

        # Log signup ID management results
        if self._signup_id_process:
            logger.info(f"Total signup IDs: {self._signup_id_process.total_count}")
            logger.info(f"Used: {self._signup_id_process.used_count}")
            logger.info(f"Available: {self._signup_id_process.unused_count}")
            if self._signup_id_process.is_emergency:
                logger.warning("⚠️ EMERGENCY: Low signup IDs!")

        # Log data analysis results
        if self._data_analysis_process:
            logger.info(f"Export Job ID: {self._data_analysis_process.job_id}")
            logger.info(f"Job Status: {self._data_analysis_process.job_status}")
            if self._data_analysis_process.file_path:
                logger.info(f"File: {self._data_analysis_process.file_path}")

        # Log report path
        if self._report_path:
            logger.info(f"Report: {self._report_path}")

        logger.info("Process finalized")
