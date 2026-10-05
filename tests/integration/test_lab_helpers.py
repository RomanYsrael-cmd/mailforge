import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import lab_common
import stalwart_plan


class LabHelperTests(unittest.TestCase):
    def test_runtime_state_must_resolve_to_the_checkout_data_directory(self):
        with patch.object(lab_common, "STATE", ROOT / "var" / "test-temp"):
            with self.assertRaisesRegex(RuntimeError, "unexpected runtime path"):
                lab_common.safe_state_path()

    def test_lab_networks_are_non_overlapping_and_static_addresses_fit(self):
        values = lab_common.lab_network_values({})
        self.assertEqual("172.29.240.10", values["MAILFORGE_LAB_ORIGIN_IP"])

    def test_overlapping_networks_are_rejected(self):
        values = dict(lab_common.DEFAULTS)
        values["MAILFORGE_LAB_SINK_SUBNET"] = values["MAILFORGE_LAB_PRIVATE_SUBNET"]
        with self.assertRaisesRegex(ValueError, "overlaps"):
            lab_common.lab_network_values(values)

    def test_wireguard_examples_keep_origin_initiated_cgnat_configuration(self):
        edge = (ROOT / "wireguard" / "edge.conf.example").read_text(encoding="utf-8")
        origin = (ROOT / "wireguard" / "origin.conf.example").read_text(encoding="utf-8")
        self.assertIn("AllowedIPs = 10.77.0.2/32", edge)
        self.assertIn("AllowedIPs = 10.77.0.1/32", origin)
        self.assertIn("PersistentKeepalive = 25", origin)
        self.assertNotIn("Endpoint =", edge)
        self.assertIn("Endpoint = mx1.mail.example.net:51820", origin)
        self.assertIn("<INJECT_EDGE_PRIVATE_KEY_AT_DEPLOYMENT>", edge)
        self.assertIn("<INJECT_ORIGIN_PRIVATE_KEY_AT_DEPLOYMENT>", origin)

    def test_postfix_maps_come_from_the_shared_domain_fixtures(self):
        root = ROOT / "var" / "test-temp"
        root.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=root) as temporary:
            state = Path(temporary) / "state"
            runtime = state / "runtime"
            generated = runtime / "generated"
            account_secrets = {
                f"{local}@{record['domain']}": {"username": f"{local}@{record['domain']}", "password": "unit-test-only"}
                for record in lab_common.load_domains()
                for local in record["mailboxes"]
            }
            with (
                patch.object(lab_common, "STATE", state),
                patch.object(lab_common, "RUNTIME", runtime),
                patch.object(lab_common, "GENERATED", generated),
            ):
                lab_common.write_runtime(
                    {"accounts": account_secrets, "recovery": {"username": "test", "password": "test-only"}},
                    lab_common.lab_network_values({}),
                )
                postfix = generated / "postfix"
                self.assertIn("example.com OK", (postfix / "relay_domains").read_text(encoding="utf-8"))
                self.assertIn("example.org OK", (postfix / "relay_domains").read_text(encoding="utf-8"))
                recipients = (postfix / "relay_recipients").read_text(encoding="utf-8")
                self.assertIn("abuse@example.com OK", recipients)
                self.assertIn("abuse@example.org OK", recipients)
                self.assertIn("relayhost = [172.30.240.10]:2525", (postfix / "main.cf").read_text(encoding="utf-8"))
                self.assertIn("example.org smtp:[172.29.240.10]:25", (postfix / "transport").read_text(encoding="utf-8"))

    def test_stalwart_plan_keeps_domains_aliases_and_dkim_separate(self):
        root = ROOT / "var" / "test-temp"
        root.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=root) as temporary:
            runtime = Path(temporary) / "runtime"
            generated = runtime / "generated"
            generated_dkim = generated / "dkim"
            generated_dkim.mkdir(parents=True)
            domains = lab_common.load_domains()
            accounts = {
                f"{local}@{record['domain']}": {"username": f"{local}@{record['domain']}", "password": "unit-test-only"}
                for record in domains
                for local in record["mailboxes"]
            }
            (runtime / "secrets.json").write_text(json.dumps({"accounts": accounts}), encoding="utf-8")
            for record in domains:
                selector = record["dkim"]["selector"]
                (generated_dkim / f"{selector}.private.pem").write_text("FAKE-KEY-FOR-UNIT-TEST", encoding="utf-8")
            with patch.object(stalwart_plan, "RUNTIME", runtime), patch.object(stalwart_plan, "GENERATED", generated):
                plan = stalwart_plan.build_plan()
            domain_ops = [item for item in plan if item["object"] == "Domain"]
            self.assertEqual(
                {"example.com", "example.org"},
                {value["name"] for operation in domain_ops for value in operation["value"].values()},
            )
            account_op = next(item for item in plan if item["object"] == "Account")
            aliases = [alias for account in account_op["value"].values() for alias in account["aliases"].values()]
            self.assertEqual({("abuse", "#domain-0"), ("abuse", "#domain-1")}, {(item["name"], item["domainId"]) for item in aliases})
            dkim_op = next(item for item in plan if item["object"] == "DkimSignature")
            self.assertEqual({"mf-example-com", "mf-example-org"}, {item["selector"] for item in dkim_op["value"].values()})
            listener_op = next(item for item in plan if item["object"] == "NetworkListener")
            management = listener_op["value"]["listener-management"]
            self.assertIn("127.0.0.1:8080", management["bind"])
            self.assertIn("172.29.240.10:8080", management["bind"])
            pyzor = next(item for item in plan if item["object"] == "SpamPyzor")
            self.assertFalse(pyzor["value"]["enable"])
            strategy = next(item for item in plan if item["object"] == "MtaOutboundStrategy")
            self.assertEqual("'postfix-edge'", strategy["value"]["route"]["else"])


if __name__ == "__main__":
    unittest.main()
