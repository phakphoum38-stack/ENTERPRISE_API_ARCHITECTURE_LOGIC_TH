import 'package:flutter_test/flutter_test.dart';
import 'package:research_os_v3_flutter/src/api/v3_api.dart';
import 'package:research_os_v3_flutter/src/research_os_v3_app.dart';

class _WidgetTestApi implements V3Api {
  @override
  Future<Map<String, dynamic>> health() async => {
        'status': 'ok',
        'version': 'v3-clean',
      };

  @override
  Future<Map<String, dynamic>> master({int tasks = 1}) async => {
        'contract': 'unified-master-orchestrator-v3-clean',
        'scale': '6^3',
        'maximum_leaf_capacity': 216,
      };

  @override
  Future<Map<String, dynamic>> providers() async => {
        'providers': [
          {
            'name': 'mock',
            'ready': true,
            'connected': true,
            'secret_exposed': false,
          },
        ],
      };

  @override
  Future<Map<String, dynamic>> user() async => {
        'user_id': 'alice',
        'profile_id': 'default',
        'scope': 'users/alice/profiles/default',
        'isolated': true,
      };
}

void main() {
  testWidgets('V3 Flutter project owns its generated widget test path',
      (tester) async {
    await tester.pumpWidget(ResearchOSV3App(api: _WidgetTestApi()));
    await tester.pumpAndSettle();

    expect(find.text('V3 Control Center'), findsOneWidget);
    expect(find.text('6^3'), findsOneWidget);
    expect(find.text('216'), findsOneWidget);
  });
}
