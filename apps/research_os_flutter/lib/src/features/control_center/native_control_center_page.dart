import 'package:flutter/material.dart';

import '../../api/research_os_api_client.dart';
import 'native_control_audit_view.dart';

class NativeControlCenterPage extends StatefulWidget {
  const NativeControlCenterPage({
    required this.apiClient,
    this.onNavigate,
    super.key,
  });

  final ResearchOSApiClient apiClient;
  final ValueChanged<int>? onNavigate;

  @override
  State<NativeControlCenterPage> createState() => _NativeControlCenterPageState();
}

class _NativeControlCenterPageState extends State<NativeControlCenterPage>
    with SingleTickerProviderStateMixin {
  late final TabController _tabs;
  final _command = TextEditingController();
  final _inspector = TextEditingController();
  final List<NativeControlAuditSnapshot> _auditSnapshots = <NativeControlAuditSnapshot>[];
  bool _loading = false;
  bool _simulation = false;
  int _livePulse = 0;
  String _selectedObject = '';
  Map<String, dynamic>? _health;
  Map<String, dynamic>? _brain;
  Map<String, dynamic>? _skills;
  Map<String, dynamic>? _providers;
  Map<String, dynamic>? _agents;
  Map<String, dynamic>? _agentReadiness;
  Map<String, dynamic>? _orchestrations;
  final List<String> _events = <String>[
    'Control Center initialized',
    'Human authority boundary active',
  ];

  static const commands = <String>[
    'Open Research',
    'Open Friend',
    'Open Runtime',
    'Open Evidence',
    'Open Audit',
    'Inspect object',
    'Simulation mode',
    'Refresh runtime',
  ];

  @override
  void initState() {
    super.initState();
    _tabs = TabController(length: 10, vsync: this);
    _load();
  }

  @override
  void dispose() {
    _tabs.dispose();
    _command.dispose();
    _inspector.dispose();
    super.dispose();
  }

  Future<void> _load() async {
    if (_loading) return;
    setState(() => _loading = true);
    try {
      final values = await Future.wait(<Future<Map<String, dynamic>>>[
        widget.apiClient.getHealth(),
        widget.apiClient.getBrainCapacity(),
        widget.apiClient.getBrainSkills(),
        widget.apiClient.getProviders(),
        widget.apiClient.getAgents(),
        widget.apiClient.getAgentReadiness(),
        widget.apiClient.getOrchestrations(limit: 20),
      ]);
      if (!mounted) return;
      setState(() {
        _health = values[0];
        _brain = values[1];
        _skills = values[2];
        _providers = values[3];
        _agents = values[4];
        _agentReadiness = values[5];
        _orchestrations = values[6];
        _livePulse++;
        _events.insert(0, 'Runtime state observed');
      });
    } catch (error) {
      if (!mounted) return;
      setState(() => _events.insert(0, 'Runtime observation unavailable: $error'));
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  void _runCommand(String value) {
    final command = value.trim();
    if (command.isEmpty) return;
    _command.clear();

    if (command == 'Refresh runtime') {
      _load();
      return;
    }
    if (command == 'Simulation mode') {
      setState(() {
        _simulation = !_simulation;
        _events.insert(
          0,
          _simulation ? 'Simulation mode enabled' : 'Simulation mode disabled',
        );
      });
      _tabs.animateTo(0);
      return;
    }

    const routes = <String, int>{
      'Open Research': 0,
      'Open Friend': 13,
      'Open Runtime': 8,
    };
    final route = routes[command];
    if (route != null) {
      widget.onNavigate?.call(route);
      setState(() => _events.insert(0, '$command prepared'));
      return;
    }

    if (command == 'Open Evidence') {
      _tabs.animateTo(4);
    } else if (command == 'Open Audit') {
      _tabs.animateTo(5);
    } else if (command == 'Inspect object') {
      _tabs.animateTo(6);
    }
  }

  void _runAudit() {
    final checks = <Map<String, String>>[
      _auditCheck('Runtime', _health?['status']?.toString() == 'ok'),
      _auditCheck('Brain capacity', _brain != null && _brain!.isNotEmpty),
      _auditCheck('Brain skills', _skills != null && _skills!.isNotEmpty),
      _auditCheck('Providers', _providers != null && _providers!.isNotEmpty),
      _auditCheck('Agents', _agents != null && _agents!.isNotEmpty),
      _auditCheck('Agent readiness', (_agentReadiness?['status'] ?? _agentReadiness?['readiness']) != null),
      _auditCheck('Workflow observation', _orchestrationItems(_orchestrations).isNotEmpty),
      _auditDeferred('Offline package audit'),
      _auditDeferred('Installed baseline'),
      _auditDeferred('Release authority decision'),
    ];
    final hasFail = checks.any((item) => item['state'] == 'FAIL');
    final hasDeferred = checks.any((item) => item['state'] == 'DEFERRED');
    final now = DateTime.now().toUtc();
    final snapshot = NativeControlAuditSnapshot(
      auditId: 'audit-${now.millisecondsSinceEpoch}',
      observedAt: now,
      status: hasFail ? 'FAIL' : (hasDeferred ? 'DEFERRED' : 'PASS'),
      checks: checks,
      source: 'Native Control Center existing observation surfaces',
    );
    setState(() {
      _auditSnapshots.insert(0, snapshot);
      if (_auditSnapshots.length > 20) _auditSnapshots.removeLast();
      _events.insert(0, 'Main Final Audit captured: ${snapshot.status}');
    });
    _tabs.animateTo(5);
  }

  Map<String, String> _auditCheck(String name, bool pass) => <String, String>{
        'check': name,
        'state': pass ? 'PASS' : 'FAIL',
        'detail': pass ? 'Observed' : 'Required observation unavailable',
      };

  Map<String, String> _auditDeferred(String name) => <String, String>{
        'check': name,
        'state': 'DEFERRED',
        'detail': 'Not exposed by the current read-only API surface',
      };

  @override
  Widget build(BuildContext context) {
    final query = _command.text.trim().toLowerCase();
    final matches = commands
        .where((item) => item.toLowerCase().contains(query))
        .take(8)
        .toList();

    return Material(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: <Widget>[
          _Header(
            simulation: _simulation,
            loading: _loading,
            onSimulation: () => _runCommand('Simulation mode'),
            onRefresh: _loading ? null : _load,
          ),
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 0, 16, 8),
            child: TextField(
              controller: _command,
              onChanged: (_) => setState(() {}),
              onSubmitted: _runCommand,
              decoration: InputDecoration(
                prefixIcon: const Icon(Icons.search),
                suffixText: 'Ctrl/⌘ K',
                hintText: 'Command, navigation, inspect…',
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(14),
                ),
              ),
            ),
          ),
          if (query.isNotEmpty)
            Card(
              margin: const EdgeInsets.fromLTRB(16, 0, 16, 8),
              child: Column(
                children: matches.isEmpty
                    ? <Widget>[
                        const ListTile(title: Text('No matching command')),
                      ]
                    : matches
                        .map(
                          (item) => ListTile(
                            leading: const Icon(Icons.bolt_outlined),
                            title: Text(item),
                            subtitle: const Text(
                              'Prepared through the native control lifecycle',
                            ),
                            onTap: () => _runCommand(item),
                          ),
                        )
                        .toList(),
              ),
            ),
          if (_loading) const LinearProgressIndicator(minHeight: 2),
          TabBar(
            controller: _tabs,
            isScrollable: true,
            tabs: const <Tab>[
              Tab(text: 'Overview', icon: Icon(Icons.dashboard_outlined)),
              Tab(text: 'Activity', icon: Icon(Icons.timeline_outlined)),
              Tab(text: 'State', icon: Icon(Icons.account_tree_outlined)),
              Tab(text: 'System Map', icon: Icon(Icons.hub_outlined)),
              Tab(text: 'Evidence', icon: Icon(Icons.fact_check_outlined)),
              Tab(text: 'Audit', icon: Icon(Icons.rule_folder_outlined)),
              Tab(text: 'Inspector', icon: Icon(Icons.manage_search_outlined)),
              Tab(text: 'Failures', icon: Icon(Icons.warning_amber_outlined)),
              Tab(text: 'History', icon: Icon(Icons.history_outlined)),
              Tab(text: 'Simulation', icon: Icon(Icons.science_outlined)),
            ],
          ),
          Expanded(
            child: TabBarView(
              controller: _tabs,
              children: <Widget>[
                _Overview(
                  key: ValueKey('overview-$_livePulse'),
                  health: _health,
                  brain: _brain,
                  skills: _skills,
                  providers: _providers,
                  agents: _agents,
                  agentReadiness: _agentReadiness,
                  orchestrations: _orchestrations,
                  simulation: _simulation,
                ),
                _Activity(events: _events),
                _StateView(health: _health, brain: _brain),
                _SystemMap(
                  health: _health,
                  brain: _brain,
                  agents: _agents,
                ),
                _EvidenceView(health: _health),
                NativeControlAuditView(
                  health: _health,
                  brain: _brain,
                  skills: _skills,
                  providers: _providers,
                  agents: _agents,
                  agentReadiness: _agentReadiness,
                  orchestrations: _orchestrations,
                  snapshots: _auditSnapshots,
                  onRun: _runAudit,
                ),
                _Inspector(
                  controller: _inspector,
                  selectedObject: _selectedObject,
                  onInspect: (id) => setState(() {
                    _selectedObject = id;
                    _events.insert(0, 'Inspector opened: $id');
                  }),
                ),
                _FailureView(health: _health, orchestrations: _orchestrations),
                _Activity(events: _events),
                _Simulation(
                  enabled: _simulation,
                  onToggle: (value) => setState(() {
                    _simulation = value;
                    _events.insert(
                      0,
                      value
                          ? 'Simulation mode enabled'
                          : 'Simulation mode disabled',
                    );
                  }),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _Header extends StatelessWidget {
  const _Header({
    required this.simulation,
    required this.loading,
    required this.onSimulation,
    required this.onRefresh,
  });

  final bool simulation;
  final bool loading;
  final VoidCallback onSimulation;
  final VoidCallback? onRefresh;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 14, 16, 12),
      child: Row(
        children: <Widget>[
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: <Widget>[
                Text(
                  'Native Core Workspace',
                  style: theme.textTheme.headlineSmall
                      ?.copyWith(fontWeight: FontWeight.w700),
                ),
                const SizedBox(height: 3),
                Text(
                  'Command • Activity • State • Evidence • Inspector • Simulation',
                  style: theme.textTheme.bodySmall?.copyWith(
                    color: theme.colorScheme.onSurfaceVariant,
                  ),
                ),
              ],
            ),
          ),
          FilterChip(
            selected: simulation,
            onSelected: (_) => onSimulation(),
            avatar: const Icon(Icons.science_outlined, size: 17),
            label: Text(simulation ? 'SIMULATION' : 'LIVE'),
          ),
          const SizedBox(width: 8),
          IconButton(
            tooltip: 'Refresh runtime',
            onPressed: onRefresh,
            icon: loading
                ? const SizedBox.square(
                    dimension: 18,
                    child: CircularProgressIndicator(strokeWidth: 2),
                  )
                : const Icon(Icons.refresh),
          ),
        ],
      ),
    );
  }
}

class _Overview extends StatelessWidget {
  const _Overview({
    super.key,
    required this.health,
    required this.brain,
    required this.skills,
    required this.providers,
    required this.agents,
    required this.agentReadiness,
    required this.orchestrations,
    required this.simulation,
  });

  final Map<String, dynamic>? health;
  final Map<String, dynamic>? brain;
  final Map<String, dynamic>? skills;
  final Map<String, dynamic>? providers;
  final Map<String, dynamic>? agents;
  final Map<String, dynamic>? agentReadiness;
  final Map<String, dynamic>? orchestrations;
  final bool simulation;

  @override
  Widget build(BuildContext context) {
    final status = health?['status']?.toString() ?? 'UNKNOWN';
    final capabilities = (health?['capabilities'] as List?)?.length ?? 0;
    final skillsCount = (skills?['skills'] as List?)?.length ?? 0;
    final providerCount = (providers?['providers'] as List?)?.length ?? 0;
    final agentCount = (agents?['agents'] as List?)?.length ?? 0;
    final readiness = agentReadiness?['status']?.toString() ??
        agentReadiness?['readiness']?.toString() ?? 'UNKNOWN';
    final runs = _orchestrationItems(orchestrations);
    final orchestrationCount = runs.length;

    return ListView(
      key: const ValueKey('control-center-overview-scroll'),
      padding: const EdgeInsets.all(16),
      children: <Widget>[
        if (simulation)
          const Card(
            child: ListTile(
              leading: Icon(Icons.science_outlined),
              title: Text('Simulation mode'),
              subtitle: Text(
                'Actions are prepared for inspection and do not imply release authority.',
              ),
            ),
          ),
        Wrap(
          spacing: 10,
          runSpacing: 10,
          children: <Widget>[
            _Metric('Runtime', status, Icons.dns_outlined),
            _Metric('Capabilities', '$capabilities', Icons.extension_outlined),
            _Metric('Brain skills', '$skillsCount', Icons.psychology_alt_outlined),
            _Metric('Providers', '$providerCount', Icons.cloud_outlined),
            _Metric('Agents', '$agentCount', Icons.smart_toy_outlined),
            _Metric('Agent readiness', readiness, Icons.health_and_safety_outlined),
            _Metric('Workflow runs', '$orchestrationCount', Icons.account_tree_outlined),
            _Metric('Running', '${_statusCount(runs, 'running')}', Icons.play_circle_outline),
            _Metric('Failed', '${_statusCount(runs, 'failed')}', Icons.error_outline),
          ],
        ),
        const SizedBox(height: 12),
        Card(
          child: ListTile(
            leading: Icon(
              status == 'ok'
                  ? Icons.check_circle_outline
                  : Icons.help_outline,
            ),
            title: Text(
              status == 'ok'
                  ? 'LIVE SYSTEM — runtime observed'
                  : 'SYSTEM STATE — UNKNOWN',
            ),
            subtitle: const Text(
              'Observation is sourced from existing Research OS API surfaces.',
            ),
          ),
        ),
        const SizedBox(height: 12),
        const SizedBox(height: 12),
        Card(
          child: ListTile(
            leading: const Icon(Icons.route_outlined),
            title: const Text('Workflow control surface'),
            subtitle: Text(
              'Existing orchestration API observed: $orchestrationCount run(s). '
              'Agent readiness: $readiness. Execution remains behind existing human authorization.',
            ),
          ),
        ),
        const SizedBox(height: 12),
        const _BoundaryCard(),
      ],
    );
  }
}

class _Metric extends StatelessWidget {
  const _Metric(this.label, this.value, this.icon);
  final String label;
  final String value;
  final IconData icon;

  @override
  Widget build(BuildContext context) => SizedBox(
        width: 190,
        child: Card(
          margin: EdgeInsets.zero,
          child: Padding(
            padding: const EdgeInsets.all(14),
            child: Row(
              children: <Widget>[
                Icon(icon),
                const SizedBox(width: 10),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: <Widget>[
                      Text(label, style: Theme.of(context).textTheme.bodySmall),
                      const SizedBox(height: 4),
                      Text(
                        value,
                        style: Theme.of(context)
                            .textTheme
                            .titleLarge
                            ?.copyWith(fontWeight: FontWeight.w700),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
        ),
      );
}

class _Activity extends StatelessWidget {
  const _Activity({required this.events});
  final List<String> events;

  @override
  Widget build(BuildContext context) => ListView.separated(
        padding: const EdgeInsets.all(16),
        itemCount: events.length,
        separatorBuilder: (_, __) => const Divider(height: 1),
        itemBuilder: (_, index) => ListTile(
          dense: true,
          leading: const Icon(Icons.circle_outlined, size: 18),
          title: Text(events[index]),
          subtitle: const Text('OBSERVED'),
        ),
      );
}

class _StateView extends StatelessWidget {
  const _StateView({required this.health, required this.brain});
  final Map<String, dynamic>? health;
  final Map<String, dynamic>? brain;

  @override
  Widget build(BuildContext context) => _JsonView(
        title: 'Current state',
        data: <String, dynamic>{
          'health': health ?? <String, dynamic>{},
          'brain': brain ?? <String, dynamic>{},
        },
      );
}

class _SystemMap extends StatelessWidget {
  const _SystemMap({
    required this.health,
    required this.brain,
    required this.agents,
  });

  final Map<String, dynamic>? health;
  final Map<String, dynamic>? brain;
  final Map<String, dynamic>? agents;

  @override
  Widget build(BuildContext context) {
    final nodes = <String, Map<String, dynamic>>{
      'ROOT': <String, dynamic>{'state': 'OBSERVED'},
      'CORE': health ?? <String, dynamic>{},
      'BRAIN': brain ?? <String, dynamic>{},
      'AGENTS': agents ?? <String, dynamic>{},
      'ASSURANCE': <String, dynamic>{},
      'REALITY': <String, dynamic>{},
    };
    return ListView(
      padding: const EdgeInsets.all(16),
      children: <Widget>[
        const Card(
          child: ListTile(
            leading: Icon(Icons.hub_outlined),
            title: Text('Live System Map'),
            subtitle: Text(
              'Observations only — no authority grant and no fabricated state.',
            ),
          ),
        ),
        ...nodes.entries.map(
          (entry) => Card(
            child: ListTile(
              leading: const Icon(Icons.account_tree_outlined),
              title: Text(entry.key),
              subtitle: Text(
                entry.value.isEmpty ? 'UNKNOWN / NOT EXPOSED' : 'OBSERVED',
              ),
            ),
          ),
        ),
      ],
    );
  }
}

class _EvidenceView extends StatelessWidget {
  const _EvidenceView({required this.health});
  final Map<String, dynamic>? health;

  @override
  Widget build(BuildContext context) => _JsonView(
        title: 'Evidence / observation',
        data: health ?? <String, dynamic>{},
      );
}

class _Inspector extends StatelessWidget {
  const _Inspector({
    required this.controller,
    required this.selectedObject,
    required this.onInspect,
  });

  final TextEditingController controller;
  final String selectedObject;
  final ValueChanged<String> onInspect;

  @override
  Widget build(BuildContext context) => ListView(
        padding: const EdgeInsets.all(16),
        children: <Widget>[
          Row(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: <Widget>[
              Expanded(
                child: TextField(
                  controller: controller,
                  onSubmitted: onInspect,
                  decoration: const InputDecoration(
                    labelText: 'Object ID',
                    hintText: 'task, source, evidence, service…',
                  ),
                ),
              ),
              const SizedBox(width: 10),
              FilledButton(
                onPressed: () => onInspect(controller.text.trim()),
                child: const Text('Inspect'),
              ),
            ],
          ),
          const SizedBox(height: 12),
          Card(
            child: ListTile(
              leading: const Icon(Icons.manage_search_outlined),
              title: Text(
                selectedObject.isEmpty ? 'No object selected' : selectedObject,
              ),
              subtitle: Text(
                selectedObject.isEmpty
                    ? 'UNKNOWN until an object is selected.'
                    : 'Selection only; inspection does not grant execution authority.',
              ),
            ),
          ),
        ],
      );
}

class _FailureView extends StatelessWidget {
  const _FailureView({required this.health, this.orchestrations});
  final Map<String, dynamic>? health;
  final Map<String, dynamic>? orchestrations;

  @override
  Widget build(BuildContext context) {
    final rawRuns = _orchestrationItems(orchestrations);
    final failedRuns = rawRuns.where((item) => item['status']?.toString().toLowerCase() == 'failed').toList();
    final failures = health?['failures'];
    if ((failures is! List || failures.isEmpty) && failedRuns.isEmpty) {
      return const Card(
        child: ListTile(
          leading: Icon(Icons.info_outline),
          title: Text('Failure feed unavailable'),
          subtitle: Text(
            'This is not interpreted as zero failures. The current API does not expose a failure collection.',
          ),
        ),
      );
    }
    final items = failures is List
        ? failures
        : failedRuns.map((run) => <String, dynamic>{
            'id': run['run_id'] ?? run['id'] ?? 'failed-run',
            'status': run['status'] ?? 'failed',
          }).toList();
    return ListView.builder(
      padding: const EdgeInsets.all(16),
      itemCount: items.length,
      itemBuilder: (_, index) => ListTile(
        leading: const Icon(Icons.warning_amber_outlined),
        title: Text(
          items[index] is Map
              ? (items[index] as Map)['id']?.toString() ?? 'Failure'
              : items[index].toString(),
        ),
      ),
    );
  }
}

class _Simulation extends StatelessWidget {
  const _Simulation({required this.enabled, required this.onToggle});
  final bool enabled;
  final ValueChanged<bool> onToggle;

  @override
  Widget build(BuildContext context) => ListView(
        padding: const EdgeInsets.all(16),
        children: <Widget>[
          Card(
            child: SwitchListTile(
              value: enabled,
              onChanged: onToggle,
              title: const Text('Simulation / Dry Run'),
              subtitle: const Text(
                'Prepare and inspect a lifecycle without treating preparation as authorization.',
              ),
              secondary: const Icon(Icons.science_outlined),
            ),
          ),
          const Card(
            child: Padding(
              padding: EdgeInsets.all(16),
              child: Text(
                'INTENT → VALIDATE → AUTHORIZE → EXECUTE → OBSERVE → EVIDENCE → COMPLETE',
              ),
            ),
          ),
        ],
      );
}

class _BoundaryCard extends StatelessWidget {
  const _BoundaryCard();

  @override
  Widget build(BuildContext context) => const Card(
        child: Padding(
          padding: EdgeInsets.all(16),
          child: Wrap(
            spacing: 8,
            runSpacing: 8,
            children: <Widget>[
              Chip(avatar: Icon(Icons.check, size: 16), label: Text('Observe')),
              Chip(avatar: Icon(Icons.check, size: 16), label: Text('Analyze')),
              Chip(avatar: Icon(Icons.check, size: 16), label: Text('Research')),
              Chip(avatar: Icon(Icons.check, size: 16), label: Text('Prepare')),
              Chip(
                avatar: Icon(Icons.lock_outline, size: 16),
                label: Text('Approve — human'),
              ),
              Chip(
                avatar: Icon(Icons.lock_outline, size: 16),
                label: Text('Authorize — human'),
              ),
              Chip(
                avatar: Icon(Icons.lock_outline, size: 16),
                label: Text('Release — human'),
              ),
            ],
          ),
        ),
      );
}

class _JsonView extends StatelessWidget {
  const _JsonView({required this.title, required this.data});
  final String title;
  final Map<String, dynamic> data;

  @override
  Widget build(BuildContext context) => ListView(
        padding: const EdgeInsets.all(16),
        children: <Widget>[
          Text(
            title,
            style: Theme.of(context)
                .textTheme
                .titleLarge
                ?.copyWith(fontWeight: FontWeight.w700),
          ),
          const SizedBox(height: 12),
          ...data.entries.map(
            (entry) => Card(
              child: ListTile(
                title: Text(entry.key),
                subtitle: SelectableText(entry.value.toString()),
              ),
            ),
          ),
        ],
      );
}

int _statusCount(Object? raw, String status) {
  if (raw is! List) return 0;
  return raw.where((item) => item is Map && item['status']?.toString().toLowerCase() == status).length;
}

List<Map<String, dynamic>> _orchestrationItems(Map<String, dynamic>? payload) {
  final raw = payload?['runs'] ?? payload?['orchestrations'];
  if (raw is! List) return <Map<String, dynamic>>[];
  return raw.whereType<Map>().map((item) => Map<String, dynamic>.from(item)).toList();
}
