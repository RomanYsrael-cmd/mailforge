# ADR-0005: Keep secrets out of Git

- Status: Accepted
- Date: 2026-10-05

## Context

MailForge is public and mail infrastructure contains high-impact credentials/private keys.

## Decision

Git stores templates/public config only. Runtime secrets come from operator-controlled files/environment/secret stores excluded from version control.

## Consequences

Examples use placeholders, CI should detect accidental secrets, operators need a separate secret-recovery plan, and any committed production secret is rotated as compromised.
