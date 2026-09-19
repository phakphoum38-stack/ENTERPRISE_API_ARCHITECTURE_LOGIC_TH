import 'package:research_os_contracts/research_os_contracts.dart';

import '../api/v3_api.dart';

/// V3 compatibility boundary while V3 release contracts remain active.
final class V3CompatibilityAdapter
    implements RuntimeStatusCapability, ProviderCapability {
  V3CompatibilityAdapter(this.api);

  final V3Api api;

  @override
  Future<Map<String, dynamic>> runtimeStatus() => api.health();

  @override
  Future<Map<String, dynamic>> providers() => api.providers();

  @override
  Future<Map<String, dynamic>> providerStatus() => api.providers();

  Future<Map<String, dynamic>> master({int tasks = 1}) =>
      api.master(tasks: tasks);

  Future<Map<String, dynamic>> user() => api.user();
}
