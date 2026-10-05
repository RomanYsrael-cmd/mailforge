# Configuration Model

## Goal

The repository must not encode one operator, one domain, one IP address, or one DNS provider as an architectural assumption.

## Layers

### Repository defaults

Public schemas, examples, CI rules, and non-secret defaults.

### Deployment configuration

Installation-specific but non-secret values such as infrastructure hostnames, tunnel subnet, edge IP, storage paths, and feature toggles. These may live in untracked local files generated from committed examples.

### Secrets

Never committed: WireGuard private keys, mailbox/admin passwords, API tokens, DNS credentials, backup keys, TLS private keys, and DKIM private keys unless protected inside authoritative Stalwart state.

## Conceptual domain object

```yaml
name: example.com
enabled: true
dns:
  mode: manual
mail:
  catch_all: false
  plus_addressing: true
security:
  dkim: automatic
  dmarc_policy: none
```

This is an architectural example, not yet a runtime schema.

## Domain independence

Adding a second domain must not require another VPS, Postfix instance, Stalwart instance, or WireGuard tunnel. It should require only domain-specific config, DNS, and identities.

## Naming

Future implementation should use generic variables such as `MAILFORGE_EDGE_HOSTNAME`, `MAILFORGE_CLIENT_HOSTNAME`, and `MAILFORGE_EDGE_PUBLIC_IP`, never names tied to one hosted application/domain.

## Validation

Before services start, validate required hostnames, production placeholder replacement, tunnel address conflicts, explicit relay domains, secret file permissions, pinned images, and documented public ports.

## Future control plane

A future CLI may automate domain/mailbox creation, DNS verification, health checks, backups, and upgrades. It must orchestrate Stalwart/Postfix rather than create a second source of truth for mailbox state.
