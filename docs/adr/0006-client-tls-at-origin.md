# ADR-0006: Terminate client TLS at the origin

- Status: Accepted
- Date: 2026-10-05

## Context

IMAPS, submission, and HTTPS/JMAP must be reachable through the edge. TLS termination at edge would duplicate certificate/authentication concerns.

## Decision

Use L4/TCP proxying for client protocols and terminate TLS at Stalwart. SMTP/25 is excluded because Postfix intentionally terminates it for queueing.

## Consequences

The edge proxy forwards TCP without decrypting mailbox credentials. Stalwart owns client certificates. DNS-01 ACME or another behind-NAT-compatible certificate workflow is preferred.
