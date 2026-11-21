#!/usr/bin/env python3
"""Provision cursor_prod from trusted SSH, then verify the existing read replica."""

import argparse
import configparser
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import stat
import subprocess
import sys
import tempfile


class SetupError(Exception):
    pass


def private_read(path):
    if not path.exists() and not path.is_symlink():
        return ""
    meta = path.lstat()
    if not stat.S_ISREG(meta.st_mode) or meta.st_uid != os.geteuid():
        raise SetupError(f"Expected an owned regular file: {path.name}")
    return path.read_text()


def services(text):
    parser = configparser.ConfigParser(interpolation=None, inline_comment_prefixes=None)
    parser.read_string(text)
    return parser


def password_fields(line):
    """Decode libpq's escaped colons and backslashes without shell parsing."""
    fields, field, escape = [], "", False
    for char in line:
        if escape:
            field += char
            escape = False
        elif char == "\\":
            escape = True
        elif char == ":":
            fields.append(field)
            field = ""
        else:
            field += char
    if escape:
        raise SetupError("Invalid password-file escape")
    return fields + [field]


def export_source(home):
    config = services(private_read(home / ".pg_service.conf"))
    if "cursor_prod" not in config:
        raise SetupError("SSH source has no cursor_prod service")
    settings = dict(config["cursor_prod"])
    settings.setdefault("port", "5432")
    # Machine-local paths, passwords, and session options are not portable.
    if set(settings) - {"host", "port", "dbname", "user", "sslmode"}:
        raise SetupError("Source service contains nonportable settings; review it first")
    if not all(settings.get(key) for key in ("host", "dbname", "user")):
        raise SetupError("Source service is incomplete")
    if settings.get("sslmode") not in ("require", "verify-ca", "verify-full"):
        raise SetupError("Source service must require TLS")
    identity = [settings["host"], settings.get("port", "5432"), settings["dbname"], settings["user"]]
    if any(value == "*" or any(c in value for c in "\r\n\x00") for value in identity):
        raise SetupError("Source connection must have a specific identity")
    for line in private_read(home / ".pgpass").splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        fields = password_fields(line)
        if len(fields) == 5 and all(a == "*" or a == b for a, b in zip(fields[:4], identity)):
            if not fields[4] or any(c in fields[4] for c in "\r\n\x00"):
                raise SetupError("Source password is empty or invalid")
            return {"service": settings, "password": fields[4]}
    raise SetupError("Source password file has no matching credential")


def psql_path():
    found = shutil.which("psql")
    if found:
        return found
    for prefix in ("/opt/homebrew", "/usr/local"):
        for suffix in ("opt/libpq/bin/psql", "bin/psql"):
            candidate = Path(prefix) / suffix
            if candidate.is_file() and os.access(candidate, os.X_OK):
                return str(candidate)
    raise SetupError("psql is missing; run ./bootstrap apply psql")


def verify(service_file, pass_file):
    # No write probes, SET commands, role changes, or forced read-only PGOPTIONS.
    query = """SELECT json_build_object(
      'replica', pg_is_in_recovery(),
      'read_only', current_setting('transaction_read_only') = 'on',
      'tls', (SELECT ssl FROM pg_stat_ssl WHERE pid = pg_backend_pid()),
      'select_ok', 1 = 1);"""
    env = {key: value for key, value in os.environ.items() if not key.startswith("PG")}
    env.update(PGSERVICEFILE=str(service_file), PGPASSFILE=str(pass_file), PGCONNECT_TIMEOUT="10")
    result = subprocess.run(
        [psql_path(), "-X", "-w", "service=cursor_prod", "-At", "-v", "ON_ERROR_STOP=1", "-c", query],
        env=env, capture_output=True, text=True, timeout=20,
    )
    if result.returncode:
        raise SetupError("cursor_prod connection failed; credentials and server details withheld")
    try:
        report = json.loads(result.stdout)
    except (ValueError, TypeError):
        raise SetupError("Unexpected psql verification response") from None
    if not all(report.get(key) is True for key in ("replica", "read_only", "tls", "select_ok")):
        raise SetupError("cursor_prod must reach a TLS read replica with transaction_read_only=on")
    return report


def import_source():
    source = os.environ.get("FLEET_PSQL_SOURCE", "ubuntu-hub")
    if not source or source.startswith("-") or not re.fullmatch(r"[A-Za-z0-9_.@:-]+", source):
        raise SetupError("FLEET_PSQL_SOURCE must be a trusted SSH alias or user@host")
    # Send this same, reviewed exporter to the source. Its output stays in memory.
    code = Path(__file__).read_text()
    command = shlex.join(["python3", "-c", code, "--export"])
    result = subprocess.run(
        ["ssh", "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=yes", "-o", "ConnectTimeout=8", source, command],
        capture_output=True, text=True, timeout=25,
    )
    if result.returncode:
        raise SetupError("Cannot import cursor_prod. Verify SSH to ubuntu-hub or set FLEET_PSQL_SOURCE to a configured trusted host")
    try:
        return json.loads(result.stdout)
    except ValueError:
        raise SetupError("SSH source returned an invalid configuration") from None


def atomic_write(path, text, expected):
    if private_read(path) != expected:
        raise SetupError("Local PostgreSQL files changed during setup; rerun")
    fd, temp = tempfile.mkstemp(prefix=".fleet-psql-", dir=path.parent)
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "w") as stream:
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
        if private_read(path) != expected:
            raise SetupError("Local PostgreSQL files changed during setup; rerun")
        os.replace(temp, path)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)


def apply(home):
    service_file, pass_file = home / ".pg_service.conf", home / ".pgpass"
    old_service, old_pass = private_read(service_file), private_read(pass_file)
    if "cursor_prod" in services(old_service):
        # Verify before fixing permissions, and never replace existing credentials.
        with tempfile.TemporaryDirectory(prefix=".fleet-psql-", dir=home) as temp:
            service, password = Path(temp) / "service", Path(temp) / "pass"
            atomic_write(service, old_service, "")
            atomic_write(password, old_pass, "")
            verify(service, password)
        for path in (service_file, pass_file):
            os.chmod(path, 0o600)
        print("cursor_prod: reused existing configuration; verified TLS read replica")
        return
    bundle = import_source()
    # Re-validate the received structure without printing any credential values.
    with tempfile.TemporaryDirectory(prefix=".fleet-psql-", dir=home) as temp:
        staged_home = Path(temp)
        config = configparser.ConfigParser(interpolation=None)
        config["cursor_prod"] = bundle["service"]
        import io
        buffer = io.StringIO()
        # libpq rejects spaces before '=' even though Python's INI parser accepts them.
        config.write(buffer, space_around_delimiters=False)
        section = buffer.getvalue()
        identity = [bundle["service"][key] for key in ("host", "port", "dbname", "user")]
        def escaped(value):
            return value.replace("\\", "\\\\").replace(":", "\\:")
        entry = ":".join(escaped(value) for value in identity + [bundle["password"]]) + "\n"
        atomic_write(staged_home / ".pg_service.conf", section, "")
        atomic_write(staged_home / ".pgpass", entry, "")
        export_source(staged_home)
        verify(staged_home / ".pg_service.conf", staged_home / ".pgpass")
        # The exact entry goes before existing wildcard entries. Preserve all others.
        merged_service = old_service + ("\n" if old_service and not old_service.endswith("\n") else "") + section
        atomic_write(pass_file, entry + old_pass, old_pass)
        atomic_write(service_file, merged_service, old_service)
    print("cursor_prod: imported over SSH; verified TLS read replica; files mode 0600")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("plan", "apply", "doctor"), nargs="?", default="plan")
    parser.add_argument("--export", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    home = Path.home()
    if args.export:
        print(json.dumps(export_source(home)))
        return
    if args.action == "plan":
        print("psql client: " + ("available" if shutil.which("psql") else "discover or install PostgreSQL client"))
        exists = "cursor_prod" in services(private_read(home / ".pg_service.conf"))
        print("cursor_prod: " + ("verify existing local service" if exists else "import from trusted SSH source, default ubuntu-hub"))
        print("Verify SELECT, TLS, pg_is_in_recovery(), and transaction_read_only; no database changes")
    elif args.action == "apply":
        apply(home)
    else:
        for name in (".pg_service.conf", ".pgpass"):
            path = home / name
            private_read(path)
            if not path.exists() or stat.S_IMODE(path.stat().st_mode) != 0o600:
                raise SetupError(f"{name} must exist with permissions 0600")
        verify(home / ".pg_service.conf", home / ".pgpass")
        print("cursor_prod: OK; SELECT succeeded, TLS on, replica=true, transaction_read_only=on; files 0600")


if __name__ == "__main__":
    try:
        main()
    except SetupError as error:
        print(f"fleet psql: {error}", file=sys.stderr)
        sys.exit(1)
    except Exception as error:
        # Parser and subprocess exceptions can contain credentials. Do not echo them.
        print(f"fleet psql: setup failed ({type(error).__name__}); details withheld", file=sys.stderr)
        sys.exit(1)
