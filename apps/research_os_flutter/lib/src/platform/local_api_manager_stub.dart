import 'local_api_types.dart';

const bool supported = false;

Future<LocalApiCommandResult> _unsupported() async => const LocalApiCommandResult(
      ok: false,
      message: 'Local API Control รองรับเฉพาะ Windows Desktop',
    );

Future<LocalApiCommandResult> status() => _unsupported();
Future<LocalApiCommandResult> start() => _unsupported();
Future<LocalApiCommandResult> stop() => _unsupported();
Future<LocalApiCommandResult> backup() => _unsupported();
Future<LocalApiCommandResult> openDataFolder() => _unsupported();
Future<LocalApiCommandResult> enableAutostart() => _unsupported();
Future<LocalApiCommandResult> disableAutostart() => _unsupported();
