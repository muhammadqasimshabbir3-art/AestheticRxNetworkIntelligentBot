"""Update Payment Sheet Module.

This module handles updating payment status in Google Sheet.
When RUN_UPDATE_PAYMENT_PROCESS is True and PAYMENT_IDS_LIST is provided,
it updates the specified orders' status from 'pending' to 'paid'.

Main Entry Point:
    from processes.payment import UpdatePaymentProcess

    process = UpdatePaymentProcess(payment_ids=["id1", "id2"])
    process.start()

Robocorp Work Item Inputs:
    - RUN_UPDATE_PAYMENT_PROCESS: bool (True to enable)
    - PAYMENT_IDS_LIST: list[str] (comma-separated IDs)
"""

from processes.payment.update_payment_process import UpdatePaymentProcess

__all__ = [
    "UpdatePaymentProcess",
]
