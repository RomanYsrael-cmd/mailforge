# Configuration Model

## Goal

The repository must not encode one operator, one domain, one IP address, or one DNS provider as an architectural assumption.

## Layers

### Repository defaults

Public schemas, examples, CI rules, and non-secret defaults. `.env.example` contains only reserved domains, TEST-NET addresses, and RFC1918 tunnel addresses.

### Deployment configuration

Installation-specific but non-secret values such as infrastructure hostnames, tunnel subnet, edge IP, storage paths, and feature toggles. These may live in an untracked `.env` generated from the committed example.

### Secrets

Never committed: WireGuard private keys, mailbox/admin passwords, API tokens, DNS credentials, backup keys, TLS private keys, and DKIM private keys unless protected inside authoritative Stalwart state.

## Domain examples

`examples/domains/*.json` demonstrates independent domain-scoped mailboxes, aliases, DKIM selectors, and DNS records. Both examples use one shared infrastructure hostname and edge address. These JSON files illustrate the model; Stalwart remains the runtime authority and there is no second domain registry.

## Validation

Run `python scripts/validate_config.py --env-file .env.example` or use `scripts/validate-config.sh` on POSIX systems. The dependency-free validator checks required deployment values, hostnames, addresses, relay domains, WireGuard collisions/subnet consistency, repository paths, domain examples, image tags, internal Markdown links, and obvious committed key/token material. For production, pass a deployment-specific env file and `--environment production`; example domains, TEST-NET addresses, and non-global edge addresses are rejected.

Compose defaults to non-published services behind an internal Docker network. Its opt-in `local-scaffold` profile exists to render and review service boundaries only; it is not a deployable mail path.

## Future control plane

A future CLI may automate domain/mailbox creation, DNS verification, health checks, backups, and upgrades. It must orchestrate Stalwart/Postfix rather than create a second source of truth for mailbox state.
