# Security Model

## Objectives

Protect mailbox confidentiality/integrity, account credentials, signing keys, sending authority, infrastructure credentials, and backups.

Assume Internet scanning, credential stuffing, spam-relay probing, malicious mail content, compromised clients, a compromised edge, accidental secret commits, and operator mistakes.

## Trust boundaries

- Internet → edge: hostile/untrusted.
- Edge → origin: authenticated infrastructure link, but least privilege still applies.
- User → mailbox: authenticated identity scope.
- Repository → deployment: public; never a secret store.
- Backup target: highly sensitive.

## Secrets

Never commit real `.env` files, private keys, passwords, API tokens, DNS credentials, backup credentials, TLS private material, WireGuard private keys, or DKIM private keys.

The repository ignores local secret/config files, private-key extensions, runtime state, mail queues, mailbox data, backups, and logs. CI scans files for common PEM/SSH private-key markers, WireGuard key values, and obvious token patterns. These checks catch common accidents but do not replace code review or secret rotation.

A committed production secret is compromised even if later deleted from the latest revision: rotate first, then clean history if appropriate.

## Authentication

Use strong unique credentials. Prefer MFA for administration where supported. Administrative access should be more restricted than end-user mail access.

## Open-relay prevention

Relaying is allowed only when destination is a configured hosted domain going toward origin, or source is the trusted origin using the approved outbound path. Automated external open-relay testing is a production gate. The Phase 1 Postfix scaffold configures no hosted domains and rejects unauthenticated relay.

## TLS and tunnel

Client protocols require TLS. Edge-origin transport is protected by WireGuard. Internet SMTP uses normal opportunistic TLS behavior. Do not globally disable certificate validation to make deployment easier.

## Host/container hardening

Pin versions, minimize writable mounts/capabilities, avoid privileged containers without documented necessity, patch hosts, use firewall default-deny inbound, and avoid credential logging.

## Backup security

Backups contain mailbox data and must be encrypted when stored outside a physically trusted boundary. Backup credentials/keys should not share the same single point of failure as the origin.
