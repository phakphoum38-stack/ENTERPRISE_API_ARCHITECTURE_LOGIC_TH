/// Durable work lifecycle and replay semantics.
library;

enum WorkLifecycle {
  discovered,
  queued,
  leased,
  running,
  observing,
  evidenced,
  completed,
  failed,
  cancelled,
  recovering,
}

final class WorkIdentity {
  const WorkIdentity({
    required this.workId,
    required this.correlationId,
    required this.idempotencyKey,
  });

  final String workId;
  final String correlationId;
  final String idempotencyKey;
}

abstract interface class LifecycleContract {
  WorkLifecycle get state;
  Future<bool> replay(WorkIdentity identity);
  Future<bool> recover(WorkIdentity identity);
}
