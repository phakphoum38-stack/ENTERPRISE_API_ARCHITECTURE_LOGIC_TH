import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:research_os_flutter/src/api/research_os_api_client.dart';
import 'package:research_os_flutter/src/app_shell.dart';

class BrainSkillsApiClient extends ResearchOSApiClient {
  BrainSkillsApiClient() : super(baseUrl: 'http://127.0.0.1:8787');

  @override
  Future<Map<String, dynamic>> getBrainCapacity() async => <String, dynamic>{
        'capacity': <String, dynamic>{
          'default_assistant_mode': 'assistant_6x3',
          'assistant_6x3_capacity': 216,
          'max_leaf_capacity': 46656,
          'max_active_workers': 36,
          'hard_active_worker_limit': 1296,
          'assistant_modes': <Map<String, dynamic>>[
            <String, dynamic>{
              'mode': 'assistant_6x3',
              'label': 'Adaptive 6^3 Assistant Crew',
              'theoretical_assistants': 216,
              'recommended_max_active_workers': 36,
            },
            <String, dynamic>{
              'mode': 'compound_6x6',
              'label': 'Adaptive 6^6 Compound Brain',
              'theoretical_assistants': 46656,
              'recommended_max_active_workers': 1296,
            },
          ],
        },
      };

  @override
  Future<Map<String, dynamic>> getBrainSkills() async => <String, dynamic>{
        'brain': <String, dynamic>{
          'skill_count': 2,
          'skills': <Map<String, dynamic>>[
            <String, dynamic>{
              'skill_id': 'planning',
              'name': 'Planning',
              'description': 'Break work into bounded steps.',
              'requires_approval_for_writes': false,
            },
            <String, dynamic>{
              'skill_id': 'safety',
              'name': 'Safety',
              'description': 'Apply approval and policy gates.',
              'requires_approval_for_writes': true,
            },
          ],
        },
      };

  @override
  Future<Map<String, dynamic>> getBrainProviders() async =>
      <String, dynamic>{
        'providers': <String, dynamic>{
          'openai-responses': <String, dynamic>{
            'configured': true,
            'credential_source': 'OPENAI_API_KEY',
            'secret_exposed': false,
          },
        },
      };

  @override
  void close() {}
}

void main() {
  testWidgets('Brain Skills tab shows 6^3, 6^6 and safe provider status',
      (tester) async {
    tester.view.physicalSize = const Size(1440, 1000);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    await tester.pumpWidget(
      MaterialApp(
        home: ResearchOSAppShell(apiClient: BrainSkillsApiClient()),
      ),
    );
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 100));

    final destination = find.byKey(const Key('desktop-nav-11'));
    await tester.ensureVisible(destination);
    await tester.tap(destination);
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 100));

    expect(find.byKey(const Key('brain-skills-page')), findsOneWidget);
    expect(find.text('Adaptive Brain 6³ → 6⁶'), findsOneWidget);
    expect(find.text('ผู้ช่วย 6³'), findsOneWidget);
    expect(find.text('สมองผสม 6⁶'), findsOneWidget);
    expect(find.text('Planning'), findsOneWidget);
    expect(find.text('Safety'), findsOneWidget);
    expect(find.textContaining('OPENAI_API_KEY'), findsOneWidget);
    expect(find.textContaining('secret hidden'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });
}
