#!/usr/bin/env python3
"""U-MAP discovery primitives consumed by AEOS Master Assurance."""
from __future__ import annotations
import json, os, re, subprocess
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
DIMENSIONS = ("MAIN", "PRS", "WORKFLOWS", "SOURCE", "TESTS", "ARTIFACTS", "CONTRACTS", "PROVENANCE", "FORENSIC")

def _run(*args: str) -> tuple[int, str]:
    try:
        p = subprocess.run(args, cwd=ROOT, text=True, capture_output=True)
        return p.returncode, (p.stdout + "\n" + p.stderr).strip()
    except Exception as exc:
        return 125, f"{type(exc).__name__}:{exc}"

def discover_main() -> dict[str, object]:
    rc, sha = _run("git", "rev-parse", "HEAD")
    return {"dimension":"MAIN","status":"PASS" if rc == 0 and SHA_RE.fullmatch(sha) else "INSUFFICIENT_EVIDENCE","sha":sha if rc == 0 else None,"branch":_run("git","branch","--show-current")[1],"protected_baseline":"565ab068d5a1540ea799b594ff031ba003e068af"}

def discover_prs() -> dict[str, object]:
    rc, out = _run("gh","pr","list","--state","all","--limit","200","--json","number,title,state,isDraft,mergedAt,headRefName,baseRefName,headRefOid,mergeCommit")
    if rc != 0: return {"dimension":"PRS","status":"INSUFFICIENT_EVIDENCE","error":out}
    try: items = json.loads(out or "[]")
    except json.JSONDecodeError as exc: return {"dimension":"PRS","status":"FAIL","error":f"invalid_gh_json:{exc}"}
    return {"dimension":"PRS","status":"PASS","count":len(items),"items":items}

def discover_workflows() -> dict[str, object]:
    d = ROOT / ".github" / "workflows"
    files = sorted(str(p.relative_to(ROOT)) for p in d.glob("*.y*ml")) if d.is_dir() else []
    return {"dimension":"WORKFLOWS","status":"PASS" if d.is_dir() else "INSUFFICIENT_EVIDENCE","count":len(files),"files":files}

def discover_source_tests() -> tuple[dict[str, object], dict[str, object]]:
    source_files=[]; test_files=[]
    for root in ("tools","owner_special","v3","apps"):
        p=ROOT/root
        if p.exists(): source_files += [str(x.relative_to(ROOT)) for x in p.rglob("*.py") if "__pycache__" not in x.parts]
    for root in ("tests","owner_special/tests","v3/tests","apps"):
        p=ROOT/root
        if p.exists(): test_files += [str(x.relative_to(ROOT)) for x in p.rglob("test_*.py") if "__pycache__" not in x.parts]
    return ({"dimension":"SOURCE","status":"PASS","count":len(set(source_files)),"files":sorted(set(source_files))},{"dimension":"TESTS","status":"PASS","count":len(set(test_files)),"files":sorted(set(test_files))})

def discover_artifacts_contracts() -> tuple[dict[str, object], dict[str, object]]:
    d=ROOT/"current"; files=sorted(d.glob("*")) if d.is_dir() else []
    artifacts=[str(p.relative_to(ROOT)) for p in files if p.suffix in {".json",".sha256",".manifest",".md"} and any(k in p.name.upper() for k in ("EVIDENCE","MANIFEST","FORENSIC","ASSURANCE"))]
    contracts=[str(p.relative_to(ROOT)) for p in files if p.suffix==".json" and "CONTRACT" in p.name.upper()]
    return ({"dimension":"ARTIFACTS","status":"PASS","count":len(artifacts),"files":artifacts},{"dimension":"CONTRACTS","status":"PASS","count":len(contracts),"files":contracts})

def discover_provenance_forensic() -> tuple[dict[str, object], dict[str, object]]:
    d=ROOT/"current"; files=list(d.glob("*")) if d.is_dir() else []
    provenance=[str(p.relative_to(ROOT)) for p in files if any(k in p.name.upper() for k in ("PROVENANCE","EVIDENCE_LEDGER","LINEAGE"))]
    forensic=[str(p.relative_to(ROOT)) for p in files if "FORENSIC" in p.name.upper()]
    return ({"dimension":"PROVENANCE","status":"PASS","count":len(provenance),"files":provenance},{"dimension":"FORENSIC","status":"PASS","count":len(forensic),"files":forensic})

def discover_all() -> dict[str, object]:
    source,tests=discover_source_tests(); artifacts,contracts=discover_artifacts_contracts(); provenance,forensic=discover_provenance_forensic()
    dims=[discover_main(),discover_prs(),discover_workflows(),source,tests,artifacts,contracts,provenance,forensic]
    return {"schema":"U_MAP_DISCOVERY_V1","canonical_main_expected":os.environ.get("AEOS_EXPECTED_SHA",""),"dimensions":dims,"dimension_count":len(dims)}

if __name__ == "__main__": print(json.dumps(discover_all(),ensure_ascii=False,indent=2,sort_keys=True))
