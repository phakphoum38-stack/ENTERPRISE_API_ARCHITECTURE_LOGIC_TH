import 'dart:async';
import 'dart:convert';

import 'package:http/http.dart' as http;

import 'api_auto_discovery_stub.dart'
    if (dart.library.io) 'api_auto_discovery_io.dart' as platform;
import 'api_endpoint_store.dart';

class ApiDiscoveryResult {
  const ApiDiscoveryResult({
    required this.baseUrl,
    required this.latency,
    required this.source,
  });

  final String baseUrl;
  final Duration latency;
  final String source;
}

class ApiAutoDiscovery {
  ApiAutoDiscovery._();

  static const int defaultPort = 8787;
  static const Duration probeTimeout = Duration(milliseconds: 1100);
  static const int _batchSize = 48;

  static Future<ApiDiscoveryResult?> discover({
    String? preferredUrl,
    bool scanLan = true,
  }) async {
    final preferred = preferredUrl?.trim();
    if (preferred != null && preferred.isNotEmpty) {
      final hit = await probe(preferred, source: 'saved');
      if (hit != null) return hit;
    }

    final standard = <String>{
      ApiEndpointStore.buildDefault,
      'http://localhost:$defaultPort',
      'http://[::1]:$defaultPort',
      'http://10.0.2.2:$defaultPort',
      'http://10.0.3.2:$defaultPort',
      ApiEndpointStore.renderDefault,
    }
      ..add(ApiEndpointStore.localDefault)
      ..removeWhere((value) => preferred != null && value == preferred);

    final standardHit = await _fastestHealthy(
      standard.toList(growable: false),
      source: 'standard',
    );
    if (standardHit != null) return standardHit;

    if (!scanLan) return null;
    final lan = await platform.lanCandidates(port: defaultPort);
    return _fastestHealthy(lan, source: 'lan');
  }

  static Future<ApiDiscoveryResult?> probe(
    String value, {
    String source = 'manual',
  }) async {
    String baseUrl;
    try {
      baseUrl = ApiEndpointStore.normalize(value);
    } on FormatException {
      return null;
    }

    final client = http.Client();
    final watch = Stopwatch()..start();
    try {
      final response = await client
          .get(Uri.parse('$baseUrl/health'))
          .timeout(probeTimeout);
      watch.stop();
      if (response.statusCode < 200 || response.statusCode >= 300) return null;
      final decoded = jsonDecode(response.body);
      if (decoded is! Map<String, dynamic>) return null;
      final status = decoded['status']?.toString().toLowerCase();
      if (status != null &&
          status.isNotEmpty &&
          status != 'ok' &&
          status != 'ready' &&
          status != 'healthy') {
        return null;
      }
      return ApiDiscoveryResult(
        baseUrl: baseUrl,
        latency: watch.elapsed,
        source: source,
      );
    } on Object {
      return null;
    } finally {
      client.close();
    }
  }

  static Future<ApiDiscoveryResult?> _fastestHealthy(
    List<String> candidates, {
    required String source,
  }) async {
    for (var start = 0; start < candidates.length; start += _batchSize) {
      final end = (start + _batchSize < candidates.length)
          ? start + _batchSize
          : candidates.length;
      final results = await Future.wait(
        candidates
            .sublist(start, end)
            .map((candidate) => probe(candidate, source: source)),
      );
      final healthy = results.whereType<ApiDiscoveryResult>().toList()
        ..sort((a, b) => a.latency.compareTo(b.latency));
      if (healthy.isNotEmpty) return healthy.first;
    }
    return null;
  }
}
