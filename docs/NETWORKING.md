# Networking

## Production assumption

The origin may be behind CGNAT. The production design must not require unsolicited Internet traffic to reach the origin. The origin will establish and maintain a WireGuard relationship to the edge in Phase 3.

## Phase 2 Compose networks

All lab networks are Docker bridge networks marked internal. No service publishes a host port.

| Network | Members | Purpose |
|---|---|---|
| untrusted | test SMTP client, Postfix edge, HAProxy | Simulates an untrusted client reaching inbound SMTP and client protocol proxy ports |
| private | Postfix edge, HAProxy, Stalwart origin, CLI provisioner, TLS probe | Simulates the restricted edge-to-origin path |
| sink-only | Postfix edge, local SMTP sink | Provides the only route for remote-recipient mail |

The edge has a fixed address on each network. Stalwart has one fixed private address. Postfix trusts only that Stalwart /32. The test client is not attached to the private or sink network. Stalwart is not attached to the sink network, so it must use Postfix for outbound mail.

The private Compose network tests the logical trust boundary and routing policy. It is not a WireGuard tunnel: it does not test encryption, peer keys, handshakes, CGNAT traversal, or host firewall rules. Phase 3 must validate those on real edge/origin hosts.

## Lab ports

| Port | Purpose | Terminates at |
|---|---|---|
| 25/tcp | inbound server-to-server SMTP | Postfix |
| 443/tcp | HTTPS/JMAP and Web UI | Stalwart via HAProxy TCP forwarding |
| 465/tcp | implicit TLS submission | Stalwart via HAProxy TCP forwarding |
| 587/tcp | STARTTLS submission | Stalwart via HAProxy TCP forwarding |
| 993/tcp | IMAPS | Stalwart via HAProxy TCP forwarding |
| 8080/tcp | Stalwart management API | Stalwart, bound only to its private lab address |

The SMTP sink listens on 2525 only on the sink-only network. It has no host binding.

## Production firewall principles

Edge: allow only required public SMTP/client/tunnel ports, deny other unsolicited traffic, and trust outbound relay only from the WireGuard origin address or an explicit authenticated route.

Origin: allow required services from the edge tunnel address, restrict management, and keep default-deny inbound where practical.

SMTP/25 terminates at Postfix for queueing. Client TLS terminates at Stalwart. Do not publish AAAA until IPv6 is intentionally configured, reachable, firewalled, and tested.

## Production acceptance tests

Phase 3 and later must verify external TCP/25, edge outbound TCP/25, fresh WireGuard handshake, origin-bound services, no open relay, production client TLS, and the public address observed by recipients.
