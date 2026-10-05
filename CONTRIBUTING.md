# Contributing

MailForge is architecture-first. Before implementation work, read the project charter, architecture, security model, implementation plan, and relevant accepted ADRs.

PRs should stay within one coherent milestone, update docs when behavior changes, include tests, avoid deployment secrets, use reserved/example domains and addresses in public examples, and preserve deny-by-default relay behavior. Architecture-changing PRs should add or supersede an ADR.

For Phase 1 checks, run:

```sh
python scripts/validate_config.py --env-file .env.example
python -m unittest discover -s tests -p 'test_*.py' -v
docker compose --profile local-scaffold config --quiet
```

CI also syntax-checks the shell wrapper and validates the HAProxy and closed Postfix scaffolds. It does not need production secrets, live DNS, a VPS, or external SMTP.

Never commit real environment files, private keys, tokens, passwords, mailbox exports/message data, runtime state, queue contents, or backup archives. Contributions are accepted under Apache License 2.0.
