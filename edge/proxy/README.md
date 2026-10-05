# L4 client proxy scaffold

HAProxy forwards TCP/443, 465, 587, and 993 to the Stalwart service. The configuration uses `mode tcp`; it does not inspect or terminate TLS. Client TLS and certificates remain owned by Stalwart, as required by ADR-0006.

The backend hostname is resolved at runtime through Docker's embedded DNS, and `init-addr none` allows offline syntax validation before the Compose network exists. The proxy is attached only to the internal Compose network and has no host-published ports in Phase 1. Routing through WireGuard on real edge/origin hosts is planned for Phase 2. SMTP/25 is intentionally handled by Postfix, not by this proxy.
