# Security Policy

MailForge is currently pre-release and should not yet be treated as production-ready software. Phase 1 provides repository/local scaffolding only; it does not implement a production mail path.

## Reporting a vulnerability

Avoid public issues containing live credentials, private keys, exploit payloads, or immediately actionable details against deployed instances. Prefer GitHub private vulnerability reporting when enabled, or a private maintainer channel.

## Secret handling

This repository is public. Production secrets must never be committed. The repository ignores local environment files, key material, secret/runtime directories, queues, mailbox data, backups, and logs. CI scans repository files for common private-key markers, WireGuard private-key values, and obvious credential tokens. This automated check supplements review; it is not a guarantee that every secret format can be detected.

If a production secret is accidentally committed, treat it as compromised and rotate it immediately. Rewriting Git history does not undo exposure to anyone who already fetched it.

## Supported versions

No production version is supported yet. A formal support policy will be added with the first tagged release.
