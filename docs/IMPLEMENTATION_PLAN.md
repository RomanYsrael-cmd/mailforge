# Implementation Plan

## Completed: Phase 1 scaffolding

Phase 1 created the edge/origin/tunnel boundaries, domain-neutral fixtures, secret protections, validation tooling, tests, and CI. Its Postfix main.cf remains a closed default configuration.

## Completed: Phase 2 local two-node mail path

Phase 2 implements a repeatable isolated lab:

- Postfix accepts the two fixture domains and only fixture-listed mailboxes and aliases.
- Hosted mail routes to Stalwart's fixed private lab address. Stalwart owns mailbox state.
- Postfix trusts the origin's single /32 address for outbound relay and sends all relayed mail to the local SMTP sink.
- Stalwart uses RocksDB persistence, fixture-derived domains/accounts/aliases, separate generated DKIM keys, SMTP submission, IMAPS, HTTPS, and declarative CLI provisioning.
- HAProxy forwards TCP ports 443, 465, 587, and 993; TLS remains at Stalwart.
- The integration suite proves inbound delivery to each domain, aliases, recipient/domain and open-relay rejection, authenticated outbound sink delivery, DKIM signature domain/selector, queue retention while the origin is down, and automatic queue retry after it returns.
- Three internal Compose networks prevent Internet egress and isolate the untrusted client, the private origin path, and the SMTP sink.

The Compose private network validates the trust boundary in a local container lab. It does not run WireGuard or prove CGNAT traversal. The actual tunnel and network path are Phase 3 gates.

## Next milestone: Phase 3 real edge and CGNAT origin

Provision a real VPS edge, verify public IPv4 and TCP/25 policy, establish WireGuard from the private origin, configure host firewall rules, and add tunnel health checks. Do not change DNS until the production gates pass.

## Deferred choices

Monitoring stack, backup vendor/tooling, automatic DNS provider integration, webmail, secondary MX/HA, and a production provisioning CLI remain deferred.

## Production gate

No live MX change until public SMTP reachability, outbound delivery, PTR/forward DNS, no-open-relay, production TLS, queue/retry, SPF/DKIM/DMARC, backup and restore, and firewall/secret reviews pass.
