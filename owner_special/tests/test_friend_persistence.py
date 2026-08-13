import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from research_os_friend import FriendRequest, FriendRuntime, OwnerBundleBuilder


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
OWNER_SPECIAL_ROOT = REPOSITORY_ROOT / "owner_special"


class FriendPersistenceTests(unittest.TestCase):
    def test_persistent_memory_survives_runtime_restart(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            runtime = FriendRuntime.create_owner_special(
                "phakphum",
                data_root=root,
                repository_root=REPOSITORY_ROOT,
            )
            runtime.ask(
                FriendRequest(
                    owner_id="phakphum",
                    profile_id="work",
                    session_id="project-a",
                    text="remember this project context",
                )
            )
            restarted = FriendRuntime.create_owner_special(
                "phakphum",
                data_root=root,
                repository_root=REPOSITORY_ROOT,
            )
            items = restarted.orchestrator.memory.recall(
                owner_id="phakphum",
                profile_id="work",
                session_id="project-a",
            )
            self.assertEqual(len(items), 2)
            self.assertEqual(restarted.architecture()["memory_persistence"], "disk")

    def test_persistent_memory_isolated_between_owners(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            first = FriendRuntime.create_owner_special("owner-a", data_root=root)
            first.ask(FriendRequest(owner_id="owner-a", text="owner a context"))
            second = FriendRuntime.create_owner_special("owner-b", data_root=root)
            self.assertEqual(
                second.orchestrator.memory.recall(owner_id="owner-b", profile_id="default", session_id="default"),
                (),
            )
            self.assertNotEqual(
                root / "owners" / "owner-a" / "memory" / "memory.json",
                root / "owners" / "owner-b" / "memory" / "memory.json",
            )

    def test_capability_manifest_contains_complete_friend_layers(self) -> None:
        runtime = FriendRuntime.create_owner_special("phakphum", repository_root=REPOSITORY_ROOT)
        names = set(runtime.architecture()["capabilities"])
        required = {
            "identity",
            "brain",
            "reasoning-summary",
            "skills",
            "persistent-memory",
            "context",
            "policy",
            "tools",
            "providers",
            "v3-bridge",
            "orchestrator",
            "factory",
            "evidence",
            "owner-bundle",
            "tests",
        }
        self.assertTrue(required.issubset(names))

    def test_v3_bridge_detects_owned_core(self) -> None:
        runtime = FriendRuntime.create_owner_special("phakphum", repository_root=REPOSITORY_ROOT)
        bridge = runtime.architecture()["v3_bridge"]
        self.assertTrue(bridge["available"], bridge.get("reason"))
        self.assertIn("UnifiedMasterOrchestrator", bridge["exports"])
        self.assertIn("FactoryExecutionEngine", bridge["exports"])
        self.assertIn("OpenAICompatibleProvider", bridge["exports"])
        self.assertIn("UserDataLayout", bridge["exports"])

    def test_owner_bundle_contains_architecture_not_runtime_owner_data(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            destination = Path(temporary) / "friend-complete.zip"
            result = OwnerBundleBuilder(OWNER_SPECIAL_ROOT).build(destination)
            self.assertTrue(result["source_only"])
            with zipfile.ZipFile(destination) as archive:
                names = set(archive.namelist())
                self.assertIn("OWNER_MANIFEST.json", names)
                self.assertIn("research_os_friend/runtime.py", names)
                self.assertIn("research_os_friend/brain.py", names)
                self.assertIn("research_os_friend/skills.py", names)
                self.assertIn("research_os_friend/persistent_memory.py", names)
                self.assertIn("research_os_friend/v3_bridge.py", names)
                self.assertIn("BUNDLE_MANIFEST.json", names)
                manifest = json.loads(archive.read("BUNDLE_MANIFEST.json"))
                self.assertEqual(manifest["edition"], "owner-special")
                self.assertFalse(any(name.startswith("data/") for name in names))


if __name__ == "__main__":
    unittest.main()
