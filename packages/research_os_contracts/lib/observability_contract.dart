/// Shared correlation, health and audit vocabulary.
library;

enum ComponentHealth { unknown, healthy, degraded, unavailable, recovering }

final class ObservationContext {
  const ObservationContext({
    required this.correlationId,
    this.causationId,
    this.runId,
  });

  final String correlationId;
  final String? causationId;
  final String? runId;
}

final class AuditRecord {
  const AuditRecord({
    required this.correlationId,
    required this.actor,
    required this.action,
    required this.result,
    required this.timestamp,
  });

  final String correlationId;
  final String actor;
  final String action;
  final String result;
  final DateTime timestamp;
}
