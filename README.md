# MailForge

MailForge is a reusable, multi-domain email platform designed for operators whose mailbox origin may live behind CGNAT.

> Status: Phase 0 documentation, Phase 1 scaffold, and Phase 2 isolated local mail path are implemented. No production deployment, live domain migration, or DNS cutover has started. Phase 3 is next.

## Phase 2 local lab

The lab proves the mail path with real Postfix, Stalwart, SMTP, IMAP, and HAProxy traffic:

- Untrusted SMTP reaches Postfix on port 25. Postfix accepts only the configured example domains and recipients, and queues mail while Stalwart is unavailable.
- Stalwart is authoritative for domains, accounts, aliases, mailboxes, message state, and per-domain DKIM.
- Authenticated submission reaches Stalwart through HAProxy. HAProxy forwards TCP only, and TLS terminates at Stalwart.
- Stalwart sends remote-recipient mail through the trusted Postfix edge. Postfix sends all lab outbound mail to a local SMTP sink.
- Domain and recipient maps are generated from the same examples/domains JSON fixtures used to provision Stalwart.

The three Docker networks are internal and no service publishes a host port. They separate untrusted clients, the edge-to-origin path, and the sink. The private Compose network represents the edge/origin trust boundary; Phase 2 does not run a WireGuard tunnel or validate a tunnel handshake. Phase 3 must prove WireGuard connectivity from an origin behind CGNAT.

Stalwart is pinned to v0.16.24 and provisioned with the versioned Stalwart CLI v1.0.13. The old TOML identity seed has been replaced with the v0.16 JSON datastore configuration and management API objects.

## Run the lab

Prerequisites are Docker Compose, Python 3, and OpenSSL. OpenSSL generates disposable 2048-bit DKIM test keys. Set MAILFORGE_OPENSSL or pass --openssl if it is not on PATH. Set MAILFORGE_DOCKER if the Docker CLI is not on PATH.

    python scripts/validate_config.py --env-file .env.example
    python -m unittest discover -s tests -p 'test_*.py' -v
    python scripts/lab.py up
    python scripts/run_phase2_tests.py
    python scripts/lab.py down

The tests run SMTP and IMAP clients inside disposable containers. They cover both example domains, aliases, unknown recipient/domain rejection, untrusted relay rejection, authenticated outbound delivery, DKIM headers, origin-down queueing and automatic retry, and TLS passthrough on ports 443, 465, 587, and 993.

Runtime credentials, DKIM keys, Stalwart RocksDB data, Postfix queue files, and sink messages are created under ignored var/mailforge/. The random test credentials are stored there for repeatable runs. The lab uses reserved example domains and has no Internet egress through its Docker networks.

Use python scripts/lab.py reset to stop the lab and remove only the generated var/mailforge/ state. This deletes its test mail, queue, credentials, and generated DKIM keys.

## Architecture

Postfix is the transport edge. Stalwart owns users, mailboxes, aliases, message storage, and DKIM. HAProxy is TCP-mode only. The local SMTP sink receives all simulated remote mail.

Production remains out of scope: no real VPS, public TCP/25, WireGuard deployment, real domains, credentials, DNS records, firewall rules, current mail provider, or live mail has been touched. Do not treat the Phase 2 defaults or self-signed lab certificate as production configuration.

See [docs/INDEX.md](docs/INDEX.md), [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md), [docs/NETWORKING.md](docs/NETWORKING.md), [docs/SECURITY_MODEL.md](docs/SECURITY_MODEL.md), [docs/OPERATIONS.md](docs/OPERATIONS.md), and [docs/TEST_STRATEGY.md](docs/TEST_STRATEGY.md).

## Non-goals for v1

MailForge is not a commercial multi-tenant SaaS, bulk-mail platform, newsletter sender, anonymous relay, or replacement for domain registration and DNS hosting.

## License

Apache License 2.0. See LICENSE.
