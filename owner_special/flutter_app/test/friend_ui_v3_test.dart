import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:research_os_owner_special/src/friend_ui_v3.dart';
import 'package:research_os_owner_special/src/owner_api.dart';

class FakeOwnerFriendApiV3 extends OwnerFriendApi {
  int? lastHelperBudget;
  List<String> lastRequestedSkills = const <String>[];

  @override
  Future<Map<String, dynamic>> health() async => <String, dynamic>{'status': 'ok'};

  @override
  Future<Map<String, dynamic>> status() async => <String, dynamic>{
        'brain_profiles': <String, int>{
          '1^3': 1,
          '3^3': 27,
          '6^3': 216,
          '6^6': 46656,
          'fast-1m': 1000000,
        },
        'helper_scheduler': <String, int>{
          'max_logical_helpers': 1000000,
          'max_active_workers': 128,
        },
        'capabilities': <String>['brain', 'skills', 'persistent-memory', 'factory'],
      };

  @override
  Future<Map<String, dynamic>> memory() async => <String, dynamic>{'count': 0, 'items': <Object>[]};

  @override
  Future<Map<String, dynamic>> providerStatus() async => <String, dynamic>{
        'enabled': false,
        'credential_present': false,
        'secret_backend': 'test',
        'base_url': '',
        'model': '',
      };

  @override
  Future<Map<String, dynamic>> configureProvider({required String baseUrl, required String model, String? apiKey}) async => <String, dynamic>{
        'enabled': true,
        'credential_present': true,
        'secret_backend': 'test',
        'base_url': baseUrl,
        'model': model,
      };

  @override
  Future<Map<String, dynamic>> testProvider() async => <String, dynamic>{'connected': true};

  @override
  Future<Map<String, dynamic>> chat(
    String text, {
    int complexity = 4,
    int risk = 2,
    int parallelism = 2,
    int helperBudget = 0,
    List<String> requestedSkills = const <String>[],
    List<String> requestedTools = const <String>[],
  }) async {
    lastHelperBudget = helperBudget;
    lastRequestedSkills = List<String>.from(requestedSkills);
    return <String, dynamic>{
      'text': 'friend-v3:$text',
      'provider': 'test-provider',
      'decision': <String, dynamic>{
        'scale': helperBudget >= 1000000 ? 'fast-1m' : '6^6',
        'capacity': helperBudget >= 1000000 ? 1000000 : 46656,
      },
      'helpers': <String, dynamic>{'active_workers': 128, 'batches': 7813},
      'factory': <String, dynamic>{
        'stages': <String>['master', 'factory', 'team', 'tests', 'release'],
      },
    };
  }
}

void main() {
  testWidgets('Friend UI V3 is the interactive desktop shell', (tester) async {
    final api = FakeOwnerFriendApiV3();
    await tester.pumpWidget(OwnerFriendAppV3(api: api));
    await tester.pumpAndSettle();

    expect(find.text('UI V3'), findsOneWidget);
    expect(find.text('วันนี้ให้ Research OS Friend ช่วยอะไร?'), findsOneWidget);

    await tester.enterText(find.byKey(const Key('friend-v3-input')), 'สวัสดีครับ');
    await tester.tap(find.byKey(const Key('friend-v3-send')));
    await tester.pumpAndSettle();

    expect(find.textContaining('friend-v3:สวัสดีครับ'), findsOneWidget);
    expect(find.text('Brain scale: fast-1m'), findsOneWidget);
    expect(api.lastHelperBudget, 1000000);
    expect(api.lastRequestedSkills, containsAll(<String>['analysis', 'planning', 'memory', 'quality']));
  });

  testWidgets('Friend UI V3 exposes the new plus menu', (tester) async {
    await tester.pumpWidget(OwnerFriendAppV3(api: FakeOwnerFriendApiV3()));
    await tester.pumpAndSettle();

    await tester.tap(find.byKey(const Key('friend-v3-tools-menu')));
    await tester.pumpAndSettle();

    expect(find.text('เพิ่มรูปภาพและไฟล์'), findsOneWidget);
    expect(find.text('เพิ่มจากคลัง'), findsOneWidget);
    expect(find.text('สร้างรูปภาพ'), findsOneWidget);
    expect(find.text('ค้นหาเว็บ'), findsOneWidget);
    expect(find.text('หาข้อมูลเชิงลึก'), findsOneWidget);
    expect(find.text('Google Calendar'), findsOneWidget);
  });
}
