import 'package:flutter_test/flutter_test.dart';
import 'package:research_os_v3_flutter/src/api/v3_api.dart';
import 'package:research_os_v3_flutter/src/startup_probe.dart';

class FakeApi implements V3Api {
  int healthCalls = 0;
  int providerCalls = 0;

  @override
  Future<Map<String, dynamic>> health() async {
    healthCalls++;
    return {'status': 'ok', 'version': 'v3-clean'};
  }

  @override
  Future<Map<String, dynamic>> master({int tasks = 1}) async {
    return {
      'contract': 'unified-master-orchestrator-v3-clean',
      'scale': '1^3',
      'maximum_leaf_capacity': 1,
    };
  }

  @override
  Future<Map<String, dynamic>> providers() async {
    providerCalls++;
    return {
      'providers': [
        {
          'name': 'mock',
          'ready': true,
          'connected': true,
          'secret_exposed': false,
        },
      ],
    };
  }
}

void main() {
  test('startup probe proves health and provider routes', () async {
    final api = FakeApi();

    final connected = await StartupProbe(
      api,
      attempts: 1,
      retryDelay: Duration.zero,
    ).run();

    expect(connected, isTrue);
    expect(api.healthCalls, 1);
    expect(api.providerCalls, 1);
  });
}
