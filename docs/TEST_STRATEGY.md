# Test Strategy

Testing must prove the mail path and relay boundaries, not merely that containers start.

## Phase 1 checks retained

CI continues to validate configuration values, example domains, image references, documentation links, private-key/token scans, Python tests, shell syntax, Compose rendering, HAProxy configuration, and the closed Postfix image default.

## Phase 2 container-backed checks

Run python scripts/lab.py ci for a fresh, disposable integration run. It builds the lab containers, starts Stalwart in recovery mode, provisions through the official CLI, restarts in normal mode, runs protocol tests, and tears the containers and generated state down in a finally block.

The integration suite uses SMTP/IMAP clients inside Compose and verifies:

- inbound delivery to example.com and example.org mailboxes and each domain's abuse alias;
- rejection of unknown local parts, unknown domains, and untrusted remote relay recipients during SMTP;
- exact-origin /32 Postfix trust, explicit fixture-derived relay domains/recipients/transports, and sink-only outbound route;
- authenticated STARTTLS submission for both domains and delivery into the local SMTP sink;
- DKIM-Signature domain and selector evidence for each domain;
- an accepted Postfix queue item while Stalwart is stopped, then automatic delivery and queue drain after Stalwart recovers;
- TLS certificate identity equality through HAProxy and directly at Stalwart on HTTPS 443, implicit TLS 465/993, and STARTTLS 587;
- no host-published service ports and all lab networks marked internal.

These are actual container protocol flows. The suite does not mock Stalwart, Postfix, HAProxy, SMTP, or IMAP. It does not send mail to the Internet, query public DNS, use a VPS, or require GitHub secrets.

## Queue failure test

The test stops the origin, sends a valid hosted message through Postfix, and confirms the unique sender remains in Postfix's on-disk queue. It restarts Stalwart and waits for Postfix's scheduled retry; it does not force a manual queue flush. The lab retry window is shortened to keep CI bounded.

## Phase 3 and production gates

The Compose private network does not implement WireGuard. Phase 3 must test actual key exchange, routes, service binding, firewall behavior, tunnel recovery, and queue behavior over the tunnel. Production acceptance later adds external SMTP reachability, certificate/name validation, DNS authentication, monitoring, and backup restore.
