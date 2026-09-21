import 'package:flutter/material.dart';

import '../../api/research_os_api_client.dart';

class NativeControlCenterPage extends StatefulWidget {
  const NativeControlCenterPage({required this.apiClient, super.key});

  final ResearchOSApiClient apiClient;

  @override
  State<NativeControlCenterPage> createState() => _NativeControlCenterPageState();
}

class _NativeControlCenterPageState extends State<NativeControlCenterPage>
    with SingleTickerProviderStateMixin {
  late final TabController _tabs;
  final _commandController = TextEditingController();
  bool _loading = false;
  bool _simulation = false;
  Map<String, dynamic>? _health;
  Map<String, dynamic>? _brain;
  Map<String, dynamic>? _providers;
  Map<String, dynamic>? _agents;
  final List<String> _activity = <String>[
    'Control Center initialized',
    'Human authority boundary active',
  ];

  static const _commands = <String>[
    'Refresh system',
    'Open Research',
    'Open Friend',
    'Open Runtime',
    'Open Evidence',
    'Simulation mode',
  ];

  @override
  void initState() {
    super.initState();
    _tabs = TabController(length: 6, vsync: this);
    _refresh();
  }

  @override
  void dispose() {
    _tabs.dispose();
    _commandController.dispose();
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
        _activity.insert(0, 'System state observed');
      });
    } catch (error) {
      if (!mounted) return;
      setState(() => _activity.insert(0, 'System observation unavailable: $error'));
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  void _runCommand(String value) {
    final command = value.trim();
    if (command.isEmpty) return;
    _commandController.clear();
    switch (command) {
      case 'Refresh system':
        _refresh();
      case 'Simulation mode':
        setState(() {
          _simulation = !_simulation;
          _activity.insert(
            0,
            _simulation
                ? 'Simulation mode enabled'
                : 'Simulation mode disabled',
          );
        });
      default:
        setState(() => _activity.insert(0, '$command prepared'));
    }
  }

  @override
  Widget build(BuildContext context) {
    final query = _commandController.text.trim().toLowerCase();
    final matches = _commands
        .where((item) => item.toLowerCase().contains(query))
        .toList();

    return Scaffold(
      appBar: AppBar(
        title: const Text('Control Center'),
        actions: <Widget>[
          FilterChip(
            selected: _simulation,
            avatar: const Icon(Icons.science_outlined, size: 17),
            label: Text(_simulation ? 'SIMULATION' : 'LIVE'),
            onSelected: (_) => _runCommand('Simulation mode'),
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
              controller: _commandController,
              onChanged: (_) => setState(() {}),
              onSubmitted: _runCommand,
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
                children: matches.map((item) {
                  return ListTile(
                    leading: const Icon(Icons.bolt_outlined),
                    title: Text(item),
                    onTap: () => _runCommand(item),
                  );
                }).toList(),
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
                ),
                _Activity(events: _activity),
                _StateView(health: _health, brain: _brain),
                _SystemMap(health: _health, brain: _brain, agents: _agents),
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
  });

  final Map<String, dynamic>? health;
  final Map<String, dynamic>? brain;
  final Map<String, dynamic>? providers;
  final Map<String, dynamic>? agents;
  final bool simulation;

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
        if (simulation)
          Card(
            color: scheme.tertiaryContainer,
            child: const ListTile(
              leading: Icon(Icons.science_outlined),
              title: Text('Simulation mode'),
              subtitle: Text(
                'Commands are prepared only; live execution is not implied.',
              ),
            ),
          ),
        Wrap(
          spacing: 12,
          runSpacing: 12,
          children: <Widget>[
            _MetricCard(
              label: 'Runtime',
              value: status,
              icon: Icons.dns_outlined,
            ),
            _MetricCard(
              label: 'Capabilities',
              value: '$capabilities',
              icon: Icons.extension_outlined,
            ),
            _MetricCard(
              label: 'Brain skills',
              value: '$skills',
              icon: Icons.psychology_alt_outlined,
            ),
            _MetricCard(
              label: 'Providers',
              value: '$providerCount',
              icon: Icons.cloud_outlined,
            ),
            _MetricCard(
              label: 'Agents',
              value: '$agentCount',
              icon: Icons.smart_toy_outlined,
            ),
          ],
        ),
      ],
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
  final List<String> events;

  @override
  Widget build(BuildContext context) {
    return ListView.builder(
      padding: const EdgeInsets.all(16),
      itemCount: events.length,
      itemBuilder: (context, index) => Card(
        child: ListTile(
          leading: const Icon(Icons.bolt_outlined),
          title: Text(events[index]),
        ),
      ),
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
  });

  final Map<String, dynamic>? health;
  final Map<String, dynamic>? brain;
  final Map<String, dynamic>? agents;

  @override
  Widget build(BuildContext context) {
    final nodes = <String, Map<String, dynamic>>{
      'CORE': health ?? const <String, dynamic>{},
      'BRAIN': brain ?? const <String, dynamic>{},
      'AGENTS': agents ?? const <String, dynamic>{},
    };
    return ListView(
      padding: const EdgeInsets.all(16),
      children: nodes.entries
          .map(
            (entry) => Card(
              child: ListTile(
                leading: const Icon(Icons.hub_outlined),
                title: Text(entry.key),
                subtitle: Text(
                  entry.value.isEmpty ? 'UNKNOWN' : 'Observed',
                ),
              ),
            ),
          )
          .toList(),
    );
  }
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
