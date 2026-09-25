#!/usr/bin/env python3
"""Build a source-SHA-pinned searchable M.2 inventory and relationship graph."""
from __future__ import annotations
import argparse,json,re,subprocess
from tools.research_os_test_case_inventory import discover as discover_test_cases
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
EXCLUDES={".git",".dart_tool","build","dist","node_modules","__pycache__",".venv","venv"}
TEXT_SUFFIXES={".py",".dart",".json",".yml",".yaml",".md",".txt",".ps1",".sh",".toml",".html",".css",".js",".cs",".cpp",".h"}
CONTRACT_RE=re.compile(r"current/[A-Z0-9_./-]+\.(?:json|ya?ml)")
INV_RE=re.compile(r"\bINV-\d{3}\b")
CAPABILITY_RULES=[
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
 found=[n for n,needles in CAPABILITY_RULES if any(x in hay for x in needles)]
 return found or ["general"]
def nid(k,path): return k.upper()+":"+path

def required_authority_paths(by_path):
 gate_path="current/RESEARCH_OS_UNIFIED_FINAL_GATE.yml"
 if gate_path not in by_path:
  return [], []
 text=read_text(by_path[gate_path])
 def section(name):
  match=re.search(rf"^{name}:\n((?:  - .+\n)+)",text,re.MULTILINE)
  return [line[4:].strip() for line in match.group(1).splitlines()] if match else []
 return section("required_contracts"), section("required_workflows")

def build_index():
 source=git_sha(); ps=files(); by_path={rel(p):p for p in ps}; rows=[]
 test_case_inventory=discover_test_cases()
 required_contracts,required_workflows=required_authority_paths(by_path)
 for p in ps:
  path=rel(p); txt=read_text(p)
  rows.append({"path":path,"kind":kind(path),"size":p.stat().st_size,
   "capabilities":capabilities(path,txt),
   "contract_refs":sorted({x for x in CONTRACT_RE.findall(txt) if x in by_path}),
   "invariant_refs":sorted(set(INV_RE.findall(txt))),
   "has_contract_reference":bool(CONTRACT_RE.search(txt)),
   "has_test_reference":bool(re.search(r"(?:test_|_test\.)",txt)),
   "has_workflow_reference":".github/workflows/" in txt,
   "has_evidence_reference":bool(re.search(r"evidence|provenance|lineage",txt,re.I)),
   "has_final_gate_reference":bool(re.search(r"final[_ -]?gate|release_authority",txt,re.I))})
 contracts=[r["path"] for r in rows if r["kind"]=="contract"]
 tests=[r["path"] for r in rows if r["kind"]=="test"]
 workflows=[r["path"] for r in rows if r["kind"]=="workflow"]
 implementations=[r["path"] for r in rows if r["kind"]=="implementation"]
 nodes=[]; node_ids=set(); edges=[]
 def add_node(i,k,path=None,state="UNKNOWN"):
  if i not in node_ids:
   node_ids.add(i); nodes.append({"id":i,"kind":k,"path":path,"state":state})
 for r in rows:
  k=r["kind"].upper(); add_node(nid(k,r["path"]),k,r["path"])
  for c in r["contract_refs"]:
   add_node(nid("CONTRACT",c),"CONTRACT",c)
   edges.append({"from":nid(k,r["path"]),"relation":"REFERENCES","to":nid("CONTRACT",c)})
  for inv in r["invariant_refs"]:
   add_node("INVARIANT:"+inv,"INVARIANT",inv)
   edges.append({"from":nid(k,r["path"]),"relation":"ENFORCES_OR_REFERENCES","to":"INVARIANT:"+inv})
 for c in contracts:
  stem=Path(c).stem.lower().replace("-contract","")
  exact=[t for t in tests if c in read_text(by_path[t])]
  named=[t for t in tests if stem and stem in Path(t).stem.lower()]
  for t in sorted(set(exact+named)):
   edges.append({"from":nid("CONTRACT",c),"relation":"VERIFIED_BY","to":nid("TEST",t)})
 workflow_names={Path(w).name:w for w in workflows}
 for w in workflows:
  txt=read_text(by_path[w])
  for name,target in workflow_names.items():
   if target!=w and name in txt:
    edges.append({"from":nid("WORKFLOW",w),"relation":"DISPATCHES_OR_REFERENCES","to":nid("WORKFLOW",target)})
 final_gate_path="current/RESEARCH_OS_UNIFIED_FINAL_GATE.yml"
 final_gate_exists=final_gate_path in by_path
 if final_gate_exists:
  add_node("FINAL_GATE:UNIFIED","AUTHORITY",final_gate_path,"VERIFIED")
 for r in rows:
  if r["has_final_gate_reference"] and r["kind"]!="workflow":
   edges.append({"from":nid(r["kind"],r["path"]),"relation":"BINDS_TO","to":"FINAL_GATE:UNIFIED"})
 for w in workflows:
  if "unified-final-gate" in w or "RESEARCH_OS_UNIFIED_FINAL_GATE" in read_text(by_path[w]):
   edges.append({"from":nid("WORKFLOW",w),"relation":"PARTICIPATES_IN","to":"FINAL_GATE:UNIFIED"})
 edges=sorted({(e["from"],e["relation"],e["to"]):e for e in edges}.values(),key=lambda e:(e["from"],e["relation"],e["to"]))
 targets={n["id"] for n in nodes}; dangling=[e for e in edges if e["from"] not in targets or e["to"] not in targets]
 findings=[]
 for required in required_contracts:
  if required not in by_path or required not in contracts:
   findings.append({"state":"MISSING","code":"REQUIRED_FINAL_GATE_CONTRACT_MISSING_FROM_M2","path":required})
 for required in required_workflows:
  if required not in by_path or required not in workflows:
   findings.append({"state":"MISSING","code":"REQUIRED_FINAL_GATE_WORKFLOW_MISSING_FROM_M2","path":required})
 for c in contracts:
  stem=Path(c).stem.lower().replace("-contract","")
  if not any((c in read_text(by_path[t])) or (stem and stem in Path(t).stem.lower()) for t in tests):
   findings.append({"state":"INCOMPLETE","code":"CONTRACT_WITHOUT_NAMED_TEST","path":c})
 integrity={
  "exact_source_sha":bool(re.fullmatch(r"[0-9a-f]{40}",source)),
  "inventory_completeness":bool(rows),\n  "test_case_inventory":test_case_inventory["source_sha"]==source and test_case_inventory["inventory"]["test_files"]>0 and test_case_inventory["inventory"]["discovered_test_cases"]>0,
  "duplicate_path_detection":len({r["path"] for r in rows})==len(rows),
  "unique_node_ids":len(node_ids)==len(nodes),
  "no_dangling_edges":not dangling,
  "contract_test_linkage":bool(contracts) and any(e["from"].startswith("CONTRACT:") and e["relation"]=="VERIFIED_BY" and e["to"].startswith("TEST:") for e in edges) and all(any(e["from"]==nid("CONTRACT",c) and e["relation"]=="VERIFIED_BY" for e in edges) for c in contracts if any(c in read_text(by_path[t]) or Path(c).stem.lower().replace("-contract","") in Path(t).stem.lower() for t in tests)),
  "contract_implementation_linkage":bool(implementations) and any(e["from"].startswith("IMPLEMENTATION:") and e["relation"]=="REFERENCES" and e["to"].startswith("CONTRACT:") for e in edges) and all(any(e["from"]==nid("IMPLEMENTATION",i) and e["relation"]=="REFERENCES" and e["to"].startswith("CONTRACT:") for e in edges) for i in implementations if any(c in read_text(by_path[i]) for c in contracts)),
  "workflow_inventory":bool(workflows),
  "contract_inventory":bool(contracts),
  "required_contract_inventory":bool(required_contracts) and all(path in contracts for path in required_contracts),
  "required_workflow_inventory":bool(required_workflows) and all(path in workflows for path in required_workflows),
  "invariant_inventory":any(r["invariant_refs"] for r in rows),
  "final_gate_node":final_gate_exists and "FINAL_GATE:UNIFIED" in targets,
 }
 return {"schema":"RESEARCH_OS_M2_AUDIT_GRAPH_V2","source_sha":source,"root":str(ROOT),
  "inventory":{"files":len(rows),"contracts":len(contracts),"implementations":len(implementations),"tests":len(tests),"workflows":len(workflows),"required_contracts":len(required_contracts),"required_workflows":len(required_workflows),"test_case_inventory":test_case_inventory["inventory"],"nodes":len(nodes),"edges":len(edges),"findings":len(findings)},
  "integrity":integrity,"findings":findings,"nodes":nodes,"edges":edges,"files":rows,"dangling_edges":dangling}
def build_graph(): return build_index()
def main():
 p=argparse.ArgumentParser(); p.add_argument("--output",default="m2_audit_index.json"); p.add_argument("--summary",default="m2_audit_index_summary.txt"); p.add_argument("--query",default=""); a=p.parse_args()
 g=build_index()
 if not all(g["integrity"].values()):
  print("M2_AUDIT_INDEX=FAIL")
  for k,v in g["integrity"].items():
   if not v: print("INTEGRITY_FAIL="+k)
  return 2
 if a.query:
  q=a.query.lower()
  nodes=[n for n in g["nodes"] if q in n["id"].lower() or q in (n.get("path") or "").lower()]
  edges=[e for e in g["edges"] if q in json.dumps(e).lower()]
  print(json.dumps({"query":a.query,"nodes":nodes,"edges":edges},ensure_ascii=False,indent=2)); return 0
 Path(a.output).write_text(json.dumps(g,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 s=["RESEARCH OS M.2 WHOLE-SYSTEM AUDIT GRAPH",f"SOURCE_SHA={g['source_sha']}",
    *[f"{k.upper()}={v}" for k,v in g["inventory"].items()],
    "M2_AUDIT_GRAPH=PASS","M2_AUDIT_INDEX=PASS"]
 Path(a.summary).write_text("\n".join(s)+"\n",encoding="utf-8"); print("\n".join(s)); return 0
if __name__=="__main__": raise SystemExit(main())
