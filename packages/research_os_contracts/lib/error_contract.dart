/// Stable cross-surface error and recovery semantics.
library;

enum ResearchOSErrorKind {
  validation,
  authentication,
  authorization,
  unavailable,
  timeout,
  conflict,
  rateLimited,
  network,
  persistence,
  compatibility,
  integrity,
  unknown,
}

final class ResearchOSError {
  const ResearchOSError({
    required this.kind,
    required this.code,
    required this.message,
    this.retryable = false,
    this.correlationId,
  });

  final ResearchOSErrorKind kind;
  final String code;
  final String message;
  final bool retryable;
  final String? correlationId;
}

abstract interface class ErrorRecoveryContract {
  ResearchOSError normalize(Object error);
  Future<bool> recover(ResearchOSError error);
}
