# Security Model

## Objectives and trust boundaries

Protect mailbox data, account credentials, signing keys, sending authority, infrastructure credentials, and backups.

- Untrusted lab client to Postfix: hostile SMTP input.
- Stalwart to Postfix: trusted only by the origin's fixed private /32.
- Postfix to Stalwart: hosted delivery only over the private network.
- Postfix to sink: only simulated outbound path.
- Repository to deployment: public; never a secret store.

The Compose networks are internal and no service publishes a host port. The test client is not attached to the private or sink networks. Stalwart is not attached to the sink network. The lab has no Internet egress path.

## Relay policy

Postfix lists only fixture domains in relay_domains and only fixture addresses in relay_recipient_maps. Those maps are generated from the same JSON fixtures used by Stalwart provisioning. An untrusted client may deliver only to a listed hosted address. An arbitrary destination is rejected by reject_unauth_destination. The only trusted mynetworks entry beyond loopback is the fixed Stalwart /32. All accepted remote-recipient mail from Stalwart goes to the isolated SMTP sink.

## Secrets and test material

Never commit real .env files, mailbox/admin passwords, API tokens, TLS private material, WireGuard keys, or DKIM private keys. The local lab creates random account passwords, a temporary recovery credential, and 2048-bit DKIM keys under ignored var/mailforge/. The recovery credential is removed from the normal Stalwart container after provisioning. The secret scan checks tracked and unignored workspace files.

The Phase 2 admin@example.com account has an Admin role only to run the isolated lab. It is randomly passworded and is not a production account.

## TLS and tunnel

HAProxy runs in TCP mode and does not terminate TLS. The test compares certificate fingerprints through HAProxy and directly at Stalwart, including SMTP STARTTLS. The lab's self-signed certificate is only test evidence; it does not establish production certificate validity.

Phase 2 does not run WireGuard. Its private network emulates the routing boundary only. Production requires WireGuard, firewall rules, peer-key management, and tunnel-health checks in Phase 3.

## Host/container hardening

Pin image versions, minimize writable mounts and capabilities, avoid privileged containers, and keep Postfix's relay trust narrow. The SMTP sink is a small standard-library server and is reachable only on the sink-only network.

## Backups

Stalwart state is authoritative and sensitive. Protect backups with encryption and test restores. Postfix queue state is transient operational data; sink messages are disposable test evidence.
