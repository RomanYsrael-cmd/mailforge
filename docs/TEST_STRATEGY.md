# Test Strategy

Testing must prove MailForge is safe to expose, not merely that containers start.

## Layers

### Static validation

Validate configuration syntax, duplicate ports, missing variables, production placeholders, secret permissions, version policy, and documentation links.

### Local integration

Simulate edge and origin and prove:

- edge accepts only configured relay domains;
- unauthorized relay is rejected;
- Stalwart accepts trusted edge delivery;
- outbound Stalwart mail relays through edge;
- multiple domains remain independent;
- client proxying reaches origin.

### Failure tests

Stop Stalwart and verify edge queues; restart and verify drain. Break WireGuard and verify defer/retry behavior. Restart edge and verify origin data unaffected.

### Security tests

Before production: external open-relay test, TLS/hostname check, firewall scan, admin exposure review, default-credential check, repository secret scan, and brute-force/rate-limit assessment.

### DNS/authentication tests

Per domain: verify MX, FCrDNS/PTR, SPF, DKIM, DMARC, and outbound authentication headers.

### Multi-domain acceptance

The release is not reusable until two unrelated domains operate simultaneously with independent identities and DKIM/DNS policy.

## CI

Early CI validates docs/config/secrets. Later CI adds ephemeral integration tests. CI must not need production secrets.
