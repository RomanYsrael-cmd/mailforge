# Documentation Index

This directory is the source of truth for MailForge architecture and implementation planning.

## Read in this order

1. [PROJECT_CHARTER.md](PROJECT_CHARTER.md) — purpose, scope, success criteria.
2. [REQUIREMENTS.md](REQUIREMENTS.md) — functional and non-functional requirements.
3. [ARCHITECTURE.md](ARCHITECTURE.md) — components, trust boundaries, mail flows.
4. [CONFIGURATION_MODEL.md](CONFIGURATION_MODEL.md) — how deployments and domains are represented.
5. [NETWORKING.md](NETWORKING.md) — ports, WireGuard, public/private exposure.
6. [DNS_AND_DELIVERABILITY.md](DNS_AND_DELIVERABILITY.md) — MX, PTR, SPF, DKIM, DMARC, TLS.
7. [SECURITY_MODEL.md](SECURITY_MODEL.md) — threat model, secret handling, hardening.
8. [OPERATIONS.md](OPERATIONS.md) — provisioning, upgrades, observability, incidents.
9. [BACKUP_AND_RECOVERY.md](BACKUP_AND_RECOVERY.md) — what is backed up and how recovery is validated.
10. [TEST_STRATEGY.md](TEST_STRATEGY.md) — validation before any production cutover.
11. [ROADMAP.md](ROADMAP.md) — staged delivery plan.
12. [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) — exact next coding milestones.

Architecture decisions are recorded under [adr/](adr/README.md).

## Documentation rules

- Architecture-changing implementation must update the relevant document and, when appropriate, add an ADR.
- Examples must use reserved/example domains and placeholder IPs unless a deployment-specific runbook explicitly requires real values.
- Secrets, private keys, passwords, API tokens, recovery codes, and live credentials must never appear in Git history.
- A document describing an unimplemented capability must label it as planned rather than implying it exists.
