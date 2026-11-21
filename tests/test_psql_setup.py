"""CLI contracts for preserving configuration and withholding credential output.

The psql stub supplies transport responses, not SQL semantics. Live replica
validation is exercised separately through bootstrap doctor on the fleet.
"""

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
REAL_PSQL = shutil.which("psql")
SECRET = "fixture-only:credential\\with-specials"
BUNDLE = {
    "service": {"host": "replica.invalid", "port": "5432", "dbname": "app", "user": "reader", "sslmode": "require"},
    "password": SECRET,
}


class PostgreSQLSetup(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name)
        self.bin = self.home / "bin"
        self.bin.mkdir()
        self.env = dict(os.environ, HOME=str(self.home), PATH=str(self.bin) + os.pathsep + os.environ["PATH"])
        self.env.pop("FLEET_PSQL_SOURCE", None)
        self.stub("ssh", "import sys; print(" + repr(json.dumps(BUNDLE)) + ")")
        self.stub("psql", 'print(\'{"replica":true,"read_only":true,"tls":true,"select_ok":true}\')')

    def stub(self, name, code):
        script = self.bin / name
        script.write_text("#!" + sys.executable + "\n" + code + "\n")
        script.chmod(0o700)

    def run_cli(self, action, ok=True):
        result = subprocess.run([sys.executable, str(ROOT / "install-psql.py"), action], env=self.env, capture_output=True, text=True)
        self.assertEqual(result.returncode == 0, ok, result.stdout + result.stderr)
        self.assertNotIn(SECRET, result.stdout + result.stderr)
        return result

    def test_import_preserves_other_services_and_passwords_and_reapply_needs_no_source(self):
        other_service = "# Keep this comment\n[local_dev]\nhost=localhost\nport=5544\n"
        other_pass = "# Keep credentials for another service\n*:5544:*:local:another-password\n"
        (self.home / ".pg_service.conf").write_text(other_service)
        (self.home / ".pgpass").write_text(other_pass)
        self.run_cli("apply")
        service = (self.home / ".pg_service.conf").read_bytes()
        password = (self.home / ".pgpass").read_bytes()
        self.assertTrue(service.startswith(other_service.encode()))
        self.assertTrue(password.endswith(other_pass.encode()))
        self.assertTrue(password.startswith(b"replica.invalid:5432:app:reader:fixture-only\\:credential\\\\with-specials\n"))
        for name in (".pg_service.conf", ".pgpass"):
            self.assertEqual((self.home / name).stat().st_mode & 0o777, 0o600)
        self.stub("ssh", "raise SystemExit('SSH must not run for an existing service')")
        self.run_cli("apply")
        self.assertEqual((self.home / ".pg_service.conf").read_bytes(), service)
        self.assertEqual((self.home / ".pgpass").read_bytes(), password)
        self.run_cli("doctor")

    def test_writable_endpoint_is_rejected_before_publishing_files(self):
        self.stub("psql", 'print(\'{"replica":false,"read_only":false,"tls":true,"select_ok":true}\')')
        self.run_cli("apply", ok=False)
        self.assertFalse((self.home / ".pg_service.conf").exists())
        self.assertFalse((self.home / ".pgpass").exists())
        self.assertEqual(sorted(p.name for p in self.home.iterdir()), ["bin"])

    @unittest.skipUnless(REAL_PSQL, "requires the real PostgreSQL client")
    def test_generated_service_is_accepted_by_real_libpq_parser(self):
        self.run_cli("apply")
        env = {key: value for key, value in self.env.items() if not key.startswith("PG")}
        env.update(PGSERVICEFILE=str(self.home / ".pg_service.conf"), PGPASSFILE=str(self.home / ".pgpass"), LC_ALL="C")
        # A closed loopback port exercises libpq parsing without a database or DNS.
        result = subprocess.run(
            [REAL_PSQL, "-X", "-w", "service=cursor_prod host=127.0.0.1 port=1 connect_timeout=1", "-c", "SELECT 1"],
            env=env, capture_output=True, text=True, timeout=5,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("connection", result.stderr.lower())
        self.assertNotIn("syntax error", result.stderr.lower())

    def test_failed_client_diagnostics_never_print_credentials(self):
        self.stub("psql", "import sys; print(" + repr(SECRET) + ", file=sys.stderr); raise SystemExit(2)")
        self.run_cli("apply", ok=False)
        self.assertFalse((self.home / ".pgpass").exists())

    def test_missing_source_is_noninteractive_and_leaves_existing_files_intact(self):
        self.stub("ssh", "import sys; print(" + repr(SECRET) + ", file=sys.stderr); raise SystemExit(255)")
        original = "[local_dev]\nhost=localhost\n"
        (self.home / ".pg_service.conf").write_text(original)
        self.run_cli("apply", ok=False)
        self.assertEqual((self.home / ".pg_service.conf").read_text(), original)
        self.assertFalse((self.home / ".pgpass").exists())

    def test_plan_makes_no_network_calls_or_config_changes(self):
        self.stub("ssh", "raise SystemExit(99)")
        self.stub("psql", "raise SystemExit(99)")
        self.run_cli("plan")
        self.assertEqual(sorted(p.name for p in self.home.iterdir()), ["bin"])

    def test_symlinked_credentials_are_not_followed_or_replaced(self):
        target = self.home / "another-secret-file"
        target.write_text("do not change")
        (self.home / ".pgpass").symlink_to(target)
        self.run_cli("apply", ok=False)
        self.assertEqual(target.read_text(), "do not change")
        self.assertTrue((self.home / ".pgpass").is_symlink())


if __name__ == "__main__":
    unittest.main()
