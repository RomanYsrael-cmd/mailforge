# Configuration Model

## Goal

The repository must not encode one operator, one domain, one IP address, or one DNS provider as an architectural assumption.

## Layers

### Repository defaults

Public schemas, examples, CI rules, and non-secret defaults. examples/domains/*.json contains only reserved example domains and test identities.

### Lab runtime configuration

python scripts/lab.py up creates ignored files under var/mailforge/runtime/: random mailbox/recovery credentials, disposable DKIM keys, Stalwart config, Postfix main.cf, relay domain/recipient/transport maps, and Compose network settings.

Postfix maps are generated from the same examples/domains/*.json files that scripts/stalwart_plan.py uses to provision Stalwart. They are a generated SMTP-time acceptance cache for the lab, not a second handwritten mailbox registry.

The Stalwart config.json contains only the v0.16 RocksDB DataStore object. Domains, accounts, aliases, listeners, routes, and DKIM signatures are provisioned as JMAP configuration objects through the pinned Stalwart CLI.

### Secrets

Never committed: WireGuard private keys, mailbox/admin passwords, API tokens, DNS credentials, backup keys, TLS private keys, and DKIM private keys. Generated lab secrets and keys are ignored under var/mailforge/.

## Domain examples and validation

examples/domains/*.json demonstrates independent domain-scoped mailboxes, aliases, DKIM selectors, and DNS policy. Stalwart remains the runtime authority. The Postfix map is generated only to reject unknown recipients during SMTP.

Run python scripts/validate_config.py --env-file .env.example or scripts/validate-config.sh. The dependency-free validator checks environment values, domain fixtures, image pins, required files, Markdown links, and obvious private key/token material.

The local profiles have three internal networks and no host-published ports. The Compose profile is lab; protocol clients and the management CLI use lab-tools.
