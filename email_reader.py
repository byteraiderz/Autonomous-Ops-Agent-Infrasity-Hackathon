"""Fetch the newest unread customer email from a Gmail inbox over IMAP."""

import imaplib
import os
import queue
import socket
import threading
from dotenv import load_dotenv
import email
from email import policy
from email.message import Message
load_dotenv()
from email.utils import parseaddr


GMAIL_ADDRESS = os.getenv("GMAIL_ADDRESS", "").strip()
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD", "").strip()


def _plain_text_body(message: Message) -> str:
    """Extract the plain-text body, ignoring attachments and HTML alternatives."""
    if message.is_multipart():
        for part in message.walk():
            if part.get_content_type() == "text/plain" and part.get_content_disposition() != "attachment":
                content = part.get_content()
                if isinstance(content, str) and content.strip():
                    return content.strip()
        return ""

    if message.get_content_type() == "text/plain":
        content = message.get_content()
        return content.strip() if isinstance(content, str) else ""
    return ""


def _resolve_imap_addresses(timeout_seconds: float = 5.0):
    """Resolve Gmail with a bound; Windows DNS lookups can otherwise block the UI."""
    result_queue: queue.Queue = queue.Queue(maxsize=1)

    def resolve() -> None:
        try:
            result_queue.put_nowait(
                socket.getaddrinfo("imap.gmail.com", 993, type=socket.SOCK_STREAM)
            )
        except OSError as error:
            result_queue.put_nowait(error)

    threading.Thread(target=resolve, daemon=True).start()
    try:
        result = result_queue.get(timeout=timeout_seconds)
    except queue.Empty as error:
        raise RuntimeError(
            f"DNS lookup for imap.gmail.com did not respond within {timeout_seconds:.0f} seconds. Check the network's DNS service, then retry."
        ) from error

    if isinstance(result, OSError):
        raise RuntimeError(
            "Can't resolve imap.gmail.com. Check the PC's internet connection and DNS, then retry."
        ) from result
    return result


class _ResolvedIMAP4SSL(imaplib.IMAP4_SSL):
    """Connect to pre-resolved addresses while preserving Gmail TLS hostname checks."""

    def __init__(self, host: str, port: int, addresses, timeout: float = 6.0):
        self._resolved_addresses = addresses
        super().__init__(host, port, timeout=timeout)

    def _create_socket(self, timeout):
        last_error = None
        for family, socktype, proto, _canonname, sockaddr in self._resolved_addresses:
            sock = socket.socket(family, socktype, proto)
            if timeout is not None:
                sock.settimeout(timeout)
            try:
                sock.connect(sockaddr)
                return self.ssl_context.wrap_socket(sock, server_hostname=self.host)
            except OSError as error:
                sock.close()
                last_error = error
        if last_error:
            raise last_error
        raise OSError("DNS returned no addresses for imap.gmail.com.")


def fetch_latest_customer_email() -> dict[str, str] | None:
    """Return the newest unread email's body and sender, or None if inbox is clear."""
    if not GMAIL_ADDRESS or not GMAIL_APP_PASSWORD:
        raise RuntimeError(
            "Gmail credentials are missing. Set GMAIL_ADDRESS and GMAIL_APP_PASSWORD in .env."
        )

    try:
        addresses = _resolve_imap_addresses()
        mailbox = _ResolvedIMAP4SSL("imap.gmail.com", 993, addresses, timeout=6)
    except (TimeoutError, OSError) as error:
        raise RuntimeError(
            "Can't connect to Gmail IMAP on port 993. Check the internet connection or network firewall."
        ) from error

    try:
        try:
            mailbox.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
        except imaplib.IMAP4.error as error:
            raise RuntimeError(
                "Gmail sign-in failed. Check the Gmail address, App Password, and IMAP access."
            ) from error

        status, _ = mailbox.select("INBOX")
        if status != "OK":
            raise RuntimeError("Could not open the Gmail inbox.")

        status, search_data = mailbox.search(None, "UNSEEN")
        if status != "OK":
            raise RuntimeError("Could not search for unread Gmail messages.")

        message_ids = search_data[0].split() if search_data and search_data[0] else []
        if not message_ids:
            return None

        latest_id = message_ids[-1]
        # PEEK retrieves the message body without marking the unread email as read.
        status, fetch_data = mailbox.fetch(latest_id, "(BODY.PEEK[])")
        if status != "OK":
            raise RuntimeError("Could not fetch the latest unread email.")

        raw_message = next(
            (item[1] for item in fetch_data if isinstance(item, tuple) and len(item) > 1),
            None,
        )
        if raw_message is None:
            raise RuntimeError("Gmail returned an empty message.")

        parsed_message = email.message_from_bytes(raw_message, policy=policy.default)
        body = _plain_text_body(parsed_message)
        _, sender = parseaddr(parsed_message.get("From", ""))
        if not body or not sender:
            return None
        return {"body": body, "sender": sender}
    finally:
        try:
            mailbox.close()
        except (imaplib.IMAP4.error, OSError):
            pass
        try:
            mailbox.logout()
        except (imaplib.IMAP4.error, OSError):
            pass
