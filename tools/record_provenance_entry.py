#!/usr/bin/env python3
"""Append one deterministic provenance entry; derived identity is never caller-supplied."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

DOMAIN = b"provenance-entry-v1\x00"


def canonical(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def digest(value: object) -> str:
    return hashlib.sha256(DOMAIN + canonical(value).encode("utf-8")).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ledger", required=True)
    parser.add_argument("--entry", required=True, help="JSON entry without derived sequence, previous_entry_hash, or entry_hash")
    args = parser.parse_args()
    try:
        ledger_path, entry_path = Path(args.ledger), Path(args.entry)
        ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
        entry = json.loads(entry_path.read_text(encoding="utf-8"))
        entries = ledger.get("entries")
        if not isinstance(entries, list):
            raise ValueError("entries_collection_missing")
        if any(k in entry for k in ("sequence", "previous_entry_hash", "entry_hash")):
            raise ValueError("derived_fields_must_not_be_supplied")
        if not isinstance(entry.get("entry_id"), str) or not entry["entry_id"]:
            raise ValueError("missing:entry_id")
        if any(isinstance(e, dict) and e.get("entry_id") == entry["entry_id"] for e in entries):
            raise ValueError("duplicate_entry_id:" + entry["entry_id"])
        entry["sequence"] = len(entries) + 1
        entry["previous_entry_hash"] = entries[-1]["entry_hash"] if entries else None
        entry["entry_hash"] = digest(entry)
        entries.append(entry)
        ledger_path.write_text(json.dumps(ledger, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
        print(json.dumps({"status":"PASS","entry_id":entry["entry_id"],"sequence":entry["sequence"],"entry_hash":entry["entry_hash"]}, sort_keys=True))
        return 0
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(json.dumps({"status":"FAIL","error":str(exc)}, sort_keys=True))
        return 1


if __name__ == "__main__":
    sys.exit(main())
