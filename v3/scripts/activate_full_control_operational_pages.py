from __future__ import annotations

import argparse
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--workspace', required=True)
    args = parser.parse_args()
    workspace = Path(args.workspace).resolve()
    app_root = workspace / 'v3' / 'flutter_app' / 'lib'
    src = app_root / 'src'
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

    # Once all Workspace/System routes are tool-backed, the old placeholder
    # class is obsolete. Remove it from the generated product source instead
    # of suppressing the analyzer warning.
    placeholder_start = text.find('\nclass _OperationalPage extends StatelessWidget {')
    placeholder_end = text.find('\nclass _ToolDiscoveryCard extends StatelessWidget {', placeholder_start)
    if placeholder_start < 0 or placeholder_end < 0:
        raise SystemExit('obsolete operational placeholder block not found')
    text = text[:placeholder_start] + text[placeholder_end:]
    target.write_text(text, encoding='utf-8', newline='\n')

    # The isolated Full Product build launches the generated morning-style
    # Full Control Center as the one canonical application shell.
    main_path = app_root / 'main.dart'
    if not main_path.is_file():
        raise SystemExit(f'missing Flutter entrypoint: {main_path}')
    main_text = main_path.read_text(encoding='utf-8')
    main_text = main_text.replace(
        "import 'src/research_os_full_app.dart';",
        "import 'src/research_os_v3_app.dart';",
    )
    main_text = main_text.replace(
        'runApp(ResearchOSFullApp(api: api));',
        'runApp(ResearchOSV3App(api: api));',
    )
    if "import 'src/research_os_v3_app.dart';" not in main_text or 'ResearchOSV3App(api: api)' not in main_text:
        raise SystemExit('could not normalize Full Product Flutter entrypoint')
    main_path.write_text(main_text, encoding='utf-8', newline='\n')

    # These were temporary direct-shell prototypes used while converging on
    # the canonical generated morning Full Control Center. They are not part
    # of the product runtime and must not enter the staged Full Product tree.
    retired: list[str] = []
    for name in ('research_os_full_app.dart', 'full_control_operational.dart'):
        candidate = src / name
        if candidate.is_file():
            candidate.unlink()
            retired.append(name)

    print('activated live operational pages in generated Research OS Full Control Center')
    print('removed obsolete generated _OperationalPage placeholder')
    print('normalized Flutter entrypoint to ResearchOSV3App')
    print(f'retired duplicate experimental UI files from isolated product workspace: {retired}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
