# Domain Onboarding Runbook

The files under examples/domains/ are reserved, illustrative lab fixtures. The Phase 2 lab provisions example.com and example.org from those files and derives the Postfix SMTP recipient map from the same input. Do not apply the example DNS values literally.

Production onboarding commands and DNS automation remain deferred. Phase 3 must establish the real edge/origin transport and production operating controls first.

## Production preconditions

Confirm domain/DNS control, healthy edge/origin/tunnel, current backup, and a migration plan if the domain already receives mail elsewhere.

## Planned production steps

1. Create/enable the domain in Stalwart.
2. Create initial mailbox and aliases.
3. Generate or confirm per-domain DKIM.
4. Add the domain to the edge's explicit relay and recipient maps.
5. Produce reviewed DNS records.
6. Publish DKIM/SPF, then MX.
7. Publish DMARC in monitoring mode.
8. Verify external DNS.
9. Test unknown-recipient rejection.
10. Test inbound and outbound with controlled external providers.
11. Inspect authentication headers.
12. Record successful onboarding.

If replacing an existing provider, account for DNS TTL and temporary dual-delivery risk.

Domain removal is separate and must decide mailbox export/retention, alias migration, DNS changes, and signing-key retirement.
