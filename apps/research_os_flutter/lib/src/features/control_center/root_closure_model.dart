import 'package:flutter/foundation.dart';

enum RootClosureStatus { closed, repaired, verified, blocked, unknown }

@immutable
class RootClosureRecord {
  const RootClosureRecord({
    required this.name,
    required this.status,
    required this.description,
    this.failureId,
    this.rootCause,
    this.introducedBy,
    this.sourceSha,
    this.file,
    this.symbol,
    this.consumer,
    this.repairTarget,
    this.evidenceRef,
  });

  final String name;
  final RootClosureStatus status;
  final String description;
  final String? failureId;
  final String? rootCause;
  final String? introducedBy;
  final String? sourceSha;
  final String? file;
  final String? symbol;
  final String? consumer;
  final String? repairTarget;
  final String? evidenceRef;

  bool get hasProvenance =>
      introducedBy != null && sourceSha != null && sourceSha!.isNotEmpty;

  bool get hasRepairTarget =>
      repairTarget != null && repairTarget!.isNotEmpty;

  bool get hasEvidence => evidenceRef != null && evidenceRef!.isNotEmpty;
}
