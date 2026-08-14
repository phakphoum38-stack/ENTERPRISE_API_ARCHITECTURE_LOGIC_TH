import tempfile
import unittest
from pathlib import Path

from research_os_v3 import DataLayout, UserContext, safe_local_user_id


class UserIsolationTests(unittest.TestCase):
    def test_user_and_profile_ids_reject_path_traversal(self) -> None:
        invalid = ("", ".", "..", "../bob", "alice/bob", r"alice\bob", "a" * 65)
        for value in invalid:
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    UserContext(value)

    def test_local_user_fallback_is_deterministic_and_safe(self) -> None:
        first = safe_local_user_id(r"DOMAIN\Alice Smith")
        second = safe_local_user_id(r"DOMAIN\Alice Smith")
        self.assertEqual(first, second)
        self.assertTrue(first.startswith("user-"))
        self.assertNotIn("/", first)
        self.assertNotIn("\\", first)

    def test_users_and_profiles_have_distinct_roots(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            layout = DataLayout(Path(temporary)).ensure()
            alice_default = layout.for_user(UserContext("alice")).ensure()
            alice_work = layout.for_user(UserContext("alice", "work")).ensure()
            bob_default = layout.for_user(UserContext("bob")).ensure()

            self.assertNotEqual(alice_default.root, alice_work.root)
            self.assertNotEqual(alice_default.root, bob_default.root)

            marker = alice_default.sessions / "private.marker"
            marker.write_text("alice-only", encoding="utf-8")

            self.assertFalse((alice_work.sessions / marker.name).exists())
            self.assertFalse((bob_default.sessions / marker.name).exists())
            self.assertEqual(marker.read_text(encoding="utf-8"), "alice-only")

    def test_legacy_root_and_user_scopes_can_coexist_without_aliasing(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            layout = DataLayout(Path(temporary)).ensure()
            legacy_marker = layout.sessions / "legacy.marker"
            legacy_marker.write_text("legacy", encoding="utf-8")

            alice = layout.for_user(UserContext("alice")).ensure()
            user_marker = alice.sessions / "user.marker"
            user_marker.write_text("alice", encoding="utf-8")

            self.assertNotEqual(layout.sessions, alice.sessions)
            self.assertEqual(legacy_marker.read_text(encoding="utf-8"), "legacy")
            self.assertEqual(user_marker.read_text(encoding="utf-8"), "alice")


if __name__ == "__main__":
    unittest.main()
