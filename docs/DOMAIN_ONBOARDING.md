# Domain Onboarding Runbook

Phase 1 includes safe illustrative records in `examples/domains/`. Production onboarding commands remain deferred until a tested Phase 2 mail path exists. Do not apply the example DNS values literally.

## Preconditions

Domain/DNS control, healthy edge/origin/tunnel, current backup, and a migration plan if the domain already receives mail elsewhere.

## Planned steps

1. create/enable domain in Stalwart;
2. create initial mailbox/aliases;
3. generate or confirm per-domain DKIM;
4. add domain to the edge's explicit relay map;
5. produce DNS records;
6. publish DKIM/SPF and then MX;
7. publish DMARC in monitoring mode;
8. verify external DNS;
9. test unknown-recipient rejection;
10. test inbound from multiple providers;
11. test outbound to multiple providers;
12. inspect authentication headers;
13. record successful onboarding.

If replacing an existing provider, account for DNS TTL and temporary dual-delivery risk.

Domain removal is separate and must decide mailbox export/retention, alias migration, DNS changes, and signing-key retirement.
