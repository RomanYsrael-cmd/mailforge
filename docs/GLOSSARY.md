# Glossary

**Edge** — Public VPS role that terminates Internet SMTP, queues mail, and provides the public egress IP.

**Origin** — Authoritative Stalwart host owning mailboxes, identities, domains, and message storage.

**Hosted domain** — A domain for which MailForge accepts local recipients.

**Infrastructure domain** — Optional neutral domain used for shared MailForge hostnames.

**MTA** — Mail Transfer Agent; Postfix is the public edge MTA.

**MUA** — Mail User Agent such as Thunderbird or a mobile mail client.

**Submission** — Authenticated client SMTP, normally 587 or 465.

**MX** — DNS record identifying inbound mail server(s).

**PTR/rDNS** — Reverse mapping from IP to hostname.

**SPF** — DNS authorization for sending hosts.

**DKIM** — Cryptographic mail signature with public key in DNS.

**DMARC** — Policy/reporting based on SPF/DKIM alignment.

**Open relay** — Dangerous MTA accepting arbitrary third-party forwarding.

**CGNAT** — Carrier-grade NAT preventing unsolicited inbound connections to the origin.

**WireGuard** — Encrypted tunnel between edge and origin.
