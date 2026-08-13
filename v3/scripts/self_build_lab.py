from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from research_os_v3.self_build import ResearchOSSelfBuilder  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Stage Research OS into an isolated governed self-build workspace."
    )
    parser.add_argument("--source", required=True, help="Repository source root")
    parser.add_argument("--workspace", required=True, help="Fresh output workspace outside source")
    parser.add_argument("--source-sha", default="unknown", help="Source commit SHA for provenance")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    builder = ResearchOSSelfBuilder(Path(args.source))
    result = builder.stage(Path(args.workspace), source_sha=args.source_sha)
    summary = {
        "contract": builder.contract,
        "workspace": str(result.workspace),
        "manifest": str(result.manifest_path),
        "file_count": result.file_count,
        "total_bytes": result.total_bytes,
        "source_tree_sha256": result.source_tree_sha256,
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
