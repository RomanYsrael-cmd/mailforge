# WireGuard scaffold

The public edge listens on the configured UDP port. The origin uses the edge endpoint and `PersistentKeepalive` to initiate and maintain the tunnel from behind CGNAT; no unsolicited public connection to the origin is required.

The `.conf.example` files use only TEST-NET/RFC1918 addresses and unmistakable key placeholders. They are templates, not loadable deployments. Generate keys on the target hosts during a later deployment phase and inject private keys through a secret store or protected files outside Git. Never commit a filled configuration. Client and mail services should bind to the tunnel where appropriate; do not expose the origin directly to the Internet.
