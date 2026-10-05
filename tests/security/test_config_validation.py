import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("mailforge_validator", ROOT / "scripts" / "validate_config.py")
validator = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(validator)


class EnvironmentValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.example = validator.parse_env_file(ROOT / ".env.example")

    def test_valid_example_environment_passes(self):
        self.assertEqual([], validator.validate_environment(self.example))

    def test_missing_required_field_fails(self):
        values = dict(self.example)
        values["MAILFORGE_CLIENT_HOSTNAME"] = ""
        errors = validator.validate_environment(values)
        self.assertTrue(any("MAILFORGE_CLIENT_HOSTNAME" in error for error in errors))

    def test_production_rejects_example_domain_and_hostname(self):
        values = dict(self.example)
        values["MAILFORGE_ENVIRONMENT"] = "production"
        values["MAILFORGE_EDGE_HOSTNAME"] = "mx.mail.example.net"
        errors = validator.validate_environment(values)
        self.assertTrue(any("example" in error for error in errors))

    def test_production_rejects_test_net_address(self):
        values = dict(self.example)
        values["MAILFORGE_ENVIRONMENT"] = "production"
        values["MAILFORGE_RELAY_DOMAINS"] = "mailforge.invalid"
        values["MAILFORGE_EDGE_HOSTNAME"] = "mx.mailforge.invalid"
        values["MAILFORGE_CLIENT_HOSTNAME"] = "mail.mailforge.invalid"
        errors = validator.validate_environment(values)
        self.assertTrue(any("TEST-NET" in error for error in errors))

    def test_duplicate_wireguard_addresses_fail(self):
        values = dict(self.example)
        values["MAILFORGE_WG_ORIGIN_ADDRESS"] = values["MAILFORGE_WG_EDGE_ADDRESS"]
        errors = validator.validate_environment(values)
        self.assertTrue(any("collide" in error for error in errors))

    def test_empty_or_wildcard_relay_domain_fails(self):
        for relay_domains in ("", "*.example.com"):
            with self.subTest(relay_domains=relay_domains):
                values = dict(self.example)
                values["MAILFORGE_RELAY_DOMAINS"] = relay_domains
                self.assertTrue(validator.validate_environment(values))

    def test_floating_image_tag_fails(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "compose.yaml").write_text("services:\n  mail:\n    image: example/mail:latest\n", encoding="utf-8")
            self.assertTrue(validator.validate_image_pins(root))

    def test_private_key_marker_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            fixture = root / "sample.txt"
            fixture.write_text("-----BEGIN " + "PRIVATE KEY-----\\nfixture\\n", encoding="utf-8")
            errors = validator.scan_private_material(root, [fixture])
            self.assertTrue(any("private key marker" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
