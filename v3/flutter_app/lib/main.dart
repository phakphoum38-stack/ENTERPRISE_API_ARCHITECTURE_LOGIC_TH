import 'dart:async';
import 'dart:io';

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
  final rawUser = Platform.environment['RESEARCH_OS_V3_USER_ID'] ??
      Platform.environment['USERNAME'] ??
      Platform.environment['USER'] ??
      'local-user';
  final rawProfile =
      Platform.environment['RESEARCH_OS_V3_PROFILE_ID'] ?? 'default';

  final api = HttpV3Api(
    baseUrl: baseUrl,
    userId: _safeIdentifier(rawUser, fallbackPrefix: 'user'),
    profileId: _safeIdentifier(rawProfile, fallbackPrefix: 'profile'),
  );

  runApp(ResearchOSV3App(api: api));

  final proveInstalledChat =
      Platform.environment['RESEARCH_OS_V3_E2E_CHAT'] == '1';
  unawaited(
    StartupProbe(
      api,
      chatProbeMessage: proveInstalledChat
          ? 'Research OS V3 installed app end-to-end probe'
          : null,
    ).run(),
  );
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
