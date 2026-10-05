# Networking

## Assumption

The origin may be behind CGNAT. No design may require unsolicited Internet traffic to reach the origin's residential interface. The origin maintains a WireGuard relationship to the edge.

## Public edge ports

| Port | Purpose | Terminates at |
|---|---|---|
| 25/tcp | server-to-server SMTP | Postfix edge |
| 443/tcp | HTTPS/JMAP/Web UI as enabled | Stalwart via L4 proxy |
| 465/tcp | implicit TLS submission | Stalwart via L4 proxy |
| 587/tcp | SMTP submission | Stalwart via L4 proxy |
| 993/tcp | IMAPS | Stalwart via L4 proxy |
| configurable UDP | WireGuard | WireGuard |

SSH is operational infrastructure and should be restricted by administrator policy. POP3 is disabled by default.

## Origin exposure

Origin mail services bind to WireGuard/loopback/private interfaces as appropriate. They should not be exposed directly to the residential WAN.

## Tunnel addressing

Use a dedicated RFC1918 subnet, for example `10.77.0.1/30` edge and `10.77.0.2/30` origin. Actual addresses are deployment-specific.

## Firewall principles

Edge: allow SMTP/client/tunnel ports, deny other unsolicited traffic, and trust outbound relay only from the WireGuard origin or explicit authenticated routes.

Origin: allow required services from the edge tunnel address, restrict management, and keep default-deny inbound where practical.

## L4 proxying

Client protocols use TCP-mode forwarding so TLS terminates at Stalwart. SMTP/25 is intentionally different: Postfix terminates it to provide queueing.

## DNS and IPv6

MX resolves to the public edge, never the CGNAT origin. PTR should map the edge public IP to its SMTP hostname, and forward DNS should resolve back.

Do not publish AAAA until IPv6 is intentionally configured, reachable, firewall-protected, and tested.

## Network acceptance tests

Verify external TCP/25 reachability, edge outbound TCP/25, WireGuard handshake freshness, intended origin-only interfaces, no open relay, client TLS, and the public IP observed by remote recipients.
