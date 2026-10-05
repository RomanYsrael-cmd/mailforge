# Controlled Debian release series; package refreshes are reviewed in CI.
FROM debian:bookworm-slim

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update \
    && apt-get install --yes --no-install-recommends postfix netcat-openbsd rsyslog \
    && printf 'mail.* -/dev/stdout\n' > /etc/rsyslog.d/20-mailforge.conf \
    && rm -rf /var/lib/apt/lists/*

COPY main.cf /etc/postfix/main.cf
COPY docker-entrypoint.sh /usr/local/bin/mailforge-postfix-entrypoint
RUN chmod 0755 /usr/local/bin/mailforge-postfix-entrypoint

# Without generated Phase 2 maps the image keeps the closed Phase 1 main.cf.
ENTRYPOINT ["/usr/local/bin/mailforge-postfix-entrypoint"]
CMD ["postfix", "start-fg"]
