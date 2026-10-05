# ADR-0003: Use WireGuard to cross the CGNAT boundary

- Status: Accepted
- Date: 2026-10-05

## Context

The origin may be behind carrier-grade NAT and cannot accept arbitrary inbound Internet connections.

## Decision

Use WireGuard between the public edge and private origin; the origin maintains connectivity toward the edge.

## Consequences

No public IPv4/port forward is required at origin. Services can bind to the tunnel. Private keys never enter Git. Tunnel health becomes an operational signal.

Reference: https://www.wireguard.com/quickstart/
