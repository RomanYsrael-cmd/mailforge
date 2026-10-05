# Requirements

## Functional requirements

### Domains and identities

- MF-FR-001: Host multiple independent email domains on one origin.
- MF-FR-002: Adding a domain must not require another Stalwart instance.
- MF-FR-003: Each domain supports independent mailboxes, aliases, DKIM keys, SPF policy, and DMARC policy.
- MF-FR-004: Unknown recipients are rejected by default; catch-all is opt-in.
- MF-FR-005: Domain removal requires explicit operator action and a retention decision.

### Mail transport

- MF-FR-010: Public edge accepts Internet SMTP on TCP/25 for configured relay domains only.
- MF-FR-011: Public edge queues accepted inbound mail while origin is temporarily unavailable.
- MF-FR-012: Origin relays outbound Internet mail through public edge.
- MF-FR-013: Edge rejects unauthorized third-party relaying.
- MF-FR-014: DKIM signing occurs per sender domain before Internet delivery.

### Client access

- MF-FR-020: Encrypted authenticated submission.
- MF-FR-021: Encrypted IMAP.
- MF-FR-022: HTTPS/JMAP/admin endpoints use TLS.
- MF-FR-023: CGNAT origin does not require a directly routable public IPv4.

### Operations

- MF-FR-030: Operators can determine edge queue depth and origin reachability.
- MF-FR-031: Operators can back up and restore authoritative origin state.
- MF-FR-032: Production does not track uncontrolled floating image tags.
- MF-FR-033: Domain onboarding has a DNS verification checklist.
- MF-FR-034: A repeatable second-domain acceptance test proves reuse.

## Non-functional requirements

### Security

- MF-NFR-001: No production secrets in Git.
- MF-NFR-002: Edge-origin traffic uses WireGuard or equivalently authenticated encryption.
- MF-NFR-003: Administrative interfaces are no more exposed than necessary.
- MF-NFR-004: SMTP relay policy is deny-by-default.
- MF-NFR-005: Services use least privilege practical for their role.

### Reliability

- MF-NFR-010: Temporary origin outage must not immediately lose already-accepted inbound messages.
- MF-NFR-011: Backups are not valid until restore is tested.
- MF-NFR-012: Queue retention exceeds expected short home/ISP outages.

### Maintainability

- MF-NFR-020: Domain-specific values are externalized.
- MF-NFR-021: Architecture changes require documentation.
- MF-NFR-022: Deployment configuration is reviewable without revealing secrets.
- MF-NFR-023: Replacing the edge does not require mailbox migration.

## External prerequisites

Production requires authoritative DNS control and a public edge host with dedicated IP, inbound/outbound TCP/25, configurable reverse DNS, and acceptable IP reputation. A VPS that blocks outbound TCP/25 is not suitable as the direct MailForge edge.
