/// Upgrade, rollback and reconciliation contract.
library;

enum MigrationPhase { preflight, compatible, migrate, verify, rollback, postflight }

final class MigrationPlan {
  const MigrationPlan({
    required this.id,
    required this.fromVersion,
    required this.toVersion,
    required this.rollbackSupported,
  });

  final String id;
  final String fromVersion;
  final String toVersion;
  final bool rollbackSupported;
}

abstract interface class MigrationContract {
  Future<bool> preflight(MigrationPlan plan);
  Future<bool> migrate(MigrationPlan plan);
  Future<bool> verify(MigrationPlan plan);
  Future<bool> rollback(MigrationPlan plan);
}
