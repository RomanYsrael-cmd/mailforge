#!/usr/bin/env python3
"""Build an idempotent Stalwart v0.16 management plan from the shared lab fixtures."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from lab_common import GENERATED, RUNTIME, lab_network_values, load_domains, write_text


def set_map(items: list[dict[str, Any]]) -> dict[str, Any]:
    return {str(index): item for index, item in enumerate(items)}


def build_plan() -> list[dict[str, Any]]:
    domains = load_domains()
    secrets_path = RUNTIME / "secrets.json"
    secrets_data = json.loads(secrets_path.read_text(encoding="utf-8"))
    operations: list[dict[str, Any]] = []

    domain_refs: dict[str, str] = {}
    for index, record in enumerate(domains):
        domain = record["domain"]
        ref = f"domain-{index}"
        domain_refs[domain] = ref
        operations.append(
            {
                "@type": "upsert",
                "object": "Domain",
                "matchOn": ["name"],
                "value": {
                    ref: {
                        "name": domain,
                        "isEnabled": True,
                        "allowRelaying": False,
                        "subAddressing": {"@type": "Disabled"},
                        "description": f"MailForge isolated lab domain {domain}",
                    }
                },
            }
        )

    accounts: dict[str, dict[str, Any]] = {}
    for record in domains:
        domain = record["domain"]
        for mailbox in record["mailboxes"]:
            local = mailbox.lower()
            address = f"{local}@{domain}"
            account_secret = secrets_data["accounts"][address]
            aliases = [
                {
                    "name": alias.lower(),
                    "domainId": f"#{domain_refs[domain]}",
                    "enabled": True,
                }
                for alias, target in record["aliases"].items()
                if target.lower() == local
            ]
            accounts[f"account-{len(accounts)}"] = {
                "@type": "User",
                "name": local,
                "domainId": f"#{domain_refs[domain]}",
                "credentials": {
                    "0": {
                        "@type": "Password",
                        "secret": account_secret["password"],
                    }
                },
                "memberGroupIds": {},
                "roles": {"@type": "Admin" if address == "admin@example.com" else "User"},
                "permissions": {"@type": "Inherit"},
                "quotas": {},
                "aliases": set_map(aliases),
                "encryptionAtRest": {"@type": "Disabled"},
                "description": f"MailForge Phase 2 lab account {address}",
            }
    operations.append(
        {
            "@type": "upsert",
            "object": "Account",
            "matchOn": ["name", "domainId"],
            "value": accounts,
        }
    )

    dkim_values: dict[str, dict[str, Any]] = {}
    for index, record in enumerate(domains):
        selector = record["dkim"]["selector"]
        key_path = GENERATED / "dkim" / f"{selector}.private.pem"
        key = key_path.read_text(encoding="utf-8")
        dkim_values[f"dkim-{index}"] = {
            "@type": "Dkim1RsaSha256",
            "domainId": f"#{domain_refs[record['domain']]}",
            "selector": selector,
            "privateKey": {"@type": "Text", "secret": key},
            "canonicalization": "relaxed/relaxed",
        }
    operations.append(
        {
            "@type": "upsert",
            "object": "DkimSignature",
            "matchOn": ["domainId", "selector"],
            "value": dkim_values,
        }
    )

    origin_ip = lab_network_values()["MAILFORGE_LAB_ORIGIN_IP"]
    listeners = [
        {"name": "smtp", "protocol": "smtp", "bind": {"0.0.0.0:25": True}},
        {"name": "https", "protocol": "http", "bind": {"0.0.0.0:443": True}, "useTls": True},
        {"name": "submissions", "protocol": "smtp", "bind": {"0.0.0.0:465": True}, "useTls": True, "tlsImplicit": True},
        {"name": "submission", "protocol": "smtp", "bind": {"0.0.0.0:587": True}, "useTls": True, "tlsImplicit": False},
        {"name": "imaps", "protocol": "imap", "bind": {"0.0.0.0:993": True}, "useTls": True, "tlsImplicit": True},
        {"name": "management", "protocol": "http", "bind": {f"{origin_ip}:8080": True}, "useTls": False},
    ]
    operations.append(
        {
            "@type": "upsert",
            "object": "NetworkListener",
            "matchOn": ["name"],
            "value": {f"listener-{item['name']}": item for item in listeners},
        }
    )

    route_values: dict[str, dict[str, Any]] = {
        "route-local": {"@type": "Local", "name": "local"},
        "route-postfix": {
            "@type": "Relay",
            "name": "postfix-edge",
            "address": "edge-postfix",
            "port": 25,
            "protocol": "smtp",
            "implicitTls": False,
            "allowInvalidCerts": False,
            "authSecret": {"@type": "None"},
            "description": "Isolated lab edge; its only outbound path is the local SMTP sink.",
        },
    }
    operations.append(
        {
            "@type": "upsert",
            "object": "MtaRoute",
            "matchOn": ["name"],
            "value": route_values,
        }
    )

    first_domain = domains[0]["domain"]
    operations.extend(
        [
            {
                "@type": "update",
                "object": "SystemSettings",
                "value": {
                    "defaultHostname": "mail.mail.example.net",
                    "defaultDomainId": f"#{domain_refs[first_domain]}",
                },
            },
            {
                "@type": "update",
                "object": "SenderAuth",
                "value": {
                    "dkimSignDomain": {
                        "match": {
                            "0": {
                                "if": "is_local_domain(sender_domain) && !is_empty(authenticated_as)",
                                "then": "sender_domain",
                            }
                        },
                        "else": "false",
                    }
                },
            },
            {
                "@type": "update",
                "object": "MtaOutboundStrategy",
                "value": {
                    "route": {
                        "match": {
                            "0": {
                                "if": "is_local_domain(rcpt_domain)",
                                "then": "'local'",
                            }
                        },
                        "else": "'postfix-edge'",
                    }
                },
            },
        ]
    )
    return operations


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=RUNTIME / "provision" / "plan.ndjson")
    args = parser.parse_args()
    operations = build_plan()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    body = "\n".join(json.dumps(item, separators=(",", ":")) for item in operations) + "\n"
    write_text(args.output, body, 0o600)
    print(f"Generated {len(operations)} Stalwart operations for {len(load_domains())} fixture domains.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
