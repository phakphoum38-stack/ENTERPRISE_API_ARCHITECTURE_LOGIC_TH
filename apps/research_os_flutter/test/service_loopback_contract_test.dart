import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

void main() {
  test('Windows service contract binds the local API to loopback', () {
    final serviceScript = File('../../scripts/research-os-service.ps1');
    final serviceHost = File('../../tools/research_os_service/Program.cs');

    expect(serviceScript.existsSync(), isTrue);
    expect(serviceHost.existsSync(), isTrue);

    final script = serviceScript.readAsStringSync();
    final host = serviceHost.readAsStringSync();

    expect(script, contains('RESEARCH_OS_API_HOST=127.0.0.1'));
    expect(host, contains('?? "127.0.0.1"'));
    expect(script, isNot(contains('RESEARCH_OS_API_HOST=0.0.0.0')));
  });
}
