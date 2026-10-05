# Backup and Recovery

## Principle

A backup is valid only after restore is tested.

## Must back up

- Stalwart authoritative data stores;
- mailbox/message data;
- domain/account/alias config;
- non-reproducible application config;
- continuity-critical certificate/account state;
- recovery secrets through a separate secure mechanism.

## Reconstruct from Git

Compose/manifests, templates, scripts, documentation, and non-secret defaults.

The edge queue is transient operational state, not authoritative mailbox storage.

## Strategy

Use frequent origin backups/snapshots, off-host encrypted copies, multiple restore points, and periodic restore drills. Exact tooling depends on the selected Stalwart storage backend and its consistency requirements.

## Recovery order

1. recover secrets/config needed for origin;
2. recover Stalwart and mailbox data;
3. verify local integrity;
4. restore tunnel;
5. restore edge mail path;
6. confirm DNS/PTR;
7. test inbound/outbound;
8. monitor queue drain.

## Restore test

A restore passes only if an isolated restored origin starts, enumerates expected domains/users, accesses representative mailboxes/messages, has a valid DKIM continuity or rotation path, and passes service health checks.

Do not commit backup passwords, encryption keys, or cloud credentials.
