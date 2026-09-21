import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../../api/research_os_api_client.dart';

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
    with TickerProviderStateMixin {
  late final TabController _tabs;
  late final AnimationController _pulse;
  final _commandController = TextEditingController();
  final _commandFocus = FocusNode();

  bool _loading = false;
  bool _simulation = false;
  Map<String, dynamic>? _health;
  Map<String, dynamic>? _brain;
  Map<String, dynamic>? _providers;
  Map<String, dynamic>? _agents;

  final List<_ActivityEvent> _activity = <_ActivityEvent>[
    _ActivityEvent('Control Center initialized', Icons.dashboard_outlined),
    _ActivityEvent('Human authority boundary active', Icons.verified_user_outlined),
  ];

  static const _commands = <_Command>[
    _Command('Refresh system', Icons.refresh, tab: 0),
    _Command('Open Activity', Icons.timeline_outlined, tab: 1),
    _Command('Open State', Icons.account_tree_outlined, tab: 2),
    _Command('Open System Map', Icons.hub_outlined, tab: 3),
    _Command('Open Evidence', Icons.fact_check_outlined, tab: 4),
    _Command('Open Inspector', Icons.manage_search_outlined, tab: 5),
    _Command('Open Home', Icons.home_outlined, routeIndex: 0),
    _Command('Open Friend', Icons.forum_outlined, routeIndex: 1),
    _Command('Open Runtime', Icons.monitor_heart_outlined, routeIndex: 8),
    _Command('Open Brain', Icons.psychology_alt_outlined, routeIndex: 11),
    _Command('Open Settings', Icons.settings_outlined, routeIndex: 9),
    _Command('Simulation mode', Icons.science_outlined),
  ];

  @override
  void initState() {
    super.initState();
    _tabs = TabController(length: 6, vsync: this);
    _pulse = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1400),
      lowerBound: .88,
      upperBound: 1,
    )..repeat(reverse: true);
    _refresh();
  }

  @override
  void dispose() {
    _tabs.dispose();
    _pulse.dispose();
    _commandController.dispose();
    _commandFocus.dispose();
    super.dispose();
  }

  Future<void> _refresh() async {
    if (_loading) return;
    setState(() => _loading = true);
    try {
      final results = await Future.wait(<Future<Map<String, dynamic>>>[
        widget.apiClient.getHealth(),
        widget.apiClient.getBrainCapacity(),
        widget.apiClient.getProviders(),
        widget.apiClient.getAgents(),
      ]);
      if (!mounted) return;
      setState(() {
        _health = results[0];
        _brain = results[1];
        _providers = results[2];
        _agents = results[3];
        _activity.insert(
          0,
          _ActivityEvent('System state observed', Icons.visibility_outlined),
        );
      });
    } catch (error) {
      if (!mounted) return;
      setState(() {
        _activity.insert(
          0,
          _ActivityEvent(
            'System observation unavailable: $error',
            Icons.error_outline,
          ),
        );
      });
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  void _toggleSimulation() {
    setState(() {
      _simulation = !_simulation;
      _activity.insert(
        0,
        _ActivityEvent(
          _simulation ? 'Simulation mode enabled' : 'Live mode restored',
          _simulation ? Icons.science_outlined : Icons.play_circle_outline,
        ),
      );
    });
  }

  void _runCommand(_Command command) {
    _commandController.clear();
    _commandFocus.unfocus();

    if (command.label == 'Refresh system') {
      _refresh();
      return;
    }
    if (command.label == 'Simulation mode') {
      _toggleSimulation();
      return;
    }
    if (command.tab != null) {
      _tabs.animateTo(command.tab!);
      setState(() {
        _activity.insert(
          0,
          _ActivityEvent(command.label, command.icon),
        );
      });
      return;
    }
    if (command.routeIndex != null) {
      widget.onNavigate?.call(command.routeIndex!);
      return;
    }
  }

  @override
  Widget build(BuildContext context) {
    final query = _commandController.text.trim().toLowerCase();
    final matches = _commands
        .where((item) => item.label.toLowerCase().contains(query))
        .toList();

    return Shortcuts(
      shortcuts: <ShortcutActivator, Intent>{
        const SingleActivator(LogicalKeyboardKey.keyK, control: true):
            const _OpenCommandIntent(),
        const SingleActivator(LogicalKeyboardKey.keyK, meta: true):
            const _OpenCommandIntent(),
      },
      child: Actions(
        actions: <Type, Action<Intent>>{
          _OpenCommandIntent: CallbackAction<_OpenCommandIntent>(
            onInvoke: (_) {
              _commandFocus.requestFocus();
              return null;
            },
          ),
        },
        child: Focus(
          autofocus: true,
          child: Scaffold(
            appBar: AppBar(
              title: Row(
                children: <Widget>[
                  ScaleTransition(
                    scale: _pulse,
                    child: const Icon(Icons.radar_outlined, size: 22),
                  ),
                  const SizedBox(width: 10),
                  const Text('Control Center'),
                  const SizedBox(width: 10),
                  _LiveBadge(simulation: _simulation),
                ],
              ),
              actions: <Widget>[
                FilterChip(
                  selected: _simulation,
                  avatar: const Icon(Icons.science_outlined, size: 17),
                  label: Text(_simulation ? 'SIMULATION' : 'LIVE'),
                  onSelected: (_) => _toggleSimulation(),
                ),
                const SizedBox(width: 8),
                IconButton(
                  tooltip: 'Refresh system',
                  onPressed: _loading ? null : _refresh,
                  icon: _loading
                      ? const SizedBox.square(
                          dimension: 18,
                          child: CircularProgressIndicator(strokeWidth: 2),
                        )
                      : const Icon(Icons.refresh),
                ),
                const SizedBox(width: 8),
              ],
            ),
            body: Column(
              children: <Widget>[
                Padding(
                  padding: const EdgeInsets.fromLTRB(16, 12, 16, 8),
                  child: TextField(
                    focusNode: _commandFocus,
                    controller: _commandController,
                    onChanged: (_) => setState(() {}),
                    onSubmitted: (_) {
                      if (matches.length == 1) _runCommand(matches.single);
                    },
                    decoration: InputDecoration(
                      prefixIcon: const Icon(Icons.search),
                      hintText: 'Command, navigation, inspect…',
                      suffixText: 'Ctrl/⌘ K',
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
                      children: matches
                          .take(8)
                          .map(
                            (item) => ListTile(
                              leading: Icon(item.icon),
                              title: Text(item.label),
                              trailing: const Icon(Icons.chevron_right),
                              onTap: () => _runCommand(item),
                            ),
                          )
                          .toList(),
                    ),
                  ),
                TabBar(
                  controller: _tabs,
                  isScrollable: true,
                  tabs: const <Tab>[
                    Tab(text: 'Overview', icon: Icon(Icons.dashboard_outlined)),
                    Tab(text: 'Activity', icon: Icon(Icons.timeline_outlined)),
                    Tab(text: 'State', icon: Icon(Icons.account_tree_outlined)),
                    Tab(text: 'System Map', icon: Icon(Icons.hub_outlined)),
                    Tab(text: 'Evidence', icon: Icon(Icons.fact_check_outlined)),
                    Tab(text: 'Inspector', icon: Icon(Icons.manage_search_outlined)),
                  ],
                ),
                Expanded(
                  child: TabBarView(
                    controller: _tabs,
                    children: <Widget>[
                      _Overview(
                        health: _health,
                        brain: _brain,
                        providers: _providers,
                        agents: _agents,
                        simulation: _simulation,
                        pulse: _pulse,
                      ),
                      _Activity(events: _activity),
                      _StateView(health: _health, brain: _brain),
                      _SystemMap(
                        health: _health,
                        brain: _brain,
                        agents: _agents,
                        pulse: _pulse,
                      ),
                      _EvidenceView(health: _health),
                      _Inspector(
                        health: _health,
                        brain: _brain,
                        providers: _providers,
                        agents: _agents,
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class _OpenCommandIntent extends Intent {
  const _OpenCommandIntent();
}

class _Command {
  const _Command(
    this.label,
    this.icon, {
    this.tab,
    this.routeIndex,
  });

  final String label;
  final IconData icon;
  final int? tab;
  final int? routeIndex;
}

class _ActivityEvent {
  const _ActivityEvent(this.label, this.icon);

  final String label;
  final IconData icon;
}

class _LiveBadge extends StatelessWidget {
  const _LiveBadge({required this.simulation});

  final bool simulation;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return DecoratedBox(
      decoration: BoxDecoration(
        color: simulation
            ? scheme.tertiaryContainer
            : scheme.primaryContainer,
        borderRadius: BorderRadius.circular(20),
      ),
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 9, vertical: 4),
        child: Text(
          simulation ? 'SIMULATION' : 'LIVE',
          style: Theme.of(context).textTheme.labelSmall?.copyWith(
                fontWeight: FontWeight.w800,
              ),
        ),
      ),
    );
  }
}

class _Overview extends StatelessWidget {
  const _Overview({
    required this.health,
    required this.brain,
    required this.providers,
    required this.agents,
    required this.simulation,
    required this.pulse,
  });

  final Map<String, dynamic>? health;
  final Map<String, dynamic>? brain;
  final Map<String, dynamic>? providers;
  final Map<String, dynamic>? agents;
  final bool simulation;
  final Animation<double> pulse;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final status = health?['status']?.toString() ?? 'UNKNOWN';
    final capabilities = (health?['capabilities'] as List?)?.length ?? 0;
    final skills = (brain?['skills'] as List?)?.length ?? 0;
    final providerCount = (providers?['providers'] as List?)?.length ?? 0;
    final agentCount = (agents?['agents'] as List?)?.length ?? 0;

    return ListView(
      padding: const EdgeInsets.all(16),
      children: <Widget>[
        Card(
          child: Padding(
            padding: const EdgeInsets.all(18),
            child: Row(
              children: <Widget>[
                ScaleTransition(
                  scale: pulse,
                  child: Icon(
                    status.toUpperCase() == 'OK'
                        ? Icons.check_circle_outline
                        : Icons.help_outline,
                    size: 32,
                    color: status.toUpperCase() == 'OK'
                        ? scheme.primary
                        : scheme.error,
                  ),
                ),
                const SizedBox(width: 14),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: <Widget>[
                      Text(
                        status.toUpperCase() == 'OK'
                            ? 'Research OS is responding'
                            : 'Research OS state is unresolved',
                        style: Theme.of(context).textTheme.titleMedium?.copyWith(
                              fontWeight: FontWeight.w800,
                            ),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        simulation
                            ? 'Simulation is active. Actions are prepared without implying live execution.'
                            : 'Live observation is enabled. Unknown values remain UNKNOWN.',
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
        ),
        const SizedBox(height: 12),
        Wrap(
          spacing: 12,
          runSpacing: 12,
          children: <Widget>[
            _MetricCard(label: 'Runtime', value: status, icon: Icons.dns_outlined),
            _MetricCard(label: 'Capabilities', value: '$capabilities', icon: Icons.extension_outlined),
            _MetricCard(label: 'Brain skills', value: '$skills', icon: Icons.psychology_alt_outlined),
            _MetricCard(label: 'Providers', value: '$providerCount', icon: Icons.cloud_outlined),
            _MetricCard(label: 'Agents', value: '$agentCount', icon: Icons.smart_toy_outlined),
          ],
        ),
        const SizedBox(height: 16),
        _QuickActions(onNavigate: widgetOnNavigate(context)),
      ],
    );
  }

  ValueChanged<int>? widgetOnNavigate(BuildContext context) {
    final state = context.findAncestorStateOfType<_NativeControlCenterPageState>();
    return state?.widget.onNavigate;
  }
}

class _QuickActions extends StatelessWidget {
  const _QuickActions({required this.onNavigate});

  final ValueChanged<int>? onNavigate;

  @override
  Widget build(BuildContext context) {
    final actions = <(String, IconData, int)>[
      ('Friend', Icons.forum_outlined, 1),
      ('Runtime', Icons.monitor_heart_outlined, 8),
      ('Brain', Icons.psychology_alt_outlined, 11),
      ('Settings', Icons.settings_outlined, 9),
    ];
    return Wrap(
      spacing: 10,
      runSpacing: 10,
      children: actions
          .map(
            (item) => OutlinedButton.icon(
              onPressed: onNavigate == null ? null : () => onNavigate!(item.$3),
              icon: Icon(item.$2),
              label: Text(item.$1),
            ),
          )
          .toList(),
    );
  }
}

class _MetricCard extends StatelessWidget {
  const _MetricCard({
    required this.label,
    required this.value,
    required this.icon,
  });

  final String label;
  final String value;
  final IconData icon;

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: 190,
      child: Card(
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Row(
            children: <Widget>[
              Icon(icon),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: <Widget>[
                    Text(label, style: Theme.of(context).textTheme.labelMedium),
                    const SizedBox(height: 4),
                    Text(
                      value,
                      style: Theme.of(context).textTheme.titleLarge?.copyWith(
                            fontWeight: FontWeight.w800,
                          ),
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
}

class _Activity extends StatelessWidget {
  const _Activity({required this.events});
  final List<_ActivityEvent> events;

  @override
  Widget build(BuildContext context) {
    return ListView.builder(
      padding: const EdgeInsets.all(16),
      itemCount: events.length,
      itemBuilder: (context, index) {
        final event = events[index];
        return Card(
          child: ListTile(
            leading: Icon(event.icon),
            title: Text(event.label),
            trailing: Text(
              index == 0 ? 'NOW' : 'RECENT',
              style: Theme.of(context).textTheme.labelSmall,
            ),
          ),
        );
      },
    );
  }
}

class _StateView extends StatelessWidget {
  const _StateView({required this.health, required this.brain});
  final Map<String, dynamic>? health;
  final Map<String, dynamic>? brain;

  @override
  Widget build(BuildContext context) {
    return _JsonView(
      title: 'Current state',
      data: <String, dynamic>{
        'health': health ?? const <String, dynamic>{},
        'brain': brain ?? const <String, dynamic>{},
      },
    );
  }
}

class _SystemMap extends StatelessWidget {
  const _SystemMap({
    required this.health,
    required this.brain,
    required this.agents,
    required this.pulse,
  });

  final Map<String, dynamic>? health;
  final Map<String, dynamic>? brain;
  final Map<String, dynamic>? agents;
  final Animation<double> pulse;

  @override
  Widget build(BuildContext context) {
    final status = health?['status']?.toString() ?? 'UNKNOWN';
    final nodes = <_SystemNode>[
      _SystemNode('CORE', status, Icons.memory_outlined),
      _SystemNode('FRIEND', agents == null ? 'UNKNOWN' : 'OBSERVED', Icons.forum_outlined),
      _SystemNode('BRAIN', brain == null ? 'UNKNOWN' : 'OBSERVED', Icons.psychology_alt_outlined),
      _SystemNode('ASSURANCE', 'BOUNDARY ACTIVE', Icons.verified_outlined),
    ];

    return ListView(
      padding: const EdgeInsets.all(16),
      children: <Widget>[
        Text(
          'Live system map',
          style: Theme.of(context).textTheme.titleLarge?.copyWith(
                fontWeight: FontWeight.w800,
              ),
        ),
        const SizedBox(height: 8),
        Text('Select a node to inspect the currently observed state.'),
        const SizedBox(height: 16),
        ...nodes.map(
          (node) => Card(
            child: ListTile(
              leading: ScaleTransition(
                scale: pulse,
                child: Icon(
                  node.state == 'UNKNOWN'
                      ? Icons.help_outline
                      : Icons.circle,
                  color: node.state == 'UNKNOWN'
                      ? Theme.of(context).colorScheme.outline
                      : Theme.of(context).colorScheme.primary,
                  size: 18,
                ),
              ),
              title: Text(node.name),
              subtitle: Text(node.state),
              trailing: const Icon(Icons.chevron_right),
            ),
          ),
        ),
      ],
    );
  }
}

class _SystemNode {
  const _SystemNode(this.name, this.state, this.icon);

  final String name;
  final String state;
  final IconData icon;
}

class _EvidenceView extends StatelessWidget {
  const _EvidenceView({required this.health});
  final Map<String, dynamic>? health;

  @override
  Widget build(BuildContext context) {
    return _JsonView(
      title: 'Evidence / observation',
      data: health ?? const <String, dynamic>{},
    );
  }
}

class _Inspector extends StatelessWidget {
  const _Inspector({
    required this.health,
    required this.brain,
    required this.providers,
    required this.agents,
  });

  final Map<String, dynamic>? health;
  final Map<String, dynamic>? brain;
  final Map<String, dynamic>? providers;
  final Map<String, dynamic>? agents;

  @override
  Widget build(BuildContext context) {
    return _JsonView(
      title: 'Universal Inspector',
      data: <String, dynamic>{
        'health': health ?? const <String, dynamic>{},
        'brain': brain ?? const <String, dynamic>{},
        'providers': providers ?? const <String, dynamic>{},
        'agents': agents ?? const <String, dynamic>{},
      },
    );
  }
}

class _JsonView extends StatelessWidget {
  const _JsonView({required this.title, required this.data});

  final String title;
  final Map<String, dynamic> data;

  @override
  Widget build(BuildContext context) {
    final entries = data.entries.toList();
    if (entries.isEmpty) {
      return Center(
        child: Text(
          'UNKNOWN — no observation available yet.',
          style: Theme.of(context).textTheme.bodyLarge,
        ),
      );
    }
    return ListView(
      padding: const EdgeInsets.all(16),
      children: <Widget>[
        Text(
          title,
          style: Theme.of(context).textTheme.titleLarge?.copyWith(
                fontWeight: FontWeight.w700,
              ),
        ),
        const SizedBox(height: 12),
        ...entries.map(
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
}
