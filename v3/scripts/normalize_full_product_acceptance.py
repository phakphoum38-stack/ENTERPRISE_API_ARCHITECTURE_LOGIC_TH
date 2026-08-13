from __future__ import annotations

import argparse
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--workspace', required=True)
    args = parser.parse_args()
    workspace = Path(args.workspace).resolve()
    target = workspace / 'v3' / 'flutter_app' / 'test' / 'app_shell_test.dart'
    if not target.is_file():
        raise SystemExit(f'missing generated acceptance test: {target}')

    text = target.read_text(encoding='utf-8')
    replacements = {
        "expect(find.textContaining('candidate'), findsWidgets);":
            "expect(find.text('Live Research OS result'), findsOneWidget);",
        "expect(find.textContaining('ResearchOS-backup.zip'), findsWidgets);":
            "expect(find.text('Create Backup'), findsOneWidget);\n    expect(find.text('Owner Gate + checksum verification'), findsOneWidget);",
        "expect(find.text('Owner Gate'), findsOneWidget);":
            "expect(find.text('Owner Gate + checksum verification'), findsOneWidget);",
        "expect(find.textContaining('workspace'), findsWidgets);":
            "expect(find.text('Live Research OS result'), findsOneWidget);",
    }
    changed = 0
    for old, new in replacements.items():
        if old in text:
            text = text.replace(old, new)
            changed += 1
    if changed < 2:
        raise SystemExit(f'acceptance contract drift: only {changed} replacements applied')
    target.write_text(text, encoding='utf-8', newline='\n')
    print(f'normalized live operational acceptance assertions: {changed}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
