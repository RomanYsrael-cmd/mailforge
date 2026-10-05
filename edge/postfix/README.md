# Postfix edge

Postfix is the Phase 2 SMTP transport edge. It has no mailbox database. The generated lab configuration receives untrusted SMTP on port 25, accepts only fixture domains and recipients, routes hosted mail to the fixed Stalwart address, and trusts only that one origin address for remote relay.

The generated runtime maps are derived from the same examples/domains JSON fixtures used to provision Stalwart. main.cf remains the closed Phase 1 default; main.cf.template is used only when python scripts/lab.py up has prepared ignored runtime files.

All outbound Postfix mail is directed to lab-sink:2525. The sink is attached to a separate internal-only Docker network. The lab networks are internal, and no service publishes a host port, so the lab has no Internet SMTP route.

Relay policy uses permit_mynetworks, reject_unauth_destination with a single Stalwart /32 in mynetworks. Unknown hosted recipients are checked against a generated relay_recipient_maps database. The external client is not trusted and cannot relay to arbitrary domains.
