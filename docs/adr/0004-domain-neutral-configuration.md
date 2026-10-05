# ADR-0004: Keep infrastructure domain-neutral

- Status: Accepted
- Date: 2026-10-05

## Context

Hard-coding a current domain would turn the repository into one installation's backup rather than reusable software.

## Decision

Hosted domains are configuration/data. Generic infrastructure naming is used in source, and public examples use reserved domains such as `example.com`.

## Consequences

One deployment can host many domains; each keeps independent DNS/DKIM/mailboxes; adding a domain does not duplicate the stack.
