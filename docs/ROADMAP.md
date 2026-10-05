# Roadmap

## Phase 0 — Documentation foundation

Complete. Architecture, trust boundaries, requirements, accepted ADRs, and production gates are documented.

## Phase 1 — Repository/local scaffolding

Complete. Repository boundaries, safe examples, secret exclusions and scanning, validation, tests, and CI are in place.

## Phase 2 — Local two-node mail path

Implemented. The internal lab proves Postfix inbound routing and queueing, Stalwart mailbox delivery and authenticated outbound submission, local sink delivery, per-domain DKIM evidence, open-relay rejection, multi-domain isolation, and HAProxy TLS passthrough.

The lab emulates the edge/origin trust boundary with an internal Compose network. It does not exercise a real WireGuard interface, handshake, CGNAT, or host firewall.

## Phase 3 — Real edge and CGNAT origin

Provision a real VPS edge, establish WireGuard from the private origin, enforce firewalls, and add queue/tunnel health checks. No DNS cutover until gates pass.

## Phase 4 — First production domain

Configure PTR, TLS, MX, SPF, DKIM, DMARC, one mailbox, external acceptance tests, monitoring, and backups.

## Phase 5 — Second-domain proof

Onboard another unrelated domain on the same infrastructure and prove independent DKIM/DNS/mailboxes without stack duplication.

## Phase 6 — Operational hardening

Test restore, upgrade/rollback, alerts, log retention, rate limiting, and abuse controls.

## Phase 7 — Automation/control CLI

Automate proven workflows such as domain/mailbox creation, DNS verification, status, backups, and upgrades after the architecture is proven.
