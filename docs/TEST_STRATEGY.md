# Test Strategy

Testing must prove MailForge is safe to expose, not merely that containers start.

## Phase 1 checks

Current automated checks run without production resources and cover:

- required/non-empty environment values, hostname/IP/CIDR syntax, production placeholder rejection, tunnel address collision, and explicit relay-domain rules;
- domain example structure, independent mailboxes/aliases/DKIM selectors, and shared infrastructure;
- image tag policy, expected repository paths, Markdown references, and obvious private-key/token material;
- Python unit tests, shell syntax, rendered Compose configuration, HAProxy TCP configuration, and Postfix's deny-by-default relay settings.

The local Compose profile is isolated and has no published ports. Rendering Compose does not start containers.

## Later layers

### Local integration

Phase 2 will simulate edge and origin and prove:

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

Phase 1 CI validates docs/config/secrets and scaffold syntax. CI must not need production secrets. Later CI adds isolated integration tests; no test may rely on a production VPS, DNS, or real mail provider.
