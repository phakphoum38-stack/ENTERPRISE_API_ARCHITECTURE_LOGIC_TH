import 'package:flutter_test/flutter_test.dart';

import 'package:research_os_owner_special/src/control_center_engines.dart';

void main() {
  test('four-engine hub preserves unknown and descriptive boundaries', () {
    final hub = ResearchOSEngineHub();

    final snapshots = hub.snapshot();

    expect(snapshots.map((item) => item.name),
        containsAll(<String>['CONTROL', 'EXPERIENCE', 'KNOWLEDGE', 'ASSURANCE']));
    expect(snapshots[0].state, EngineState.ready);
    expect(snapshots[1].state, EngineState.unknown);
    expect(snapshots[2].state, EngineState.unknown);
    expect(snapshots[3].state, EngineState.unknown);
    expect(snapshots[3].details['authority'], 'descriptive_only');
  });

  test('control engine records commands and simulation state', () {
    final hub = ResearchOSEngineHub();

    expect(hub.control.dispatch(const ControlCommand('Inspect object', target: 'EV-001')), isTrue);
    hub.control.setMode(ControlMode.simulation);

    final snapshot = hub.control.snapshot();

    expect(snapshot.details['mode'], 'simulation');
    expect(snapshot.details['commands'], 1);
  });

  test('knowledge and assurance only become observed when backend exposes data', () {
    final hub = ResearchOSEngineHub();

    final snapshots = hub.snapshot(status: <String, dynamic>{
      'capabilities': <Object?>['brain', 'memory'],
      'brain_profiles': <String, dynamic>{'default': 1},
      'evidence': <Object?>[<String, dynamic>{'id': 'EV-1'}],
      'provenance': <Object?>[<String, dynamic>{'source': 'runtime'}],
    });

    expect(snapshots[2].state, EngineState.observed);
    expect(snapshots[3].state, EngineState.observed);
  });
}
