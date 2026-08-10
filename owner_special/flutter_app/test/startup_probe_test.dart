import 'package:flutter_test/flutter_test.dart';
import 'package:research_os_owner_special/src/owner_api.dart';
import 'package:research_os_owner_special/src/startup_probe.dart';

class ProbeApi implements OwnerFriendApi {
  final List<String> calls = <String>[];

  @override
  Future<Map<String, dynamic>> health() async {
    calls.add('health');
    return <String, dynamic>{'status': 'ok'};
  }

  @override
  Future<Map<String, dynamic>> status() async {
    calls.add('status');
    return <String, dynamic>{'edition': 'owner-special'};
  }

  @override
  Future<Map<String, dynamic>> memory() async => <String, dynamic>{};

  @override
  Future<Map<String, dynamic>> chat(String text, {int complexity = 4, int risk = 2, int parallelism = 2, List<String> requestedSkills = const <String>[], List<String> requestedTools = const <String>[]}) async => <String, dynamic>{};
}

void main() {
  test('startup probe proves health and status', () async {
    final api = ProbeApi();
    final result = await OwnerStartupProbe(api).run();
    expect(api.calls, <String>['health', 'status']);
    expect((result['health'] as Map)['status'], 'ok');
  });
}
