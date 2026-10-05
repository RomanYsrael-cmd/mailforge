# ADR-0002: Use Postfix as the public SMTP edge

- Status: Accepted
- Date: 2026-10-05

## Context

Transparent forwarding of SMTP/25 would not provide durable queueing during origin/home outages, and the edge must provide the stable public sending IP.

## Decision

Use Postfix on the public VPS as the Internet-facing server-to-server SMTP MTA.

## Consequences

Postfix listens on TCP/25, accepts only configured relay domains, queues toward origin, accepts trusted outbound relay from origin, and delivers to recipient MX hosts. It stores no user mailboxes. Relay policy is security-critical and requires automated open-relay tests.

Reference: https://www.postfix.org/SMTPD_ACCESS_README.html
