#!/bin/sh
set -eu

source_config=/run/mailforge/postfix/main.cf
source_maps=/run/mailforge/postfix/maps

if [ -r "$source_config" ] && [ -d "$source_maps" ]; then
    echo "Installing generated MailForge Postfix configuration."
    cp "$source_config" /etc/postfix/main.cf
    install -d -o root -g root -m 0755 /etc/postfix/generated
    for map in relay_domains relay_recipients transport; do
        cp "$source_maps/$map" "/etc/postfix/generated/$map"
        postmap "hash:/etc/postfix/generated/$map"
    done
    if ! postfix set-permissions; then
        echo "Postfix set-permissions failed." >&2
        exit 1
    fi
    if ! postfix check; then
        echo "Postfix configuration check failed." >&2
        exit 1
    fi
    if [ -x /usr/sbin/rsyslogd ]; then
        rsyslogd
    fi
    echo "Postfix configuration is valid; starting the SMTP service."
    exec postfix start-fg
fi

# Keep the Phase 1 image default closed when runtime-generated lab maps are absent.
exec "$@"
