#!/usr/bin/env python3
"""Manage the opt-in, isolated MailForge Phase 2 lab."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

from lab_common import ROOT, RUNTIME, STATE, prepare_state, safe_state_path, write_text

COMPOSE_FILE = ROOT / "compose.yaml"
CLI_ENV = RUNTIME / "cli.env"
PLAN_FILE = RUNTIME / "provision" / "plan.ndjson"


def docker_binary() -> str:
    requested = os.environ.get("MAILFORGE_DOCKER")
    binary = requested or shutil.which("docker")
    if not binary:
        raise RuntimeError(
            "Docker CLI was not found on PATH. Install Docker Compose or set MAILFORGE_DOCKER to docker.exe."
        )
    return binary


def _safe_state_path() -> Path:
    return safe_state_path()


def compose_args(*, tools: bool = False, bootstrap: bool = False, cli_env: bool = False) -> list[str]:
    args = [
        docker_binary(), "compose",
        "--project-directory", str(ROOT),
        "--env-file", str(RUNTIME / "compose.env"),
        "-f", str(COMPOSE_FILE),
    ]
    if cli_env and CLI_ENV.exists():
        args.extend(["--env-file", str(CLI_ENV)])
    if bootstrap:
        args.extend(["-f", str(RUNTIME / "bootstrap.compose.yaml")])
    args.extend(["--profile", "lab"])
    if tools:
        args.extend(["--profile", "lab-tools"])
    return args


def run(
    args: list[str],
    *,
    tools: bool = False,
    bootstrap: bool = False,
    cli_env: bool = False,
    capture: bool = False,
) -> subprocess.CompletedProcess[str]:
    _safe_state_path()
    command = compose_args(tools=tools, bootstrap=bootstrap, cli_env=cli_env) + args
    result = subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.STDOUT if capture else None,
        check=False,
    )
    if result.returncode:
        detail = (result.stdout or "").strip() if capture else ""
        raise RuntimeError(f"Command failed ({result.returncode}): {' '.join(command)}\n{detail}")
    return result


def wait_healthy(service: str, timeout: int = 120, *, bootstrap: bool = False) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        lookup = run(["ps", "-q", service], capture=True, bootstrap=bootstrap)
        container_ids = (lookup.stdout or "").strip().splitlines()
        if container_ids:
            health = subprocess.run(
                [
                    docker_binary(), "inspect", "--format",
                    "{{if .State.Health}}{{.State.Health.Status}}{{else}}no-healthcheck{{end}}",
                    container_ids[0],
                ],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                check=False,
            )
            status = health.stdout.strip()
            if status == "healthy":
                return
            if status == "unhealthy":
                raise RuntimeError(f"{service} became unhealthy:\n{logs()}")
        time.sleep(2)
    raise TimeoutError(f"{service} did not become healthy within {timeout} seconds.\n{logs()}")


def logs() -> str:
    result = run(["logs", "--no-color", "--tail", "120"], capture=True)
    return result.stdout or ""


def prepare(*, fresh: bool = False, openssl: str | None = None) -> dict[str, object]:
    _safe_state_path()
    if fresh and STATE.exists():
        if (RUNTIME / "compose.env").exists():
            down()
        shutil.rmtree(_safe_state_path())
    return prepare_state(openssl=openssl, fresh_credentials=fresh)


def provision(*, recovery: bool) -> None:
    secrets_path = RUNTIME / "secrets.json"
    secrets_data = json.loads(secrets_path.read_text(encoding="utf-8"))
    bootstrap = secrets_data["recovery"]
    admin = secrets_data["accounts"]["admin@example.com"]
    cli_user = bootstrap["username"] if recovery else admin["username"]
    cli_password = bootstrap["password"] if recovery else admin["password"]
    CLI_ENV.parent.mkdir(parents=True, exist_ok=True)
    write_text(
        CLI_ENV,
        f"STALWART_USER={json.dumps(cli_user)}\nSTALWART_PASSWORD={json.dumps(cli_password)}\n",
        0o600,
    )
    PLAN_FILE.parent.mkdir(parents=True, exist_ok=True)
    try:
        plan = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "stalwart_plan.py"), "--output", str(PLAN_FILE)],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )
        if plan.returncode:
            raise RuntimeError(f"Could not generate the Stalwart provisioning plan:\n{plan.stdout}")
        run(
            ["run", "--rm", "--no-deps", "-T", "stalwart-cli", "apply", "--file", "/work/plan.ndjson", "--json"],
            tools=True,
            cli_env=True,
        )
        if not recovery:
            run(
                ["run", "--rm", "--no-deps", "-T", "stalwart-cli", "create", "Action/ReloadSettings"],
                tools=True,
                cli_env=True,
            )
    finally:
        CLI_ENV.unlink(missing_ok=True)
        PLAN_FILE.unlink(missing_ok=True)


def up(*, fresh: bool = False, openssl: str | None = None) -> None:
    prepare(fresh=fresh, openssl=openssl)
    run(["up", "-d", "--build", "--remove-orphans"], bootstrap=True)
    wait_healthy("origin-stalwart", bootstrap=True)
    provision(recovery=True)
    run(["up", "-d", "--force-recreate", "origin-stalwart"])
    wait_healthy("origin-stalwart")
    provision(recovery=False)
    (RUNTIME / "bootstrap.compose.yaml").unlink(missing_ok=True)
    print("MailForge lab is ready. Runtime credentials and mail state are in ignored var/mailforge/.")


def down(*, remove_state: bool = False) -> None:
    _safe_state_path()
    if RUNTIME.exists() and (RUNTIME / "compose.env").exists():
        containers = run(["ps", "--all", "-q", "edge-postfix"], capture=True)
        if (containers.stdout or "").strip():
            run(["stop", "edge-postfix"])
            run(
                [
                    "run", "--rm", "--no-deps", "-T", "--user", "0:0",
                    "--entrypoint", "/usr/local/bin/mailforge-fix-queue-owner", "edge-postfix",
                ]
            )
        run(["down", "--remove-orphans"])
    if remove_state and STATE.exists():
        shutil.rmtree(_safe_state_path())
        print("Removed the generated lab state under var/mailforge/.")


def ci() -> None:
    prepare(fresh=True)
    try:
        run(["up", "-d", "--build", "--remove-orphans"], bootstrap=True)
        wait_healthy("origin-stalwart", bootstrap=True)
        provision(recovery=True)
        run(["up", "-d", "--force-recreate", "origin-stalwart"])
        wait_healthy("origin-stalwart")
        provision(recovery=False)
        (RUNTIME / "bootstrap.compose.yaml").unlink(missing_ok=True)
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "run_phase2_tests.py")],
            cwd=ROOT,
            text=True,
            check=False,
        )
        if result.returncode:
            raise RuntimeError(f"Phase 2 integration suite failed with exit code {result.returncode}.")
    except Exception:
        try:
            print("\n--- Phase 2 lab logs ---\n" + logs(), file=sys.stderr)
        except Exception:
            pass
        try:
            down(remove_state=True)
        except Exception as cleanup_error:
            print(
                f"Lab state was preserved because safe teardown failed: {cleanup_error}",
                file=sys.stderr,
            )
        raise
    else:
        down(remove_state=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="action", required=True)
    prepare_parser = subparsers.add_parser("prepare", help="generate ignored runtime config and random lab credentials")
    prepare_parser.add_argument("--fresh", action="store_true", help="replace only var/mailforge with fresh disposable state")
    prepare_parser.add_argument("--openssl", help="OpenSSL executable to generate disposable DKIM keys")
    up_parser = subparsers.add_parser("up", help="build, provision, and start the local isolated lab")
    up_parser.add_argument("--fresh", action="store_true", help="replace only var/mailforge with fresh disposable state")
    up_parser.add_argument("--openssl", help="OpenSSL executable to generate disposable DKIM keys")
    subparsers.add_parser("down", help="stop the lab while preserving queue, mail, and credentials")
    subparsers.add_parser("reset", help="stop the lab and remove only generated var/mailforge state")
    subparsers.add_parser("ci", help="fresh start, provision, integration test, and remove lab state")
    args = parser.parse_args()
    try:
        if args.action == "prepare":
            prepare(fresh=args.fresh, openssl=args.openssl)
            print(f"Prepared ignored lab state under {STATE}.")
        elif args.action == "up":
            up(fresh=args.fresh, openssl=args.openssl)
        elif args.action == "down":
            down()
        elif args.action == "reset":
            down(remove_state=True)
        elif args.action == "ci":
            ci()
        return 0
    except Exception as exc:
        print(f"MailForge lab error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
