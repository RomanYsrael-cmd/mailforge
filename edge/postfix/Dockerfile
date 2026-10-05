# Controlled Debian release series; package refreshes are reviewed in CI.
FROM debian:bookworm-slim

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update \
    && apt-get install --yes --no-install-recommends postfix \
    && rm -rf /var/lib/apt/lists/*

COPY main.cf /etc/postfix/main.cf

# Phase 1 only: the bundled main.cf rejects relaying and has no hosted domains.
CMD ["postfix", "start-fg"]
