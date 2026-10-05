#!/usr/bin/env python3
"""Small standard-library SMTP sink for isolated MailForge lab traffic."""

from __future__ import annotations

import json
import os
import re
import socketserver
import sys
import uuid
from pathlib import Path

DATA = Path(os.environ.get("MAILFORGE_SINK_DATA", "/var/lib/mailforge/sink"))
ADDRESS_RE = re.compile(r"<([^>]*)>")


class SmtpHandler(socketserver.StreamRequestHandler):
    def reply(self, code: int, message: str) -> None:
        self.wfile.write(f"{code} {message}\r\n".encode("ascii", "replace"))
        self.wfile.flush()

    def multiline(self) -> None:
        for line in (
            "250-lab-sink",
            "250-PIPELINING",
            "250-SIZE 52428800",
            "250-8BITMIME",
            "250 HELP",
        ):
            self.wfile.write((line + "\r\n").encode("ascii"))
        self.wfile.flush()

    def handle(self) -> None:
        DATA.mkdir(parents=True, exist_ok=True)
        sender: str | None = None
        recipients: list[str] = []
        self.reply(220, "lab-sink ESMTP ready")
        while True:
            raw = self.rfile.readline(65536)
            if not raw:
                return
            line = raw.decode("utf-8", "replace").rstrip("\r\n")
            command, _, argument = line.partition(" ")
            command = command.upper()
            if command in {"EHLO", "LHLO"}:
                self.multiline()
            elif command == "HELO":
                self.reply(250, "lab-sink")
            elif command == "MAIL":
                match = ADDRESS_RE.search(argument)
                if not match:
                    self.reply(501, "invalid sender")
                else:
                    sender = match.group(1)
                    recipients = []
                    self.reply(250, "sender accepted")
            elif command == "RCPT":
                match = ADDRESS_RE.search(argument)
                if sender is None or not match:
                    self.reply(503, "send MAIL FROM first")
                else:
                    recipients.append(match.group(1))
                    self.reply(250, "recipient accepted")
            elif command == "DATA":
                if sender is None or not recipients:
                    self.reply(503, "send MAIL and RCPT first")
                    continue
                self.reply(354, "end data with <CR><LF>.<CR><LF>")
                message_lines: list[bytes] = []
                while True:
                    data_line = self.rfile.readline(1024 * 1024)
                    if not data_line:
                        return
                    if data_line in {b".\r\n", b".\n"}:
                        break
                    if data_line.startswith(b".."):
                        data_line = data_line[1:]
                    message_lines.append(data_line)
                message = b"".join(message_lines)
                message_id = uuid.uuid4().hex
                (DATA / f"{message_id}.eml").write_bytes(message)
                metadata = {"sender": sender, "recipients": recipients}
                (DATA / f"{message_id}.json").write_text(
                    json.dumps(metadata, sort_keys=True) + "\n", encoding="utf-8"
                )
                print(f"accepted message {message_id} from {sender} to {len(recipients)} recipient(s)", flush=True)
                self.reply(250, f"queued as {message_id}")
                sender = None
                recipients = []
            elif command == "RSET":
                sender = None
                recipients = []
                self.reply(250, "reset")
            elif command == "NOOP":
                self.reply(250, "ok")
            elif command == "VRFY":
                self.reply(252, "cannot verify user")
            elif command == "QUIT":
                self.reply(221, "closing connection")
                return
            elif command == "STARTTLS":
                self.reply(454, "TLS not available on isolated sink")
            else:
                self.reply(500, "command unrecognized")


class Server(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True


def main() -> int:
    DATA.mkdir(parents=True, exist_ok=True)
    with Server(("0.0.0.0", 2525), SmtpHandler) as server:
        print(f"local SMTP sink listening on 0.0.0.0:2525; storage={DATA}", flush=True)
        try:
            server.serve_forever(poll_interval=0.5)
        except KeyboardInterrupt:
            pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
