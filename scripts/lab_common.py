#!/usr/bin/env python3
"""Shared, dependency-free helpers for the isolated MailForge lab."""

from __future__ import annotations

import ipaddress
import json
import os
import re
import secrets
import shutil
import subprocess
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / "var" / "mailforge"
RUNTIME = STATE / "runtime"
GENERATED = RUNTIME / "generated"
FIXTURES = ROOT / "examples" / "domains"

DEFAULTS = {
    "MAILFORGE_LAB_PUBLIC_SUBNET": "172.28.240.0/24",
    "MAILFORGE_LAB_EDGE_PUBLIC_IP": "172.28.240.2",
    "MAILFORGE_LAB_PRIVATE_SUBNET": "172.29.240.0/24",
    "MAILFORGE_LAB_EDGE_PRIVATE_IP": "172.29.240.2",
    "MAILFORGE_LAB_ORIGIN_IP": "172.29.240.10",
    "MAILFORGE_LAB_PROXY_PRIVATE_IP": "172.29.240.3",
    "MAILFORGE_LAB_SINK_SUBNET": "172.30.240.0/24",
    "MAILFORGE_LAB_EDGE_SINK_IP": "172.30.240.2",
    "MAILFORGE_LAB_SINK_IP": "172.30.240.10",
}

DOMAIN_RE = re.compile(r"^(?=.{1,253}$)(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}$")
LOCAL_RE = re.compile(r"^[a-z0-9][a-z0-9._+-]{0,63}$")


def safe_state_path() -> Path:
    """Require runtime state to resolve to the exact ignored directory in this checkout."""
    root = ROOT.resolve()
    expected = root / "var" / "mailforge"
    actual = STATE.resolve()
    if actual != expected or actual == root or actual == Path(actual.anchor):
        raise RuntimeError(f"Refusing to use an unexpected runtime path: {actual}")
    return actual


def lab_network_values(environ: Mapping[str, str] | None = None) -> dict[str, str]:
    source = os.environ if environ is None else environ
    result = {key: source.get(key, value) for key, value in DEFAULTS.items()}
    subnet_keys = (
        "MAILFORGE_LAB_PUBLIC_SUBNET",
        "MAILFORGE_LAB_PRIVATE_SUBNET",
        "MAILFORGE_LAB_SINK_SUBNET",
    )
    networks = {key: ipaddress.ip_network(result[key], strict=True) for key in subnet_keys}
    if any(network.version != 4 for network in networks.values()):
        raise ValueError("The Phase 2 Compose networks must use IPv4 subnets.")
    network_items = list(networks.items())
    for index, (left_name, left) in enumerate(network_items):
        for right_name, right in network_items[index + 1 :]:
            if left.overlaps(right):
                raise ValueError(f"{left_name} overlaps {right_name}: {left} and {right}")

    ip_to_network = {
        "MAILFORGE_LAB_EDGE_PUBLIC_IP": "MAILFORGE_LAB_PUBLIC_SUBNET",
        "MAILFORGE_LAB_EDGE_PRIVATE_IP": "MAILFORGE_LAB_PRIVATE_SUBNET",
        "MAILFORGE_LAB_ORIGIN_IP": "MAILFORGE_LAB_PRIVATE_SUBNET",
        "MAILFORGE_LAB_PROXY_PRIVATE_IP": "MAILFORGE_LAB_PRIVATE_SUBNET",
        "MAILFORGE_LAB_EDGE_SINK_IP": "MAILFORGE_LAB_SINK_SUBNET",
        "MAILFORGE_LAB_SINK_IP": "MAILFORGE_LAB_SINK_SUBNET",
    }
    used: dict[str, str] = {}
    for address_key, network_key in ip_to_network.items():
        address = ipaddress.ip_address(result[address_key])
        network = networks[network_key]
        if address.version != 4 or address not in network or address in {
            network.network_address,
            network.broadcast_address,
        }:
            raise ValueError(f"{address_key} must be a usable address in {network}.")
        if str(address) in used:
            raise ValueError(f"{address_key} collides with {used[str(address)]} at {address}.")
        used[str(address)] = address_key
    if len({result[key] for key in ip_to_network}) != len(ip_to_network):
        raise ValueError("Lab service IP addresses must be unique.")
    return result


def load_domains() -> list[dict[str, Any]]:
    domains: list[dict[str, Any]] = []
    seen_domains: set[str] = set()
    seen_addresses: set[str] = set()
    for path in sorted(FIXTURES.glob("*.json")):
        record = json.loads(path.read_text(encoding="utf-8"))
        domain = record.get("domain", "").lower().rstrip(".")
        if not DOMAIN_RE.fullmatch(domain) or domain in seen_domains:
            raise ValueError(f"Invalid or duplicate domain in {path.name}: {domain!r}")
        if record.get("enabled") is not True:
            raise ValueError(f"Lab domain must be enabled: {domain}")
        mailboxes = record.get("mailboxes")
        aliases = record.get("aliases")
        if not isinstance(mailboxes, list) or not mailboxes:
            raise ValueError(f"Domain {domain} must declare mailboxes.")
        if not isinstance(aliases, dict):
            raise ValueError(f"Domain {domain} aliases must be an object.")
        normalized_mailboxes: set[str] = set()
        for local in mailboxes:
            if not isinstance(local, str) or not LOCAL_RE.fullmatch(local.lower()):
                raise ValueError(f"Invalid mailbox local part in {domain}: {local!r}")
            local = local.lower()
            normalized_mailboxes.add(local)
            address = f"{local}@{domain}"
            if address in seen_addresses:
                raise ValueError(f"Duplicate lab address: {address}")
            seen_addresses.add(address)
        for alias, target in aliases.items():
            if not isinstance(alias, str) or not LOCAL_RE.fullmatch(alias.lower()):
                raise ValueError(f"Invalid alias local part in {domain}: {alias!r}")
            if not isinstance(target, str) or target.lower() not in normalized_mailboxes:
                raise ValueError(f"Invalid alias {alias!r} -> {target!r} in {domain}")
            address = f"{alias.lower()}@{domain}"
            if address in seen_addresses:
                raise ValueError(f"Duplicate lab address: {address}")
            seen_addresses.add(address)
        selector = record.get("dkim", {}).get("selector", "")
        if not re.fullmatch(r"[A-Za-z0-9-]{1,63}", selector):
            raise ValueError(f"Invalid DKIM selector for {domain}: {selector!r}")
        domains.append({**record, "domain": domain, "mailboxes": [value.lower() for value in mailboxes]})
        seen_domains.add(domain)
    if not domains:
        raise ValueError(f"No domain fixtures found in {FIXTURES}")
    return domains


def all_recipients(domains: list[dict[str, Any]] | None = None) -> list[str]:
    recipients: list[str] = []
    for record in domains or load_domains():
        domain = record["domain"]
        recipients.extend(f"{local.lower()}@{domain}" for local in record["mailboxes"])
        recipients.extend(f"{alias.lower()}@{domain}" for alias in record["aliases"])
    return sorted(set(recipients))


def _write_bytes(path: Path, data: bytes, mode: int = 0o600) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_name(path.name + ".tmp")
    temp_path.write_bytes(data)
    try:
        os.chmod(temp_path, mode)
    except OSError:
        pass
    temp_path.replace(path)
    try:
        os.chmod(path, mode)
    except OSError:
        pass


def write_text(path: Path, text: str, mode: int = 0o600) -> None:
    _write_bytes(path, text.encode("utf-8"), mode)


def write_json(path: Path, value: Any, mode: int = 0o600) -> None:
    write_text(path, json.dumps(value, indent=2, sort_keys=True) + "\n", mode)


def find_openssl() -> str:
    requested = os.environ.get("MAILFORGE_OPENSSL")
    binary = requested or shutil.which("openssl")
    if not binary:
        raise RuntimeError(
            "OpenSSL is required to create disposable lab DKIM keys. "
            "Install it on the data drive or set MAILFORGE_OPENSSL to its executable."
        )
    return binary


def generate_private_key(path: Path, openssl: str | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    completed = subprocess.run(
        [
            openssl or find_openssl(),
            "genpkey",
            "-algorithm",
            "RSA",
            "-pkeyopt",
            "rsa_keygen_bits:2048",
            "-out",
            str(path),
        ],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if completed.returncode:
        raise RuntimeError(f"OpenSSL could not create a lab DKIM key: {completed.stderr.strip()}")
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass


def host_uid_gid() -> tuple[str, str]:
    if os.name == "nt":
        return "2000", "2000"
    return str(os.getuid()), str(os.getgid())


def write_runtime(secrets_data: dict[str, Any], network_values: dict[str, str]) -> None:
    (STATE / "postfix-queue").mkdir(parents=True, exist_ok=True)
    (STATE / "sink").mkdir(parents=True, exist_ok=True)
    (STATE / "stalwart" / "data").mkdir(parents=True, exist_ok=True)
    (GENERATED / "postfix").mkdir(parents=True, exist_ok=True)
    (GENERATED / "stalwart").mkdir(parents=True, exist_ok=True)
    (GENERATED / "dkim").mkdir(parents=True, exist_ok=True)

    domains = load_domains()
    origin_ip = network_values["MAILFORGE_LAB_ORIGIN_IP"]
    postfix_template = (ROOT / "edge" / "postfix" / "main.cf.template").read_text(encoding="utf-8")
    write_text(GENERATED / "postfix" / "main.cf", postfix_template.replace("@LAB_ORIGIN_IP@", origin_ip), 0o644)

    relay_domains = "".join(f"{record['domain']} OK\n" for record in domains)
    transports = "".join(f"{record['domain']} smtp:[{origin_ip}]:25\n" for record in domains)
    recipients = "".join(f"{address} OK\n" for address in all_recipients(domains))
    write_text(GENERATED / "postfix" / "relay_domains", relay_domains, 0o644)
    write_text(GENERATED / "postfix" / "relay_recipients", recipients, 0o644)
    write_text(GENERATED / "postfix" / "transport", transports, 0o644)

    write_json(
        GENERATED / "stalwart" / "config.json",
        {"@type": "RocksDb", "path": "/var/lib/stalwart/"},
        0o644,
    )

    uid, gid = host_uid_gid()
    compose_values = {
        "MAILFORGE_DATA_ROOT": str(STATE.resolve()).replace("\\", "/"),
        "MAILFORGE_LAB_UID": uid,
        "MAILFORGE_LAB_GID": gid,
        **network_values,
    }
    for name, address in (
        ("MAILFORGE_TEST_ADMIN", "admin@example.com"),
        ("MAILFORGE_TEST_SUPPORT", "support@example.org"),
        ("MAILFORGE_TEST_POSTMASTER_COM", "postmaster@example.com"),
        ("MAILFORGE_TEST_POSTMASTER_ORG", "postmaster@example.org"),
    ):
        account = secrets_data["accounts"][address]
        compose_values[f"{name}_USERNAME"] = account["username"]
        compose_values[f"{name}_PASSWORD"] = account["password"]
    env_text = "".join(f"{key}={json.dumps(value)}\n" for key, value in sorted(compose_values.items()))
    write_text(RUNTIME / "compose.env", env_text, 0o600)

    recovery = secrets_data["recovery"]
    override = (
        "services:\n"
        "  origin-stalwart:\n"
        "    environment:\n"
        '      STALWART_RECOVERY_MODE: "1"\n'
        f"      STALWART_RECOVERY_ADMIN: {json.dumps(recovery['username'] + ':' + recovery['password'])}\n"
    )
    write_text(RUNTIME / "bootstrap.compose.yaml", override, 0o600)


def prepare_state(openssl: str | None = None, fresh_credentials: bool = False) -> dict[str, Any]:
    safe_state_path()
    STATE.mkdir(parents=True, exist_ok=True)
    (GENERATED / "dkim").mkdir(parents=True, exist_ok=True)
    network_values = lab_network_values()
    domains = load_domains()

    secrets_path = RUNTIME / "secrets.json"
    if not fresh_credentials and secrets_path.exists():
        secrets_data = json.loads(secrets_path.read_text(encoding="utf-8"))
    else:
        accounts: dict[str, dict[str, str]] = {}
        for record in domains:
            for local in record["mailboxes"]:
                address = f"{local.lower()}@{record['domain']}"
                accounts[address] = {"username": address, "password": secrets.token_urlsafe(24)}
        recovery = {"username": "mailforge-recovery", "password": secrets.token_urlsafe(32)}
        secrets_data = {"accounts": accounts, "recovery": recovery}
        write_json(secrets_path, secrets_data, 0o600)

    for record in domains:
        selector = record["dkim"]["selector"]
        key_path = GENERATED / "dkim" / f"{selector}.private.pem"
        if not key_path.exists() or fresh_credentials:
            generate_private_key(key_path, openssl)

    write_runtime(secrets_data, network_values)
    return secrets_data
