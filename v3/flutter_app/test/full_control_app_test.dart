import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:research_os_v3_flutter/src/api/v3_api.dart';
import 'package:research_os_v3_flutter/src/research_os_v3_app.dart';

class FullControlFakeApi implements V3Api {
  final List<String> toolCalls = <String>[];

  @override
  Future<Map<String, dynamic>> health() async => {
        'status': 'ok',
        'version': 'v3-full-10x10',
        'maximum_scale': '10^10',
        'maximum_logical_capacity': 10000000000,
      };

  @override
  Future<Map<String, dynamic>> providers() async => {
        'providers': [
          {'name': 'mock', 'ready': true, 'connected': true, 'model': 'mock-model', 'secret_exposed': false},
        ],
      };

  @override
  Future<Map<String, dynamic>> master({int tasks = 1, int risk = 1, int parallelism = 1}) async => {
        'contract': 'unified-master-orchestrator-v3-full',
        'scale': '6^3',
        'maximum_leaf_capacity': 216,
        'system_maximum_scale': '10^10',
      };

  @override
  Future<Map<String, dynamic>> user() async => {
        'user_id': 'owner',
        'profile_id': 'default',
        'scope': 'users/owner/profiles/default',
        'isolated': true,
      };

  @override
  Future<Map<String, dynamic>> skills() async => {
        'skills': [
          {'name': 'analysis', 'description': 'Analyze intent'},
          {'name': 'research', 'description': 'Research tools'},
          {'name': 'quality', 'description': 'Validate evidence'},
        ],
      };

  @override
  Future<Map<String, dynamic>> tools() async => {
        'tools': [
          {'name': 'workspace-files-list', 'description': 'Browse Drive', 'risk': 'read-only', 'approval_required': false},
          {'name': 'research-shell', 'description': 'Bounded diagnostics', 'risk': 'read-only', 'approval_required': false},
        ],
      };

  @override
  Future<Map<String, dynamic>> agents() async => {
        'agents': [
          {'name': 'planner', 'role': 'planning', 'description': 'Planner'},
        ],
      };

  @override
  Future<Map<String, dynamic>> memory({String query = '', int limit = 20}) async => {
        'memory': <Map<String, dynamic>>[],
      };

  @override
  Future<Map<String, dynamic>> factoryPlan({int tasks = 1, int risk = 1, int parallelism = 1}) async => {
        'scale': '6^3',
        'stage_order': ['master', 'factory', 'team', 'tests', 'release'],
      };

  @override
  Future<Map<String, dynamic>> chat(String prompt, {String? agent, String? preferredProvider, int memoryLimit = 8}) async => {
        'text': 'answer:$prompt',
        'provider': preferredProvider ?? 'mock',
        'model': 'mock-model',
        'memory_hits': [],
      };

  @override
  Future<Map<String, dynamic>> addMemory(String text, {List<String> tags = const []}) async => {
        'memory': {'text': text, 'tags': tags},
      };

  @override
  Future<Map<String, dynamic>> runAgent(String name, String prompt) async => {
        'agent': name,
        'text': prompt,
      };

  @override
  Future<Map<String, dynamic>> executeTool(String name, Map<String, dynamic> arguments, {bool approved = false}) async {
    toolCalls.add(name);
    switch (name) {
      case 'workspace-files-list':
        return {
          'tool': name,
          'result': {
            'root': r'G:\DRIVE_VIRTUAL_CLOUD',
            'path': arguments['path'] ?? '',
            'entries': [
              {'name': 'github', 'path': 'github', 'directory': true, 'size': 0},
              {'name': 'README.txt', 'path': 'README.txt', 'directory': false, 'size': 120},
            ],
          },
        };
      case 'workspace-repositories':
        return {
          'tool': name,
          'result': {
            'repositories': [
              {'owner': 'phakphoum38-stack', 'name': 'ENTERPRISE_API_ARCHITECTURE_LOGIC_TH', 'files': 232},
            ],
          },
        };
      case 'github-status':
        return {'tool': name, 'result': {'mode': 'local-mirror', 'repository_count': 1}};
      case 'drive-status':
        return {'tool': name, 'result': {'available': true, 'root': r'G:\DRIVE_VIRTUAL_CLOUD'}};
      case 'runtime-status':
        return {'tool': name, 'result': {'python': '3.12', 'service_process': true}};
      case 'installer-status':
        return {'tool': name, 'result': {'installed': true, 'build_sha': 'candidate'}};
      case 'backups-list':
        return {
          'tool': name,
          'result': {
            'backups': [
              {'name': 'ResearchOS-backup.zip', 'size': 1048576, 'sha256': 'abcdef123456'},
            ],
          },
        };
      case 'research-shell':
        return {
          'tool': name,
          'result': {
            'command': arguments['command'] ?? 'help',
            'commands': ['help', 'workspace', 'drive', 'repos', 'backups', 'runtime', 'installer'],
          },
        };
      default:
        return {'tool': name, 'result': arguments, 'approved': approved};
    }
  }
}

Future<void> pumpFullControl(WidgetTester tester, FullControlFakeApi api) async {
  await tester.binding.setSurfaceSize(const Size(1920, 1200));
  addTearDown(() => tester.binding.setSurfaceSize(null));
  await tester.pumpWidget(ResearchOSV3App(api: api));
  await tester.pumpAndSettle();
}

void main() {
  testWidgets('canonical Full Control Center exposes all Research OS pages', (tester) async {
    final api = FullControlFakeApi();
    await pumpFullControl(tester, api);

    expect(find.text('Full Control Center'), findsWidgets);
    for (final label in [
      'Home', 'Chat AI', 'Agents', 'Memory', 'Skills', 'Tools', 'Factory', 'Providers',
      'Files', 'Repositories', 'GitHub', 'Drive', 'Runtime', 'Installer', 'Backup', 'Restore', 'Shell',
    ]) {
      expect(find.text(label), findsWidgets, reason: 'missing page $label');
    }
  });

  testWidgets('operational pages execute their V3 tools instead of placeholders', (tester) async {
    final api = FullControlFakeApi();
    await pumpFullControl(tester, api);

    await tester.tap(find.text('Files').first);
    await tester.pumpAndSettle();
    expect(find.textContaining('README.txt'), findsWidgets);
    expect(api.toolCalls, contains('workspace-files-list'));

    await tester.tap(find.text('Repositories').first);
    await tester.pumpAndSettle();
    expect(find.textContaining('ENTERPRISE_API_ARCHITECTURE_LOGIC_TH'), findsWidgets);
    expect(api.toolCalls, contains('workspace-repositories'));

    await tester.tap(find.text('Drive').first);
    await tester.pumpAndSettle();
    expect(find.textContaining('DRIVE_VIRTUAL_CLOUD'), findsWidgets);
    expect(api.toolCalls, contains('drive-status'));

    await tester.tap(find.text('Shell').first);
    await tester.pumpAndSettle();
    expect(find.textContaining('workspace'), findsWidgets);
    expect(api.toolCalls, contains('research-shell'));
  });
}
