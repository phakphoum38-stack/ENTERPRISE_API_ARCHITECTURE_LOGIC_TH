import 'dart:async';
import 'dart:io';

import 'package:flutter/widgets.dart';

import 'src/api/v3_api.dart';
import 'src/research_os_v3_app.dart';
import 'src/startup_probe.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();

  const compiledBaseUrl = String.fromEnvironment(
    'RESEARCH_OS_V3_BASE_URL',
    defaultValue: 'http://127.0.0.1:8788',
  );
  final environment = Platform.environment;
  final baseUrl = environment['RESEARCH_OS_V3_BASE_URL'] ?? compiledBaseUrl;
  final rawUser = environment['RESEARCH_OS_V3_USER'] ??
      environment['RESEARCH_OS_V3_USER_ID'] ??
      environment['USERNAME'] ??
      environment['USER'] ??
      'local-user';
  final rawProfile = environment['RESEARCH_OS_V3_PROFILE'] ??
      environment['RESEARCH_OS_V3_PROFILE_ID'] ??
      'default';

  final api = HttpV3Api(
    baseUrl: baseUrl,
    userId: _safeIdentifier(rawUser, fallbackPrefix: 'user'),
    profileId: _safeIdentifier(rawProfile, fallbackPrefix: 'profile'),
  );

  final proveInstalledChat = environment['RESEARCH_OS_V3_E2E_CHAT'] == '1';
  if (proveInstalledChat) {
    // CI-only installed-binary proof. Run it before creating the window so the
    // HTTP evidence is deterministic even on a non-interactive Windows runner.
    final connected = await StartupProbe(
      api,
      chatProbeMessage: 'installed-exe-e2e',
    ).run();
    if (!connected) {
      stderr.writeln(
        'Research OS V3 installed executable failed its end-to-end startup probe.',
      );
      exitCode = 2;
      return;
    }
  }

  runApp(ResearchOSV3App(api: api));

  if (!proveInstalledChat) {
    unawaited(StartupProbe(api).run());
  }
}

String _safeIdentifier(String raw, {required String fallbackPrefix}) {
  final candidate = raw.trim();
  final valid = RegExp(r'^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$');
  if (valid.hasMatch(candidate) && candidate != '.' && candidate != '..') {
    return candidate;
  }

  // FNV-1a is used only to create a deterministic, non-secret path-safe suffix.
  var hash = 0x811C9DC5;
  for (final unit in candidate.codeUnits) {
    hash ^= unit;
    hash = (hash * 0x01000193) & 0xFFFFFFFF;
  }
  final suffix = hash.toRadixString(16).padLeft(8, '0');
  return '$fallbackPrefix-$suffix';
}
