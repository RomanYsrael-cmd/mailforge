# Stalwart origin

Stalwart is the single source of truth for hosted domains, users, mailboxes, aliases, per-domain DKIM, and message storage. The Phase 2 lab pins stalwartlabs/stalwart:v0.16.24 and the official management CLI image ghcr.io/stalwartlabs/cli:1.0.13.

Stalwart v0.16 uses config.json for the datastore and JMAP objects for other configuration. The example startup file config.json.example contains a single RocksDb DataStore with data stored under /var/lib/stalwart. The old TOML identity seed is no longer used.

python scripts/lab.py up creates disposable mailbox credentials and DKIM keys under ignored var/mailforge/runtime, starts a recovery-mode instance, applies domains/accounts/aliases/listeners/routes/signatures through the versioned CLI, removes the recovery administrator environment, and restarts in normal mode. Provisioning is idempotent. The admin@example.com fixture account has an Admin role only in the lab.

The normal management listener binds to the Stalwart private lab address on port 8080. It is not routed through HAProxy. Client HTTPS, SMTP submission, and IMAPS are forwarded in TCP mode and TLS terminates at Stalwart. The lab certificate may be self-signed.

The container's RocksDB data is persistent at var/mailforge/stalwart/data. Do not put generated passwords, recovery credentials, or DKIM private keys in Git. The Compose profile is lab and publishes no host ports.
