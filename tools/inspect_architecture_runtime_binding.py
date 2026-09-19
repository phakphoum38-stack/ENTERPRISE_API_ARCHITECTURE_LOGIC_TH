#!/usr/bin/env python3
"""Read-only runtime-binding inspector for the three Flutter roots."""
from __future__ import annotations
import argparse, json
from pathlib import Path

ROOTS = {
    "general": Path("apps/research_os_flutter"),
    "owner_special": Path("owner_special/flutter_app"),
    "v3": Path("v3/flutter_app"),
}
SHARED = Path('packages/research_os_contracts')
ADAPTERS = {
    "general": ("research_os_api_adapter.dart",),
    "owner_special": ("owner_friend_capability_adapter.dart",),
    "v3": ("v3_compatibility_adapter.dart",),
}
UIS = {
    "general": ("app_shell.dart", "enterprise_navigation.dart", "adaptive_navigation.dart"),
    "owner_special": ("friend_app_shell.dart", "friend_app.dart"),
    "v3": ("research_os_v3_app.dart",),
}
APIS = {
    "general": ("research_os_api_client.dart",),
    "owner_special": ("owner_api.dart",),
    "v3": ("v3_api.dart",),
}
DIMENSIONS = ["contract","ownership","implementation","adapter","ui_surface","api_surface","state","navigation","error_recovery","security_authority","audit_observability","offline_recovery","idempotency_concurrency","schema_versioning","platform_parity","design_system","accessibility","performance","feature_flags","artifact_provenance","migration","retirement"]

def text(path):
    try: return path.read_text(encoding='utf-8')
    except (OSError, UnicodeDecodeError): return ''

def named(root, names):
    return [str(p.relative_to(root)) for p in root.rglob('*') if p.is_file() and p.name in names]

def shared_import(root):
    return any('package:research_os_contracts/' in text(p) for p in root.rglob('*.dart'))

def dimension(d, e):
    if d in ('contract','adapter'): return 'PASS' if e['shared_import'] and e['adapter_files'] else 'UNPROVEN'
    if d == 'implementation': return 'PASS' if e['dart_files'] else 'UNPROVEN'
    if d == 'ui_surface': return 'PASS' if e['ui_files'] else 'UNPROVEN'
    if d == 'api_surface': return 'PASS' if e['api_files'] and e['adapter_files'] else 'UNPROVEN'
    if d == 'navigation': return 'PARTIAL' if len(e['ui_files']) > 1 else ('PASS' if e['ui_files'] else 'UNPROVEN')
    if d == 'design_system': return 'PARTIAL' if e['theme_files'] or e['token_files'] else 'UNPROVEN'
    if d == 'platform_parity': return 'PASS' if e['platform_dirs'] else 'UNPROVEN'
    if d == 'ownership': return 'PARTIAL'
    return 'UNPROVEN'

def inspect(root):
    contract = json.loads(text(root/'current/ARCHITECTURE_COMPLETENESS_CONTRACT.json'))
    results = {}
    for key, rel in ROOTS.items():
        base = root/rel
        e = {
            'root': str(rel),
            'dart_files': [str(p.relative_to(root)) for p in base.rglob('*.dart')] if base.is_dir() else [],
            'shared_import': shared_import(base),
            'adapter_files': named(base, ADAPTERS[key]),
            'ui_files': named(base, UIS[key]),
            'api_files': named(base, APIS[key]),
            'theme_files': named(base, ('friend_theme.dart',)),
            'token_files': named(base, ('v5_design_tokens.dart',)),
            'platform_dirs': [str(p.relative_to(root)) for p in (base.glob('windows') if base.is_dir() else [])],
        }
        e['dimensions'] = {d: dimension(d,e) for d in contract['required_dimensions']}
        results[key] = e
    failures = [{'root':k,'dimension':d,'status':s} for k,e in results.items() for d,s in e['dimensions'].items() if s in ('UNPROVEN','DUPLICATED')]
    partial = [{'root':k,'dimension':d} for k,e in results.items() for d,s in e['dimensions'].items() if s == 'PARTIAL']
    entry = text(SHARED/'lib/research_os_contracts.dart')
    exports = {x: (x in entry) for x in ('navigation_contract.dart','state_contract.dart','error_contract.dart','control_contract.dart','observability_contract.dart')}
    return {'contract_id':contract['contract_id'],'schema_version':contract['schema_version'],'mode':'read_only_runtime_binding_inspection','status':'FAIL' if failures or not all(exports.values()) else 'PASS','summary':{'roots':len(results),'dimensions_per_root':len(contract['required_dimensions']),'unproven_or_duplicate':len(failures),'partial':len(partial),'shared_contract_exports_ok':all(exports.values())},'shared_contract_exports':exports,'roots':results,'failures':failures,'partial':partial,'note':'Structural presence is not runtime proof; UNPROVEN fails closed.'}

def main():
    p=argparse.ArgumentParser(); p.add_argument('--root',type=Path,default=Path('.')); p.add_argument('--json-out',type=Path); a=p.parse_args()
    result=inspect(a.root.resolve()); payload=json.dumps(result,indent=2,sort_keys=True)+'\n'; print(payload,end='')
    if a.json_out: a.json_out.write_text(payload,encoding='utf-8')
    return 0 if result['status']=='PASS' else 1

if __name__ == '__main__': raise SystemExit(main())