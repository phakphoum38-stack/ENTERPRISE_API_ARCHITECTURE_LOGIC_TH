import 'package:flutter/foundation.dart';

enum ControlMode { live, simulation }

enum EngineState { unknown, observed, ready, degraded, failed }

@immutable
final class ControlCommand {
  const ControlCommand(this.name, {this.target = ''});

  final String name;
  final String target;
}

@immutable
final class EngineSnapshot {
  const EngineSnapshot({
    required this.name,
    required this.state,
    this.details = const <String, Object?>{},
  });

  final String name;
  final EngineState state;
  final Map<String, Object?> details;
}

final class ControlEngine {
  ControlMode mode = ControlMode.live;
  final List<ControlCommand> history = <ControlCommand>[];

  EngineSnapshot snapshot() => EngineSnapshot(
        name: 'CONTROL',
        state: EngineState.ready,
        details: <String, Object?>{
          'mode': mode.name,
          'commands': history.length,
        },
      );

  bool dispatch(ControlCommand command) {
    if (command.name.trim().isEmpty) return false;
    history.insert(0, command);
    return true;
  }

  void setMode(ControlMode value) => mode = value;
}

final class ExperienceEngine {
  const ExperienceEngine();

  EngineSnapshot project({
    required bool runtimeObserved,
    required bool loading,
  }) {
    return EngineSnapshot(
      name: 'EXPERIENCE',
      state: loading
          ? EngineState.observed
          : runtimeObserved
              ? EngineState.ready
              : EngineState.unknown,
      details: <String, Object?>{
        'motion': runtimeObserved ? 'state-driven' : 'reduced',
        'reduced_motion_supported': true,
      },
    );
  }
}

final class KnowledgeEngine {
  const KnowledgeEngine();

  EngineSnapshot observe(Map<String, dynamic>? status) {
    final capabilities = status?['capabilities'];
    final brain = status?['brain_profiles'];
    final hasKnowledge = capabilities is List && capabilities.isNotEmpty;
    return EngineSnapshot(
      name: 'KNOWLEDGE',
      state: hasKnowledge ? EngineState.observed : EngineState.unknown,
      details: <String, Object?>{
        'capabilities': capabilities is List ? capabilities.length : 0,
        'brain_profiles': brain is Map ? brain.length : 0,
        'unknown_preserved': true,
      },
    );
  }
}

final class AssuranceEngine {
  const AssuranceEngine();

  EngineSnapshot observe(Map<String, dynamic>? status) {
    final evidence = status?['evidence'];
    final provenance = status?['provenance'];
    final evidenceKnown = evidence is List && evidence.isNotEmpty;
    final provenanceKnown = provenance is List && provenance.isNotEmpty;
    return EngineSnapshot(
      name: 'ASSURANCE',
      state: evidenceKnown && provenanceKnown
          ? EngineState.observed
          : EngineState.unknown,
      details: <String, Object?>{
        'evidence': evidenceKnown ? evidence.length : 0,
        'provenance': provenanceKnown ? provenance.length : 0,
        'unknown_preserved': true,
        'authority': 'descriptive_only',
      },
    );
  }
}

final class ResearchOSEngineHub {
  ResearchOSEngineHub()
      : experience = const ExperienceEngine(),
        knowledge = const KnowledgeEngine(),
        assurance = const AssuranceEngine();

  final ControlEngine control = ControlEngine();
  final ExperienceEngine experience;
  final KnowledgeEngine knowledge;
  final AssuranceEngine assurance;

  List<EngineSnapshot> snapshot({
    Map<String, dynamic>? status,
    bool loading = false,
  }) {
    final observed = status != null;
    return <EngineSnapshot>[
      control.snapshot(),
      experience.project(runtimeObserved: observed, loading: loading),
      knowledge.observe(status),
      assurance.observe(status),
    ];
  }
}
