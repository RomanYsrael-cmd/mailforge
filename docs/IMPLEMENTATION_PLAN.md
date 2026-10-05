# Implementation Plan

This is the handoff from architecture to coding.

## Documentation definition of done

The docs phase is complete when component responsibilities, trust boundaries, public ports, domain-neutral config, secret policy, mail flows, failure behavior, testing, and production gates are explicit. The current documentation set meets that bar.

## Next milestone: Phase 1 scaffolding

The first coding PR must not modify live DNS or an existing mail provider.

Target layout:

```text
/
├── edge/
│   ├── postfix/
│   └── proxy/
├── origin/
│   └── stalwart/
├── wireguard/
├── scripts/
├── tests/
│   ├── integration/
│   └── security/
├── examples/
│   └── domains/
├── docs/
├── .env.example
└── compose*.yml
```

Exact filenames may change if implementation shows a cleaner structure.

### Phase 1 acceptance criteria

- no real credentials/private keys;
- reviewed pinned versions/series;
- `.gitignore` excludes secrets/runtime state;
- examples use reserved domains/IPs;
- config validator distinguishes non-production from production expectations;
- CI detects common committed secrets/private keys;
- compose/config renders without contacting production;
- README accurately reports implemented status.

## Phase 2 boundaries

**Edge:** Postfix public SMTP listener, explicit relay domains, origin next-hop, origin-only trusted outbound path, persistent queue, health checks.

**Origin:** Stalwart persistent data, local domains/accounts, trusted edge delivery, outbound relay through edge, submission/IMAP/HTTPS, per-domain DKIM.

**Tunnel:** WireGuard point-to-point; no inbound requirement on CGNAT origin.

**Client proxy:** L4 forwarding; TLS remains at Stalwart unless an ADR supersedes that decision.

## Deferred choices

These do not block Phase 1: observability stack, backup vendor/tool, automatic DNS provider integration, optional webmail, secondary MX/HA, and CLI language.

## Production gate

No live MX change until external TCP/25, outbound TCP/25, PTR+forward DNS, no-open-relay, TLS, queue/retry, SPF/DKIM/DMARC, backup+restore rehearsal, and exposed-port/secret review all pass.
