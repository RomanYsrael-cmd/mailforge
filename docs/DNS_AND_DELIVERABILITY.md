# DNS and Deliverability

MailForge can provide protocol correctness; no self-hosted platform can guarantee inbox placement or IP reputation.

Phase 2 uses reserved example domains only. It does not query public DNS, publish records, or send mail to external providers. These records are documentation examples only and must not be applied literally.

## Infrastructure records

Example only:

    mx1.mail.example.net.   A   203.0.113.10
    mail.mail.example.net.  A   203.0.113.10
    PTR: 203.0.113.10 -> mx1.mail.example.net

## Hosted domain

For example.com:

    example.com. MX 10 mx1.mail.example.net.
    example.com. TXT "v=spf1 ip4:203.0.113.10 -all"
    _dmarc.example.com. TXT "v=DMARC1; p=none; rua=mailto:dmarc@example.com"

Use a separate DKIM key/selector per hosted domain. Publish only the public key. Start DMARC in monitoring mode, then tighten policy after all legitimate sources align.

## Alignment

Production outbound mail should satisfy SPF authorization for the edge IP and DKIM alignment with the visible From domain. DMARC should pass through at least one aligned mechanism.

## Production onboarding sequence

1. Confirm domain/DNS control.
2. Add the domain to Stalwart.
3. Generate/confirm DKIM.
4. Add the domain to edge relay and recipient destinations.
5. Publish MX/SPF/DKIM/DMARC.
6. Verify external DNS.
7. Test inbound and outbound to controlled providers.
8. Inspect authentication headers.
9. Tighten DMARC only after confidence is established.

## PTR and reputation

PTR belongs to the shared public edge identity, not each hosted domain. Before production, check provider TCP/25 policy and blocklists, confirm HELO/PTR consistency, avoid high-volume bursts, send only legitimate authenticated mail, and monitor bounces/abuse.

## Optional hardening

After baseline stability, evaluate MTA-STS, TLS-RPT, DANE/TLSA where justified, and client autodiscovery.

## References

- https://stalw.art/docs/install/dns/
- https://stalw.art/docs/server/dns/
- https://stalw.art/docs/domains/dns-records/
- https://stalw.art/docs/mta/authentication/dkim/sign/
