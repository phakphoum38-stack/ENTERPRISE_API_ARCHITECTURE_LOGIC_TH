import 'dart:async';

import 'package:flutter/material.dart';

import 'src/api/local_service_startup_probe.dart';
import 'src/research_os_app.dart';

void main() {
  // Warm the local-first service as soon as the installed Flutter binary starts.
  // The probe retries /health and /v1/providers while the Windows service is
  // becoming ready, and remains best-effort so UI startup is never blocked.
  unawaited(LocalServiceStartupProbe.run());
  runApp(const ResearchOSApp());
}
