# Implementation Plan

This document tracks the handoff from architecture to implementation.

## Completed: Phase 1 scaffolding

The repository now contains:

- distinct `edge/postfix/`, `edge/proxy/`, `origin/stalwart/`, and `wireguard/` scaffolds;
- a safe, domain-neutral `.env.example` and independent example domain records;
- an opt-in internal Compose topology with no published ports;
- secret/runtime exclusions, a repository validator, tests, and CI checks;
- updated docs describing what is and is not implemented.

This does not provide a functional or production-ready mail path. The Postfix config has no hosted relay map; the Stalwart seed is incomplete; WireGuard keys are placeholders; the proxy only describes the intended TCP forwarding.

## Next milestone: Phase 2 local mail path

**Edge:** Postfix public SMTP listener, explicit relay domains, origin next-hop, origin-only trusted outbound path, persistent queue, and health checks.

**Origin:** Stalwart persistent data, local domains/accounts, trusted edge delivery, outbound relay through edge, submission/IMAP/HTTPS, and per-domain DKIM.

**Tunnel:** WireGuard point-to-point; no inbound requirement at a CGNAT origin.

**Client proxy:** L4 forwarding; TLS remains at Stalwart unless an ADR supersedes that decision.

### Phase 2 acceptance criteria

- no real credentials/private keys;
- local inbound/outbound relay is deny-by-default and automated no-open-relay tests pass;
- two example domains work independently through one stack;
- tunnel behavior works without unsolicited inbound connectivity to the origin;
- Compose and service configuration validate without production resources;
- documentation describes the tested behavior accurately.

## Deferred choices

Observability stack, backup vendor/tool, automatic DNS provider integration, optional webmail, secondary MX/HA, and CLI language remain deferred.

## Production gate

No live MX change until external TCP/25, outbound TCP/25, PTR+forward DNS, no-open-relay, TLS, queue/retry, SPF/DKIM/DMARC, backup+restore rehearsal, and exposed-port/secret review all pass.
