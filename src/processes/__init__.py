"""Process modules for QwebsiteAutomationBot.

This package contains all the automation processes:
- advertisement: Advertisement management and approval
- business_report: Business intelligence reporting
- data_analysis: Data export and analysis (includes business_report)
- order: Order management workflow
- payment: Payment status updates
- signup: Signup ID management
- user: User management and approval
"""

from processes.advertisement import AdvertisementManagementProcess
from processes.business_report import BusinessReportProcess
from processes.data_analysis import DataAnalysisProcess
from processes.order import OrderManagementProcess
from processes.payment import UpdatePaymentProcess
from processes.signup import SignupIDManagementProcess
from processes.user import UserManagementProcess

__all__ = [
    "AdvertisementManagementProcess",
    "BusinessReportProcess",
    "DataAnalysisProcess",
    "OrderManagementProcess",
    "SignupIDManagementProcess",
    "UpdatePaymentProcess",
    "UserManagementProcess",
]

