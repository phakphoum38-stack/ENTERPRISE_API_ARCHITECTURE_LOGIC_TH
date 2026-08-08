import 'package:flutter/foundation.dart';

enum ApiConnectionPhase { searching, connected, reconnecting, offline }

class ApiConnectionSnapshot {
  const ApiConnectionSnapshot({
    required this.phase,
    this.baseUrl,
    this.latency,
    this.source,
  });

  final ApiConnectionPhase phase;
  final String? baseUrl;
  final Duration? latency;
  final String? source;

  String get label => switch (phase) {
        ApiConnectionPhase.searching => 'Searching',
        ApiConnectionPhase.connected => 'Connected',
        ApiConnectionPhase.reconnecting => 'Reconnecting',
        ApiConnectionPhase.offline => 'Offline',
      };
}

final ValueNotifier<ApiConnectionSnapshot> apiConnectionState =
    ValueNotifier<ApiConnectionSnapshot>(
  const ApiConnectionSnapshot(phase: ApiConnectionPhase.searching),
);
