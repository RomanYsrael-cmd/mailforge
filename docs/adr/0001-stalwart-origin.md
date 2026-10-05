# ADR-0001: Use Stalwart as the mailbox origin

- Status: Accepted
- Date: 2026-10-05

## Context

MailForge needs one authoritative service for multiple local domains, accounts, mailbox storage, IMAP/JMAP, submission, DKIM, and administration.

## Decision

Use Stalwart Mail Server as the origin mail platform.

## Consequences

Mailbox/domain identity centers on Stalwart; MailForge should not duplicate its source of truth. Upgrades must respect Stalwart storage/migration guidance.

References: https://stalw.art/docs/install/platform/docker/ and https://stalw.art/docs/domains/
