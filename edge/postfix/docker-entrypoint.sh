#!/bin/sh
set -eu

source_config=/run/mailforge/postfix/main.cf
source_maps=/run/mailforge/postfix/maps

if [ -r "$source_config" ] && [ -d "$source_maps" ]; then
    cp "$source_config" /etc/postfix/main.cf
    install -d -o root -g root -m 0755 /etc/postfix/generated
    for map in relay_domains relay_recipients transport; do
        cp "$source_maps/$map" "/etc/postfix/generated/$map"
        postmap "hash:/etc/postfix/generated/$map"
    done
    postfix set-permissions
    postfix check
    if [ -x /usr/sbin/rsyslogd ]; then
        rsyslogd
    fi
    postfix start-fg &
    postfix_pid=$!
    return_queue_ownership() {
        chown -R "${MAILFORGE_LAB_UID:-0}:${MAILFORGE_LAB_GID:-0}" /var/spool/postfix 2>/dev/null || true
    }
    shutdown_postfix() {
        trap - TERM INT
        kill -TERM "$postfix_pid" 2>/dev/null || true
        wait "$postfix_pid" 2>/dev/null || true
        return_queue_ownership
        exit 0
    }
    trap shutdown_postfix TERM INT
    if wait "$postfix_pid"; then
        status=0
    else
        status=$?
    fi
    return_queue_ownership
    exit "$status"
fi

# Keep the Phase 1 image default closed when runtime-generated lab maps are absent.
exec "$@"
