from __future__ import annotations

import argparse
from pathlib import Path

from self_repair_generated_dart import repair

# Acceptance tests prove that the generated single-shell Full Control Center
# uses live V3 APIs/tool bindings instead of the old placeholder pages.
TEST = r'''import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:research_os_v3_flutter/src/api/v3_api.dart';
import 'package:research_os_v3_flutter/src/research_os_v3_app.dart';

class FakeApi implements V3Api {
  @override
  Future<Map<String, dynamic>> health() async => {
        'status': 'ok', 'version': 'v3.1.0-full-10x10', 'maximum_scale': '10^10',
        'maximum_logical_capacity': 10000000000,
      };
  @override
  Future<Map<String, dynamic>> master({int tasks = 1, int risk = 1, int parallelism = 1}) async => {
        'scale': '6^3', 'system_maximum_scale': '10^10',
      };
  @override
  Future<Map<String, dynamic>> providers() async => {'providers': [
        {'name': 'mock', 'ready': true, 'connected': true, 'model': 'mock-model'}
      ]};
  @override
  Future<Map<String, dynamic>> user() async => {'user_id': 'owner', 'profile_id': 'default', 'isolated': true};
  @override
  Future<Map<String, dynamic>> skills() async => {'skills': [
        {'name': 'analysis', 'description': 'Analyze goals'},
        {'name': 'research', 'description': 'Research sources'},
        {'name': 'quality', 'description': 'Validate evidence'},
      ]};
  @override
  Future<Map<String, dynamic>> tools() async => {'tools': [
        {'name': 'echo', 'description': 'Echo', 'risk': 'read-only'},
        {'name': 'drive-tools-list', 'description': 'Discover tools', 'risk': 'read-only'},
        {'name': 'workspace-files-list', 'description': 'Files', 'risk': 'read-only'},
        {'name': 'research-shell', 'description': 'Diagnostics', 'risk': 'read-only'},
      ]};
  @override
  Future<Map<String, dynamic>> agents() async => {'agents': [
        {'name': 'architect', 'role': 'architecture', 'description': 'Architect'},
      ]};
  @override
  Future<Map<String, dynamic>> memory({String query = '', int limit = 20}) async => {'memory': <Map<String, dynamic>>[]};
  @override
  Future<Map<String, dynamic>> factoryPlan({int tasks = 1, int risk = 1, int parallelism = 1}) async => {
        'scale': '6^3', 'stage_order': ['master', 'factory', 'team', 'tests', 'release']
      };
  @override
  Future<Map<String, dynamic>> chat(String prompt, {String? agent, String? preferredProvider, int memoryLimit = 8}) async => {
        'text': 'answer:$prompt', 'provider': preferredProvider ?? 'mock', 'model': 'mock-model', 'memory_hits': []
      };
  @override
  Future<Map<String, dynamic>> addMemory(String text, {List<String> tags = const []}) async => {'memory': {'text': text}};
  @override
  Future<Map<String, dynamic>> runAgent(String name, String prompt) async => {'agent': name, 'text': prompt};
  @override
  Future<Map<String, dynamic>> executeTool(String name, Map<String, dynamic> arguments, {bool approved = false}) async {
    switch (name) {
      case 'workspace-files-list':
        return {'tool': name, 'result': {'root': r'G:\DRIVE_VIRTUAL_CLOUD', 'path': arguments['path'] ?? '', 'entries': [
          {'name': 'README.txt', 'path': 'README.txt', 'directory': false, 'size': 120}
        ]}};
      case 'workspace-repositories':
        return {'tool': name, 'result': {'repositories': [
          {'owner': 'owner', 'name': 'research-os', 'files': 232}
        ]}};
      case 'github-status':
        return {'tool': name, 'result': {'mode': 'local-mirror', 'repository_count': 1}};
      case 'drive-status':
        return {'tool': name, 'result': {'available': true, 'root': r'G:\DRIVE_VIRTUAL_CLOUD'}};
      case 'runtime-status':
        return {'tool': name, 'result': {'python': '3.12', 'service_process': true}};
      case 'installer-status':
        return {'tool': name, 'result': {'installed': true, 'build_sha': 'candidate'}};
      case 'backups-list':
        return {'tool': name, 'result': {'backups': [
          {'name': 'ResearchOS-backup.zip', 'size': 1048576, 'sha256': 'abcdef123456'}
        ]}};
      case 'research-shell':
        return {'tool': name, 'result': {'command': arguments['command'] ?? 'help', 'commands': ['help','workspace','drive','repos','backups','runtime','installer']}};
      case 'drive-tools-list':
        return {'tool': name, 'result': {'status': {'available': true}, 'packages': <Map<String, dynamic>>[]}};
      default:
        return {'tool': name, 'result': arguments, 'approved': approved};
    }
  }
}

void main() {
  testWidgets('self-built Full Control Center renders V3-backed shell and chat', (tester) async {
    await tester.binding.setSurfaceSize(const Size(1800, 1000));
    addTearDown(() => tester.binding.setSurfaceSize(null));
    await tester.pumpWidget(ResearchOSV3App(api: FakeApi()));
    await tester.pumpAndSettle();

    expect(find.text('Full Control Center'), findsWidgets);
    expect(find.text('Morning GUI · V3.1 single backend authority'), findsOneWidget);
    expect(find.text('Chat AI'), findsOneWidget);
    expect(find.text('Files'), findsWidgets);
    expect(find.text('Repositories'), findsWidgets);
    expect(find.text('Restore'), findsWidgets);
    expect(find.text('Shell'), findsWidgets);

    await tester.tap(find.text('Chat AI').first);
    await tester.pumpAndSettle();
    expect(find.text('AI Context'), findsOneWidget);
    expect(find.textContaining('Tool Discovery:'), findsOneWidget);

    final composer = find.widgetWithText(TextField, 'Message Research OS AI…');
    expect(composer, findsOneWidget);
    await tester.enterText(composer, 'hello self build');
    await tester.tap(find.text('Send'));
    await tester.pumpAndSettle();
    expect(find.text('answer:hello self build'), findsOneWidget);
  });

  testWidgets('workspace and system pages execute V3 tools instead of placeholders', (tester) async {
    await tester.binding.setSurfaceSize(const Size(1800, 1000));
    addTearDown(() => tester.binding.setSurfaceSize(null));
    await tester.pumpWidget(ResearchOSV3App(api: FakeApi()));
    await tester.pumpAndSettle();

    await tester.tap(find.text('Drive').first);
    await tester.pumpAndSettle();
    expect(find.text('drive-status'), findsOneWidget);
    expect(find.textContaining('DRIVE_VIRTUAL_CLOUD'), findsWidgets);
    expect(find.text('Tool Discovery & Governance'), findsOneWidget);

    await tester.tap(find.text('Installer').first);
    await tester.pumpAndSettle();
    expect(find.text('installer-status'), findsOneWidget);
    expect(find.textContaining('candidate'), findsWidgets);

    await tester.tap(find.text('Backup').first);
    await tester.pumpAndSettle();
    expect(find.text('backups-list'), findsOneWidget);
    expect(find.textContaining('ResearchOS-backup.zip'), findsWidgets);

    await tester.tap(find.text('Restore').first);
    await tester.pumpAndSettle();
    expect(find.text('backups-list'), findsOneWidget);
    expect(find.text('Owner Gate'), findsOneWidget);

    await tester.tap(find.text('Shell').first);
    await tester.pumpAndSettle();
    expect(find.text('research-shell'), findsOneWidget);
    expect(find.textContaining('workspace'), findsWidgets);
  });
}
'''


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--workspace', required=True)
    args = parser.parse_args()
    workspace = Path(args.workspace).resolve()
    app_target = workspace / 'v3' / 'flutter_app' / 'lib' / 'src' / 'research_os_v3_app.dart'
    repaired = repair(app_target)
    if repaired < 2:
        raise SystemExit('expected Research OS generated GUI to require strict style and layout repair')
    print(f'self-repaired generated GUI statements/layout: {repaired}')

    test_dir = workspace / 'v3' / 'flutter_app' / 'test'
    obsolete = test_dir / 'widget_test.dart'
    if obsolete.exists():
        obsolete.unlink()
        print(f'retired obsolete pre-morning GUI test: {obsolete}')

    target = test_dir / 'app_shell_test.dart'
    target.write_text(TEST, encoding='utf-8', newline='\n')
    print(target)
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
