# Backup and Recovery

## Principle

A backup is valid only after restore is tested.

## Phase 2 lab state

Stalwart is the authoritative store. Its local RocksDB state is mounted at var/mailforge/stalwart/data. The startup config is generated under var/mailforge/runtime/generated/stalwart/config.json. Lab credentials and DKIM private keys also live in ignored runtime state.

Postfix queue data under var/mailforge/postfix-queue is transient transport state. The local SMTP sink files under var/mailforge/sink are test evidence and can be discarded. The Phase 2 CI workflow removes all generated state after testing.

## Production backup contents

- Stalwart authoritative datastore and mailbox/message data;
- domain/account/alias configuration;
- non-reproducible application configuration;
- continuity-critical certificate/account state;
- recovery secrets through a separate secure mechanism.

The edge queue is not authoritative mailbox storage. Reconstruct Compose manifests, templates, scripts, docs, and non-secret defaults from Git.

## Recovery order

1. Recover secrets/config needed for the origin.
2. Restore Stalwart and mailbox data using the selected backend's consistency procedure.
3. Verify local integrity and expected accounts/messages.
4. Restore the tunnel.
5. Restore the edge mail path.
6. Confirm DNS/PTR only during an approved production recovery.
7. Test inbound/outbound and monitor queue drain.

A restore passes only if an isolated restored origin starts, enumerates expected domains/users, accesses representative mailbox messages, has a DKIM continuity or rotation path, and passes service health checks.

Do not commit backup passwords, encryption keys, or cloud credentials.
