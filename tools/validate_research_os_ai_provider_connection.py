#!/usr/bin/env python3
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
 contract=json.loads((ROOT/"current/RESEARCH_OS_AI_PROVIDER_CONNECTION_CONTRACT.json").read_text())
 evidence=json.loads((ROOT/"current/RESEARCH_OS_AI_PROVIDER_CONNECTION_EVIDENCE_CONTRACT.json").read_text())
 impl=ROOT/"tools/research_os_ai_provider_connection.py"
 if not {"openai","gemini"}.issubset({x["id"] for x in contract["providers"]}):raise SystemExit("AI_PROVIDER_CONNECTION=FAIL: providers")
 if any(contract["authority"][x] for x in ("may_authorize","may_merge","may_release")):raise SystemExit("AI_PROVIDER_CONNECTION=FAIL: authority")
 if contract["routing"]["flutter_direct_provider_calls"]:raise SystemExit("AI_PROVIDER_CONNECTION=FAIL: direct calls")
 if not evidence["secret_values_forbidden"] or not impl.is_file():raise SystemExit("AI_PROVIDER_CONNECTION=FAIL: boundary")
 text=impl.read_text()
 for marker in ("def inspect(","def connect(","def disconnect(","def health_check(","PLATFORM_CONNECTOR","PLATFORM_API_FALLBACK","secrets_excluded","FINAL_GATE"):
  if marker not in text:raise SystemExit(f"AI_PROVIDER_CONNECTION=FAIL: {marker}")
 print("AI_PROVIDER_CONNECTION=PASS")
 print("PROVIDERS=OPENAI_GPT,GEMINI")
 print("CREDENTIAL_BOUNDARY=SERVER_ONLY")
 print("FLUTTER_DIRECT_PROVIDER_CALLS=FORBIDDEN")
 print("RELEASE_AUTHORITY=FINAL_GATE")
if __name__=="__main__":main()
