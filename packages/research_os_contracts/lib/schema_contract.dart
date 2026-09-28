/// Schema and compatibility contract.
library;

enum CompatibilityMode { exact, backwardCompatible, forwardCompatible, breaking }

final class SchemaContract {
  const SchemaContract({
    required this.id,
    required this.version,
    required this.compatibility,
    this.migrationRef,
  });

  final String id;
  final int version;
  final CompatibilityMode compatibility;
  final String? migrationRef;
}

abstract interface class SchemaEvolutionContract {
  bool accepts(SchemaContract producer, SchemaContract consumer);
  String? migrationPlan(SchemaContract from, SchemaContract to);
}
