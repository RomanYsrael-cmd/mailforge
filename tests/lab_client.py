#!/usr/bin/env python3
"""Protocol helpers executed inside Compose networks, not on the host."""

from __future__ import annotations

import argparse
import hashlib
import imaplib
import json
import os
import smtplib
import socket
import ssl
import sys
import time
from email.message import EmailMessage


def resolve_account(args: argparse.Namespace) -> None:
    if args.account:
        prefix = "MAILFORGE_TEST_" + args.account.upper()
        args.username = args.username or os.environ.get(prefix + "_USERNAME")
        args.password = args.password or os.environ.get(prefix + "_PASSWORD")
    if args.username is not None and not args.password:
        raise ValueError("A password is required whenever a mailbox username is supplied.")


def smtp_send(args: argparse.Namespace) -> int:
    resolve_account(args)
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    if args.mode == "implicit":
        client: smtplib.SMTP = smtplib.SMTP_SSL(args.host, args.port, timeout=10, context=context)
    else:
        client = smtplib.SMTP(args.host, args.port, timeout=10)
    try:
        client.ehlo("mailforge-lab-client.invalid")
        if args.mode == "starttls":
            client.starttls(context=context)
            client.ehlo("mailforge-lab-client.invalid")
        if args.username:
            client.login(args.username, args.password or "")
        code, response = client.mail(args.sender)
        if code >= 400:
            if args.expect_reject:
                print(f"expected MAIL rejection: {code} {response.decode(errors='replace')}")
                return 0
            raise RuntimeError(f"MAIL FROM rejected: {code} {response!r}")
        code, response = client.rcpt(args.recipient)
        if args.expect_reject:
            if code >= 500:
                print(f"expected RCPT rejection: {code} {response.decode(errors='replace')}")
                return 0
            raise RuntimeError(f"recipient was unexpectedly accepted: {code} {response!r}")
        if code >= 400:
            raise RuntimeError(f"RCPT TO rejected: {code} {response!r}")
        message = EmailMessage()
        message["From"] = args.sender
        message["To"] = args.recipient
        message["Subject"] = "MailForge Phase 2 lab message"
        message["Message-ID"] = f"<{args.message_id}>"
        message["X-MailForge-Lab"] = "phase2"
        message.set_content(args.body)
        code, response = client.data(message.as_bytes())
        if code >= 400:
            raise RuntimeError(f"DATA rejected: {code} {response!r}")
        print(f"SMTP accepted {args.message_id} for {args.recipient}: {code}")
        return 0
    finally:
        try:
            client.quit()
        except (smtplib.SMTPException, OSError):
            client.close()


def mailbox_check(args: argparse.Namespace) -> int:
    resolve_account(args)
    if not args.username:
        raise ValueError("Use --account admin or support to select a generated lab mailbox.")
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    deadline = time.monotonic() + args.timeout
    while time.monotonic() < deadline:
        client: imaplib.IMAP4_SSL | None = None
        try:
            client = imaplib.IMAP4_SSL(args.host, args.port, ssl_context=context, timeout=10)
            client.login(args.username, args.password or "")
            status, _ = client.select("INBOX", readonly=True)
            if status != "OK":
                raise RuntimeError("Could not select INBOX.")
            status, data = client.search(None, "ALL")
            if status == "OK":
                for message_number in data[0].split():
                    status, fetched = client.fetch(message_number, "(RFC822)")
                    if status == "OK":
                        payload = b"".join(
                            item[1] for item in fetched if isinstance(item, tuple) and isinstance(item[1], bytes)
                        )
                        if args.message_id.encode("ascii") in payload and args.body.encode("utf-8") in payload:
                            print(f"IMAP confirmed {args.message_id} in {args.username}.")
                            return 0
        except (OSError, imaplib.IMAP4.error, smtplib.SMTPException):
            pass
        finally:
            if client is not None:
                try:
                    client.logout()
                except Exception:
                    pass
        time.sleep(1)
    raise TimeoutError(f"Message {args.message_id} did not arrive in {args.username} within {args.timeout} seconds.")


def _read_smtp_response(stream) -> tuple[int, list[bytes]]:
    first = stream.readline()
    if not first:
        raise ConnectionError("SMTP peer closed during TLS probe.")
    code = int(first[:3])
    lines = [first.rstrip(b"\r\n")]
    while len(first) > 3 and first[3:4] == b"-":
        first = stream.readline()
        if not first:
            raise ConnectionError("SMTP peer closed during multiline reply.")
        lines.append(first.rstrip(b"\r\n"))
    return code, lines


def tls_fingerprint(host: str, port: int, *, starttls: bool) -> str:
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    raw = socket.create_connection((host, port), timeout=10)
    if starttls:
        stream = raw.makefile("rwb", buffering=0)
        code, _ = _read_smtp_response(stream)
        if code != 220:
            raise RuntimeError(f"SMTP greeting on {host}:{port} failed: {code}")
        stream.write(b"EHLO tls-probe.invalid\r\n")
        code, _ = _read_smtp_response(stream)
        if code != 250:
            raise RuntimeError(f"EHLO on {host}:{port} failed: {code}")
        stream.write(b"STARTTLS\r\n")
        code, _ = _read_smtp_response(stream)
        if code != 220:
            raise RuntimeError(f"STARTTLS on {host}:{port} failed: {code}")
        stream.close()
        secured = context.wrap_socket(raw, server_hostname="mail.mail.example.net")
    else:
        secured = context.wrap_socket(raw, server_hostname="mail.mail.example.net")
    try:
        return hashlib.sha256(secured.getpeercert(binary_form=True)).hexdigest()
    finally:
        secured.close()


def probe_tls(_: argparse.Namespace) -> int:
    pairs = []
    for port, starttls in ((443, False), (465, False), (587, True), (993, False)):
        fingerprints = {}
        mode = "STARTTLS" if starttls else "implicit TLS"
        for host in ("origin-stalwart", "edge-proxy"):
            try:
                fingerprints[host] = tls_fingerprint(host, port, starttls=starttls)
            except Exception as exc:
                raise RuntimeError(f"{mode} probe failed for {host}:{port}: {exc}") from exc
        direct = fingerprints["origin-stalwart"]
        proxied = fingerprints["edge-proxy"]
        if direct != proxied:
            raise AssertionError(f"Port {port} certificate differs across the L4 proxy.")
        pairs.append({"port": port, "sha256": direct, "path": "STARTTLS" if starttls else "implicit/HTTPS"})
    print(json.dumps({"tls_passthrough": pairs}, sort_keys=True))
    return 0


def add_account_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--account", choices=("admin", "support", "postmaster_com", "postmaster_org"))
    parser.add_argument("--username")
    parser.add_argument("--password")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="action", required=True)

    smtp = subparsers.add_parser("smtp-send")
    smtp.add_argument("--host", default="edge-postfix")
    smtp.add_argument("--port", type=int, default=25)
    smtp.add_argument("--mode", choices=("plain", "starttls", "implicit"), default="plain")
    smtp.add_argument("--sender", required=True)
    smtp.add_argument("--recipient", required=True)
    smtp.add_argument("--message-id", default="mailforge-test")
    smtp.add_argument("--body", default="MailForge isolated lab test message")
    add_account_options(smtp)
    smtp.add_argument("--expect-reject", action="store_true")
    smtp.set_defaults(func=smtp_send)

    mailbox = subparsers.add_parser("mailbox-check")
    mailbox.add_argument("--host", default="edge-proxy")
    mailbox.add_argument("--port", type=int, default=993)
    add_account_options(mailbox)
    mailbox.add_argument("--message-id", required=True)
    mailbox.add_argument("--body", required=True)
    mailbox.add_argument("--timeout", type=int, default=45)
    mailbox.set_defaults(func=mailbox_check)

    tls = subparsers.add_parser("tls-probe")
    tls.set_defaults(func=probe_tls)

    args = parser.parse_args()
    try:
        return args.func(args)
    except Exception as exc:
        print(f"Protocol test failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
