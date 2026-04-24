"""Email reader module for fetching OTP codes from Gmail.

Uses IMAP with Google App Password to read emails.
"""

import email
import imaplib
import re
import time
from datetime import UTC, datetime
from email.header import decode_header
from email.utils import parsedate_to_datetime

from libraries.logger import logger


class GmailReader:
    """Read emails from Gmail using IMAP."""

    IMAP_SERVER = "imap.gmail.com"
    IMAP_PORT = 993

    def __init__(self, email_address: str, app_password: str):
        """Initialize Gmail reader.

        Args:
            email_address: Gmail address
            app_password: Google App Password (not regular password)
        """
        self.email_address = email_address
        self.app_password = app_password
        self.connection: imaplib.IMAP4_SSL | None = None

    def connect(self) -> bool:
        """Connect to Gmail IMAP server.

        Returns:
            bool: True if connected successfully
        """
        try:
            logger.info(f"Connecting to Gmail IMAP as {self.email_address}...")
            self.connection = imaplib.IMAP4_SSL(self.IMAP_SERVER, self.IMAP_PORT)
            self.connection.login(self.email_address, self.app_password)
            logger.info("Connected to Gmail successfully")
            return True
        except imaplib.IMAP4.error as e:
            logger.error(f"Failed to connect to Gmail: {e}")
            return False
        except Exception as e:
            logger.error(f"Error connecting to Gmail: {e}")
            return False

    def disconnect(self) -> None:
        """Disconnect from Gmail."""
        if self.connection:
            try:
                self.connection.logout()
                logger.info("Disconnected from Gmail")
            except Exception:
                pass
            self.connection = None

    def search_otp_email(
        self,
        sender_filter: str = "aestheticrxnetwork",
        subject_filter: str = "otp",
        max_emails: int = 10,
        received_after: datetime | None = None,
        mark_as_read: bool = True,
    ) -> str | None:
        """Search for OTP email and extract the code.

        Args:
            sender_filter: Filter emails by sender (partial match)
            subject_filter: Filter emails by subject (partial match)
            max_emails: Maximum number of recent emails to check
            received_after: Only check emails received after this timestamp (UTC)
            mark_as_read: If True, mark email as read after extracting OTP

        Returns:
            str: OTP code if found, None otherwise
        """
        if not self.connection and not self.connect():
            return None

        try:
            # Select inbox
            self.connection.select("INBOX")

            # Search for ALL recent emails - we'll filter by timestamp
            status, messages = self.connection.search(None, "ALL")

            if status != "OK":
                logger.error("Failed to search emails")
                return None

            email_ids = messages[0].split()
            if not email_ids:
                logger.info("No emails found in inbox")
                return None

            # Check most recent emails first
            recent_ids = email_ids[-max_emails:] if len(email_ids) > max_emails else email_ids
            recent_ids = list(reversed(recent_ids))  # Most recent first

            if received_after:
                time_str = received_after.strftime("%H:%M:%S")
                logger.info(f"Checking {len(recent_ids)} recent emails for OTP (after {time_str})...")
            else:
                logger.info(f"Checking {len(recent_ids)} recent emails for OTP...")

            for email_id in recent_ids:
                status, msg_data = self.connection.fetch(email_id, "(RFC822)")
                if status != "OK":
                    continue

                for response_part in msg_data:
                    if isinstance(response_part, tuple):
                        msg = email.message_from_bytes(response_part[1])

                        # Get sender
                        sender = msg.get("From", "").lower()
                        subject = self._decode_header(msg.get("Subject", "")).lower()

                        # Check if email matches filters
                        if sender_filter.lower() not in sender and subject_filter.lower() not in subject:
                            continue

                        # Check email timestamp - skip emails received BEFORE our marker
                        email_date_str = msg.get("Date")
                        if email_date_str and received_after:
                            try:
                                email_date = parsedate_to_datetime(email_date_str)
                                # Ensure both are timezone-aware for comparison
                                if email_date.tzinfo is None:
                                    email_date = email_date.replace(tzinfo=UTC)
                                received_after_utc = (
                                    received_after if received_after.tzinfo else received_after.replace(tzinfo=UTC)
                                )

                                if email_date < received_after_utc:
                                    logger.debug(f"Skipping old email (before timestamp): {subject[:40]}...")
                                    continue
                                email_time = email_date.strftime("%H:%M:%S")
                                after_time = received_after_utc.strftime("%H:%M:%S")
                                logger.info(f"✓ Email received at: {email_time} (after {after_time})")
                            except Exception as e:
                                logger.warning(f"Could not parse email date '{email_date_str}': {e}")

                        logger.info(f"Found potential OTP email: {subject}")

                        # Extract body
                        body = self._get_email_body(msg)

                        # Search for OTP in body
                        otp = self._extract_otp(body)
                        if otp:
                            # Log all numbers for debugging
                            all_numbers = re.findall(r"\b(\d{6})\b", body) if body else []
                            logger.info(f"6-digit numbers in email: {all_numbers} → Selected: {otp}")
                            # Mark as read to prevent reusing this OTP
                            if mark_as_read:
                                try:
                                    self.connection.store(email_id, "+FLAGS", "\\Seen")
                                    logger.info("Marked OTP email as read")
                                except Exception as e:
                                    logger.warning(f"Could not mark email as read: {e}")
                            return otp

            logger.warning("No OTP found in recent emails")
            return None

        except Exception as e:
            logger.error(f"Error searching for OTP email: {e}")
            return None

    def _decode_header(self, header: str) -> str:
        """Decode email header."""
        if not header:
            return ""
        decoded_parts = decode_header(header)
        result = ""
        for part, encoding in decoded_parts:
            if isinstance(part, bytes):
                result += part.decode(encoding or "utf-8", errors="ignore")
            else:
                result += part
        return result

    def _get_email_body(self, msg: email.message.Message) -> str:
        """Extract text body from email message."""
        body = ""

        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                if content_type == "text/plain":
                    try:
                        payload = part.get_payload(decode=True)
                        if payload:
                            charset = part.get_content_charset() or "utf-8"
                            body += payload.decode(charset, errors="ignore")
                    except Exception:
                        pass
                elif content_type == "text/html" and not body:
                    try:
                        payload = part.get_payload(decode=True)
                        if payload:
                            charset = part.get_content_charset() or "utf-8"
                            html_body = payload.decode(charset, errors="ignore")
                            # Strip HTML tags for OTP extraction
                            body = re.sub(r"<[^>]+>", " ", html_body)
                    except Exception:
                        pass
        else:
            try:
                payload = msg.get_payload(decode=True)
                if payload:
                    charset = msg.get_content_charset() or "utf-8"
                    body = payload.decode(charset, errors="ignore")
            except Exception:
                pass

        return body

    def _extract_otp(self, text: str) -> str | None:
        """Extract OTP code from email text.

        Looks for AestheticRxNetwork-specific OTP patterns.

        Args:
            text: Email body text

        Returns:
            str: OTP code if found
        """
        if not text:
            return None

        # Normalize whitespace for better pattern matching
        normalized_text = re.sub(r"\s+", " ", text)

        # AestheticRxNetwork-specific patterns - MOST SPECIFIC FIRST
        # The email format: "Your One-Time Password (OTP) is: 123456"
        patterns = [
            # AestheticRxNetwork exact format (most reliable)
            r"One-Time\s+Password\s*\(\s*OTP\s*\)\s*is\s*[:\s]*(\d{6})",
            # Variations with "Your" prefix
            r"Your\s+One-Time\s+Password.*?(\d{6})",
            # OTP is: followed by number
            r"OTP\s*\)\s*is\s*[:\s]*(\d{6})",
            # Simpler "OTP is:" pattern
            r"OTP\s+is\s*[:\s]+(\d{6})",
        ]

        for pattern in patterns:
            match = re.search(pattern, normalized_text, re.IGNORECASE)
            if match:
                return match.group(1)

        # Fallback: Look for 6-digit number that appears AFTER specific keywords
        # Find the last occurrence of "OTP" or "is:" and get the number after it
        all_numbers = re.findall(r"\b(\d{6})\b", normalized_text)
        if all_numbers:
            # Look for number right after "OTP) is:" pattern (allowing for HTML artifacts)
            otp_is_match = re.search(r"OTP\s*\)?\s*is\s*[:\s]*(\d{6})", normalized_text, re.IGNORECASE)
            if otp_is_match:
                return otp_is_match.group(1)

            # Find the position of "is:" and return the first number after it
            is_pos = normalized_text.lower().rfind(" is:")
            if is_pos == -1:
                is_pos = normalized_text.lower().rfind(" is ")

            if is_pos >= 0:
                after_is = normalized_text[is_pos:]
                after_is_match = re.search(r"\b(\d{6})\b", after_is)
                if after_is_match:
                    return after_is_match.group(1)

            # Last resort: return the LAST 6-digit number (OTP is usually at the end)
            return all_numbers[-1]

        return None

    def wait_for_otp(
        self,
        received_after: datetime,
        sender_filter: str = "aestheticrxnetwork",
        subject_filter: str = "otp",
        timeout_seconds: int = 120,
        check_interval: int = 5,
        initial_delay: int = 20,
    ) -> str | None:
        """Wait for OTP email to arrive and extract the code.

        Args:
            received_after: Only consider emails received AFTER this timestamp
            sender_filter: Filter emails by sender
            subject_filter: Filter emails by subject
            timeout_seconds: Maximum time to wait for OTP
            check_interval: Seconds between email checks
            initial_delay: Seconds to wait before first check (allow email to arrive)

        Returns:
            str: OTP code if found within timeout
        """
        time_str = received_after.strftime("%H:%M:%S")
        logger.info(f"Waiting for OTP email after {time_str} (timeout: {timeout_seconds}s)...")

        # Initial delay to allow the new OTP email to arrive
        if initial_delay > 0:
            logger.info(f"Waiting {initial_delay}s for new OTP email to arrive...")
            time.sleep(initial_delay)

        start_time = time.time()

        while time.time() - start_time < timeout_seconds:
            # Search for emails received AFTER our timestamp marker
            otp = self.search_otp_email(
                sender_filter=sender_filter,
                subject_filter=subject_filter,
                received_after=received_after,
                mark_as_read=True,
            )
            if otp:
                return otp

            remaining = int(timeout_seconds - (time.time() - start_time))
            logger.info(f"OTP not found yet, checking again in {check_interval}s... ({remaining}s remaining)")
            time.sleep(check_interval)

        logger.error("Timeout waiting for OTP email")
        return None


def get_otp_from_gmail(
    email_address: str,
    app_password: str,
    received_after: datetime,
    sender_filter: str = "aestheticrxnetwork",
    timeout_seconds: int = 120,
    initial_delay: int = 20,
) -> str | None:
    """Convenience function to get OTP from Gmail.

    Args:
        email_address: Gmail address
        app_password: Google App Password
        received_after: Only consider emails received AFTER this timestamp
        sender_filter: Filter emails by sender
        timeout_seconds: Maximum time to wait
        initial_delay: Seconds to wait before first check

    Returns:
        str: OTP code if found
    """
    reader = GmailReader(email_address, app_password)

    try:
        return reader.wait_for_otp(
            received_after=received_after,
            sender_filter=sender_filter,
            timeout_seconds=timeout_seconds,
            initial_delay=initial_delay,
        )
    finally:
        reader.disconnect()
