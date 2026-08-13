from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import zipfile
from collections import defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path, PurePosixPath


SOURCE_EXTENSIONS = {
    '.py', '.pyi', '.dart', '.ps1', '.psm1', '.psd1', '.cs', '.csproj', '.sln',
    '.js', '.mjs', '.cjs', '.ts', '.tsx', '.jsx', '.html', '.htm', '.css', '.scss',
    '.sh', '.bash', '.zsh', '.bat', '.cmd', '.yml', '.yaml', '.json', '.toml', '.ini',
    '.cfg', '.conf', '.xml', '.plist', '.gradle', '.kts', '.swift', '.m', '.mm', '.h',
    '.hpp', '.c', '.cc', '.cpp', '.rs', '.go', '.java', '.kt', '.md', '.rst', '.txt',
    '.iss', '.lock', '.properties', '.xcconfig', '.entitlements', '.pbxproj', '.xcworkspacedata',
    '.png', '.jpg', '.jpeg', '.gif', '.webp', '.ico', '.icns', '.svg',
}

EXTENSIONLESS = {'Dockerfile', 'Makefile', 'Procfile', 'Gemfile', 'Rakefile', 'Podfile', 'LICENSE', 'NOTICE'}
FONT_EXTENSIONS = {'.ttf', '.otf', '.woff', '.woff2', '.eot'}
EXCLUDED_PARTS = {
    '.git', '.dart_tool', '.idea', '.pytest_cache', '.mypy_cache', '.ruff_cache', '__pycache__',
    'node_modules', '.venv', 'venv', 'env', 'build', 'dist', 'out', 'coverage', 'DerivedData',
    'Pods', '.gradle', '.pub-cache', '.packages', 'cache', 'temp', 'tmp',
}
EXCLUDED_PREFIXES = (
    'v3/installer/output/', 'v3/installer/package/runtime/python/', 'artifacts/', 'logs/',
    'releases/', 'release/', 'backup/', 'tools/build_unified_source.py', 'tools/build_unified_source_v2.py',
    '.github/workflows/unified-source-archive.yml',
)
SECRET_PATH_RE = re.compile(
    r'(^|/)(\.env($|\.)|.*\.(pem|pfx|p12|key|keystore|jks)$|credentials?($|[._-])|secrets?($|[._-]))',
    re.IGNORECASE,
)
SECRET_PATTERNS = [
    re.compile(rb'\bsk-(?:proj-)?[A-Za-z0-9_-]{20,}\b'),
    re.compile(rb'\bgh[pousr]_[A-Za-z0-9]{20,}\b'),
    re.compile(rb'AIza[0-9A-Za-z_-]{30,}'),
    re.compile(rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----'),
]

SNAPSHOT_PATTERNS = [
    re.compile(r'^versions/[^/]+/(.+)$'),
    re.compile(r'^current/(.+)$'),
]
CI_VERSION_RE = re.compile(r'^ci/research-os-v[^/]+/(.+)$', re.IGNORECASE)


@dataclass
class Candidate:
    logical_path: str
    original_path: str
    commit: str
    blob: str
    timestamp: int


@dataclass
class Retained:
    path: str
    original_path: str
    commit: str
    blob: str
    sha256: str
    size: int


def run(*args: str, check: bool = True, binary: bool = False):
    return subprocess.run(
        args,
        check=check,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=not binary,
    )


def git(*args: str, check: bool = True) -> str:
    return run('git', *args, check=check).stdout


def git_bytes(*args: str) -> bytes:
    return run('git', *args, binary=True).stdout


def norm(path: str) -> str:
    return str(PurePosixPath(path.replace('\\', '/')))


def logical_path(path: str) -> tuple[str, str | None]:
    p = norm(path)
    for pattern in SNAPSHOT_PATTERNS:
        m = pattern.match(p)
        if m:
            return norm(m.group(1)), 'version/current snapshot collapsed'
    m = CI_VERSION_RE.match(p)
    if m:
        return norm('apps/research_os_flutter/' + m.group(1)), 'versioned Flutter CI snapshot collapsed'
    return p, None


def excluded(path: str) -> tuple[bool, str]:
    p = norm(path)
    pure = PurePosixPath(p)
    if set(pure.parts) & EXCLUDED_PARTS:
        return True, 'generated/cache/dependency directory'
    if any(p.startswith(prefix) for prefix in EXCLUDED_PREFIXES):
        return True, 'generated/archive-tool/output path'
    if SECRET_PATH_RE.search(p):
        return True, 'secret-bearing path'
    if pure.suffix.lower() in FONT_EXTENSIONS:
        return True, 'font binary excluded'
    if pure.name.lower() in {'thumbs.db', '.ds_store'}:
        return True, 'OS metadata'
    return False, ''


def is_source(path: str) -> tuple[bool, str]:
    yes, reason = excluded(path)
    if yes:
        return False, reason
    pure = PurePosixPath(path)
    if pure.suffix.lower() in SOURCE_EXTENSIONS:
        return True, ''
    if pure.name in EXTENSIONLESS:
        return True, ''
    if pure.name in {'.gitignore', '.gitattributes', '.editorconfig'}:
        return True, ''
    return False, 'non-source/non-required asset'


def has_secret(data: bytes) -> bool:
    return any(p.search(data) for p in SECRET_PATTERNS)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def list_tree(commit: str):
    for line in git('ls-tree', '-r', '--full-tree', commit).splitlines():
        if not line:
            continue
        meta, path = line.split('\t', 1)
        mode, obj_type, blob = meta.split(' ', 2)
        if obj_type == 'blob':
            yield norm(path), blob, mode


def all_paths() -> list[str]:
    out = git('log', '--all', '--name-only', '--pretty=format:')
    return sorted({norm(x.strip()) for x in out.splitlines() if x.strip()})


def latest_revision(path: str) -> Candidate | None:
    for commit in git('log', '--all', '--format=%H', '--', path).splitlines():
        if not commit:
            continue
        cp = run('git', 'cat-file', '-e', f'{commit}:{path}', check=False)
        if cp.returncode != 0:
            continue
        blob = git('rev-parse', f'{commit}:{path}').strip()
        ts = int(git('show', '-s', '--format=%ct', commit).strip())
        lp, _ = logical_path(path)
        return Candidate(lp, path, commit, blob, ts)
    return None


def branch_rows():
    out = git(
        'for-each-ref',
        '--format=%(refname:short)|%(objectname)|%(committerdate:iso8601-strict)|%(subject)',
        'refs/remotes/origin/',
    )
    rows = []
    for line in out.splitlines():
        if not line or line.startswith('origin/HEAD'):
            continue
        name, commit, date, subject = line.split('|', 3)
        rows.append({'branch': name.removeprefix('origin/'), 'sha': commit, 'date': date, 'subject': subject})
    rows.sort(key=lambda x: (x['date'], x['branch']))
    return rows


def first_commit():
    commit = git('rev-list', '--all', '--reverse').splitlines()[0]
    sha_, date, subject = git('show', '-s', '--format=%H|%aI|%s', commit).strip().split('|', 2)
    return {'sha': sha_, 'date': date, 'subject': subject}


def copy_canonical(project: Path, target: str):
    hashes: dict[str, list[str]] = defaultdict(list)
    active_paths: set[str] = set()
    files = []
    excluded_rows = []
    collapsed_rows = []

    for original, blob, mode in list_tree(target):
        lp, collapsed_reason = logical_path(original)
        if collapsed_reason:
            collapsed_rows.append({'path': original, 'logical_path': lp, 'reason': collapsed_reason, 'source_commit': target})
            continue
        keep, reason = is_source(original)
        if not keep:
            excluded_rows.append({'path': original, 'reason': reason, 'source_commit': target})
            continue
        data = git_bytes('show', f'{target}:{original}')
        if has_secret(data):
            excluded_rows.append({'path': original, 'reason': 'secret pattern detected', 'source_commit': target})
            continue
        digest = sha(data)
        dest = project / lp
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
        if mode == '100755':
            dest.chmod(dest.stat().st_mode | 0o111)
        active_paths.add(lp)
        hashes[digest].append(lp)
        files.append({'path': lp, 'source_path': original, 'blob': blob, 'sha256': digest, 'bytes': len(data)})

    return active_paths, hashes, files, excluded_rows, collapsed_rows


def recover(project: Path, active_paths: set[str], hashes: dict[str, list[str]]):
    grouped: dict[str, Candidate] = {}
    superseded = []
    excluded_rows = []
    collapsed_candidates = []

    for original in all_paths():
        keep, reason = is_source(original)
        if not keep:
            excluded_rows.append({'path': original, 'reason': reason, 'source_commit': None})
            continue
        candidate = latest_revision(original)
        if candidate is None:
            continue
        lp, collapse_reason = logical_path(original)
        if lp in active_paths:
            superseded.append({
                'original_path': original,
                'logical_path': lp,
                'source_commit': candidate.commit,
                'reason': 'logical path already exists in canonical latest tree',
            })
            continue
        if collapse_reason:
            collapsed_candidates.append({
                'original_path': original,
                'logical_path': lp,
                'source_commit': candidate.commit,
                'reason': collapse_reason,
            })
        previous = grouped.get(lp)
        if previous is None or candidate.timestamp > previous.timestamp:
            grouped[lp] = candidate

    retained: list[Retained] = []
    duplicate_content = []
    seen: dict[str, str] = {}

    for lp, candidate in sorted(grouped.items()):
        data = git_bytes('show', f'{candidate.commit}:{candidate.original_path}')
        if has_secret(data):
            excluded_rows.append({'path': candidate.original_path, 'reason': 'secret pattern detected', 'source_commit': candidate.commit})
            continue
        digest = sha(data)
        if digest in hashes:
            duplicate_content.append({
                'original_path': candidate.original_path,
                'logical_path': lp,
                'source_commit': candidate.commit,
                'matches_path': hashes[digest][0],
                'sha256': digest,
            })
            continue
        if digest in seen:
            duplicate_content.append({
                'original_path': candidate.original_path,
                'logical_path': lp,
                'source_commit': candidate.commit,
                'matches_path': seen[digest],
                'sha256': digest,
            })
            continue
        out_path = f'retained_legacy/{lp}'
        dest = project / out_path
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
        hashes[digest].append(out_path)
        seen[digest] = out_path
        retained.append(Retained(out_path, candidate.original_path, candidate.commit, candidate.blob, digest, len(data)))

    return retained, duplicate_content, superseded, excluded_rows, collapsed_candidates


def duplicate_groups(hashes: dict[str, list[str]]):
    return [{'sha256': h, 'paths': paths} for h, paths in sorted(hashes.items()) if len(paths) > 1]


def write_reports(project: Path, target: str, active_files, retained, dup_content, superseded, excluded_rows, collapsed_rows, collapsed_candidates, hashes):
    branches = branch_rows()
    manifest = {
        'schema': 'research-os.unified-source.v2',
        'repository': os.environ.get('GITHUB_REPOSITORY', 'phakphoum38-stack/ENTERPRISE_API_ARCHITECTURE_LOGIC_TH'),
        'canonical_target_sha': target,
        'first_reachable_commit': first_commit(),
        'reachable_commit_count': int(git('rev-list', '--count', '--all').strip()),
        'branch_count': len(branches),
        'branches': branches,
        'policy': {
            'one_active_tree': True,
            'version_snapshot_roots_collapsed': ['versions/<version>/', 'current/', 'ci/research-os-v<version>/ -> apps/research_os_flutter/'],
            'logical_path_rule': 'If a historical/versioned path maps to a canonical latest path, the latest canonical file wins and the older copy is not duplicated.',
            'retired_unique_rule': 'Only the newest recoverable file for a logical path missing from the canonical tree is retained once under retained_legacy/.',
            'content_rule': 'Retired source with SHA-256 already present is skipped.',
            'safety': 'Build/cache/dependencies, detected secrets/private keys/credential paths, and font binaries are excluded.',
        },
        'counts': {
            'canonical_files': len(active_files),
            'retained_historical_unique_files': len(retained),
            'logical_historical_copies_superseded': len(superseded),
            'content_duplicates_skipped': len(dup_content),
            'snapshot_records_collapsed': len(collapsed_rows) + len(collapsed_candidates),
            'excluded_records': len(excluded_rows),
            'exact_duplicate_groups_final': len(duplicate_groups(hashes)),
        },
        'canonical_files': active_files,
        'retained_historical_unique_files': [asdict(x) for x in retained],
        'logical_historical_copies_superseded': superseded,
        'content_duplicates_skipped': dup_content,
        'snapshot_records_collapsed': collapsed_rows + collapsed_candidates,
        'excluded': excluded_rows,
        'exact_duplicate_groups_final': duplicate_groups(hashes),
    }
    (project / 'SOURCE_HISTORY_MANIFEST.json').write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')

    lines = [
        '# Research OS Unified Source — No-Duplicate Report', '',
        f"Canonical target SHA: `{target}`", '',
        f"- Reachable commits inspected: **{manifest['reachable_commit_count']}**",
        f"- Remote branches inspected: **{manifest['branch_count']}**",
        f"- Canonical active files: **{len(active_files)}**",
        f"- Historical unique logical files retained: **{len(retained)}**",
        f"- Historical/version copies superseded by canonical logical paths: **{len(superseded)}**",
        f"- Content-identical retired files skipped: **{len(dup_content)}**",
        f"- Version/current/CI snapshot records collapsed: **{manifest['counts']['snapshot_records_collapsed']}**",
        f"- Exact duplicate groups in final unified archive: **{manifest['counts']['exact_duplicate_groups_final']}**",
        '',
        '## Structure', '',
        'The project root is the latest active source tree. There are no side-by-side v1/v2/v3 project copies.',
        '`versions/<version>/`, `current/`, and `ci/research-os-v<version>/` are treated as historical snapshots and collapsed to logical paths.',
        'Source that disappeared from the latest tree and has no canonical logical replacement is retained once under `retained_legacy/`.',
        '',
        '## Retained historical unique source', '',
    ]
    if retained:
        lines += [f"- `{x.path}` ← `{x.original_path}` @ `{x.commit[:12]}`" for x in retained]
    else:
        lines.append('- None')
    (project / 'DEDUP_REPORT.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')

    version = [
        '# Version / Branch Provenance', '',
        'No Git tags existed at build time. Full reachable commit and branch provenance was inspected.', '',
        '| Date | Branch | SHA | Subject |', '|---|---|---|---|',
    ]
    for row in branches:
        version.append(f"| {row['date']} | `{row['branch']}` | `{row['sha'][:12]}` | {row['subject'].replace('|', '\\|')} |")
    (project / 'VERSION_PROVENANCE.md').write_text('\n'.join(version) + '\n', encoding='utf-8')

    (project / 'UNIFIED_SOURCE_README.md').write_text(
        f"""# Research OS Unified Source\n\nSingle-project source consolidated from the repository history, from the first reachable commit through canonical target `{target}`.\n\n- The project root is the latest active source.\n- Version snapshots are collapsed rather than copied as separate projects.\n- Removed-but-still-unique logical source is retained once under `retained_legacy/`.\n- Build/cache/dependency output, detected credentials/private keys, and font binaries are excluded.\n\nSee `SOURCE_HISTORY_MANIFEST.json`, `DEDUP_REPORT.md`, and `VERSION_PROVENANCE.md`.\n""",
        encoding='utf-8',
    )
    return manifest


def zip_tree(project: Path, output: Path):
    with zipfile.ZipFile(output, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for path in sorted(project.rglob('*')):
            if path.is_file():
                zf.write(path, (Path(project.name) / path.relative_to(project)).as_posix())


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--target', default=os.environ.get('TARGET_SHA', 'HEAD'))
    ap.add_argument('--output-dir', default='unified-source-output-v2')
    ap.add_argument('--name', default='Research_OS_UNIFIED_SOURCE_FIRST_to_V3.1_NO_DUP')
    args = ap.parse_args()

    target = git('rev-parse', args.target).strip()
    out = Path(args.output_dir).resolve()
    project = out / args.name
    if out.exists():
        shutil.rmtree(out)
    project.mkdir(parents=True)

    active_paths, hashes, active_files, excluded_current, collapsed_current = copy_canonical(project, target)
    retained, dup_content, superseded, excluded_history, collapsed_history = recover(project, active_paths, hashes)
    manifest = write_reports(
        project, target, active_files, retained, dup_content, superseded,
        excluded_current + excluded_history, collapsed_current, collapsed_history, hashes,
    )

    zpath = out / f'{args.name}_{target[:12]}.zip'
    zip_tree(project, zpath)
    digest = hashlib.sha256(zpath.read_bytes()).hexdigest()
    (out / f'{zpath.name}.sha256').write_text(f'{digest}  {zpath.name}\n', encoding='ascii')
    summary = {
        'target_sha': target,
        'zip': str(zpath),
        'zip_sha256': digest,
        'zip_bytes': zpath.stat().st_size,
        **manifest['counts'],
        'branches': manifest['branch_count'],
        'commits': manifest['reachable_commit_count'],
        'first_commit': manifest['first_reachable_commit'],
    }
    (out / 'BUILD_SUMMARY.json').write_text(json.dumps(summary, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
