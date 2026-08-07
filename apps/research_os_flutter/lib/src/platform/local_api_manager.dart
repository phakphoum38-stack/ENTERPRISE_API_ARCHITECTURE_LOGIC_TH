import 'local_api_manager_stub.dart'
    if (dart.library.io) 'local_api_manager_io.dart' as impl;

class LocalApiCommandResult {
  const LocalApiCommandResult({
    required this.ok,
    required this.message,
    this.details = '',
  });

  final bool ok;
  final String message;
  final String details;
}

class LocalApiManager {
  const LocalApiManager();

  bool get supported => impl.supported;

  Future<LocalApiCommandResult> status() => impl.status();

  Future<LocalApiCommandResult> start() => impl.start();

  Future<LocalApiCommandResult> stop() => impl.stop();

  Future<LocalApiCommandResult> restart() async {
    await stop();
    return start();
  }

  Future<LocalApiCommandResult> backup() => impl.backup();

  Future<LocalApiCommandResult> openDataFolder() => impl.openDataFolder();

  Future<LocalApiCommandResult> enableAutostart() => impl.enableAutostart();

  Future<LocalApiCommandResult> disableAutostart() => impl.disableAutostart();
}
