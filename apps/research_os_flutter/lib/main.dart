import 'package:flutter/material.dart';

import 'src/api/local_service_startup_probe.dart';
import 'src/research_os_app.dart';

Future<void> main() async {
  // Keep app-to-service proof independent from the desktop window lifecycle.
  // This makes the installed binary itself perform /health and /v1/providers
  // before Flutter creates a GUI window, which is deterministic on Windows CI
  // runners while remaining best-effort for normal local-first startup.
  await LocalServiceStartupProbe.run(
    attempts: 12,
    retryDelay: const Duration(milliseconds: 500),
    requestTimeout: const Duration(seconds: 1),
  );

  runApp(const ResearchOSApp());
}
