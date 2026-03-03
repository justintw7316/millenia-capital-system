"""
integrations/gmail_client.py — Gmail email outreach (STUBBED).

# TODO: WIRE REAL API — https://developers.google.com/gmail/api
# Used for outreach email sending in Steps 7b, 8, 10.
"""
from typing import List, Optional

from core.logger import get_logger

logger = get_logger(__name__)

_SENT_LOG: List[dict] = []


class GmailClient:
    """STUBBED Gmail client. Logs emails without sending."""

    def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        from_alias: Optional[str] = None,
        cc: Optional[List[str]] = None,
    ) -> str:
        """
        Send an email via Gmail API.

        # STUB CALL: send_email
        # TODO: WIRE REAL API — POST https://gmail.googleapis.com/gmail/v1/users/me/messages/send
        Args:
            to: Recipient email address.
            subject: Email subject line.
            body: Email body (plain text or HTML).
            from_alias: Optional sender display name.
            cc: Optional list of CC addresses.
        Returns:
            message_id string.
        """
        logger.debug(
            f"# STUB CALL: GmailClient.send_email(to={to!r}, subject={subject!r})"
        )
        import uuid
        message_id = f"gmail_msg_{uuid.uuid4().hex[:8]}"
        record = {
            "message_id": message_id,
            "to": to,
            "subject": subject,
            "body_preview": body[:100] + "…" if len(body) > 100 else body,
            "from_alias": from_alias,
            "cc": cc or [],
            "sent_at": "2026-02-24T12:00:00Z",
        }
        _SENT_LOG.append(record)
        logger.info(f"[Gmail STUB] Email queued → {to} | Subject: {subject!r} | ID: {message_id}")
        return message_id

    def get_sent_log(self) -> List[dict]:
        """Return all emails 'sent' during this session (for testing)."""
        return _SENT_LOG
