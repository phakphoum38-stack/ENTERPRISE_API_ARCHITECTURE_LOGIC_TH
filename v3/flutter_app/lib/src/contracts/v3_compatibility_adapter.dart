import 'api/v3_api.dart';

/// Compatibility boundary for V3 while V3 release contracts remain active.
///
/// The canonical Control Center consumes this adapter instead of importing
/// V3 HTTP transport directly.
final class V3CompatibilityAdapter {
  V3CompatibilityAdapter(this.api);

  final V3Api api;

  Future<Map<String, dynamic>> runtimeStatus() => api.health();

  Future<Map<String, dynamic>> providers() => api.providers();

  Future<Map<String, dynamic>> master({int tasks = 1}) =>
      api.master(tasks: tasks);

  Future<Map<String, dynamic>> user() => api.user();
}
