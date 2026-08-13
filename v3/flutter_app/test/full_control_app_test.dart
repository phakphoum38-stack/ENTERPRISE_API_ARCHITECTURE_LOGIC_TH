import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:research_os_v3_flutter/src/api/v3_api.dart';
import 'package:research_os_v3_flutter/src/research_os_full_app.dart';

class FakeApi implements V3Api {
  final List<String> toolCalls = <String>[];

  @override
  Future<Map<String, dynamic>> health() async => <String, dynamic>{
        'status': 'ok',
        'version': 'v3.1.0-full-10x10',
        'maximum_scale': '10^10',
        'maximum_logical_capacity': 10000000000,
      };

  @override
  Future<Map<String, dynamic>> providers() async => <String, dynamic>{
        'providers': <Map<String, dynamic>>[
          <String, dynamic>{'name': 'mock', 'ready': true, 'connected': true, 'model': 'mock-model'},
        ],
      };

  @override
  Future<Map<String, dynamic>> master({int tasks = 1, int risk = 1, int parallelism = 1}) async => <String, dynamic>{
        'scale': '6^3',
        'system_maximum_scale': '10^10',
        'demand': <String, dynamic>{'tasks': tasks, 'risk': risk, 'parallelism': parallelism},
      };

  @override
  Future<Map<String, dynamic>> user() async => <String, dynamic>{'user_id': 'owner', 'profile_id': 'default', 'isolated': true};

  @override
  Future<Map<String, dynamic>> skills() async => <String, dynamic>{
        'skills': <Map<String, dynamic>>[
          <String, dynamic>{'name': 'analysis', 'description': 'Analyze goals', 'capability': 'reasoning'},
          <String, dynamic>{'name': 'research', 'description': 'Research sources', 'capability': 'knowledge'},
          <String, dynamic>{'name': 'quality', 'description': 'Validate evidence', 'capability': 'assurance'},
        ],
      };

  @override
  Future<Map<String, dynamic>> tools() async => <String, dynamic>{
        'tools': <Map<String, dynamic>>[
          <String, dynamic>{'name': 'workspace-files-list', 'description': 'List files', 'risk': 'read-only', 'approval_required': false},
          <String, dynamic>{'name': 'research-shell', 'description': 'Diagnostics', 'risk': 'read-only', 'approval_required': false},
          <String, dynamic>{'name': 'drive-tool-execute', 'description': 'Verified Drive tool', 'risk': 'write', 'approval_required': true},
        ],
      };

  @override
  Future<Map<String, dynamic>> agents() async => <String, dynamic>{
        'agents': <Map<String, dynamic>>[
          <String, dynamic>{'name': 'planner', 'role': 'planning', 'description': 'Planner Agent'},
          <String, dynamic>{'name': 'builder', 'role': 'building', 'description': 'Builder Agent'},
        ],
      };

  @override
  Future<Map<String, dynamic>> memory({String query = '', int limit = 20}) async => <String, dynamic>{
        'memory': <Map<String, dynamic>>[
          <String, dynamic>{'text': query.isEmpty ? 'Research OS memory' : 'match:$query', 'tags': <String>['test']},
        ],
      };

  @override
  Future<Map<String, dynamic>> factoryPlan({int tasks = 1, int risk = 1, int parallelism = 1}) async => <String, dynamic>{
        'scale': '6^3',
        'stage_order': <String>['master', 'factory', 'team', 'tests', 'release'],
        'tasks': tasks,
        'risk': risk,
        'parallelism': parallelism,
      };

  @override
  Future<Map<String, dynamic>> chat(String prompt, {String? agent, String? preferredProvider, int memoryLimit = 8}) async => <String, dynamic>{
        'text': 'answer:$prompt',
        'provider': preferredProvider ?? 'mock',
        'model': 'mock-model',
        'memory_hits': <dynamic>[],
      };

  @override
  Future<Map<String, dynamic>> addMemory(String text, {List<String> tags = const <String>[]}) async => <String, dynamic>{
        'memory': <String, dynamic>{'text': text, 'tags': tags},
      };

  @override
  Future<Map<String, dynamic>> runAgent(String name, String prompt) async => <String, dynamic>{'agent': name, 'text': 'agent:$prompt'};

  @override
  Future<Map<String, dynamic>> executeTool(String name, Map<String, dynamic> arguments, {bool approved = false}) async {
    toolCalls.add(name);
    switch (name) {
      case 'workspace-files-list':
        return <String, dynamic>{
          'tool': name,
          'result': <String, dynamic>{
            'root': r'G:\DRIVE_VIRTUAL_CLOUD',
            'path': arguments['path'] ?? '',
            'entries': <Map<String, dynamic>>[
              <String, dynamic>{'name': 'github', 'path': 'github', 'directory': true, 'size': 0},
              <String, dynamic>{'name': 'README.txt', 'path': 'README.txt', 'directory': false, 'size': 120},
            ],
          },
        };
      case 'workspace-file-read':
        return <String, dynamic>{'tool': name, 'result': <String, dynamic>{'path': arguments['path'], 'size': 120, 'sha256': 'abc123', 'text': 'Research OS file preview'}};
      case 'workspace-repositories':
        return <String, dynamic>{
          'tool': name,
          'result': <String, dynamic>{
            'repositories': <Map<String, dynamic>>[
              <String, dynamic>{
                'owner': 'phakphoum38-stack',
                'name': 'ENTERPRISE_API_ARCHITECTURE_LOGIC_TH',
                'path': 'github/repositories/phakphoum38-stack/ENTERPRISE_API_ARCHITECTURE_LOGIC_TH',
                'files': 232,
                'bundle': <String, dynamic>{'name': 'ENTERPRISE_API_ARCHITECTURE_LOGIC_TH.bundle', 'size': 123456, 'sha256': '1234567890abcdef'},
              },
            ],
          },
        };
      case 'github-status':
        return <String, dynamic>{'tool': name, 'result': <String, dynamic>{'mode': 'local-mirror', 'repository_count': 1, 'drive_ready': true}};
      case 'drive-status':
        return <String, dynamic>{'tool': name, 'result': <String, dynamic>{'configured': true, 'available': true, 'root': r'G:\DRIVE_VIRTUAL_CLOUD', 'directories': <String>['github', 'backup']}};
      case 'runtime-status':
        return <String, dynamic>{'tool': name, 'result': <String, dynamic>{'python': '3.12', 'service_process': true, 'pid': 1234}};
      case 'installer-status':
        return <String, dynamic>{'tool': name, 'result': <String, dynamic>{'installed': true, 'install_root': r'C:\Program Files\Research OS V3', 'build_sha': 'test-sha'}};
      case 'backups-list':
        return <String, dynamic>{
          'tool': name,
          'result': <String, dynamic>{
            'backups': <Map<String, dynamic>>[
              <String, dynamic>{'name': 'ResearchOS-test.zip', 'path': 'backup/restore_points/ResearchOS-test.zip', 'size': 1048576, 'sha256': 'abcdef1234567890'},
            ],
          },
        };
      case 'research-shell':
        return <String, dynamic>{'tool': name, 'result': <String, dynamic>{'command': arguments['command'] ?? 'help', 'commands': <String>['help', 'workspace', 'drive', 'repos', 'backups', 'runtime', 'installer']}};
      case 'drive-tools-list':
        return <String, dynamic>{'tool': name, 'result': <String, dynamic>{'status': <String, dynamic>{'available': true}, 'packages': <Map<String, dynamic>>[]}};
      default:
        return <String, dynamic>{'tool': name, 'result': arguments, 'approved': approved};
    }
  }
}

Future<void> pumpFull(WidgetTester tester, FakeApi api) async {
  await tester.binding.setSurfaceSize(const Size(1920, 1200));
  addTearDown(() => tester.binding.setSurfaceSize(null));
  await tester.pumpWidget(ResearchOSFullApp(api: api));
  await tester.pumpAndSettle();
}

void main() {
  testWidgets('single Full Control Center renders target navigation and live Chat AI', (tester) async {
    final api = FakeApi();
    await pumpFull(tester, api);

    expect(find.text('Research OS'), findsOneWidget);
    expect(find.text('Full Control Center'), findsWidgets);
    for (final label in <String>[
      'Home', 'Chat AI', 'Agents', 'Memory', 'Skills', 'Tools', 'Factory', 'Providers',
      'Files', 'Repositories', 'GitHub', 'Drive', 'Runtime', 'Installer', 'Backup', 'Restore', 'Shell',
    ]) {
      expect(find.text(label), findsWidgets, reason: 'missing navigation: $label');
    }
    expect(find.text('1. Intent Analysis'), findsOneWidget);
    expect(find.text('7. Result & Learn'), findsOneWidget);

    final composer = find.widgetWithText(TextField, 'Message Research OS AI…');
    expect(composer, findsOneWidget);
    await tester.enterText(composer, 'hello full research os');
    await tester.tap(find.text('Send'));
    await tester.pumpAndSettle();
    expect(find.text('answer:hello full research os'), findsOneWidget);
  });

  testWidgets('workspace pages call V3 tools instead of placeholders', (tester) async {
    final api = FakeApi();
    await pumpFull(tester, api);

    await tester.tap(find.text('Files').first);
    await tester.pumpAndSettle();
    expect(find.text('README.txt'), findsOneWidget);
    expect(api.toolCalls, contains('workspace-files-list'));
    await tester.tap(find.text('README.txt'));
    await tester.pumpAndSettle();
    expect(find.text('Research OS file preview'), findsOneWidget);
    await tester.tap(find.text('Close'));
    await tester.pumpAndSettle();

    await tester.tap(find.text('Repositories').first);
    await tester.pumpAndSettle();
    expect(find.text('phakphoum38-stack/ENTERPRISE_API_ARCHITECTURE_LOGIC_TH'), findsOneWidget);
    expect(api.toolCalls, contains('workspace-repositories'));

    await tester.tap(find.text('GitHub').first);
    await tester.pumpAndSettle();
    expect(find.textContaining('local-mirror'), findsOneWidget);
    expect(api.toolCalls, contains('github-status'));

    await tester.tap(find.text('Drive').first);
    await tester.pumpAndSettle();
    expect(find.textContaining('DRIVE_VIRTUAL_CLOUD'), findsWidgets);
    expect(api.toolCalls, contains('drive-status'));
  });

  testWidgets('system pages are tool-backed and shell is bounded', (tester) async {
    final api = FakeApi();
    await pumpFull(tester, api);

    await tester.tap(find.text('Runtime').first);
    await tester.pumpAndSettle();
    expect(find.textContaining('3.12'), findsOneWidget);
    expect(api.toolCalls, contains('runtime-status'));

    await tester.tap(find.text('Installer').first);
    await tester.pumpAndSettle();
    expect(find.textContaining('Program Files'), findsOneWidget);
    expect(api.toolCalls, contains('installer-status'));

    await tester.tap(find.text('Backup').first);
    await tester.pumpAndSettle();
    expect(find.text('ResearchOS-test.zip'), findsOneWidget);
    expect(api.toolCalls, contains('backups-list'));

    await tester.tap(find.text('Restore').first);
    await tester.pumpAndSettle();
    expect(find.text('ResearchOS-test.zip'), findsOneWidget);

    await tester.tap(find.text('Shell').first);
    await tester.pumpAndSettle();
    expect(find.textContaining('arbitrary OS shell is disabled'), findsOneWidget);
    await tester.tap(find.text('Run Command'));
    await tester.pumpAndSettle();
    expect(find.textContaining('workspace'), findsOneWidget);
    expect(api.toolCalls, contains('research-shell'));
  });
}
