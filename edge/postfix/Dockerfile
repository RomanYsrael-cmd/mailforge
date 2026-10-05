# Controlled Debian release series; package refreshes are reviewed in CI.
FROM debian:bookworm-slim

ENV DEBIAN_FRONTEND=noninteractive
# Debian slim omits documentation files, but Postfix still lists them in its permission manifest.
RUN apt-get update \
    && apt-get install --yes --no-install-recommends postfix netcat-openbsd rsyslog \
    && sed -i \
        -e '/^[[:space:]]*\$manpage_directory\//d' \
        -e '/^[[:space:]]*\$readme_directory\//d' \
        -e '/^[[:space:]]*\$html_directory\//d' \
        /etc/postfix/postfix-files \
    && printf 'mail.* -/dev/stdout\n' > /etc/rsyslog.d/20-mailforge.conf \
    && rm -rf /var/lib/apt/lists/*

COPY main.cf /etc/postfix/main.cf
COPY docker-entrypoint.sh /usr/local/bin/mailforge-postfix-entrypoint
COPY fix-queue-owner.sh /usr/local/bin/mailforge-fix-queue-owner
RUN chmod 0755 /usr/local/bin/mailforge-postfix-entrypoint /usr/local/bin/mailforge-fix-queue-owner

# Without generated Phase 2 maps the image keeps the closed Phase 1 main.cf.
ENTRYPOINT ["/usr/local/bin/mailforge-postfix-entrypoint"]
CMD ["postfix", "start-fg"]
