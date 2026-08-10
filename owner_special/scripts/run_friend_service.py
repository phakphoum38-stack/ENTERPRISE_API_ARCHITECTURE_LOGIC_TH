from __future__ import annotations

import argparse
from pathlib import Path

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
