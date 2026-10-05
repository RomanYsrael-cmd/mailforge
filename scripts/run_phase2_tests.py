#!/usr/bin/env python3
"""Run real container-backed SMTP, IMAP, TLS, relay-policy, and queue tests."""

from __future__ import annotations

import json
import re
import subprocess
import sys
import time
import uuid
from email import policy
from email.parser import BytesParser
from pathlib import Path

from lab import ROOT, STATE, compose_args, run, wait_healthy
from lab_common import lab_network_values


def protocol(*arguments: str) -> str:
    result = run(
        ["run", "--rm", "--no-deps", "-T", "smtp-test-client", *arguments],
        tools=True,
        capture=True,
    )
    return result.stdout or ""


def mailbox(account: str, message_id: str, body: str, timeout: int = 45) -> None:
    protocol(
        "mailbox-check",
        "--account", account,
        "--message-id", message_id,
        "--body", body,
        "--timeout", str(timeout),
    )


def smtp(
    recipient: str,
    message_id: str,
    body: str,
    *,
    sender: str = "sender@sender.invalid",
    host: str = "edge-postfix",
    port: int = 25,
    mode: str = "plain",
    account: str | None = None,
    expect_reject: bool = False,
) -> str:
    arguments = [
        "smtp-send",
        "--host", host,
        "--port", str(port),
        "--mode", mode,
        "--sender", sender,
        "--recipient", recipient,
        "--message-id", message_id,
        "--body", body,
    ]
    if account:
        arguments.extend(["--account", account])
    if expect_reject:
        arguments.append("--expect-reject")
    return protocol(*arguments)


def postconf(parameter: str) -> str:
    result = run(["exec", "-T", "edge-postfix", "postconf", "-h", parameter], capture=True)
    return (result.stdout or "").strip()


def queue_output() -> str:
    return run(["exec", "-T", "edge-postfix", "postqueue", "-p"], capture=True).stdout or ""


def assert_no_host_ports() -> None:
    rendered = run(["config", "--format", "json"], capture=True).stdout or ""
    config = json.loads(rendered)
    for name, service in config.get("services", {}).items():
        if service.get("ports"):
            raise AssertionError(f"{name} publishes a host port in the Phase 2 lab.")
    for network in config.get("networks", {}).values():
        if not network.get("internal"):
            raise AssertionError("Every Phase 2 lab network must be internal.")
    print("PASS: Compose has no published ports and all networks are internal.")


def check_postfix() -> None:
    restrictions = postconf("smtpd_relay_restrictions")
    if restrictions != "permit_mynetworks, reject_unauth_destination":
        raise AssertionError(f"Unexpected Postfix relay restrictions: {restrictions!r}")
    mynetworks = postconf("mynetworks")
    origin = "172.29.240.10/32"
    if origin not in mynetworks or "172.29.240.0/24" in mynetworks:
        raise AssertionError(f"Postfix does not limit trust to the origin /32: {mynetworks!r}")
    sink_ip = lab_network_values()["MAILFORGE_LAB_SINK_IP"]
    if postconf("relayhost") != f"[{sink_ip}]:2525":
        raise AssertionError("Postfix does not relay exclusively to the local sink.")
    for map_name, key, expected in (
        ("relay_domains", "example.com", "OK"),
        ("relay_domains", "example.org", "OK"),
        ("relay_domains", "outside.invalid", ""),
        ("relay_recipients", "abuse@example.com", "OK"),
        ("relay_recipients", "unknown@example.com", ""),
        ("transport", "example.org", "smtp:[172.29.240.10]:25"),
    ):
        command = compose_args() + [
            "exec", "-T", "edge-postfix", "postmap", "-q", key,
            f"hash:/etc/postfix/generated/{map_name}",
        ]
        result = subprocess.run(
            command,
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        value = result.stdout.strip()
        missing_key = expected == "" and result.returncode == 1 and not result.stderr.strip()
        if result.returncode != 0 and not missing_key:
            detail = result.stderr.strip() or result.stdout.strip()
            raise RuntimeError(f"Command failed ({result.returncode}): {' '.join(command)}\n{detail}")
        if value != expected:
            raise AssertionError(f"Postfix map {map_name} {key!r}: expected {expected!r}, got {value!r}")
    print("PASS: Postfix policy, fixture-derived maps, origin /32 trust, and sink route.")


def check_inbox_delivered(account: str, recipient: str, label: str, checks: list[str]) -> None:
    message_id = f"mf-{label}-{uuid.uuid4().hex}@mailforge.invalid"
    body = f"MailForge {label} {uuid.uuid4().hex}"
    smtp(recipient, message_id, body)
    mailbox(account, message_id, body)
    checks.append(f"{label} SMTP delivery to {recipient}")


def find_sink_message(message_id: str, timeout: int = 45):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        for path in sorted((STATE / "sink").glob("*.eml")):
            message = BytesParser(policy=policy.default).parsebytes(path.read_bytes())
            if str(message.get("Message-ID", "")).strip("<>") == message_id:
                return path, message
        time.sleep(1)
    raise TimeoutError(f"Message {message_id} did not reach the isolated SMTP sink within {timeout} seconds.")


def check_outbound(
    *,
    account: str,
    sender: str,
    domain: str,
    selector: str,
    checks: list[str],
) -> None:
    message_id = f"mf-out-{domain.replace('.', '-')}-{uuid.uuid4().hex}@mailforge.invalid"
    body = f"MailForge outbound {domain} {uuid.uuid4().hex}"
    smtp(
        "simulated-recipient@remote.invalid",
        message_id,
        body,
        sender=sender,
        host="edge-proxy",
        port=587,
        mode="starttls",
        account=account,
    )
    path, message = find_sink_message(message_id)
    signature = str(message.get("DKIM-Signature", ""))
    if body not in str(message.get_content()):
        raise AssertionError(f"The SMTP sink stored the wrong content for {message_id}.")
    if not re.search(rf"(?:^|;)\s*d={re.escape(domain)}(?:;|$)", signature):
        raise AssertionError(f"Outbound {domain} message lacks its domain DKIM signature: {signature!r}")
    if not re.search(rf"(?:^|;)\s*s={re.escape(selector)}(?:;|$)", signature):
        raise AssertionError(f"Outbound {domain} message lacks selector {selector}: {signature!r}")
    metadata = json.loads(path.with_suffix(".json").read_text(encoding="utf-8"))
    if metadata["recipients"] != ["simulated-recipient@remote.invalid"]:
        raise AssertionError(f"Unexpected sink envelope: {metadata['recipients']!r}")
    checks.append(f"authenticated outbound {domain} delivered to sink and DKIM selector {selector} observed")


def wait_for_empty_queue(timeout: int = 60) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        output = queue_output()
        if "Mail queue is empty" in output:
            return
        time.sleep(1)
    raise TimeoutError(f"Postfix queue did not drain automatically within {timeout} seconds:\n{queue_output()}")


def run_suite() -> list[str]:
    checks: list[str] = []
    for service in ("lab-sink", "origin-stalwart", "edge-postfix", "edge-proxy"):
        wait_healthy(service, timeout=90)
    assert_no_host_ports()
    check_postfix()
    checks.append("compose isolation and Postfix configuration")

    check_inbox_delivered("admin", "admin@example.com", "domain-a", checks)
    check_inbox_delivered("support", "support@example.org", "domain-b", checks)
    check_inbox_delivered("postmaster_com", "abuse@example.com", "alias-domain-a", checks)
    check_inbox_delivered("postmaster_org", "abuse@example.org", "alias-domain-b", checks)

    smtp("unknown@example.com", "unused", "unknown", expect_reject=True)
    checks.append("unknown local recipient rejected during SMTP")
    smtp("user@not-hosted.invalid", "unused", "unknown", expect_reject=True)
    checks.append("unknown domain rejected during SMTP")
    smtp("remote@outside.invalid", "unused", "open-relay", expect_reject=True)
    checks.append("untrusted arbitrary relay rejected during SMTP")

    check_outbound(
        account="admin",
        sender="admin@example.com",
        domain="example.com",
        selector="mf-example-com",
        checks=checks,
    )
    check_outbound(
        account="support",
        sender="support@example.org",
        domain="example.org",
        selector="mf-example-org",
        checks=checks,
    )

    tls_result = run(
        ["run", "--rm", "--no-deps", "-T", "private-tls-probe", "tls-probe"],
        tools=True,
        capture=True,
    ).stdout or ""
    if "tls_passthrough" not in tls_result or any(f'"port": {port}' not in tls_result for port in (443, 465, 587, 993)):
        raise AssertionError(f"TLS/L4 probe did not report all expected ports: {tls_result!r}")
    checks.append("HAProxy L4 TLS passthrough verified on 443, 465, 587, and 993")

    run(["stop", "origin-stalwart"])
    queue_id = uuid.uuid4().hex
    queue_sender = f"queue-{queue_id}@sender.invalid"
    queue_message_id = f"mf-queue-{queue_id}@mailforge.invalid"
    queue_body = f"MailForge queued while origin down {queue_id}"
    smtp(
        "support@example.org",
        queue_message_id,
        queue_body,
        sender=queue_sender,
    )
    queued = queue_output()
    if queue_sender not in queued:
        raise AssertionError(f"Valid hosted message was not retained in the Postfix queue:\n{queued}")
    checks.append("Postfix accepted and retained valid hosted mail while Stalwart was stopped")

    run(["restart", "edge-postfix"])
    wait_healthy("edge-postfix", timeout=60)
    queued_after_restart = queue_output()
    if queue_sender not in queued_after_restart:
        raise AssertionError(f"Postfix queue did not survive an edge restart:\n{queued_after_restart}")
    checks.append("Postfix queue survived an edge container restart")

    run(["up", "-d", "origin-stalwart"])
    wait_healthy("origin-stalwart", timeout=90)
    wait_for_empty_queue(timeout=60)
    mailbox("support", queue_message_id, queue_body, timeout=20)
    checks.append("Postfix automatic retry drained the queue after Stalwart recovered")

    print("\nPhase 2 integration results:")
    for item in checks:
        print(f"  PASS  {item}")
    print(f"Total: {len(checks)} integration checks passed.")
    return checks


def main() -> int:
    try:
        run_suite()
        return 0
    except Exception as exc:
        print(f"Phase 2 integration failure: {exc}", file=sys.stderr)
        raise


if __name__ == "__main__":
    raise SystemExit(main())
