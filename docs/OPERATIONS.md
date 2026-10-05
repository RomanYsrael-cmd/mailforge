# Operations

The steps below describe the future production operating model. Phase 1 has no deployed services, production credentials, or live mail path.

## Operating model

The edge is replaceable public transport infrastructure. The origin is authoritative mailbox infrastructure.

## Provisioning order

1. provision suitable edge VPS;
2. verify public IPv4, PTR control, and TCP/25 policy;
3. harden edge/firewall;
4. provision origin storage and backup;
5. establish WireGuard;
6. deploy Stalwart;
7. deploy Postfix and L4 proxy;
8. perform closed relay tests;
9. onboard first domain;
10. run external acceptance tests;
11. onboard a second domain to prove reuse.

## Version management

Do not use uncontrolled floating production tags. Read upstream release notes, stage changes, keep a rollback path, and verify mail flow after upgrades.

## Minimum observability

Edge: Postfix health, queue depth, oldest queue age, disk/inodes, outbound failures, relay rejections, WireGuard handshake, CPU/RAM.

Origin: Stalwart health, mailbox storage usage, disk health/free space, backup freshness, auth failures, cert expiry, tunnel reachability.

## Incident guidance

- **Origin unavailable:** inspect storage/service/tunnel; do not purge queue to hide retries.
- **Edge unavailable:** mailbox state remains safe; rebuild edge and re-establish routing/PTR.
- **Credential compromise:** disable/rotate, inspect logs and forwarding/alias changes.
- **DKIM compromise:** rotate selector/key using safe DNS TTL overlap.
- **Public IP change:** treat as a controlled DNS/SPF/PTR and reputation migration.

No DNS cutover or production mailbox migration should be performed from an unreviewed branch.
