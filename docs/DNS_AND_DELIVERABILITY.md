# DNS and Deliverability

MailForge can provide protocol correctness; no self-hosted platform can guarantee inbox placement or IP reputation.

## Infrastructure records

Example only:

```text
mx1.mail.example.net.   A   203.0.113.10
mail.mail.example.net. A   203.0.113.10
PTR: 203.0.113.10 -> mx1.mail.example.net
```

## Hosted domain

For `example.com`:

```dns
example.com. MX 10 mx1.mail.example.net.
example.com. TXT "v=spf1 ip4:203.0.113.10 -all"
_dmarc.example.com. TXT "v=DMARC1; p=none; rua=mailto:dmarc@example.com"
```

Do not publish the example values literally.

Use a separate DKIM key/selector per hosted domain. Publish only the public key. Start DMARC in monitoring mode, then tighten policy after all legitimate sources align.

## Alignment

Outbound mail should satisfy SPF authorization for the edge IP and DKIM alignment with the visible From domain. DMARC should pass via at least one aligned mechanism.

## Onboarding sequence

1. confirm domain/DNS control;
2. add domain to Stalwart;
3. generate/confirm DKIM;
4. add domain to edge relay destinations;
5. publish MX/SPF/DKIM/DMARC;
6. verify external DNS;
7. test inbound;
8. test outbound to multiple providers;
9. inspect authentication headers;
10. tighten DMARC only after confidence is established.

## PTR

PTR belongs to the shared public edge identity, not each hosted domain. Adding another hosted domain should not require a PTR change.

## Reputation

Before production, check blocklists, confirm provider mail policy, avoid high-volume bursts, maintain consistent HELO/PTR, send only legitimate authenticated mail, and monitor bounces/abuse.

## Optional hardening

After baseline stability, evaluate MTA-STS, TLS-RPT, DANE/TLSA where justified, and client autodiscovery.

## References

- https://stalw.art/docs/install/dns/
- https://stalw.art/docs/server/dns/
- https://stalw.art/docs/domains/dns-records/
- https://stalw.art/docs/mta/authentication/dkim/sign/
