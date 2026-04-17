"""HTML Report Generator for QwebsiteAutomationBot.

Generates beautiful HTML reports with tabs showing:
- Step execution status (pass/fail/skip)
- Update Payment Sheet process
- Order Management process
- User Management process
- Logs and errors
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from config import CONFIG
from libraries.logger import logger


class StepStatus(Enum):
    """Status of a workflow step."""

    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class StepInfo:
    """Information about a workflow step."""

    name: str
    description: str
    status: StepStatus = StepStatus.PENDING
    start_time: datetime | None = None
    end_time: datetime | None = None
    error_message: str | None = None
    details: dict[str, Any] = field(default_factory=dict)

    @property
    def duration_seconds(self) -> float | None:
        """Get step duration in seconds."""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None

    @property
    def duration_str(self) -> str:
        """Get human-readable duration string."""
        duration = self.duration_seconds
        if duration is None:
            return "N/A"
        if duration < 60:
            return f"{duration:.1f}s"
        minutes = int(duration // 60)
        seconds = duration % 60
        return f"{minutes}m {seconds:.1f}s"


class ReportGenerator:
    """Generates HTML reports for workflow execution with tabbed interface."""

    def __init__(self, report_name: str = "workflow_report") -> None:
        """Initialize the report generator.

        Args:
            report_name: Base name for the report file
        """
        self.report_name = report_name
        self.start_time: datetime | None = None
        self.end_time: datetime | None = None

        # Step tracking
        self.steps: dict[str, StepInfo] = {
            "payment_update": StepInfo(
                name="Payment Update",
                description="Update payment status in Google Sheet",
            ),
            "order_management": StepInfo(
                name="Order Management",
                description="Sync orders between API and Sheet",
            ),
            "user_management": StepInfo(
                name="User Management",
                description="Manage and approve users",
            ),
            "advertisement_management": StepInfo(
                name="Advertisement Management",
                description="Manage and approve advertisements",
            ),
            "signup_id_management": StepInfo(
                name="Signup ID Management",
                description="Monitor signup ID usage",
            ),
            "data_analysis": StepInfo(
                name="Data Analysis",
                description="Export and analyze platform data",
            ),
            "business_report": StepInfo(
                name="Business Report",
                description="Generate business intelligence report",
            ),
        }

        # Data storage for each process
        self.data: dict[str, Any] = {
            "update_payment": {
                "enabled": False,
                "payment_ids": [],
                "updated_count": 0,
                "failed_ids": [],
                "not_found_ids": [],
            },
            "order_management": {
                "enabled": False,
                "api_pending_orders": [],
                "sheet_orders_count": 0,
                "matching_orders": [],
                "new_orders": [],
                "orders_updated_to_completed": [],
                "duplicates_removed": [],
                "status_breakdown": {},
            },
            "user_management": {
                "enabled": False,
                "users": [],
                "users_count": 0,
                "new_users": [],
                "updated_users": [],
                "approved_users": [],
                "failed_approvals": [],
                "status_breakdown": {},
                "user_type_breakdown": {},
                "tier_breakdown": {},
                "admin_count": 0,
                "deactivated_count": 0,
            },
            "advertisement_management": {
                "enabled": False,
                "advertisements": [],
                "total_count": 0,
                "status_breakdown": {},
                "type_breakdown": {},
                "payment_status_breakdown": {},
                "pending_count": 0,
                "approved_count": 0,
                "approved_ads": [],
                "failed_approvals": [],
                "payment_updated_ids": [],
                "payment_update_failed_ids": [],
                "status_updated_ids": [],
            },
            "signup_id_management": {
                "enabled": False,
                "signup_ids": [],
                "total_count": 0,
                "used_count": 0,
                "unused_count": 0,
                "usage_percentage": 0.0,
                "is_emergency": False,
                "emergency_threshold": 20,
                "used_signup_ids": [],
                "unused_signup_ids": [],
                "recent_signups": [],
            },
            "data_analysis": {
                "enabled": False,
                "job_id": None,
                "job_status": "not_started",
                "file_path": None,
                "file_size": None,
                "export_jobs": [],
                "completed_jobs": [],
                "processing_jobs": [],
                "download_url": None,
                "error_message": None,
            },
            "errors": [],
            "warnings": [],
        }

    def start(self) -> None:
        """Mark the start of workflow execution."""
        self.start_time = datetime.now()
        logger.info(f"Report tracking started at {self.start_time}")

    def finish(self) -> None:
        """Mark the end of workflow execution."""
        self.end_time = datetime.now()
        logger.info(f"Report tracking finished at {self.end_time}")

    # ============================================
    # STEP TRACKING METHODS
    # ============================================
    def step_start(self, step_id: str) -> None:
        """Mark a step as started.

        Args:
            step_id: Step identifier (e.g., 'payment_update', 'order_management')
        """
        if step_id in self.steps:
            self.steps[step_id].status = StepStatus.RUNNING
            self.steps[step_id].start_time = datetime.now()
            logger.info(f"📍 Step '{self.steps[step_id].name}' started")

    def step_passed(self, step_id: str, details: dict[str, Any] | None = None) -> None:
        """Mark a step as passed.

        Args:
            step_id: Step identifier
            details: Optional details about the step result
        """
        if step_id in self.steps:
            self.steps[step_id].status = StepStatus.PASSED
            self.steps[step_id].end_time = datetime.now()
            if details:
                self.steps[step_id].details = details
            logger.info(f"✅ Step '{self.steps[step_id].name}' PASSED " f"({self.steps[step_id].duration_str})")

    def step_failed(self, step_id: str, error_message: str) -> None:
        """Mark a step as failed.

        Args:
            step_id: Step identifier
            error_message: Error message describing the failure
        """
        if step_id in self.steps:
            self.steps[step_id].status = StepStatus.FAILED
            self.steps[step_id].end_time = datetime.now()
            self.steps[step_id].error_message = error_message
            logger.error(f"❌ Step '{self.steps[step_id].name}' FAILED: {error_message}")

    def step_skipped(self, step_id: str, reason: str = "Disabled") -> None:
        """Mark a step as skipped.

        Args:
            step_id: Step identifier
            reason: Reason for skipping
        """
        if step_id in self.steps:
            self.steps[step_id].status = StepStatus.SKIPPED
            self.steps[step_id].error_message = reason
            logger.info(f"⏭️ Step '{self.steps[step_id].name}' SKIPPED: {reason}")

    def get_step_summary(self) -> dict[str, int]:
        """Get summary of step statuses.

        Returns:
            dict: Count of steps by status
        """
        summary = {
            "total": len(self.steps),
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "pending": 0,
        }
        for step in self.steps.values():
            if step.status == StepStatus.PASSED:
                summary["passed"] += 1
            elif step.status == StepStatus.FAILED:
                summary["failed"] += 1
            elif step.status == StepStatus.SKIPPED:
                summary["skipped"] += 1
            else:
                summary["pending"] += 1
        return summary

    def _generate_step_status_section(self) -> str:
        """Generate the step status section HTML."""
        summary = self.get_step_summary()

        # Status colors and icons
        status_styles = {
            StepStatus.PASSED: ("var(--success)", "✅", "Passed"),
            StepStatus.FAILED: ("var(--danger)", "❌", "Failed"),
            StepStatus.SKIPPED: ("var(--text-muted)", "⏭️", "Skipped"),
            StepStatus.PENDING: ("var(--warning)", "⏳", "Pending"),
            StepStatus.RUNNING: ("var(--info)", "🔄", "Running"),
        }

        # Generate step rows
        step_rows = ""
        for _step_id, step in self.steps.items():
            color, icon, status_text = status_styles.get(step.status, ("var(--text)", "❓", "Unknown"))

            # Get details if available
            details_html = ""
            if step.details:
                details_items = []
                for key, value in step.details.items():
                    details_items.append(f"<span>{key}: <strong>{value}</strong></span>")
                if details_items:
                    details_html = f'<div style="font-size: 0.75rem; color: var(--text-muted); margin-top: 0.25rem;">{" | ".join(details_items)}</div>'

            # Error message if failed
            error_html = ""
            if step.status == StepStatus.FAILED and step.error_message:
                error_html = f'<div style="font-size: 0.75rem; color: var(--danger); margin-top: 0.25rem;">⚠️ {step.error_message}</div>'
            elif step.status == StepStatus.SKIPPED and step.error_message:
                error_html = f'<div style="font-size: 0.75rem; color: var(--text-muted); margin-top: 0.25rem;">{step.error_message}</div>'

            step_rows += f"""
                <div class="step-row" style="display: flex; align-items: center; padding: 0.75rem 1rem;
                    background: var(--bg-tab); border-radius: 0.5rem; margin-bottom: 0.5rem;
                    border-left: 4px solid {color};">
                    <div style="font-size: 1.25rem; margin-right: 1rem;">{icon}</div>
                    <div style="flex: 1;">
                        <div style="font-weight: 600;">{step.name}</div>
                        <div style="font-size: 0.8rem; color: var(--text-muted);">{step.description}</div>
                        {details_html}
                        {error_html}
                    </div>
                    <div style="text-align: right;">
                        <div style="font-size: 0.9rem; font-weight: 500; color: {color};">{status_text}</div>
                        <div style="font-size: 0.75rem; color: var(--text-muted);">{step.duration_str}</div>
                    </div>
                </div>
            """

        # Calculate pass rate
        executed = summary["passed"] + summary["failed"]
        pass_rate = (summary["passed"] / executed * 100) if executed > 0 else 0

        # Overall status
        if summary["failed"] > 0:
            overall_status = ("var(--danger)", "❌", "FAILED")
        elif summary["passed"] == summary["total"]:
            overall_status = ("var(--success)", "✅", "ALL PASSED")
        elif summary["passed"] > 0:
            overall_status = ("var(--warning)", "⚠️", "PARTIAL")
        else:
            overall_status = ("var(--text-muted)", "⏳", "NOT RUN")

        return f"""
        <div class="step-status-section" style="background: var(--bg-card); border-radius: 1rem;
            padding: 1.5rem; margin-bottom: 2rem; border: 1px solid var(--border);">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                <h2 style="font-size: 1.25rem; display: flex; align-items: center; gap: 0.5rem;">
                    📋 Step Execution Status
                </h2>
                <div style="display: flex; gap: 1rem; align-items: center;">
                    <span style="font-size: 1.5rem;">{overall_status[1]}</span>
                    <span style="font-weight: 700; font-size: 1.1rem; color: {overall_status[0]};">
                        {overall_status[2]}
                    </span>
                </div>
            </div>

            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
                gap: 0.75rem; margin-bottom: 1.5rem;">
                <div style="background: var(--bg-tab); padding: 1rem; border-radius: 0.5rem; text-align: center;">
                    <div style="font-size: 1.5rem; font-weight: 700; color: var(--success);">{summary["passed"]}</div>
                    <div style="font-size: 0.8rem; color: var(--text-muted);">Passed</div>
                </div>
                <div style="background: var(--bg-tab); padding: 1rem; border-radius: 0.5rem; text-align: center;">
                    <div style="font-size: 1.5rem; font-weight: 700; color: var(--danger);">{summary["failed"]}</div>
                    <div style="font-size: 0.8rem; color: var(--text-muted);">Failed</div>
                </div>
                <div style="background: var(--bg-tab); padding: 1rem; border-radius: 0.5rem; text-align: center;">
                    <div style="font-size: 1.5rem; font-weight: 700; color: var(--text-muted);">{summary["skipped"]}</div>
                    <div style="font-size: 0.8rem; color: var(--text-muted);">Skipped</div>
                </div>
                <div style="background: var(--bg-tab); padding: 1rem; border-radius: 0.5rem; text-align: center;">
                    <div style="font-size: 1.5rem; font-weight: 700; color: var(--primary);">{pass_rate:.0f}%</div>
                    <div style="font-size: 0.8rem; color: var(--text-muted);">Pass Rate</div>
                </div>
            </div>

            <div class="step-list">
                {step_rows}
            </div>
        </div>
        """

    def set_update_payment_data(
        self,
        enabled: bool,
        payment_ids: list[str],
        updated_count: int,
        failed_ids: list[str],
        not_found_ids: list[str],
    ) -> None:
        """Set update payment process data."""
        self.data["update_payment"] = {
            "enabled": enabled,
            "payment_ids": payment_ids,
            "updated_count": updated_count,
            "failed_ids": failed_ids,
            "not_found_ids": not_found_ids,
        }

    def set_order_management_data(
        self,
        enabled: bool,
        api_pending_orders: list[dict],
        sheet_orders_count: int,
        matching_orders: list[dict],
        new_orders: list[dict],
        orders_updated_to_completed: list[str],
        duplicates_removed: list[str],
        status_breakdown: dict[str, int],
        doctor_debts: list[dict] | None = None,
    ) -> None:
        """Set order management process data."""
        self.data["order_management"] = {
            "enabled": enabled,
            "api_pending_orders": api_pending_orders,
            "sheet_orders_count": sheet_orders_count,
            "matching_orders": matching_orders,
            "new_orders": new_orders,
            "orders_updated_to_completed": orders_updated_to_completed,
            "duplicates_removed": duplicates_removed,
            "status_breakdown": status_breakdown,
            "doctor_debts": doctor_debts or [],
        }

    def set_user_management_data(
        self,
        enabled: bool,
        users: list[dict],
        users_count: int,
        new_users: list[dict],
        updated_users: list[str],
        approved_users: list[str],
        failed_approvals: list[str],
        status_breakdown: dict[str, int],
        user_type_breakdown: dict[str, int],
        tier_breakdown: dict[str, int],
        admin_count: int,
        deactivated_count: int,
    ) -> None:
        """Set user management process data."""
        self.data["user_management"] = {
            "enabled": enabled,
            "users": users,
            "users_count": users_count,
            "new_users": new_users,
            "updated_users": updated_users,
            "approved_users": approved_users,
            "failed_approvals": failed_approvals,
            "status_breakdown": status_breakdown,
            "user_type_breakdown": user_type_breakdown,
            "tier_breakdown": tier_breakdown,
            "admin_count": admin_count,
            "deactivated_count": deactivated_count,
        }

    def set_advertisement_management_data(
        self,
        enabled: bool,
        advertisements: list[dict],
        total_count: int,
        status_breakdown: dict[str, int],
        type_breakdown: dict[str, int],
        payment_status_breakdown: dict[str, int],
        pending_count: int = 0,
        approved_count: int = 0,
        approved_ads: list[dict] | None = None,
        failed_approvals: list[str] | None = None,
        payment_updated_ids: list[str] | None = None,
        payment_update_failed_ids: list[str] | None = None,
        status_updated_ids: list[str] | None = None,
    ) -> None:
        """Set advertisement management process data."""
        self.data["advertisement_management"] = {
            "enabled": enabled,
            "advertisements": advertisements,
            "total_count": total_count,
            "status_breakdown": status_breakdown,
            "type_breakdown": type_breakdown,
            "payment_status_breakdown": payment_status_breakdown,
            "pending_count": pending_count,
            "approved_count": approved_count,
            "approved_ads": approved_ads or [],
            "failed_approvals": failed_approvals or [],
            "payment_updated_ids": payment_updated_ids or [],
            "payment_update_failed_ids": payment_update_failed_ids or [],
            "status_updated_ids": status_updated_ids or [],
        }

    def set_signup_id_management_data(
        self,
        enabled: bool,
        signup_ids: list[dict],
        total_count: int,
        used_count: int,
        unused_count: int,
        usage_percentage: float,
        is_emergency: bool,
        emergency_threshold: int,
        used_signup_ids: list[dict],
        unused_signup_ids: list[dict],
        recent_signups: list[dict],
    ) -> None:
        """Set signup ID management process data."""
        self.data["signup_id_management"] = {
            "enabled": enabled,
            "signup_ids": signup_ids,
            "total_count": total_count,
            "used_count": used_count,
            "unused_count": unused_count,
            "usage_percentage": usage_percentage,
            "is_emergency": is_emergency,
            "emergency_threshold": emergency_threshold,
            "used_signup_ids": used_signup_ids,
            "unused_signup_ids": unused_signup_ids,
            "recent_signups": recent_signups,
        }

    def set_data_analysis_data(
        self,
        enabled: bool,
        job_id: str | None,
        job_status: str,
        file_path: str | None,
        file_size: int | None,
        export_jobs: list[dict],
        completed_jobs: list[dict],
        processing_jobs: list[dict],
        download_url: str | None,
        error_message: str | None,
    ) -> None:
        """Set data analysis process data."""
        self.data["data_analysis"] = {
            "enabled": enabled,
            "job_id": job_id,
            "job_status": job_status,
            "file_path": file_path,
            "file_size": file_size,
            "export_jobs": export_jobs,
            "completed_jobs": completed_jobs,
            "processing_jobs": processing_jobs,
            "download_url": download_url,
            "error_message": error_message,
        }

    def add_error(self, error: str) -> None:
        """Add an error message."""
        self.data["errors"].append(
            {
                "timestamp": datetime.now().isoformat(),
                "message": error,
            }
        )

    def add_warning(self, warning: str) -> None:
        """Add a warning message."""
        self.data["warnings"].append(
            {
                "timestamp": datetime.now().isoformat(),
                "message": warning,
            }
        )

    def generate_report(self) -> str:
        """Generate the HTML report.

        Returns:
            str: Path to the generated report file
        """
        # Ensure output directory exists
        CONFIG.ensure_directories()

        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"{self.report_name}_{timestamp}.html"
        filepath = CONFIG.OUTPUT_DIR / filename

        # Generate HTML content
        html_content = self._generate_html()

        # Write file
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html_content)

        logger.info(f"✓ Report generated: {filepath}")
        return str(filepath)

    def _generate_html(self) -> str:
        """Generate the HTML content with tabbed interface."""
        duration = ""
        if self.start_time and self.end_time:
            delta = self.end_time - self.start_time
            duration = f"{delta.total_seconds():.2f} seconds"

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>QwebsiteAutomationBot Report - {datetime.now().strftime("%Y-%m-%d %H:%M")}</title>
    <style>
        :root {{
            --primary: #6366f1;
            --primary-dark: #4f46e5;
            --success: #10b981;
            --warning: #f59e0b;
            --danger: #ef4444;
            --info: #3b82f6;
            --purple: #8b5cf6;
            --bg-dark: #0f172a;
            --bg-card: #1e293b;
            --bg-tab: #334155;
            --text: #e2e8f0;
            --text-muted: #94a3b8;
            --border: #334155;
        }}

        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
            background: linear-gradient(135deg, var(--bg-dark) 0%, #1a1a2e 100%);
            color: var(--text);
            min-height: 100vh;
            padding: 2rem;
        }}

        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}

        .header {{
            text-align: center;
            margin-bottom: 2rem;
            padding: 2rem;
            background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%);
            border-radius: 1rem;
            box-shadow: 0 10px 40px rgba(99, 102, 241, 0.3);
        }}

        .header h1 {{
            font-size: 2.5rem;
            margin-bottom: 0.5rem;
            text-shadow: 0 2px 4px rgba(0,0,0,0.2);
        }}

        .header .subtitle {{
            color: rgba(255,255,255,0.8);
            font-size: 1.1rem;
        }}

        .meta-info {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
            margin-bottom: 2rem;
        }}

        .meta-card {{
            background: var(--bg-card);
            padding: 1.5rem;
            border-radius: 0.75rem;
            border: 1px solid var(--border);
        }}

        .meta-card .label {{
            color: var(--text-muted);
            font-size: 0.875rem;
            margin-bottom: 0.5rem;
        }}

        .meta-card .value {{
            font-size: 1.25rem;
            font-weight: 600;
        }}

        /* Tab Styles */
        .tabs-container {{
            background: var(--bg-card);
            border-radius: 1rem;
            overflow: hidden;
            border: 1px solid var(--border);
            margin-bottom: 2rem;
        }}

        .tab-buttons {{
            display: flex;
            background: var(--bg-tab);
            border-bottom: 1px solid var(--border);
            overflow-x: auto;
        }}

        .tab-btn {{
            flex: 1;
            min-width: 100px;
            padding: 0.6rem 0.8rem;
            border: none;
            background: transparent;
            color: var(--text-muted);
            font-size: 0.8rem;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.3s ease;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            gap: 0.25rem;
            border-bottom: 3px solid transparent;
        }}

        .tab-btn:hover {{
            background: rgba(255,255,255,0.05);
            color: var(--text);
        }}

        .tab-btn.active {{
            color: var(--primary);
            background: var(--bg-card);
            border-bottom-color: var(--primary);
        }}

        .tab-btn .icon {{
            font-size: 1rem;
        }}

        .tab-btn .badge {{
            font-size: 0.6rem;
            padding: 0.15rem 0.5rem;
            border-radius: 9999px;
            margin-left: 0.5rem;
        }}

        .tab-content {{
            display: none;
            padding: 2rem;
            animation: fadeIn 0.3s ease;
        }}

        .tab-content.active {{
            display: block;
        }}

        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(10px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}

        /* Section Styles */
        .section-header {{
            display: flex;
            align-items: center;
            gap: 0.75rem;
            font-size: 1.5rem;
            margin-bottom: 1.5rem;
            padding-bottom: 1rem;
            border-bottom: 1px solid var(--border);
        }}

        .section-header .icon {{
            width: 40px;
            height: 40px;
            border-radius: 0.5rem;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.5rem;
        }}

        .icon-payment {{ background: rgba(16, 185, 129, 0.2); }}
        .icon-order {{ background: rgba(59, 130, 246, 0.2); }}
        .icon-user {{ background: rgba(139, 92, 246, 0.2); }}
        .icon-log {{ background: rgba(239, 68, 68, 0.2); }}

        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 1rem;
            margin-bottom: 1.5rem;
        }}

        .stat-card {{
            background: rgba(255,255,255,0.05);
            padding: 1.25rem;
            border-radius: 0.75rem;
            text-align: center;
            border: 1px solid rgba(255,255,255,0.1);
        }}

        .stat-card .number {{
            font-size: 2rem;
            font-weight: 700;
            margin-bottom: 0.25rem;
        }}

        .stat-card .label {{
            color: var(--text-muted);
            font-size: 0.875rem;
        }}

        .stat-success .number {{ color: var(--success); }}
        .stat-warning .number {{ color: var(--warning); }}
        .stat-danger .number {{ color: var(--danger); }}
        .stat-info .number {{ color: var(--info); }}
        .stat-purple .number {{ color: var(--purple); }}

        .badge {{
            display: inline-block;
            padding: 0.25rem 0.75rem;
            border-radius: 9999px;
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
        }}

        .badge-success {{ background: rgba(16, 185, 129, 0.2); color: var(--success); }}
        .badge-warning {{ background: rgba(245, 158, 11, 0.2); color: var(--warning); }}
        .badge-danger {{ background: rgba(239, 68, 68, 0.2); color: var(--danger); }}
        .badge-info {{ background: rgba(59, 130, 246, 0.2); color: var(--info); }}
        .badge-purple {{ background: rgba(139, 92, 246, 0.2); color: var(--purple); }}
        .badge-disabled {{ background: rgba(148, 163, 184, 0.2); color: var(--text-muted); }}

        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 1rem;
        }}

        th, td {{
            padding: 1rem;
            text-align: left;
            border-bottom: 1px solid var(--border);
        }}

        th {{
            background: rgba(255,255,255,0.05);
            font-weight: 600;
            color: var(--text-muted);
            text-transform: uppercase;
            font-size: 0.75rem;
            letter-spacing: 0.05em;
        }}

        tr:hover td {{
            background: rgba(255,255,255,0.02);
        }}

        .id-cell {{
            font-family: 'Consolas', 'Monaco', monospace;
            font-size: 0.875rem;
            color: var(--primary);
        }}

        .id-badge {{
            display: inline-block;
            padding: 0.375rem 0.75rem;
            background: var(--surface);
            border-radius: 0.5rem;
            font-family: 'Consolas', 'Monaco', monospace;
            font-size: 0.875rem;
            color: var(--success);
            border: 1px solid var(--border);
        }}

        .emergency-alert {{
            background: linear-gradient(135deg, #dc3545 0%, #b02a37 100%);
            color: white;
            padding: 1.5rem;
            border-radius: 12px;
            margin-bottom: 1.5rem;
            box-shadow: 0 4px 15px rgba(220, 53, 69, 0.4);
        }}
        .emergency-alert h3 {{
            margin: 0 0 0.5rem 0;
            font-size: 1.25rem;
        }}
        .emergency-alert p {{
            margin: 0.25rem 0;
            font-size: 1rem;
        }}
        .emergency-alert .threshold {{
            opacity: 0.9;
            font-size: 0.9rem;
        }}

        .usage-bar-container {{
            margin: 1.5rem 0;
        }}
        .usage-bar-header {{
            display: flex;
            justify-content: space-between;
            margin-bottom: 0.5rem;
        }}
        .usage-label {{
            font-weight: 600;
        }}
        .usage-stats {{
            color: var(--text-muted);
        }}
        .usage-bar-track {{
            background: var(--surface);
            border-radius: 10px;
            height: 24px;
            overflow: hidden;
        }}
        .usage-bar-fill {{
            height: 100%;
            transition: width 0.5s ease;
        }}

        .status-pending {{ color: var(--warning); }}
        .status-paid {{ color: var(--info); }}
        .status-completed {{ color: var(--success); }}

        .empty-state {{
            text-align: center;
            padding: 3rem;
            color: var(--text-muted);
        }}

        .empty-state .icon {{
            font-size: 3rem;
            margin-bottom: 1rem;
            opacity: 0.5;
        }}

        .list-group {{
            list-style: none;
        }}

        .list-group li {{
            padding: 0.75rem 1rem;
            background: rgba(255,255,255,0.03);
            border-radius: 0.5rem;
            margin-bottom: 0.5rem;
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }}

        .list-group li .icon {{
            font-size: 1.25rem;
        }}

        .footer {{
            text-align: center;
            padding: 2rem;
            color: var(--text-muted);
            font-size: 0.875rem;
        }}

        .process-flow {{
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 1rem;
            flex-wrap: wrap;
            margin: 1.5rem 0;
        }}

        .flow-step {{
            display: flex;
            align-items: center;
            gap: 0.5rem;
            padding: 0.75rem 1.25rem;
            background: rgba(255,255,255,0.05);
            border-radius: 0.5rem;
            border: 1px solid var(--border);
        }}

        .flow-arrow {{
            color: var(--text-muted);
            font-size: 1.5rem;
        }}

        .subsection {{
            margin-top: 1.5rem;
        }}

        .subsection h4 {{
            margin-bottom: 1rem;
            color: var(--text);
        }}

        @media (max-width: 768px) {{
            body {{ padding: 1rem; }}
            .header h1 {{ font-size: 1.75rem; }}
            .tab-content {{ padding: 1.5rem; }}
            .tab-btn {{ min-width: 80px; padding: 0.5rem 0.5rem; font-size: 0.7rem; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 QwebsiteAutomationBot Report</h1>
            <p class="subtitle">Workflow Execution Summary</p>
        </div>

        <div class="meta-info">
            <div class="meta-card">
                <div class="label">📅 Report Generated</div>
                <div class="value">{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</div>
            </div>
            <div class="meta-card">
                <div class="label">⏱️ Duration</div>
                <div class="value">{duration or "N/A"}</div>
            </div>
            <div class="meta-card">
                <div class="label">📊 Spreadsheet</div>
                <div class="value"><a href="https://docs.google.com/spreadsheets/d/{CONFIG.SOURCE_SPREADSHEET_ID}"
                    target="_blank" style="color: var(--primary);">View Sheet</a></div>
            </div>
        </div>

        {self._generate_step_status_section()}

        <div class="tabs-container">
            <div class="tab-buttons">
                <button class="tab-btn active" onclick="openTab(event, 'tab-payment')">
                    <span class="icon">💳</span>
                    <span>Update Payment</span>
                    {self._get_status_badge("update_payment")}
                </button>
                <button class="tab-btn" onclick="openTab(event, 'tab-order')">
                    <span class="icon">📦</span>
                    <span>Order Management</span>
                    {self._get_status_badge("order_management")}
                </button>
                <button class="tab-btn" onclick="openTab(event, 'tab-user')">
                    <span class="icon">👥</span>
                    <span>User Management</span>
                    {self._get_status_badge("user_management")}
                </button>
                <button class="tab-btn" onclick="openTab(event, 'tab-advertisement')">
                    <span class="icon">📺</span>
                    <span>Advertisement</span>
                    {self._get_status_badge("advertisement_management")}
                </button>
                <button class="tab-btn" onclick="openTab(event, 'tab-signup-id')">
                    <span class="icon">🎟️</span>
                    <span>Signup IDs</span>
                    {self._get_signup_id_badge()}
                </button>
                <button class="tab-btn" onclick="openTab(event, 'tab-data-analysis')">
                    <span class="icon">📊</span>
                    <span>Data Export</span>
                    {self._get_status_badge("data_analysis")}
                </button>
                <button class="tab-btn" onclick="openTab(event, 'tab-logs')">
                    <span class="icon">📋</span>
                    <span>Logs</span>
                    {self._get_logs_badge()}
                </button>
            </div>

            <div id="tab-payment" class="tab-content active">
                {self._generate_update_payment_section()}
            </div>

            <div id="tab-order" class="tab-content">
                {self._generate_order_management_section()}
            </div>

            <div id="tab-user" class="tab-content">
                {self._generate_user_management_section()}
            </div>

            <div id="tab-advertisement" class="tab-content">
                {self._generate_advertisement_management_section()}
            </div>

            <div id="tab-signup-id" class="tab-content">
                {self._generate_signup_id_management_section()}
            </div>

            <div id="tab-data-analysis" class="tab-content">
                {self._generate_data_analysis_section()}
            </div>

            <div id="tab-logs" class="tab-content">
                {self._generate_errors_section()}
            </div>
        </div>

        <div class="footer">
            <p>Generated by QwebsiteAutomationBot • {datetime.now().year}</p>
        </div>
    </div>

    <script>
        function openTab(evt, tabId) {{
            // Hide all tab contents
            var tabContents = document.getElementsByClassName('tab-content');
            for (var i = 0; i < tabContents.length; i++) {{
                tabContents[i].classList.remove('active');
            }}

            // Remove active class from all tab buttons
            var tabBtns = document.getElementsByClassName('tab-btn');
            for (var i = 0; i < tabBtns.length; i++) {{
                tabBtns[i].classList.remove('active');
            }}

            // Show the current tab and add active class to the button
            document.getElementById(tabId).classList.add('active');
            evt.currentTarget.classList.add('active');
        }}
    </script>
</body>
</html>"""

    def _get_status_badge(self, process: str) -> str:
        """Get status badge HTML for a process."""
        data = self.data.get(process, {})
        if data.get("enabled"):
            return '<span class="badge badge-success">ENABLED</span>'
        return '<span class="badge badge-disabled">DISABLED</span>'

    def _get_logs_badge(self) -> str:
        """Get badge for logs tab."""
        errors = len(self.data.get("errors", []))
        warnings = len(self.data.get("warnings", []))
        if errors > 0:
            return f'<span class="badge badge-danger">{errors}</span>'
        if warnings > 0:
            return f'<span class="badge badge-warning">{warnings}</span>'
        return '<span class="badge badge-success">✓</span>'

    def _get_signup_id_badge(self) -> str:
        """Get badge for signup ID tab - shows emergency status."""
        data = self.data.get("signup_id_management", {})
        if not data.get("enabled"):
            return '<span class="badge badge-disabled">DISABLED</span>'
        if data.get("is_emergency"):
            return '<span class="badge badge-danger">⚠️ EMERGENCY</span>'
        unused = data.get("unused_count", 0)
        threshold = data.get("emergency_threshold", 20)
        if unused < threshold * 2:
            return f'<span class="badge badge-warning">{unused} left</span>'
        return f'<span class="badge badge-success">{unused} available</span>'

    def _generate_update_payment_section(self) -> str:
        """Generate the Update Payment section HTML."""
        data = self.data["update_payment"]

        if not data["enabled"]:
            return """
                <div class="section-header">
                    <span class="icon icon-payment">💳</span>
                    <span>Update Payment Process</span>
                    <span class="badge badge-disabled">DISABLED</span>
                </div>
                <div class="empty-state">
                    <div class="icon">⏸️</div>
                    <p>This process was not enabled for this run</p>
                </div>"""

        ids_table = ""
        if data["payment_ids"]:
            rows = ""
            for pid in data["payment_ids"]:
                status = "✅ Updated"
                if pid in data["failed_ids"]:
                    status = "❌ Failed"
                elif pid in data["not_found_ids"]:
                    status = "⚠️ Not Found"
                rows += f"""
                    <tr>
                        <td class="id-cell">{pid}</td>
                        <td>{status}</td>
                    </tr>"""

            ids_table = f"""
            <div class="subsection">
                <h4>📝 Payment IDs Processed</h4>
                <table>
                    <thead>
                        <tr>
                            <th>Payment ID</th>
                            <th>Status</th>
                        </tr>
                    </thead>
                    <tbody>
                        {rows}
                    </tbody>
                </table>
            </div>"""

        return f"""
                <div class="section-header">
                    <span class="icon icon-payment">💳</span>
                    <span>Update Payment Process</span>
                    <span class="badge badge-success">ENABLED</span>
                </div>

                <div class="stats-grid">
                    <div class="stat-card stat-info">
                        <div class="number">{len(data["payment_ids"])}</div>
                        <div class="label">IDs Provided</div>
                    </div>
                    <div class="stat-card stat-success">
                        <div class="number">{data["updated_count"]}</div>
                        <div class="label">Updated to 'paid'</div>
                    </div>
                    <div class="stat-card stat-danger">
                        <div class="number">{len(data["failed_ids"])}</div>
                        <div class="label">Failed</div>
                    </div>
                    <div class="stat-card stat-warning">
                        <div class="number">{len(data["not_found_ids"])}</div>
                        <div class="label">Not Found</div>
                    </div>
                </div>

                {ids_table}"""

    def _generate_order_management_section(self) -> str:
        """Generate the Order Management section HTML."""
        data = self.data["order_management"]

        if not data["enabled"]:
            return """
                <div class="section-header">
                    <span class="icon icon-order">📦</span>
                    <span>Order Management Process</span>
                    <span class="badge badge-disabled">DISABLED</span>
                </div>
                <div class="empty-state">
                    <div class="icon">⏸️</div>
                    <p>This process was not enabled for this run</p>
                </div>"""

        # Status breakdown
        status_html = ""
        if data["status_breakdown"]:
            status_items = ""
            for status, count in sorted(data["status_breakdown"].items()):
                valid_statuses = ["pending", "paid", "completed"]
                status_class = f"status-{status}" if status in valid_statuses else ""
                display_status = status or "empty"
                status_items += (
                    f'<li><span class="icon">📊</span> '
                    f'<span class="{status_class}">{display_status}</span>: {count}</li>'
                )
            status_html = f"""
            <div class="subsection">
                <h4>📊 Sheet Status Breakdown</h4>
                <ul class="list-group">{status_items}</ul>
            </div>"""

        # Duplicates removed
        duplicates_html = ""
        if data["duplicates_removed"]:
            dup_items = ""
            for dup_id in data["duplicates_removed"]:
                dup_items += f'<li><span class="icon">🔄</span> <span class="id-cell">{dup_id}</span></li>'
            duplicates_html = f"""
            <div class="subsection">
                <h4>🗑️ Duplicates Removed</h4>
                <ul class="list-group">{dup_items}</ul>
            </div>"""

        # New orders added
        new_orders_html = ""
        if data["new_orders"]:
            rows = ""
            for order in data["new_orders"]:
                order_id = order.get("id") or order.get("ID") or ""
                order_num = order.get("order_number") or order.get("orderNumber") or ""
                rows += f"""
                    <tr>
                        <td class="id-cell">{order_id}</td>
                        <td>{order_num}</td>
                        <td><span class="badge badge-success">NEW</span></td>
                    </tr>"""
            new_orders_html = f"""
            <div class="subsection">
                <h4>📝 New Orders Added to Sheet</h4>
                <table>
                    <thead>
                        <tr>
                            <th>Order ID</th>
                            <th>Order Number</th>
                            <th>Status</th>
                        </tr>
                    </thead>
                    <tbody>
                        {rows}
                    </tbody>
                </table>
            </div>"""

        # Orders updated to completed
        completed_html = ""
        if data["orders_updated_to_completed"]:
            rows = ""
            for order_id in data["orders_updated_to_completed"]:
                paid_badge = '<span class="badge badge-info">paid</span>'
                done_badge = '<span class="badge badge-success">completed</span>'
                rows += f"""
                    <tr>
                        <td class="id-cell">{order_id}</td>
                        <td>{paid_badge} → {done_badge}</td>
                    </tr>"""
            completed_html = f"""
            <div class="subsection">
                <h4>✅ Orders Updated to Completed</h4>
                <table>
                    <thead>
                        <tr>
                            <th>Order ID</th>
                            <th>Status Change</th>
                        </tr>
                    </thead>
                    <tbody>
                        {rows}
                    </tbody>
                </table>
            </div>"""

        return f"""
                <div class="section-header">
                    <span class="icon icon-order">📦</span>
                    <span>Order Management Process</span>
                    <span class="badge badge-success">ENABLED</span>
                </div>

                <div class="process-flow">
                    <div class="flow-step">📥 API Pending</div>
                    <span class="flow-arrow">→</span>
                    <div class="flow-step">📋 Compare IDs</div>
                    <span class="flow-arrow">→</span>
                    <div class="flow-step">🔄 Update API</div>
                    <span class="flow-arrow">→</span>
                    <div class="flow-step">📝 Update Sheet</div>
                </div>

                <div class="stats-grid">
                    <div class="stat-card stat-info">
                        <div class="number">{len(data["api_pending_orders"])}</div>
                        <div class="label">API Pending Orders</div>
                    </div>
                    <div class="stat-card stat-info">
                        <div class="number">{data["sheet_orders_count"]}</div>
                        <div class="label">Sheet Orders</div>
                    </div>
                    <div class="stat-card stat-info">
                        <div class="number">{len(data["matching_orders"])}</div>
                        <div class="label">Matching Orders</div>
                    </div>
                    <div class="stat-card stat-success">
                        <div class="number">{len(data["new_orders"])}</div>
                        <div class="label">New Orders Added</div>
                    </div>
                    <div class="stat-card stat-success">
                        <div class="number">{len(data["orders_updated_to_completed"])}</div>
                        <div class="label">Updated to Completed</div>
                    </div>
                    <div class="stat-card stat-warning">
                        <div class="number">{len(data["duplicates_removed"])}</div>
                        <div class="label">Duplicates Removed</div>
                    </div>
                </div>

                {status_html}
                {duplicates_html}
                {new_orders_html}
                {completed_html}
                {self._generate_doctor_debts_html(data)}"""

    def _generate_doctor_debts_html(self, data: dict) -> str:
        """Generate the Doctor Debts section HTML with expandable order details.

        Args:
            data: Order management data containing doctor_debts

        Returns:
            str: HTML for doctor debts section with expandable orders
        """
        doctor_debts = data.get("doctor_debts", [])
        if not doctor_debts:
            return ""

        # Calculate total debt
        total_debt = sum(d.get("total_debt", 0) for d in doctor_debts)
        total_orders = sum(d.get("pending_orders_count", 0) for d in doctor_debts)

        # Build expandable doctor cards
        doctor_cards = ""
        for idx, doc in enumerate(doctor_debts):
            doctor_name = doc.get("doctor_name", "Unknown")
            doctor_email = doc.get("doctor_email", "")
            debt = doc.get("total_debt", 0)
            orders_count = doc.get("pending_orders_count", 0)
            pending_orders = doc.get("pending_orders", [])

            # Debt level styling
            debt_badge = "badge-success"
            if debt >= 100000:
                debt_badge = "badge-error"
            elif debt >= 50000:
                debt_badge = "badge-warning"

            # Build order rows for this doctor
            order_rows = ""
            for order in pending_orders:
                order_number = order.get("order_number", "N/A")
                product_name = order.get("product_name", "N/A")
                qty = order.get("qty", 1)
                order_total = order.get("order_total", 0)
                remaining = order.get("remaining_amount", 0)
                payment_method = order.get("payment_method", "N/A")
                order_date = order.get("order_date", "N/A")
                if order_date and "T" in str(order_date):
                    order_date = str(order_date).split("T")[0]

                # Format amounts
                try:
                    order_total = float(order_total)
                    remaining = float(remaining)
                except (ValueError, TypeError):
                    order_total = 0
                    remaining = 0

                order_rows += f"""
                    <tr>
                        <td><code>{order_number}</code></td>
                        <td>{product_name}</td>
                        <td style="text-align: center;">{qty}</td>
                        <td style="text-align: right;">₨{order_total:,.2f}</td>
                        <td style="text-align: right; color: #e74c3c;"><strong>₨{remaining:,.2f}</strong></td>
                        <td>{payment_method}</td>
                        <td>{order_date}</td>
                    </tr>"""

            # Build card HTML with proper line lengths
            card_style = "border: 1px solid #ddd; border-radius: 8px; margin-bottom: 15px"
            header_style = "padding: 15px; background: #f8f9fa; cursor: pointer"
            header_flex = "display: flex; justify-content: space-between; align-items: center"
            orders_style = "display: none; padding: 15px; background: white"

            doctor_cards += f"""
                <div class="doctor-debt-card" style="{card_style}; overflow: hidden;">
                    <div class="doctor-header" onclick="toggleDoctorOrders('doctor-orders-{idx}')"
                         style="{header_style}; {header_flex};">
                        <div>
                            <span class="toggle-icon" id="icon-doctor-orders-{idx}"
                                  style="margin-right: 10px;">▶</span>
                            <strong style="font-size: 16px;">🩺 {doctor_name}</strong>
                            <span style="color: #666; margin-left: 10px;">{doctor_email}</span>
                        </div>
                        <div style="display: flex; gap: 15px; align-items: center;">
                            <span class="badge {debt_badge}" style="font-size: 14px;">
                                ₨{debt:,.2f}</span>
                            <span style="color: #666;">{orders_count} order(s)</span>
                        </div>
                    </div>
                    <div id="doctor-orders-{idx}" class="doctor-orders" style="{orders_style};">
                        <table style="width: 100%; font-size: 13px;">
                            <thead>
                                <tr style="background: #f1f3f4;">
                                    <th style="padding: 8px;">Order #</th>
                                    <th style="padding: 8px;">Product</th>
                                    <th style="padding: 8px; text-align: center;">Qty</th>
                                    <th style="padding: 8px; text-align: right;">Total</th>
                                    <th style="padding: 8px; text-align: right;">Remaining</th>
                                    <th style="padding: 8px;">Payment Method</th>
                                    <th style="padding: 8px;">Date</th>
                                </tr>
                            </thead>
                            <tbody>
                                {order_rows}
                            </tbody>
                        </table>
                    </div>
                </div>"""

        # JavaScript for toggling
        toggle_script = """
            <script>
                function toggleDoctorOrders(id) {
                    var element = document.getElementById(id);
                    var icon = document.getElementById('icon-' + id);
                    if (element.style.display === 'none') {
                        element.style.display = 'block';
                        icon.textContent = '▼';
                    } else {
                        element.style.display = 'none';
                        icon.textContent = '▶';
                    }
                }
            </script>
        """

        return f"""
            <div class="subsection">
                <h4>💰 Doctor Debts (Pending Orders)</h4>
                <p style="color: #666; margin-bottom: 15px;">
                    Doctors with outstanding payments from pending orders.
                    Total: <strong style="color: #e74c3c;">₨{total_debt:,.2f}</strong> across
                    <strong>{total_orders}</strong> pending orders from
                    <strong>{len(doctor_debts)}</strong> doctors.
                    <br><em style="font-size: 12px;">Click on a doctor to see their pending orders.</em>
                </p>
                {doctor_cards}
            </div>
            {toggle_script}"""

    def _generate_user_management_section(self) -> str:
        """Generate the User Management section HTML."""
        data = self.data["user_management"]

        if not data["enabled"]:
            return """
                <div class="section-header">
                    <span class="icon icon-user">👥</span>
                    <span>User Management Process</span>
                    <span class="badge badge-disabled">DISABLED</span>
                </div>
                <div class="empty-state">
                    <div class="icon">⏸️</div>
                    <p>This process was not enabled for this run</p>
                </div>"""

        # User type breakdown
        user_type_html = ""
        if data.get("user_type_breakdown"):
            type_items = ""
            icons = {"doctor": "🩺", "employee": "👔", "regular_user": "👤"}
            for utype, count in sorted(data["user_type_breakdown"].items(), key=lambda x: -x[1]):
                icon = icons.get(utype, "👥")
                type_items += f'<li><span class="icon">{icon}</span> <strong>{utype}</strong>: {count}</li>'
            user_type_html = f"""
            <div class="subsection">
                <h4>👥 User Types</h4>
                <ul class="list-group">{type_items}</ul>
            </div>"""

        # Tier breakdown
        tier_html = ""
        if data.get("tier_breakdown"):
            tier_items = ""
            icons = {"Diamond Lead": "💎", "Platinum Lead": "🏆", "Expert Contributor": "⭐"}
            for tier, count in sorted(data["tier_breakdown"].items(), key=lambda x: -x[1]):
                icon = icons.get(tier, "📊")
                tier_items += f'<li><span class="icon">{icon}</span> <strong>{tier}</strong>: {count}</li>'
            tier_html = f"""
            <div class="subsection">
                <h4>🏅 Tier Distribution</h4>
                <ul class="list-group">{tier_items}</ul>
            </div>"""

        # Approved users this run
        approved_html = ""
        if data.get("approved_users"):
            items = ""
            for user_id in data["approved_users"]:
                items += f'<li><span class="icon">✅</span> <span class="id-cell">{user_id}</span></li>'
            approved_html = f"""
            <div class="subsection">
                <h4>🎉 Users Approved This Run</h4>
                <ul class="list-group">{items}</ul>
            </div>"""

        # Failed approvals
        failed_html = ""
        if data.get("failed_approvals"):
            items = ""
            for user_id in data["failed_approvals"]:
                items += f'<li><span class="icon">❌</span> <span class="id-cell">{user_id}</span></li>'
            failed_html = f"""
            <div class="subsection">
                <h4>❌ Failed Approvals</h4>
                <ul class="list-group">{items}</ul>
            </div>"""

        # All users table
        users_table = self._generate_users_table(data.get("users", []))

        return f"""
                <div class="section-header">
                    <span class="icon icon-user">👥</span>
                    <span>User Management Process</span>
                    <span class="badge badge-success">ENABLED</span>
                </div>

                <div class="process-flow">
                    <div class="flow-step">📥 Fetch Users</div>
                    <span class="flow-arrow">→</span>
                    <div class="flow-step">🔍 Check is_approved</div>
                    <span class="flow-arrow">→</span>
                    <div class="flow-step">✅ Approve Doctors</div>
                    <span class="flow-arrow">→</span>
                    <div class="flow-step">📊 Generate Report</div>
                </div>

                <div class="stats-grid">
                    <div class="stat-card stat-purple">
                        <div class="number">{data["users_count"]}</div>
                        <div class="label">Total Users</div>
                    </div>
                    <div class="stat-card stat-success">
                        <div class="number">{data.get("status_breakdown", {}).get("approved", 0)}</div>
                        <div class="label">Approved</div>
                    </div>
                    <div class="stat-card stat-warning">
                        <div class="number">{data.get("status_breakdown", {}).get("unapproved", 0)}</div>
                        <div class="label">Unapproved</div>
                    </div>
                    <div class="stat-card stat-info">
                        <div class="number">{data.get("admin_count", 0)}</div>
                        <div class="label">Admins</div>
                    </div>
                    <div class="stat-card stat-danger">
                        <div class="number">{data.get("deactivated_count", 0)}</div>
                        <div class="label">Deactivated</div>
                    </div>
                    <div class="stat-card stat-success">
                        <div class="number">{len(data.get("approved_users", []))}</div>
                        <div class="label">Approved This Run</div>
                    </div>
                </div>

                {user_type_html}
                {tier_html}
                {approved_html}
                {failed_html}
                {users_table}"""

    def _generate_users_table(self, users: list[dict]) -> str:
        """Generate HTML table for all users."""
        if not users:
            return ""

        rows = ""
        for user in users[:50]:  # Limit to 50 users
            user_id = str(user.get("id", ""))[:8] + "..."
            email = user.get("email", "N/A")
            name = user.get("doctor_name") or user.get("name") or "N/A"
            user_type = user.get("user_type", "N/A")
            tier = user.get("tier", "N/A")
            is_approved = user.get("is_approved", False)
            is_admin = user.get("is_admin", False)
            is_deactivated = user.get("is_deactivated", False)

            badges = ""
            if is_approved:
                badges += '<span class="badge badge-success">Approved</span> '
            else:
                badges += '<span class="badge badge-warning">Pending</span> '
            if is_admin:
                badges += '<span class="badge badge-purple">Admin</span> '
            if is_deactivated:
                badges += '<span class="badge badge-danger">Deactivated</span> '

            rows += f"""
                <tr>
                    <td class="id-cell">{user_id}</td>
                    <td>{email}</td>
                    <td>{name}</td>
                    <td>{user_type}</td>
                    <td>{tier}</td>
                    <td>{badges}</td>
                </tr>"""

        more_text = ""
        if len(users) > 50:
            more_text = f'<p style="color: var(--text-muted); margin-top: 1rem;">... and {len(users) - 50} more</p>'

        return f"""
            <div class="subsection">
                <h4>📋 All Users ({len(users)})</h4>
                <table>
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>Email</th>
                            <th>Name</th>
                            <th>Type</th>
                            <th>Tier</th>
                            <th>Status</th>
                        </tr>
                    </thead>
                    <tbody>
                        {rows}
                    </tbody>
                </table>
                {more_text}
            </div>"""

    def _generate_advertisement_management_section(self) -> str:
        """Generate the Advertisement Management section HTML."""
        data = self.data["advertisement_management"]

        if not data["enabled"]:
            return """
                <div class="section-header">
                    <span class="icon icon-ad">📺</span>
                    <span>Advertisement Management Process</span>
                    <span class="badge badge-disabled">DISABLED</span>
                </div>
                <div class="empty-state">
                    <div class="icon">⏸️</div>
                    <p>This process was not enabled for this run</p>
                </div>"""

        # Status breakdown
        status_html = ""
        if data.get("status_breakdown"):
            items = ""
            icons = {
                "pending": "⏳",
                "completed": "✅",
                "rejected": "❌",
                "active": "🟢",
            }
            for status, count in sorted(data["status_breakdown"].items(), key=lambda x: -x[1]):
                icon = icons.get(status, "📊")
                items += f'<li><span class="icon">{icon}</span> <strong>{status}</strong>: {count}</li>'
            status_html = f"""
            <div class="subsection">
                <h4>📊 Status Breakdown</h4>
                <ul class="list-group">{items}</ul>
            </div>"""

        # Type breakdown
        type_html = ""
        if data.get("type_breakdown"):
            items = ""
            icons = {"video": "🎬", "image": "🖼️", "animation": "🎞️"}
            for ad_type, count in sorted(data["type_breakdown"].items(), key=lambda x: -x[1]):
                icon = icons.get(ad_type, "📦")
                items += f'<li><span class="icon">{icon}</span> <strong>{ad_type}</strong>: {count}</li>'
            type_html = f"""
            <div class="subsection">
                <h4>🎨 Type Breakdown</h4>
                <ul class="list-group">{items}</ul>
            </div>"""

        # Payment status breakdown
        payment_html = ""
        if data.get("payment_status_breakdown"):
            items = ""
            icons = {"paid": "💰", "pending": "⏳", "failed": "❌"}
            for status, count in sorted(data["payment_status_breakdown"].items(), key=lambda x: -x[1]):
                icon = icons.get(status, "💳")
                items += f'<li><span class="icon">{icon}</span> <strong>{status}</strong>: {count}</li>'
            payment_html = f"""
            <div class="subsection">
                <h4>💳 Payment Status</h4>
                <ul class="list-group">{items}</ul>
            </div>"""

        # Approved advertisements this run
        approved_html = ""
        if data.get("approved_ads"):
            items = ""
            for ad in data["approved_ads"]:
                ad_id = ad.get("id", "")[:8] + "..."
                title = ad.get("title", "N/A")[:20]
                items += f'<li><span class="icon">✅</span> <span class="id-cell">{ad_id}</span> - {title}</li>'
            approved_html = f"""
            <div class="subsection">
                <h4>🎉 Advertisements Approved via API ({len(data["approved_ads"])})</h4>
                <ul class="list-group">{items}</ul>
            </div>"""

        # Status updated to active in sheet
        status_updated_html = ""
        if data.get("status_updated_ids"):
            items = ""
            for ad_id in data["status_updated_ids"]:
                items += f'<li><span class="icon">🟢</span> <span class="id-cell">{ad_id}</span> → Status: active</li>'
            status_updated_html = f"""
            <div class="subsection">
                <h4>🟢 Status Updated to 'active' in Sheet ({len(data["status_updated_ids"])})</h4>
                <ul class="list-group">{items}</ul>
            </div>"""

        # Failed approvals
        failed_html = ""
        if data.get("failed_approvals"):
            items = ""
            for ad_id in data["failed_approvals"]:
                items += f'<li><span class="icon">❌</span> <span class="id-cell">{ad_id}</span></li>'
            failed_html = f"""
            <div class="subsection">
                <h4 style="color: var(--danger);">❌ Failed Approvals ({len(data["failed_approvals"])})</h4>
                <ul class="list-group">{items}</ul>
            </div>"""

        # Payment updates this run
        payment_updates_html = ""
        if data.get("payment_updated_ids"):
            items = ""
            for ad_id in data["payment_updated_ids"]:
                items += f'<li><span class="icon">💰</span> <span class="id-cell">{ad_id}</span></li>'
            payment_updates_html = f"""
            <div class="subsection">
                <h4>💰 Payment Status Updated to Paid ({len(data["payment_updated_ids"])})</h4>
                <ul class="list-group">{items}</ul>
            </div>"""

        # Payment update failures
        payment_failed_html = ""
        if data.get("payment_update_failed_ids"):
            items = ""
            for ad_id in data["payment_update_failed_ids"]:
                items += f'<li><span class="icon">⚠️</span> <span class="id-cell">{ad_id}</span> (not found)</li>'
            failed_count = len(data["payment_update_failed_ids"])
            payment_failed_html = f"""
            <div class="subsection">
                <h4 style="color: var(--warning);">⚠️ Payment Update Failed ({failed_count})</h4>
                <ul class="list-group">{items}</ul>
            </div>"""

        # Advertisements table - show approved ads if available
        ads_to_show = data.get("approved_ads") or data.get("advertisements", [])
        ads_table = self._generate_advertisements_table(ads_to_show)

        return f"""
                <div class="section-header">
                    <span class="icon icon-ad">📺</span>
                    <span>Advertisement Management Process</span>
                    <span class="badge badge-success">ENABLED</span>
                </div>

                <div class="process-flow">
                    <div class="flow-step">📥 Fetch Ads</div>
                    <span class="flow-arrow">→</span>
                    <div class="flow-step">💰 Update Payments</div>
                    <span class="flow-arrow">→</span>
                    <div class="flow-step">🔍 Filter Pending</div>
                    <span class="flow-arrow">→</span>
                    <div class="flow-step">✅ Approve Ads</div>
                    <span class="flow-arrow">→</span>
                    <div class="flow-step">📝 Write to Sheet</div>
                </div>

                <div class="stats-grid">
                    <div class="stat-card stat-purple">
                        <div class="number">{data["total_count"]}</div>
                        <div class="label">Total Fetched</div>
                    </div>
                    <div class="stat-card stat-warning">
                        <div class="number">{data.get("pending_count", 0)}</div>
                        <div class="label">Pending Found</div>
                    </div>
                    <div class="stat-card stat-success">
                        <div class="number">{data.get("approved_count", 0)}</div>
                        <div class="label">API Approved</div>
                    </div>
                    <div class="stat-card stat-info">
                        <div class="number">{len(data.get("status_updated_ids", []))}</div>
                        <div class="label">Sheet → Active</div>
                    </div>
                    <div class="stat-card stat-secondary">
                        <div class="number">{len(data.get("payment_updated_ids", []))}</div>
                        <div class="label">Sheet → Paid</div>
                    </div>
                    <div class="stat-card stat-danger">
                        <div class="number">{len(data.get("failed_approvals", []))}</div>
                        <div class="label">Failed</div>
                    </div>
                </div>

                {approved_html}
                {status_updated_html}
                {failed_html}
                {payment_updates_html}
                {payment_failed_html}
                {status_html}
                {type_html}
                {payment_html}
                {ads_table}"""

    def _generate_advertisements_table(self, advertisements: list[dict]) -> str:
        """Generate HTML table for all advertisements."""
        if not advertisements:
            return ""

        rows = ""
        for ad in advertisements[:50]:  # Limit to 50
            ad_id = str(ad.get("id", ""))[:8] + "..."
            title = ad.get("title", "N/A")[:20]
            ad_type = ad.get("type", "N/A")
            status = ad.get("status", "N/A")
            payment_status = ad.get("payment_status", "N/A")
            total_cost = ad.get("total_cost", 0)
            paid_amount = ad.get("paid_amount", 0)
            doctor = ad.get("doctor", {})
            doctor_name = doctor.get("doctor_name", "N/A")[:15]

            # Status badges
            status_badge = {
                "completed": "badge-success",
                "pending": "badge-warning",
                "rejected": "badge-danger",
                "active": "badge-info",
            }.get(status, "badge-secondary")

            payment_badge = {
                "paid": "badge-success",
                "pending": "badge-warning",
                "failed": "badge-danger",
            }.get(payment_status, "badge-secondary")

            rows += f"""
                <tr>
                    <td class="id-cell">{ad_id}</td>
                    <td>{title}</td>
                    <td>{ad_type}</td>
                    <td><span class="badge {status_badge}">{status}</span></td>
                    <td><span class="badge {payment_badge}">{payment_status}</span></td>
                    <td>R{total_cost}</td>
                    <td>R{paid_amount}</td>
                    <td>{doctor_name}</td>
                </tr>"""

        more_text = ""
        if len(advertisements) > 50:
            more_text = (
                f'<p style="color: var(--text-muted); margin-top: 1rem;">... and {len(advertisements) - 50} more</p>'
            )

        return f"""
            <div class="subsection">
                <h4>📋 All Advertisements ({len(advertisements)})</h4>
                <table>
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>Title</th>
                            <th>Type</th>
                            <th>Status</th>
                            <th>Payment</th>
                            <th>Cost</th>
                            <th>Paid</th>
                            <th>Doctor</th>
                        </tr>
                    </thead>
                    <tbody>
                        {rows}
                    </tbody>
                </table>
                {more_text}
            </div>"""

    def _generate_signup_id_management_section(self) -> str:
        """Generate the Signup ID Management section HTML."""
        data = self.data["signup_id_management"]

        if not data["enabled"]:
            return """
                <div class="section-header">
                    <span class="icon icon-signup">🎟️</span>
                    <span>Signup ID Management Process</span>
                    <span class="badge badge-disabled">DISABLED</span>
                </div>
                <div class="empty-state">
                    <div class="icon">⏸️</div>
                    <p>This process was not enabled for this run</p>
                </div>"""

        # Emergency alert
        emergency_alert = ""
        if data.get("is_emergency"):
            unused = data["unused_count"]
            threshold = data["emergency_threshold"]
            emergency_alert = f"""
            <div class="emergency-alert">
                <h3>🚨 EMERGENCY: Low Signup IDs!</h3>
                <p>Only <strong>{unused}</strong> signup IDs remaining!</p>
                <p>Please add more signup IDs immediately.</p>
                <p class="threshold">Emergency threshold: {threshold} IDs</p>
            </div>"""

        # Usage bar
        usage_pct = data.get("usage_percentage", 0)
        bar_color = "#28a745"  # green
        if data.get("is_emergency"):
            bar_color = "#dc3545"  # red
        elif data["unused_count"] < data["emergency_threshold"] * 2:
            bar_color = "#ffc107"  # yellow

        used = data["used_count"]
        unused = data["unused_count"]
        usage_bar = f"""
        <div class="usage-bar-container">
            <div class="usage-bar-header">
                <span class="usage-label">Usage: {usage_pct:.1f}%</span>
                <span class="usage-stats">{used} used / {unused} available</span>
            </div>
            <div class="usage-bar-track">
                <div class="usage-bar-fill" style="background:{bar_color};width:{usage_pct}%;"></div>
            </div>
        </div>"""

        # Recent signups table
        recent_table = ""
        if data.get("recent_signups"):
            rows = ""
            for signup in data["recent_signups"][:10]:
                used_at = signup.get("used_at", "")
                if used_at:
                    used_at = used_at[:10]
                rows += f"""
                    <tr>
                        <td><span class="id-cell">{signup.get('signup_id', 'N/A')}</span></td>
                        <td>{signup.get('used_by_email', 'N/A')}</td>
                        <td>{used_at}</td>
                    </tr>"""

            recent_table = f"""
            <div class="subsection">
                <h4>📋 Recent Signups</h4>
                <table class="data-table">
                    <thead>
                        <tr>
                            <th>Signup ID</th>
                            <th>Email</th>
                            <th>Used At</th>
                        </tr>
                    </thead>
                    <tbody>
                        {rows}
                    </tbody>
                </table>
            </div>"""

        # Available IDs preview
        available_preview = ""
        if data.get("unused_signup_ids"):
            preview_ids = data["unused_signup_ids"][:20]
            id_badges = ""
            for sid in preview_ids:
                id_badges += f'<span class="id-badge">{sid.get("signup_id", "N/A")}</span> '
            more_text = ""
            if len(data["unused_signup_ids"]) > 20:
                remaining = len(data["unused_signup_ids"]) - 20
                more_text = (
                    f'<p style="color: var(--text-muted); margin-top: 0.5rem;">... and {remaining} more available</p>'
                )
            available_preview = f"""
            <div class="subsection">
                <h4>🔓 Available Signup IDs (Preview)</h4>
                <div style="display: flex; flex-wrap: wrap; gap: 0.5rem;">
                    {id_badges}
                </div>
                {more_text}
            </div>"""

        return f"""
                <div class="section-header">
                    <span class="icon icon-signup">🎟️</span>
                    <span>Signup ID Management Process</span>
                    <span class="badge badge-success">ENABLED</span>
                </div>

                {emergency_alert}

                <div class="process-flow">
                    <div class="flow-step">📥 Fetch IDs</div>
                    <span class="flow-arrow">→</span>
                    <div class="flow-step">📊 Analyze</div>
                    <span class="flow-arrow">→</span>
                    <div class="flow-step">⚠️ Check Status</div>
                    <span class="flow-arrow">→</span>
                    <div class="flow-step">📊 Report</div>
                </div>

                <div class="stats-grid">
                    <div class="stat-card stat-primary">
                        <div class="number">{data['total_count']}</div>
                        <div class="label">Total IDs</div>
                    </div>
                    <div class="stat-card stat-success">
                        <div class="number">{data['unused_count']}</div>
                        <div class="label">Available</div>
                    </div>
                    <div class="stat-card stat-warning">
                        <div class="number">{data['used_count']}</div>
                        <div class="label">Used</div>
                    </div>
                    <div class="stat-card {'stat-danger' if data.get('is_emergency') else 'stat-info'}">
                        <div class="number">{usage_pct:.1f}%</div>
                        <div class="label">Usage</div>
                    </div>
                </div>

                {usage_bar}
                {recent_table}
                {available_preview}"""

    def _generate_data_analysis_section(self) -> str:
        """Generate the Data Analysis section HTML."""
        data = self.data["data_analysis"]

        if not data["enabled"]:
            return """
                <div class="section-header">
                    <span class="icon icon-data">📊</span>
                    <span>Data Export Process</span>
                    <span class="badge badge-disabled">DISABLED</span>
                </div>
                <div class="empty-state">
                    <div class="icon">⏸️</div>
                    <p>This process was not enabled for this run</p>
                </div>"""

        # Error alert
        error_alert = ""
        if data.get("error_message"):
            error_alert = f"""
            <div class="error-alert" style="background: linear-gradient(135deg, #dc3545 0%, #b02a37 100%);
                color: white; padding: 1.5rem; border-radius: 12px; margin-bottom: 1.5rem;">
                <h3 style="margin: 0 0 0.5rem 0;">❌ Export Error</h3>
                <p style="margin: 0;">{data['error_message']}</p>
            </div>"""

        # Status for display
        status = data.get("job_status", "unknown")

        # File info
        file_info = ""
        if data.get("file_path"):
            file_size = data.get("file_size", 0)
            size_str = self._format_file_size(file_size) if file_size else "N/A"
            file_info = f"""
            <div class="file-info-card" style="background: var(--bg-card); padding: 1.5rem;
                border-radius: 12px; margin: 1rem 0;">
                <h4 style="margin: 0 0 1rem 0;">📁 Downloaded File</h4>
                <div style="display: grid; gap: 0.5rem;">
                    <div><strong>Path:</strong> <code>{data['file_path']}</code></div>
                    <div><strong>Size:</strong> {size_str}</div>
                </div>
            </div>"""

        # Download URL
        download_section = ""
        if data.get("download_url"):
            download_section = f"""
            <div class="download-section" style="margin: 1rem 0;">
                <a href="{data['download_url']}" target="_blank" class="btn btn-primary"
                    style="display: inline-flex; align-items: center; gap: 0.5rem;
                    padding: 0.75rem 1.5rem; background: var(--primary); color: white;
                    text-decoration: none; border-radius: 8px;">
                    <span>⬇️</span> Download Export
                </a>
            </div>"""

        # Export jobs table
        jobs_table = ""
        all_jobs = data.get("export_jobs", [])
        if all_jobs:
            rows = ""
            for job in all_jobs[:10]:
                job_id = job.get("id", "N/A")
                job_status = job.get("status", "N/A")
                created = job.get("createdAt", "")[:19].replace("T", " ") if job.get("createdAt") else "N/A"
                size = job.get("fileSize", 0)
                size_str = self._format_file_size(size) if size else "-"

                status_class = {
                    "completed": "badge-success",
                    "processing": "badge-warning",
                    "failed": "badge-danger",
                }.get(job_status, "badge-info")

                rows += f"""
                    <tr>
                        <td><span class="id-cell">{job_id}</span></td>
                        <td><span class="badge {status_class}">{job_status}</span></td>
                        <td>{created}</td>
                        <td>{size_str}</td>
                    </tr>"""

            jobs_table = f"""
            <div class="subsection">
                <h4>📋 Export Jobs History</h4>
                <table class="data-table">
                    <thead>
                        <tr>
                            <th>Job ID</th>
                            <th>Status</th>
                            <th>Created</th>
                            <th>Size</th>
                        </tr>
                    </thead>
                    <tbody>
                        {rows}
                    </tbody>
                </table>
            </div>"""

        completed_count = len(data.get("completed_jobs", []))
        processing_count = len(data.get("processing_jobs", []))

        return f"""
                <div class="section-header">
                    <span class="icon icon-data">📊</span>
                    <span>Data Export Process</span>
                    <span class="badge badge-success">ENABLED</span>
                </div>

                {error_alert}

                <div class="process-flow">
                    <div class="flow-step">🚀 Start Job</div>
                    <span class="flow-arrow">→</span>
                    <div class="flow-step">⏳ Poll Status</div>
                    <span class="flow-arrow">→</span>
                    <div class="flow-step">📥 Download</div>
                    <span class="flow-arrow">→</span>
                    <div class="flow-step">✅ Complete</div>
                </div>

                <div class="stats-grid">
                    <div class="stat-card stat-primary">
                        <div class="number">{data.get('job_id', 'N/A')[:20] if data.get('job_id') else 'N/A'}...</div>
                        <div class="label">Current Job ID</div>
                    </div>
                    <div class="stat-card {'stat-success' if status == 'completed' else 'stat-warning'}">
                        <div class="number">{status.upper()}</div>
                        <div class="label">Job Status</div>
                    </div>
                    <div class="stat-card stat-info">
                        <div class="number">{completed_count}</div>
                        <div class="label">Completed Jobs</div>
                    </div>
                    <div class="stat-card stat-warning">
                        <div class="number">{processing_count}</div>
                        <div class="label">Processing</div>
                    </div>
                </div>

                {file_info}
                {download_section}
                {jobs_table}"""

    def _format_file_size(self, size: int) -> str:
        """Format file size in human readable format."""
        for unit in ["B", "KB", "MB", "GB"]:
            if size < 1024:
                return f"{size:.2f} {unit}"
            size /= 1024
        return f"{size:.2f} TB"

    def _generate_errors_section(self) -> str:
        """Generate the Errors and Warnings section HTML."""
        errors = self.data["errors"]
        warnings = self.data["warnings"]

        if not errors and not warnings:
            return """
                <div class="section-header">
                    <span class="icon icon-log">📋</span>
                    <span>Logs</span>
                </div>
                <div class="empty-state">
                    <div class="icon">✅</div>
                    <p>No errors or warnings during execution</p>
                </div>"""

        errors_html = ""
        if errors:
            error_items = ""
            for err in errors:
                error_items += (
                    f'<li><span class="icon">❌</span> <strong>{err["timestamp"]}</strong>: {err["message"]}</li>'
                )
            errors_html = f"""
            <div class="subsection">
                <h4 style="color: var(--danger);">❌ Errors ({len(errors)})</h4>
                <ul class="list-group">{error_items}</ul>
            </div>"""

        warnings_html = ""
        if warnings:
            warning_items = ""
            for warn in warnings:
                warning_items += (
                    f'<li><span class="icon">⚠️</span> <strong>{warn["timestamp"]}</strong>: {warn["message"]}</li>'
                )
            warnings_html = f"""
            <div class="subsection">
                <h4 style="color: var(--warning);">⚠️ Warnings ({len(warnings)})</h4>
                <ul class="list-group">{warning_items}</ul>
            </div>"""

        return f"""
                <div class="section-header">
                    <span class="icon icon-log">📋</span>
                    <span>Logs</span>
                </div>
                {errors_html}
                {warnings_html}"""


# Global report instance
REPORT = ReportGenerator()
