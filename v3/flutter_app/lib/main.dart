import 'dart:async';

import 'package:flutter/widgets.dart';

import 'src/api/v3_api.dart';
import 'src/research_os_v3_app.dart';
import 'src/startup_probe.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();

  const baseUrl = String.fromEnvironment(
    'RESEARCH_OS_V3_BASE_URL',
    defaultValue: 'http://127.0.0.1:8788',
  );
  final api = HttpV3Api(baseUrl: baseUrl);

  runApp(ResearchOSV3App(api: api));

  // Paint first, then prove loopback connectivity independently of navigation.
  unawaited(StartupProbe(api).run());
}
