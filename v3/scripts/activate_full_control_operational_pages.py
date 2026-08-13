from __future__ import annotations

import argparse
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--workspace', required=True)
    args = parser.parse_args()
    workspace = Path(args.workspace).resolve()
    src = workspace / 'v3' / 'flutter_app' / 'lib' / 'src'
    target = src / 'research_os_v3_app.dart'
    if not target.is_file():
        raise SystemExit(f'missing generated app: {target}')

    text = target.read_text(encoding='utf-8')
    import_old = "import 'api/v3_api.dart';"
    import_new = "import 'api/v3_api.dart';\nimport 'operational_pages.dart';"
    route_old = "return _OperationalPage(item: _navItems[index], api: api, snapshot: snapshot);"
    route_new = "return ResearchOSOperationalPage(label: _navItems[index].label, api: api);"
    if import_old not in text or route_old not in text:
        raise SystemExit('generated app contract changed; activation patch refused')
    text = text.replace(import_old, import_new, 1).replace(route_old, route_new, 1)
    target.write_text(text, encoding='utf-8', newline='\n')

    # The full product has one canonical app shell. Retire older experimental
    # UI files only inside the isolated self-build workspace so analyzer/build
    # cannot accidentally validate or package competing application shells.
    retired: list[str] = []
    for name in ('research_os_full_app.dart', 'full_control_operational.dart'):
        candidate = src / name
        if candidate.is_file():
            candidate.unlink()
            retired.append(name)

    print('activated live operational pages in generated Research OS Full Control Center')
    print(f'retired duplicate UI sources in self-build workspace: {retired}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
