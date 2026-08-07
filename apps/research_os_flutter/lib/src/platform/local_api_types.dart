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
