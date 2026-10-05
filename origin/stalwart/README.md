# Stalwart origin scaffold

Stalwart is the single source of truth for hosted domains, users, mailboxes, aliases, per-domain DKIM, and message storage. MailForge will not add a second domain registry or mailbox database.

`config.toml.example` is an identity seed, not a complete server configuration. The `compose.yaml` scaffold reserves `${MAILFORGE_DATA_ROOT}/stalwart/config` for configuration and `${MAILFORGE_DATA_ROOT}/stalwart/data` for persistent application data. Stalwart runs as UID 2000 in the upstream container; provision writable storage with the correct ownership on Linux.

The container is opt-in through the `local-scaffold` profile, is attached to an internal network, and publishes no host ports. Production hostname, TLS, domain onboarding, accounts, DKIM keys, storage tuning, backup, and network bindings are deferred to later milestones. Never store generated credentials or private keys in this repository.
