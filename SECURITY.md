# Security Policy

MailForge is currently pre-release and should not yet be treated as production-ready software.

## Reporting a vulnerability

Avoid public issues containing live credentials, private keys, exploit payloads, or immediately actionable details against deployed instances. Prefer GitHub private vulnerability reporting when enabled, or a private maintainer channel.

## Secret handling

This repository is public. Production secrets must never be committed.

If a production secret is accidentally committed, treat it as compromised and rotate it immediately. Rewriting Git history does not undo exposure to anyone who already fetched it.

## Supported versions

No production version is supported yet. A formal support policy will be added with the first tagged release.
