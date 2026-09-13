enum RuntimeState {
  idle,
  planning,
  planned,
  executing,
  completed,
  failed,
  cancelled,
  unknown,
}

extension RuntimeStateX on RuntimeState {
  bool get isTerminal => switch (this) {
        RuntimeState.completed || RuntimeState.failed || RuntimeState.cancelled => true,
        _ => false,
      };

  String get wireName => switch (this) {
        RuntimeState.idle => 'idle',
        RuntimeState.planning => 'planning',
        RuntimeState.planned => 'planned',
        RuntimeState.executing => 'executing',
        RuntimeState.completed => 'completed',
        RuntimeState.failed => 'failed',
        RuntimeState.cancelled => 'cancelled',
        RuntimeState.unknown => 'unknown',
      };
}

RuntimeState parseRuntimeState(Object? value) {
  final normalized = value?.toString().trim().toLowerCase() ?? '';
  return switch (normalized) {
    'idle' => RuntimeState.idle,
    'planning' || 'created' => RuntimeState.planning,
    'planned' || 'pending' || 'queued' => RuntimeState.planned,
    'executing' || 'running' || 'in_progress' || 'in-progress' => RuntimeState.executing,
    'completed' || 'complete' || 'success' || 'succeeded' || 'done' => RuntimeState.completed,
    'failed' || 'failure' || 'error' => RuntimeState.failed,
    'cancelled' || 'canceled' => RuntimeState.cancelled,
    _ => RuntimeState.unknown,
  };
}

class OrchestrationRun {
  const OrchestrationRun({
    required this.id,
    required this.objective,
    required this.state,
    this.steps = const <Map<String, dynamic>>[],
  });

  final String id;
  final String objective;
  final RuntimeState state;
  final List<Map<String, dynamic>> steps;

  bool get hasId => id.isNotEmpty;

  static OrchestrationRun fromResponse(Map<String, dynamic> response) {
    final rawRun = response['run'];
    final run = rawRun is Map
        ? Map<String, dynamic>.from(rawRun)
        : response;
    final id = _firstString(<Object?>[
      response['run_id'],
      response['id'],
      run['run_id'],
      run['id'],
    ]);
    final objective = _firstString(<Object?>[
      response['objective'],
      run['objective'],
    ]);
    final state = parseRuntimeState(_firstValue(<Object?>[
      response['status'],
      response['run_status'],
      response['state'],
      run['status'],
      run['run_status'],
      run['state'],
    ]));
    final rawSteps = run['steps'] ?? response['steps'];
    final steps = rawSteps is List
        ? rawSteps.whereType<Map>().map((step) => Map<String, dynamic>.from(step)).toList(growable: false)
        : const <Map<String, dynamic>>[];
    return OrchestrationRun(
      id: id,
      objective: objective,
      state: state,
      steps: steps,
    );
  }

  static Object? _firstValue(List<Object?> values) {
    for (final value in values) {
      if (value != null && value.toString().trim().isNotEmpty) return value;
    }
    return null;
  }

  static String _firstString(List<Object?> values) =>
      _firstValue(values)?.toString() ?? '';
}

class RuntimeEvidence {
  const RuntimeEvidence({
    required this.state,
    this.events = const <Map<String, dynamic>>[],
    this.raw = const <String, dynamic>{},
  });

  final RuntimeState state;
  final List<Map<String, dynamic>> events;
  final Map<String, dynamic> raw;

  factory RuntimeEvidence.fromResponse(Map<String, dynamic> response) {
    final events = _extractEvents(response);
    Object? state;
    for (final key in const <String>['status', 'run_status', 'state', 'conclusion']) {
      if (response[key] != null) {
        state = response[key];
        break;
      }
    }
    state ??= _eventState(events);
    return RuntimeEvidence(
      state: parseRuntimeState(state),
      events: events,
      raw: response,
    );
  }

  static List<Map<String, dynamic>> _extractEvents(Map<String, dynamic> response) {
    for (final key in const <String>['events', 'timeline', 'items', 'steps']) {
      final value = response[key];
      if (value is List) {
        return value.whereType<Map>().map((item) => Map<String, dynamic>.from(item)).toList(growable: false);
      }
    }
    return const <Map<String, dynamic>>[];
  }

  static Object? _eventState(List<Map<String, dynamic>> events) {
    for (final event in events.reversed) {
      for (final key in const <String>['status', 'run_status', 'state', 'conclusion']) {
        if (event[key] != null) return event[key];
      }
    }
    return null;
  }
}
