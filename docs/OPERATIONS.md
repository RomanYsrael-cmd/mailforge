# Operations

## Phase 2 local lab

The local lab is a test environment, not a production service. It uses reserved example domains, random temporary credentials, generated DKIM keys, internal Docker networks, and a local SMTP sink.

Start it with python scripts/lab.py up. Run the real protocol suite with python scripts/run_phase2_tests.py. Stop it with python scripts/lab.py down; this preserves Stalwart data and the Postfix queue under ignored var/mailforge/. python scripts/lab.py reset stops the lab and removes only that generated test state.

The lab does not expose host ports. The test clients run as disposable Compose services. Compose networks are internal, and Postfix directs remote-recipient messages to the sink. Do not connect the lab to production credentials or real domains.

Stalwart's random test passwords and recovery bootstrap credential are stored in ignored runtime state. The recovery credential is supplied only for initial provisioning, then removed before normal mode. The lab's admin@example.com test account has the Stalwart Admin role.

## Persistent state

The local lab stores its RocksDB data under var/mailforge/stalwart/data, Postfix's transient queue under var/mailforge/postfix-queue, and SMTP sink messages under var/mailforge/sink. Back up Stalwart data for continuity; the edge queue is transient and the sink is test evidence only.

## Future production operating model

The edge is replaceable public transport infrastructure. The origin is authoritative mailbox infrastructure.

1. Provision a suitable edge VPS and verify its public IPv4, PTR control, and TCP/25 policy.
2. Harden the edge and host firewall.
3. Provision origin storage and backups.
4. Establish WireGuard from the CGNAT origin and verify peer/route state.
5. Deploy Stalwart and Postfix with production secrets managed out of Git.
6. Perform closed relay and external acceptance tests.
7. Onboard a domain only after mail, TLS, DNS, backup, and restore gates pass.

## Version management

Stalwart is pinned to v0.16.24 in the Phase 2 lab, with the versioned management CLI pinned to v1.0.13. Review upstream release notes, stage upgrades, preserve rollback data, and verify queue/mailbox behavior after upgrades.

No DNS cutover or production mailbox migration should be performed from an unreviewed branch.
