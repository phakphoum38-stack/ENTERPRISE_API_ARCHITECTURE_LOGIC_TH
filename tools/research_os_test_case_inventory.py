#!/usr/bin/env python3
"""Discover repository test cases with a flexible 13,000-14,000 target band."""
from __future__ import annotations
import argparse, ast, json, re, subprocess
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
EXCLUDES = {".git",".dart_tool","build","dist","node_modules","__pycache__",".venv","venv"}
TARGET_MIN, TARGET_MAX = 13000, 14000
def repo_files():
    return sorted(p for p in ROOT.rglob("*") if p.is_file() and not any(x in EXCLUDES for x in p.parts))
def is_test_file(path):
    s=path.as_posix()
    return (path.suffix==".py" and (path.name.startswith("test_") or path.name.endswith("_test.py") or "/tests/" in "/"+s)) or (path.suffix==".dart" and (path.name.endswith("_test.dart") or "/test/" in "/"+s))
def discover_python_test_cases(path):
    try: tree=ast.parse(path.read_text(encoding="utf-8"))
    except (OSError,UnicodeDecodeError,SyntaxError): return 0
    return sum(isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name.startswith("test") for n in ast.walk(tree))
DART_TEST_RE=re.compile(r"(?<![A-Za-z0-9_])testWidgets?\s*\(")
def discover_dart_test_cases(path):
    try: text=path.read_text(encoding="utf-8")
    except (OSError,UnicodeDecodeError): return 0
    return len(DART_TEST_RE.findall(text))
def discover():
    rows=[]; totals={"python":0,"dart":0}; unreadable=0
    for path in repo_files():
        if not is_test_file(path): continue
        try: rel=path.relative_to(ROOT).as_posix()
        except ValueError: continue
        if path.suffix==".py": language="python"; count=discover_python_test_cases(path); totals["python"]+=count
        elif path.suffix==".dart": language="dart"; count=discover_dart_test_cases(path); totals["dart"]+=count
        else: language="other"; count=0
        rows.append({"path":rel,"language":language,"discovered_cases":count})
    total=totals["python"]+totals["dart"]
    return {"schema":"RESEARCH_OS_TEST_CASE_INVENTORY_V1","source_sha":subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip(),"target_band":{"min":TARGET_MIN,"max":TARGET_MAX},"inventory":{"test_files":len(rows),"discovered_test_cases":total,"python_cases":totals["python"],"dart_cases":totals["dart"],"unreadable_test_files":unreadable},"discovery":{"python_boundary":"test* functions/methods via AST","dart_boundary":"test()/testWidgets() invocation","execution_status":"NOT_EXECUTED_BY_INVENTORY","duplicate_policy":"one case per discovered source invocation; execution deduplication remains runner evidence"},"target_status":"IN_BAND" if TARGET_MIN<=total<=TARGET_MAX else "OUT_OF_BAND","files":rows}
def main():
    p=argparse.ArgumentParser(); p.add_argument("--output",default="research_os_test_case_inventory.json"); p.add_argument("--summary",default="research_os_test_case_inventory_summary.txt"); p.add_argument("--min",dest="minimum",type=int,default=TARGET_MIN); p.add_argument("--max",dest="maximum",type=int,default=TARGET_MAX); a=p.parse_args()
    data=discover(); total=data["inventory"]["discovered_test_cases"]; data["target_band"]={"min":a.minimum,"max":a.maximum}; data["target_status"]="IN_BAND" if a.minimum<=total<=a.maximum else "OUT_OF_BAND"
    Path(a.output).write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    summary=["RESEARCH OS FULL TEST CASE INVENTORY",f"SOURCE_SHA={data['source_sha']}",f"TEST_FILES={data['inventory']['test_files']}",f"DISCOVERED_TEST_CASES={total}",f"PYTHON_CASES={data['inventory']['python_cases']}",f"DART_CASES={data['inventory']['dart_cases']}",f"TARGET_BAND={a.minimum}-{a.maximum}",f"TARGET_STATUS={data['target_status']}","EXECUTION_STATUS=NOT_EXECUTED_BY_INVENTORY"]
    Path(a.summary).write_text("\n".join(summary)+"\n",encoding="utf-8"); print("\n".join(summary)); return 0
if __name__=="__main__": raise SystemExit(main())