# Roadmap

## Phase 0 — Documentation foundation

**Status: this documentation release**

Exit: coding can begin without another architecture-discovery pass.

## Phase 1 — Repository/local scaffolding

Create structure, pinned image policy, secret-safe examples, compose profiles, config validation, and CI. No production deployment.

## Phase 2 — Local two-node mail path

Implement Stalwart origin, Postfix edge, lab tunnel/network, inbound and outbound relay, L4 client forwarding, and automated no-open-relay tests.

## Phase 3 — Real edge + CGNAT origin

Provision a real VPS edge, establish WireGuard from the private origin, enforce firewalls, and add queue/tunnel health checks. No DNS cutover until gates pass.

## Phase 4 — First production domain

Configure PTR, TLS, MX, SPF, DKIM, DMARC, one mailbox, external acceptance tests, monitoring, and backups.

## Phase 5 — Second-domain proof

Onboard another unrelated domain on the same infrastructure and prove independent DKIM/DNS/mailboxes without stack duplication.

## Phase 6 — Operational hardening

Test restore, upgrade/rollback, alerts, log retention, rate limiting, and abuse controls.

## Phase 7 — Automation/control CLI

Automate proven workflows such as domain/mailbox creation, DNS verification, status, backups, and upgrades. Automation comes after the architecture is proven.
