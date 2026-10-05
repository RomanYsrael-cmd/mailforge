# Postfix edge scaffold

Postfix will own public server-to-server SMTP on TCP/25 and its delivery queue. It will not store user mailboxes. The queue has a separate persistent mount in `compose.yaml`.

The Phase 1 `main.cf` is a deliberately closed baseline: there are no hosted relay domains, only loopback is trusted, and `smtpd_relay_restrictions` rejects unauthenticated destinations. It cannot relay arbitrary Internet mail. Do not publish its port or treat this as a working mail path.

Phase 2 will add an explicit hosted-domain transport map, origin next hop over WireGuard, and the narrowly trusted origin outbound path, with automated open-relay tests. Any relay-policy change must keep deny-by-default behavior.
