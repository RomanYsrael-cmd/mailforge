import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("mailforge_validator", ROOT / "scripts" / "validate_config.py")
validator = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(validator)


class DomainExampleTests(unittest.TestCase):
    def test_two_domains_have_independent_identities_and_dkim(self):
        directory = ROOT / "examples" / "domains"
        self.assertEqual([], validator.validate_domain_examples(directory))
        domains = [json.loads(path.read_text(encoding="utf-8")) for path in sorted(directory.glob("*.json"))]
        self.assertGreaterEqual(len(domains), 2)
        self.assertEqual(len({item["domain"] for item in domains}), len(domains))
        self.assertEqual(len({item["dkim"]["selector"] for item in domains}), len(domains))
        self.assertTrue(all(item["dkim"]["authority"] == "Stalwart" for item in domains))
        self.assertTrue(all(item["dns"]["mx"] == domains[0]["dns"]["mx"] for item in domains))
        self.assertTrue(all("@" not in mailbox for item in domains for mailbox in item["mailboxes"]))


if __name__ == "__main__":
    unittest.main()
