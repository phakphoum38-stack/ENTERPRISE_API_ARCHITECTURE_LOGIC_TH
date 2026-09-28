import tempfile
import unittest
from pathlib import Path

from tools.research_os_api.memory_fabric import MemoryFabricError, NvmeMemoryRegion, detect_host_capabilities

class MemoryFabricTests(unittest.TestCase):
    def test_mmap_backed_region_round_trip(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "memory.bin"
            with NvmeMemoryRegion(path, 4096) as region:
                region.write(128, b"Research OS")
                self.assertEqual(region.read(128, 11), b"Research OS")

    def test_bounds_are_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            with NvmeMemoryRegion(Path(tmp) / "memory.bin", 16) as region:
                with self.assertRaises(ValueError):
                    region.write(12, b"012345")
                with self.assertRaises(ValueError):
                    region.read(12, 8)

    def test_closed_region_is_not_accessible(self):
        with tempfile.TemporaryDirectory() as tmp:
            region = NvmeMemoryRegion(Path(tmp) / "memory.bin", 32)
            with region:
                pass
            with self.assertRaises(MemoryFabricError):
                region.read(0, 1)

    def test_capability_detection_is_conservative(self):
        caps = detect_host_capabilities()
        self.assertTrue(caps["storage_backed_region_supported"])
        self.assertIsNone(caps["nvme_detected"])
        self.assertIsNone(caps["pcie5_detected"])
        self.assertIsNone(caps["cxl_detected"])

if __name__ == "__main__":
    unittest.main()
