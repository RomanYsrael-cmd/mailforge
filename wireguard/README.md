# WireGuard scaffold

The example files document the intended edge/origin tunnel without containing real private keys. Never commit generated WireGuard keys.

Phase 2 uses an internal Compose network to exercise the restricted edge-to-origin service path. It does not start WireGuard, create host interfaces, test peer handshakes, or validate CGNAT traversal. Phase 3 must prove the actual WireGuard path and host firewall rules before any DNS cutover.
