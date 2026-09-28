from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Bootstrap the packaged Owner Special source root deterministically. This mirrors
# the certified V3 service entrypoint and does not depend on PYTHONPATH being
# honored by a relocated/bundled Python runtime or by the Windows SCM process.
OWNER_SPECIAL_ROOT = Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = OWNER_SPECIAL_ROOT.parent
for source_root in (OWNER_SPECIAL_ROOT, REPOSITORY_ROOT):
    if str(source_root) not in sys.path:
        sys.path.insert(0, str(source_root))

from research_os_friend import OwnerFriendService


def main() -> None:
    parser = argparse.ArgumentParser(description="Research OS Owner Special Friend Service")
    parser.add_argument("--owner-id", default="owner")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8790)
    parser.add_argument("--data-root", type=Path, default=None)
    parser.add_argument("--audit-path", type=Path, default=None)
    parser.add_argument("--repository-root", type=Path, default=Path.cwd())
    args = parser.parse_args()

    service = OwnerFriendService(
        owner_id=args.owner_id,
        host=args.host,
        port=args.port,
        data_root=args.data_root,
        audit_path=args.audit_path,
        repository_root=args.repository_root,
    )
    print(f"Owner Friend Service listening on http://{service.host}:{service.port}", flush=True)
    try:
        service.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        service.close()


if __name__ == "__main__":
    main()
