# Project Charter

## Mission

Build a reusable open-source email platform that lets one operator host mail for multiple owned domains while keeping mailbox data on self-controlled infrastructure, even when that infrastructure is behind CGNAT.

## Primary use case

An operator owns several domains and wants addresses such as `admin@example.com`, `support@example.com`, and `noreply@example.org`. The same MailForge deployment must support adding future domains without creating a separate mail stack per domain.

## Design principles

1. **Domain-neutral infrastructure.** Domains are data/configuration, not architecture.
2. **Public edge, private origin.** Internet routing concerns are separated from mailbox state.
3. **No open relay.** Relaying is explicit and least-privilege.
4. **Secrets never in Git.** Public repository safety is a first-class requirement.
5. **Recoverability over cleverness.** Queueing, backup, restore, and failure modes must be understandable.
6. **Reproducible deployment.** A fresh edge and origin can be reconstructed from source plus secret material and backups.
7. **Incremental automation.** First make the mail path correct and observable; then automate onboarding and operations.

## v1 scope

MailForge v1 will provide:

- one public edge VPS with a stable public IPv4 and configurable PTR/rDNS;
- one private origin capable of operating behind CGNAT;
- SMTP receive and send through the public edge;
- multiple local mail domains on one Stalwart origin;
- authenticated mail submission;
- IMAP and JMAP/HTTPS access;
- per-domain DKIM;
- documented SPF and DMARC onboarding;
- encrypted edge-origin transport;
- queueing at the edge when the origin is temporarily unavailable;
- backup/restore procedures;
- repeatable onboarding of at least two independent domains.

## Explicit non-goals

The first release does not promise commercial customer tenancy or billing, bulk marketing delivery, automatic reputation warming, multi-region HA, a custom webmail client, a custom mail storage engine, or bypassing anti-spam/provider restrictions.

## Current phase

Phase 0 documentation and architectural freeze is complete. Phase 1 repository/local scaffolding is implemented. The production mail path, server deployment, and DNS cutover have not started; Phase 2 is the next implementation milestone.
