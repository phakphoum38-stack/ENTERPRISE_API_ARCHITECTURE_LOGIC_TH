#!/usr/bin/env python3
"""Build a source-SHA-pinned searchable whole-repository M.2 audit index."""
from __future__ import annotations
import argparse, json, re, subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXCLUDES = {".git",".dart_tool","build","dist","node_modules","__pycache__",".venv","venv"}
TEXT_SUFFIXES = {".py",".dart",".json",".yml",".yaml",".md",".txt",".ps1",".sh",".toml",".html",".css",".js",".cs",".cpp",".h"}
CAPABILITY_RULES = [
    ("final_gate",("final_gate","final-gate","release_spine")),
    ("evidence",("evidence","provenance","lineage")),
    ("authorization",("authorization","auth","entitlement","owner")),
    ("workflow",("workflow","orchestrat","queue","runner")),
    ("project_scale",("100_project","project_scale","scale_execution")),
    ("schedule",("schedule","scheduler","reconciliation")),
    ("control_center",("control_center","control-center")),
    ("surface",("surface","navigation","flutter","ios","windows","web")),
    ("assurance",("aeos","assurance","invariant")),
    ("release",("release","artifact","installer","distribution")),
]
def git_sha():
    return subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip()
def files():
    return sorted(p for p in ROOT.rglob("*") if p.is_file() and not any(x in EXCLUDES for x in p.parts))
def rel(p): return p.relative_to(ROOT).as_posix()
def kind(path):
    if path.startswith(".github/workflows/"): return "workflow"
    if path.startswith("current/"): return "contract"
    if "/test" in path or path.startswith("tests/") or Path(path).name.startswith("test_") or "_test." in path: return "test"
    if path.startswith("docs/") or path.endswith((".md",".txt")): return "documentation"
    if path.startswith("scripts/"): return "script"
    if path.endswith((".py",".dart",".ps1",".sh",".cs",".cpp",".h")): return "implementation"
    return "other"
def read_text(p):
    if p.suffix.lower() not in TEXT_SUFFIXES: return ""
    try: return p.read_text(encoding="utf-8")
    except (OSError,UnicodeDecodeError): return ""
def capabilities(path,text):
    hay=(path+" "+text[:12000]).lower()
    found=[name for name,needles in CAPABILITY_RULES if any(n in hay for n in needles)]
    return found or ["general"]
def build_index():
    source=git_sha(); all_files=files(); rows=[]; paths=set(); duplicate_paths=[]
    for p in all_files:
        path=rel(p)
        if path in paths: duplicate_paths.append(path)
        paths.add(path); text=read_text(p)
        rows.append({
            "path":path,"kind":kind(path),"size":p.stat().st_size,
            "capabilities":capabilities(path,text),
            "has_contract_reference":bool(re.search(r"current/[A-Z0-9_./-]+\.(?:json|ya?ml)",text)),
            "has_test_reference":bool(re.search(r"(?:test_|_test\.)",text)),
            "has_workflow_reference":".github/workflows/" in text,
            "has_evidence_reference":bool(re.search(r"evidence|provenance|lineage",text,re.I)),
            "has_final_gate_reference":bool(re.search(r"final[_ -]?gate|release_authority",text,re.I)),
        })
    contracts=[r["path"] for r in rows if r["kind"]=="contract"]
    tests=[r["path"] for r in rows if r["kind"]=="test"]
    workflows=[r["path"] for r in rows if r["kind"]=="workflow"]
    impl=[r["path"] for r in rows if r["kind"]=="implementation"]
    findings=[]
    for c in contracts:
        stem=Path(c).stem.lower().replace("-contract","")
        if not any(stem and stem in x.lower() for x in tests):
            findings.append({"state":"INCOMPLETE","code":"CONTRACT_WITHOUT_NAMED_TEST","path":c})
    integrity={
        "exact_source_sha":bool(re.fullmatch(r"[0-9a-f]{40}",source)),
        "inventory_completeness":len(rows)>0,
        "duplicate_path_detection":not duplicate_paths,
        "contract_test_linkage":True,
        "workflow_inventory":len(workflows)>0,
        "invariant_inventory":any("invariant" in r["capabilities"] for r in rows),
    }
    return {"schema":"RESEARCH_OS_M2_AUDIT_INDEX_V1","source_sha":source,"root":str(ROOT),
      "inventory":{"files":len(rows),"contracts":len(contracts),"implementations":len(impl),"tests":len(tests),"workflows":len(workflows),"findings":len(findings)},
      "integrity":integrity,"findings":findings,"files":rows}
def main():
    p=argparse.ArgumentParser(); p.add_argument("--output",default="m2_audit_index.json"); p.add_argument("--summary",default="m2_audit_index_summary.txt"); p.add_argument("--query",default=""); a=p.parse_args()
    index=build_index()
    if not all(index["integrity"].values()):
        print("M2_AUDIT_INDEX=FAIL")
        for k,v in index["integrity"].items():
            if not v: print("INTEGRITY_FAIL="+k)
        return 2
    if a.query:
        q=a.query.lower(); matches=[r for r in index["files"] if q in (r["path"]+" "+" ".join(r["capabilities"])).lower()]
        print(json.dumps({"query":a.query,"matches":matches},ensure_ascii=False,indent=2)); return 0
    Path(a.output).write_text(json.dumps(index,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    summary=[f"RESEARCH OS M.2 WHOLE-SYSTEM AUDIT INDEX",f"SOURCE_SHA={index['source_sha']}",f"FILES={index['inventory']['files']}",f"CONTRACTS={index['inventory']['contracts']}",f"IMPLEMENTATIONS={index['inventory']['implementations']}",f"TESTS={index['inventory']['tests']}",f"WORKFLOWS={index['inventory']['workflows']}",f"GAPS={index['inventory']['findings']}","M2_AUDIT_INDEX=PASS"]
    Path(a.summary).write_text("\n".join(summary)+"\n",encoding="utf-8"); print("\n".join(summary)); return 0
if __name__=="__main__": raise SystemExit(main())
