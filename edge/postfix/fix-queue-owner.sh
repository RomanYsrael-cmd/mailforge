#!/bin/sh
set -eu

: "${MAILFORGE_LAB_UID:?MAILFORGE_LAB_UID is required}"
: "${MAILFORGE_LAB_GID:?MAILFORGE_LAB_GID is required}"
chown -R "${MAILFORGE_LAB_UID}:${MAILFORGE_LAB_GID}" /var/spool/postfix
