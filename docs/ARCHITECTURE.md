# Architecture

## Context

MailForge separates public SMTP transport from authoritative mailbox state. The production origin may sit behind CGNAT, so the intended edge/origin transport is WireGuard with the origin maintaining outbound connectivity.

## Phase 2 lab components

### Postfix edge

Postfix accepts untrusted SMTP on port 25 for configured hosted domains, validates recipients using generated maps, queues messages while Stalwart is unavailable, and routes hosted mail to Stalwart. It trusts only the origin's fixed private /32 for outbound relay. All relayed remote mail goes to the lab SMTP sink.

### Stalwart origin

Stalwart owns domains, accounts, aliases, mailboxes, message state, authenticated submission, IMAP/JMAP, and DKIM. The Phase 2 lab pins v0.16.24 and stores its RocksDB data under ignored var/mailforge/stalwart/data.

### HAProxy

HAProxy forwards client protocol TCP streams on ports 443, 465, 587, and 993. It does not terminate TLS; Stalwart presents the certificate and handles client authentication.

### Lab SMTP sink

The dependency-free local sink stores simulated remote messages under ignored var/mailforge/sink. It is attached only to the sink-only internal network. It has no path to the Internet.

## Phase 2 network boundary

The lab has three Docker networks, all marked internal, and no host-published ports:

- untrusted: test client, Postfix, and HAProxy;
- private: Postfix, HAProxy, Stalwart, management CLI, and a TLS probe;
- sink-only: Postfix and the SMTP sink.

Stalwart uses a fixed private address. Postfix trusts only that address as its relay client. The test client is not attached to the private or sink network. Stalwart is not attached to the sink network.

This container topology verifies the routing and trust boundaries but is not a WireGuard implementation. It does not prove encryption, peer-key exchange, CGNAT traversal, or host firewall behavior. Phase 3 must prove those conditions on real edge/origin hosts.

## Inbound flow

    untrusted SMTP client -> Postfix port 25 -> fixture domain/recipient check
        -> fixed private Stalwart address -> correct mailbox

## Outbound flow

    authenticated user -> HAProxy TCP/587 -> Stalwart DKIM and queue
        -> trusted Postfix edge -> local SMTP sink

## Production target

In production, public SMTP/25 terminates at Postfix. Hosted mail crosses WireGuard to Stalwart. Client protocol TLS terminates at Stalwart through L4 forwarding. Postfix relays remote mail to the Internet only after production egress and relay policy are configured and reviewed.

## Failure behavior

- Origin unavailable: Postfix retains accepted hosted mail and retries after recovery.
- Edge unavailable: origin mailbox state remains authoritative; new external delivery may be deferred by senders.
- Tunnel unavailable in production: behavior resembles an origin outage; monitoring must distinguish tunnel from application failure.

## Data ownership

- mailbox state and domain/account config: Stalwart;
- Postfix queue: edge transport, transient;
- DNS: authoritative DNS provider;
- private keys/secrets: deployment secret storage, never Git;
- source/templates: Git;
- lab sink contents: disposable test evidence.

## References

- https://stalw.art/docs/configuration/
- https://stalw.art/docs/management/cli/apply/
- https://stalw.art/docs/mta/outbound/routing/
- https://www.postfix.org/SMTPD_ACCESS_README.html
- https://www.wireguard.com/quickstart/
