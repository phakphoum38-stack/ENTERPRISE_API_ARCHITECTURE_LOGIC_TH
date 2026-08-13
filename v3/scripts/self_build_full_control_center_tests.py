from __future__ import annotations

import argparse
from pathlib import Path

from self_repair_generated_dart import repair

# This acceptance stage intentionally invokes the strict generated-Dart repair
# before Flutter analysis so the self-built candidate must satisfy normal lints.
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
  Future<Map<String, dynamic>> executeTool(String name, Map<String, dynamic> arguments, {bool approved = false}) async => {'tool': name, 'result': arguments};
}

void main() {
  testWidgets('self-built morning Full Control Center renders V3-backed shell and chat', (tester) async {
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

  testWidgets('workspace and system destinations remain available', (tester) async {
    await tester.binding.setSurfaceSize(const Size(1800, 1000));
    addTearDown(() => tester.binding.setSurfaceSize(null));
    await tester.pumpWidget(ResearchOSV3App(api: FakeApi()));
    await tester.pumpAndSettle();

    await tester.tap(find.text('Drive').first);
    await tester.pumpAndSettle();
    expect(find.text('Google Drive is persistent storage/tool source; executable packages require checksum validation.'), findsOneWidget);
    expect(find.text('Tool Discovery Skills'), findsOneWidget);

    await tester.tap(find.text('Installer').first);
    await tester.pumpAndSettle();
    expect(find.text('Windows installer staging and validation remain release-gated.'), findsOneWidget);
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
    if repaired < 1:
        raise SystemExit('expected Research OS generated GUI to require at least one strict style repair')
    print(f'self-repaired generated GUI control-flow statements: {repaired}')
    target = workspace / 'v3' / 'flutter_app' / 'test' / 'app_shell_test.dart'
    target.write_text(TEST, encoding='utf-8', newline='\n')
    print(target)
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
