# Architecture

## Context

MailForge separates two concerns: the Internet requires a publicly reachable SMTP identity, while the operator may want authoritative mailbox state on a private origin behind CGNAT.

## Components

### Public edge VPS

Responsibilities:

- stable public IPv4 and PTR identity;
- receive Internet SMTP on TCP/25;
- enforce relay-domain policy;
- queue mail when origin is unavailable;
- deliver outbound mail to remote MX hosts;
- provide L4 forwarding for selected client protocols;
- expose only documented public ports.

Planned software: Postfix, an L4 proxy such as HAProxy, and WireGuard. The edge does **not** own user mailbox state.

### Private origin

Responsibilities:

- authoritative local-domain configuration;
- users, mailboxes, aliases, quotas, and message state;
- authenticated submission;
- IMAP/JMAP and management UI/API;
- DKIM key management/signing;
- durable mailbox storage and backup source of truth.

Planned software: Stalwart Mail Server.

### WireGuard transport

A point-to-point encrypted network joins edge and origin. The origin maintains outbound connectivity toward the public edge, so CGNAT is not a blocker.

### DNS

External DNS advertises MX, A/AAAA where applicable, PTR/rDNS through the VPS provider, SPF, DKIM, DMARC, and optional MTA-STS/TLS-RPT/autodiscovery.

## Recommended hostnames

Prefer infrastructure-neutral names such as:

- `mx1.mail.example.net` — SMTP edge identity and PTR target;
- `mail.mail.example.net` — client access hostname.

Hosted domains such as `example.com` and `example.org` point to that shared infrastructure. A hosted domain can temporarily provide infrastructure names if no neutral domain exists yet.

## Inbound flow

```text
remote MTA -> TCP/25 -> Postfix edge -> queued relay over WireGuard -> Stalwart -> mailbox
```

## Outbound flow

```text
client/app -> authenticated Stalwart submission -> policy + DKIM -> Postfix edge -> recipient MX
```

The edge public IP is the Internet-visible sender. SPF authorizes that IP; DKIM aligns to the hosted sender domain.

## Client flow

Selected client ports are forwarded in L4/TCP mode across WireGuard and terminate at Stalwart, keeping TLS and authentication centralized at the origin.

Target public endpoints: 443, 465, 587, and 993. POP3 is not in the default v1 profile.

## Failure behavior

- **Origin unavailable:** edge queues mail; mailbox/client access unavailable; no accepted message should be silently discarded.
- **Edge unavailable:** new Internet delivery fails temporarily, but mailbox state remains on origin.
- **Tunnel unavailable:** behavior resembles origin outage; monitoring must distinguish tunnel from application failure.

## Trust boundaries

1. Internet → edge: untrusted.
2. Edge → origin: infrastructure-authenticated over WireGuard, still least-privilege.
3. User → origin: authenticated identity trust.
4. Public Git repository → deployment: never a secret store.
5. Backup target: sensitive trusted storage.

## Data ownership

- mailbox state: origin;
- user/domain config: origin + backup;
- queue: edge, transient;
- DNS: authoritative DNS provider;
- private keys/secrets: deployment secret storage, never Git;
- source/templates: Git.

## References

- https://stalw.art/docs/install/platform/docker/
- https://stalw.art/docs/domains/
- https://stalw.art/docs/mta/outbound/routing/
- https://www.postfix.org/SMTPD_ACCESS_README.html
- https://www.wireguard.com/quickstart/
