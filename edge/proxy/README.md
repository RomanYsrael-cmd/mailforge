# L4 client proxy

HAProxy forwards TCP ports 443, 465, 587, and 993 to Stalwart. It uses mode tcp and does not inspect or terminate TLS. Client TLS and certificates remain owned by Stalwart, as required by ADR-0006.

The backend hostname is resolved at runtime through Docker's embedded DNS. A container probe compares Stalwart's direct and proxied certificate fingerprints for HTTPS, implicit TLS, and STARTTLS, and authenticated mail/IMAP tests use the proxy path.

The proxy is attached to the untrusted and private internal lab networks and publishes no host ports. SMTP/25 is intentionally handled by Postfix, not by this proxy. In production, the private path will cross WireGuard; Phase 2's Compose network only emulates the routing boundary.
