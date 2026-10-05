#!/usr/bin/env python3
"""Dependency-free checks for MailForge's public scaffold and local config."""

from __future__ import annotations

import argparse
import ipaddress
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Iterable, Mapping
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
REQUIRED_ENV = (
    "MAILFORGE_ENVIRONMENT",
    "MAILFORGE_EDGE_HOSTNAME",
    "MAILFORGE_CLIENT_HOSTNAME",
    "MAILFORGE_EDGE_PUBLIC_IP",
    "MAILFORGE_WG_EDGE_ADDRESS",
    "MAILFORGE_WG_ORIGIN_ADDRESS",
    "MAILFORGE_WG_PORT",
    "MAILFORGE_DATA_ROOT",
    "MAILFORGE_RELAY_DOMAINS",
)
ENVIRONMENTS = {"development", "test", "production"}
HOSTNAME_PATTERN = re.compile(
    r"(?=.{1,253}$)[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?"
    r"(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?)+"
)
LOCAL_PART_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._+-]{0,63}$")
EXAMPLE_DOMAINS = {"example.com", "example.net", "example.org"}
TEST_NETS = tuple(
    ipaddress.ip_network(value)
    for value in ("192.0.2.0/24", "198.51.100.0/24", "203.0.113.0/24")
)
REQUIRED_PATHS = (
    ".env.example",
    ".gitignore",
    "compose.yaml",
    "edge/postfix/Dockerfile",
    "edge/postfix/.dockerignore",
    "edge/postfix/README.md",
    "edge/postfix/main.cf",
    "edge/proxy/README.md",
    "edge/proxy/haproxy.cfg",
    "origin/stalwart/README.md",
    "origin/stalwart/config.toml.example",
    "wireguard/README.md",
    "wireguard/edge.conf.example",
    "wireguard/origin.conf.example",
    "scripts/validate-config.sh",
    "scripts/validate_config.py",
    "tests/integration",
    "tests/security",
    "examples/domains",
    ".github/workflows/ci.yml",
    "docs/INDEX.md",
    "docs/PROJECT_CHARTER.md",
    "docs/REQUIREMENTS.md",
    "docs/ARCHITECTURE.md",
    "docs/CONFIGURATION_MODEL.md",
    "docs/NETWORKING.md",
    "docs/DNS_AND_DELIVERABILITY.md",
    "docs/SECURITY_MODEL.md",
    "docs/OPERATIONS.md",
    "docs/BACKUP_AND_RECOVERY.md",
    "docs/TEST_STRATEGY.md",
    "docs/ROADMAP.md",
    "docs/IMPLEMENTATION_PLAN.md",
    "docs/DOMAIN_ONBOARDING.md",
)
PRIVATE_SUFFIXES = {".key", ".private", ".p12", ".pfx", ".p7b", ".p7c", ".jks", ".keystore"}
PRIVATE_MARKERS = (
    "-----BEGIN " + "PRIVATE KEY-----",
    "-----BEGIN ENCRYPTED " + "PRIVATE KEY-----",
    "-----BEGIN RSA " + "PRIVATE KEY-----",
    "-----BEGIN EC " + "PRIVATE KEY-----",
    "-----BEGIN DSA " + "PRIVATE KEY-----",
    "-----BEGIN OPENSSH " + "PRIVATE KEY-----",
    "-----BEGIN PGP " + "PRIVATE KEY BLOCK-----",
)
PRIVATE_KEY_LINE = re.compile(r"(?im)^\s*PrivateKey\s*=\s*[A-Za-z0-9+/]{43}=\s*$")
TOKEN_PATTERNS = (
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{30,}\b"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
)


def parse_env_file(path: Path) -> dict[str, str]:
    """Read simple KEY=value lines without evaluating shell syntax."""
    values: dict[str, str] = {}
    for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:].lstrip()
        if "=" not in line:
            raise ValueError(f"{path}:{line_number}: expected KEY=value")
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", key):
            raise ValueError(f"{path}:{line_number}: invalid variable name")
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        values[key] = value
    return values


def _is_example_hostname(hostname: str) -> bool:
    lowered = hostname.lower().rstrip(".")
    return (
        lowered in EXAMPLE_DOMAINS
        or any(lowered.endswith("." + domain) for domain in EXAMPLE_DOMAINS)
        or lowered.endswith((".example", ".test", ".invalid", ".localhost"))
        or lowered in {"example", "test", "invalid", "localhost"}
    )


def _valid_hostname(hostname: str) -> bool:
    return bool(HOSTNAME_PATTERN.fullmatch(hostname))


def validate_environment(
    values: Mapping[str, str], environment_override: str | None = None
) -> list[str]:
    errors: list[str] = []
    for key in REQUIRED_ENV:
        if not values.get(key, "").strip():
            errors.append(f"required value is missing: {key}")

    environment = (environment_override or values.get("MAILFORGE_ENVIRONMENT", "")).strip().lower()
    if environment not in ENVIRONMENTS:
        errors.append("MAILFORGE_ENVIRONMENT must be development, test, or production")

    for key in ("MAILFORGE_EDGE_HOSTNAME", "MAILFORGE_CLIENT_HOSTNAME"):
        hostname = values.get(key, "").strip()
        if hostname and not _valid_hostname(hostname):
            errors.append(f"{key} is not a valid fully qualified hostname")
        elif environment == "production" and hostname and _is_example_hostname(hostname):
            errors.append(f"{key} still uses an example or placeholder hostname")

    edge_ip_value = values.get("MAILFORGE_EDGE_PUBLIC_IP", "").strip()
    if edge_ip_value:
        try:
            edge_ip = ipaddress.ip_address(edge_ip_value)
            if edge_ip.version != 4:
                errors.append("MAILFORGE_EDGE_PUBLIC_IP must be an IPv4 address")
            if environment == "production" and any(edge_ip in network for network in TEST_NETS):
                errors.append("MAILFORGE_EDGE_PUBLIC_IP must not use a TEST-NET placeholder")
            if environment == "production" and not edge_ip.is_global:
                errors.append("production MAILFORGE_EDGE_PUBLIC_IP must be globally routable")
        except ValueError:
            errors.append("MAILFORGE_EDGE_PUBLIC_IP is not a valid IP address")

    interfaces: dict[str, ipaddress.IPv4Interface] = {}
    for key in ("MAILFORGE_WG_EDGE_ADDRESS", "MAILFORGE_WG_ORIGIN_ADDRESS"):
        value = values.get(key, "").strip()
        if not value:
            continue
        try:
            parsed = ipaddress.ip_interface(value)
            if parsed.version != 4:
                errors.append(f"{key} must be an IPv4 CIDR interface")
            else:
                interfaces[key] = parsed
                if not parsed.ip.is_private:
                    errors.append(f"{key} must use private tunnel addressing")
        except ValueError:
            errors.append(f"{key} is not a valid IPv4 CIDR interface")

    edge_tunnel = interfaces.get("MAILFORGE_WG_EDGE_ADDRESS")
    origin_tunnel = interfaces.get("MAILFORGE_WG_ORIGIN_ADDRESS")
    if edge_tunnel and origin_tunnel:
        if edge_tunnel.ip == origin_tunnel.ip:
            errors.append("edge and origin WireGuard addresses collide")
        if edge_tunnel.network != origin_tunnel.network:
            errors.append("edge and origin WireGuard addresses must share one point-to-point subnet")

    port_value = values.get("MAILFORGE_WG_PORT", "").strip()
    if port_value:
        try:
            port = int(port_value)
            if not 1 <= port <= 65535:
                errors.append("MAILFORGE_WG_PORT must be between 1 and 65535")
        except ValueError:
            errors.append("MAILFORGE_WG_PORT must be an integer")

    data_root = values.get("MAILFORGE_DATA_ROOT", "").strip()
    if data_root:
        data_path = Path(data_root)
        if data_path == Path(".") or data_root in {"/", "\\"}:
            errors.append("MAILFORGE_DATA_ROOT must name a dedicated data directory")
        elif ".." in data_path.parts:
            errors.append("relative MAILFORGE_DATA_ROOT must not escape the repository")

    relay_value = values.get("MAILFORGE_RELAY_DOMAINS", "")
    relay_domains = [domain.strip().lower().rstrip(".") for domain in relay_value.split(",")]
    if not relay_value.strip() or any(not domain for domain in relay_domains):
        errors.append("MAILFORGE_RELAY_DOMAINS must list one or more explicit hosted domains")
    else:
        if len(set(relay_domains)) != len(relay_domains):
            errors.append("MAILFORGE_RELAY_DOMAINS contains duplicates")
        for domain in relay_domains:
            if "*" in domain or not _valid_hostname(domain):
                errors.append(f"unsafe or invalid relay domain: {domain}")
            elif environment == "production" and _is_example_hostname(domain):
                errors.append(f"production relay domain is still an example: {domain}")

    return errors


def validate_domain_examples(directory: Path) -> list[str]:
    errors: list[str] = []
    files = sorted(directory.glob("*.json")) if directory.is_dir() else []
    if len(files) < 2:
        return [f"{directory}: at least two independent domain examples are required"]

    domains: set[str] = set()
    selectors: set[str] = set()
    for path in files:
        try:
            document = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"{path}: invalid JSON ({exc})")
            continue
        if not isinstance(document, dict):
            errors.append(f"{path}: domain example must be a JSON object")
            continue
        domain = document.get("domain")
        if not isinstance(domain, str) or not _valid_hostname(domain):
            errors.append(f"{path}: domain must be a valid hostname")
            continue
        if domain in domains:
            errors.append(f"{path}: duplicate domain definition for {domain}")
        domains.add(domain)
        if path.stem.lower() != domain.lower():
            errors.append(f"{path}: filename must match its domain")

        mailboxes = document.get("mailboxes")
        if not isinstance(mailboxes, list) or not mailboxes:
            errors.append(f"{path}: at least one domain-scoped mailbox is required")
            mailbox_set: set[str] = set()
        else:
            mailbox_set = set()
            for mailbox in mailboxes:
                if not isinstance(mailbox, str) or not LOCAL_PART_PATTERN.fullmatch(mailbox):
                    errors.append(f"{path}: mailbox names must be valid local parts, without a domain")
                elif mailbox in mailbox_set:
                    errors.append(f"{path}: duplicate mailbox local part {mailbox}")
                else:
                    mailbox_set.add(mailbox)

        aliases = document.get("aliases")
        if not isinstance(aliases, dict):
            errors.append(f"{path}: aliases must be a domain-scoped object")
        else:
            for alias, target in aliases.items():
                if not isinstance(alias, str) or not LOCAL_PART_PATTERN.fullmatch(alias):
                    errors.append(f"{path}: alias names must be valid local parts")
                if not isinstance(target, str) or target not in mailbox_set:
                    errors.append(f"{path}: alias targets must name a mailbox in the same domain")

        dkim = document.get("dkim")
        if not isinstance(dkim, dict):
            errors.append(f"{path}: a domain-specific DKIM definition is required")
        else:
            selector = dkim.get("selector")
            if not isinstance(selector, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,63}", selector):
                errors.append(f"{path}: DKIM selector is invalid")
            elif selector in selectors:
                errors.append(f"{path}: DKIM selector must be independent per domain")
            else:
                selectors.add(selector)
            if dkim.get("authority") != "Stalwart":
                errors.append(f"{path}: Stalwart must remain the DKIM authority")
            if not dkim.get("private_key_storage"):
                errors.append(f"{path}: describe out-of-repository DKIM private key storage")

        dns = document.get("dns")
        if not isinstance(dns, dict) or not all(dns.get(key) for key in ("mx", "spf", "dmarc")):
            errors.append(f"{path}: per-domain MX, SPF, and DMARC examples are required")
    return errors


def _image_tag(reference: str) -> str | None:
    without_digest = reference.split("@", 1)[0]
    last_component = without_digest.rsplit("/", 1)[-1]
    if ":" not in last_component:
        return None
    return last_component.rsplit(":", 1)[1]


def validate_image_pins(root: Path) -> list[str]:
    errors: list[str] = []
    references: list[tuple[Path, str]] = []
    compose_path = root / "compose.yaml"
    if compose_path.exists():
        for line_number, line in enumerate(compose_path.read_text(encoding="utf-8").splitlines(), 1):
            match = re.match(r"^\s*image:\s*[\"']?([^\s\"'#]+)", line)
            if match:
                references.append((compose_path, match.group(1)))
    for dockerfile in root.rglob("Dockerfile"):
        if ".git" in dockerfile.parts:
            continue
        for line_number, line in enumerate(dockerfile.read_text(encoding="utf-8").splitlines(), 1):
            match = re.match(r"^\s*FROM\s+(?:--platform=\S+\s+)?([^\s]+)", line, re.IGNORECASE)
            if match and match.group(1).lower() != "scratch":
                references.append((dockerfile, match.group(1)))
    if not references:
        errors.append("no container image references found in Compose or Dockerfiles")
    for path, reference in references:
        tag = _image_tag(reference)
        if tag is None and "@sha256:" not in reference:
            errors.append(f"{path}: image must have a version tag or digest: {reference}")
        elif tag is not None and re.search(r"(^|[-_.])latest($|[-_.])", tag, re.IGNORECASE):
            errors.append(f"{path}: uncontrolled latest image tag is not allowed: {reference}")
    return errors


def _candidate_files(root: Path) -> list[Path]:
    try:
        result = subprocess.run(
            ["git", "-C", str(root), "ls-files", "-co", "--exclude-standard", "-z"],
            check=True,
            capture_output=True,
        )
        names = result.stdout.decode("utf-8", errors="replace").split("\0")
        return [root / name for name in names if name]
    except (OSError, subprocess.CalledProcessError):
        return [
            path
            for path in root.rglob("*")
            if path.is_file() and ".git" not in path.parts
        ]


def scan_private_material(root: Path, files: Iterable[Path] | None = None) -> list[str]:
    errors: list[str] = []
    candidate_files = list(files) if files is not None else _candidate_files(root)
    for path in candidate_files:
        if path.is_symlink() or not path.is_file():
            continue
        suffix = path.suffix.lower()
        lower_name = path.name.lower()
        relative = str(path.relative_to(root)) if path.is_relative_to(root) else str(path)
        if suffix in PRIVATE_SUFFIXES or (suffix == ".pem" and not lower_name.endswith((".crt.pem", ".cert.pem"))):
            errors.append(f"private-material file type must not be committed: {relative}")
            continue
        try:
            if path.stat().st_size > 5_000_000:
                continue
            contents = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if any(marker in contents for marker in PRIVATE_MARKERS):
            errors.append(f"private key marker found in {relative}")
        if PRIVATE_KEY_LINE.search(contents):
            errors.append(f"WireGuard private key value found in {relative}")
        if any(pattern.search(contents) for pattern in TOKEN_PATTERNS):
            errors.append(f"credential/token pattern found in {relative}")
    return errors


def validate_markdown_links(root: Path) -> list[str]:
    errors: list[str] = []
    link_pattern = re.compile(r"(?<!!)\[[^\]]*\]\(([^)]+)\)")
    for markdown in root.rglob("*.md"):
        if ".git" in markdown.parts:
            continue
        try:
            contents = markdown.read_text(encoding="utf-8")
        except OSError:
            continue
        for raw_target in link_pattern.findall(contents):
            target = raw_target.strip().split()[0].strip("<>")
            if not target or target.startswith(("#", "http://", "https://", "mailto:")):
                continue
            target_path = unquote(target.split("#", 1)[0])
            if not target_path:
                continue
            resolved = (markdown.parent / target_path).resolve()
            if not resolved.exists():
                errors.append(f"{markdown.relative_to(root)}: broken documentation link to {target_path}")
    return errors


def validate_repository(root: Path, env_file: Path, environment: str | None = None) -> list[str]:
    errors: list[str] = []
    try:
        values = parse_env_file(env_file)
    except (OSError, ValueError) as exc:
        return [f"unable to read deployment configuration {env_file}: {exc}"]

    errors.extend(validate_environment(values, environment))
    for relative in REQUIRED_PATHS:
        if not (root / relative).exists():
            errors.append(f"required repository path is missing: {relative}")
    errors.extend(validate_domain_examples(root / "examples" / "domains"))
    errors.extend(validate_image_pins(root))
    errors.extend(scan_private_material(root))
    errors.extend(validate_markdown_links(root))
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--env-file", type=Path, help="deployment env file (defaults to .env, then .env.example)")
    parser.add_argument("--environment", choices=sorted(ENVIRONMENTS), help="validate as this environment")
    args = parser.parse_args(argv)
    root = args.root.resolve()
    env_file = args.env_file
    if env_file is None:
        local_env = root / ".env"
        env_file = local_env if local_env.is_file() else root / ".env.example"
    elif not env_file.is_absolute():
        env_file = root / env_file
    errors = validate_repository(root, env_file, args.environment)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        print(f"Configuration validation failed with {len(errors)} error(s).", file=sys.stderr)
        return 1
    print(f"Configuration validation passed for {env_file.name}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
