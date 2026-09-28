import json, tempfile, unittest
from pathlib import Path
from secret_scanner import main

class SecretScannerTests(unittest.TestCase):
    def run_scan(self, root: Path, output: Path | None = None) -> int:
        import sys
        old = sys.argv
        sys.argv = ["secret_scanner.py","--root",str(root)] + ([ "--output", str(output) ] if output else [])
        try:
            return main()
        finally:
            sys.argv = old

    def test_clean_repository_passes_and_never_scans_efi(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); (root/"src").mkdir(); (root/"EFI").mkdir()
            (root/"src"/"clean.py").write_text("TOKEN = 'example-token'\n", encoding="utf-8")
            (root/"EFI"/"secret.py").write_text("API_KEY = '12345678901234567890'\n", encoding="utf-8")
            self.assertEqual(self.run_scan(root), 0)

    def test_real_secret_like_assignment_fails_without_emitting_value(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            secret = "".join(["1234567890", "1234567890"]) + "-real-secret"
            (root/"app.py").write_text("API_KEY = '" + secret + "'\n", encoding="utf-8")
            output = root/"evidence.json"
            self.assertEqual(self.run_scan(root, output), 1)
            raw = output.read_text(encoding="utf-8")
            report = json.loads(raw)
            self.assertEqual(report["status"], "FAIL")
            self.assertEqual(report["finding_count"], 1)
            self.assertNotIn(secret, raw)
            self.assertEqual(report["findings"][0]["detector"], "generic_secret_assignment")
            self.assertTrue(report["findings"][0]["value_fingerprint"])

    def test_private_key_is_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            marker = "-----BEGIN " + "PRIVATE KEY-----"
            (root/"key.pem").write_text(marker + "\nabc\n", encoding="utf-8")
            self.assertEqual(self.run_scan(root), 1)

if __name__ == "__main__":
    unittest.main()
