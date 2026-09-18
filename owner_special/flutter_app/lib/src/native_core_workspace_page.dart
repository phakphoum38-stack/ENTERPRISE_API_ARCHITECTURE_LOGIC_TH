import 'package:flutter/material.dart';

import 'owner_api.dart';

class NativeCoreWorkspacePage extends StatefulWidget {
  const NativeCoreWorkspacePage({required this.api, this.onNavigate, super.key});
  final OwnerFriendApi api;
  final ValueChanged<int>? onNavigate;

  @override
  State<NativeCoreWorkspacePage> createState() => _NativeCoreWorkspacePageState();
}

class _NativeCoreWorkspacePageState extends State<NativeCoreWorkspacePage>
    with SingleTickerProviderStateMixin {
  late final TabController _tabs;
  final _command = TextEditingController();
  final _inspector = TextEditingController();
  Map<String, dynamic>? _status;
  bool _loading = false;
  bool _simulation = false;
  String _selectedObject = '';
  final List<String> _events = <String>[
    'Control Center initialized',
    'Human authority boundary active',
  ];

  static const commands = <String>[
    'Open Research', 'Open Friend', 'Open Runtime', 'Open Evidence',
    'Inspect object', 'Simulation mode', 'Refresh runtime',
  ];

  @override
  void initState() {
    super.initState();
    _tabs = TabController(length: 6, vsync: this);
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
    setState(() => _loading = true);
    try {
      final status = await widget.api.status();
      if (!mounted) return;
      setState(() {
        _status = status;
        _events.insert(0, 'Runtime status observed');
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
        _events.insert(0, _simulation ? 'Simulation mode enabled' : 'Simulation mode disabled');
      });
      _tabs.animateTo(0);
      return;
    }
    const routes = <String, int>{
      'Open Research': 1, 'Open Runtime': 1, 'Open Friend': 2, 'Open Evidence': 4,
    };
    final route = routes[command];
    if (route != null) {
      widget.onNavigate?.call(route);
      setState(() => _events.insert(0, '$command prepared'));
      return;
    }
    if (command == 'Inspect object') _tabs.animateTo(4);
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final query = _command.text.trim().toLowerCase();
    final matches = commands.where((item) => item.toLowerCase().contains(query)).take(8).toList();

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Row(children: [
          Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text('Native Core Workspace',
                style: theme.textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.w700)),
            const SizedBox(height: 3),
            Text('Command • Activity • State • Evidence • Inspector • Simulation',
                style: theme.textTheme.bodySmall?.copyWith(color: theme.colorScheme.onSurfaceVariant)),
          ])),
          FilterChip(
            selected: _simulation,
            onSelected: (value) => setState(() {
              _simulation = value;
              _events.insert(0, value ? 'Simulation mode enabled' : 'Simulation mode disabled');
            }),
            avatar: const Icon(Icons.science_outlined, size: 17),
            label: Text(_simulation ? 'SIMULATION' : 'LIVE'),
          ),
          const SizedBox(width: 8),
          IconButton(
            tooltip: 'Refresh runtime',
            onPressed: _loading ? null : _load,
            icon: _loading
                ? const SizedBox.square(dimension: 18, child: CircularProgressIndicator(strokeWidth: 2))
                : const Icon(Icons.refresh),
          ),
        ]),
        const SizedBox(height: 12),
        TextField(
          controller: _command,
          onChanged: (_) => setState(() {}),
          onSubmitted: _runCommand,
          decoration: InputDecoration(
            prefixIcon: const Icon(Icons.search),
            suffixText: 'Ctrl/⌘ K',
            hintText: 'Command, navigation, inspect…',
            border: OutlineInputBorder(borderRadius: BorderRadius.circular(14)),
          ),
        ),
        if (query.isNotEmpty)
          Card(
            child: Column(
              children: matches.isEmpty
                  ? [const ListTile(title: Text('No matching command'))]
                  : matches.map((item) => ListTile(
                        leading: const Icon(Icons.bolt_outlined),
                        title: Text(item),
                        subtitle: const Text('Prepared through the native control lifecycle'),
                        onTap: () => _runCommand(item),
                      )).toList(),
            ),
          ),
        const SizedBox(height: 8),
        TabBar(controller: _tabs, isScrollable: true, tabs: const [
          Tab(text: 'Overview', icon: Icon(Icons.dashboard_outlined)),
          Tab(text: 'Activity', icon: Icon(Icons.timeline_outlined)),
          Tab(text: 'State', icon: Icon(Icons.account_tree_outlined)),
          Tab(text: 'Evidence', icon: Icon(Icons.fact_check_outlined)),
          Tab(text: 'Inspector', icon: Icon(Icons.manage_search_outlined)),
          Tab(text: 'Simulation', icon: Icon(Icons.science_outlined)),
        ]),
        const SizedBox(height: 8),
        Expanded(child: TabBarView(controller: _tabs, children: [
          _Overview(status: _status, simulation: _simulation),
          _Activity(events: _events),
          _StateView(status: _status),
          _EvidenceView(status: _status),
          _Inspector(controller: _inspector, selectedObject: _selectedObject, onInspect: (id) {
            setState(() {
              _selectedObject = id;
              _events.insert(0, 'Inspector opened: $id);
            });
          }),
          _Simulation(enabled: _simulation, onToggle: (value) => setState(() {
            _simulation = value;
            _events.insert(0, value ? 'Simulation mode enabled' : 'Simulation mode disabled');
          })),
        ])),
      ],
    );
  }
}

class _Overview extends StatelessWidget {
  const _Overview({required this.status, required this.simulation});
  final Map<String, dynamic>? status;
  final bool simulation;

  @override
  Widget build(BuildContext context) {
    final brain = status?['brain_profiles'] is Map
        ? Map<String, dynamic>.from(status!['brain_profiles'] as Map)
        : const <String, dynamic>{};
    final helper = status?['helper_scheduler'] is Map
        ? Map<String, dynamic>.from(status!['helper_scheduler'] as Map)
        : const <String, dynamic>{};
    final caps = (status?['capabilities'] as List? ?? const <Object>[]).length;
    return ListView(children: [
      if (simulation)
        const Card(child: ListTile(
          leading: Icon(Icons.science_outlined),
          title: Text('Simulation mode'),
          subtitle: Text('Actions are prepared for inspection and do not imply release authority.'),
        )),
      Wrap(spacing: 10, runSpacing: 10, children: [
        _Metric('Brain profiles', brain.length.toString()),
        _Metric('Active workers', helper['max_active_workers']?.toString() ?? 'UNKNOWN'),
        _Metric('Logical helpers', helper['max_logical_helpers']?.toString() ?? 'UNKNOWN'),
        _Metric('Capabilities', caps.toString()),
      ]),
      const SizedBox(height: 12),
      const _BoundaryCard(),
    ]);
  }
}

class _Activity extends StatelessWidget {
  const _Activity({required this.events});
  final List<String> events;

  @override
  Widget build(BuildContext context) => ListView.separated(
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
  const _StateView({required this.status});
  final Map<String, dynamic>? status;

  @override
  Widget build(BuildContext context) {
    final helper = status?['helper_scheduler'];
    final capabilities = status?['capabilities'];
    return ListView(children: [
      _StateRow('Control plane', status == null ? 'UNKNOWN' : 'OBSERVED',
          'GUI → CONTROL → OBSERVE → EVIDENCE'),
      _StateRow('Runtime service', status == null ? 'UNKNOWN' : 'OBSERVED',
          'Read from Owner Friend API'),
      _StateRow('Worker capacity', helper is Map ? 'OBSERVED' : 'UNKNOWN',
          helper is Map ? helper.toString() : 'Backend did not expose scheduler state'),
      _StateRow('Capabilities', capabilities is List ? 'OBSERVED' : 'UNKNOWN',
          capabilities is List ? '${capabilities.length} capability entries' : 'Not exposed'),
      const SizedBox(height: 12),
      const Card(child: ListTile(
        leading: Icon(Icons.lock_outline),
        title: Text('Authority boundary'),
        subtitle: Text('Approve • Authorize • Release remain human-controlled.'),
      )),
    ]);
  }
}

class _EvidenceView extends StatelessWidget {
  const _EvidenceView({required this.status});
  final Map<String, dynamic>? status;

  @override
  Widget build(BuildContext context) {
    final raw = status?['evidence'];
    if (raw is! List || raw.isEmpty) {
      return const Card(child: ListTile(
        leading: Icon(Icons.info_outline),
        title: Text('Evidence data unavailable'),
        subtitle: Text('No evidence collection is exposed by the current API response. The UI will not fabricate evidence.'),
      ));
    }
    return ListView.builder(
      itemCount: raw.length,
      itemBuilder: (_, index) {
        final item = raw[index];
        final title = item is Map ? item['id']?.toString() ?? 'Evidence' : item.toString();
        return ListTile(
          leading: const Icon(Icons.verified_outlined),
          title: Text(title),
          subtitle: Text(item is Map ? item.toString() : 'Observed evidence item'),
        );
      },
    );
  }
}

class _Inspector extends StatelessWidget {
  const _Inspector({required this.controller, required this.selectedObject, required this.onInspect});
  final TextEditingController controller;
  final String selectedObject;
  final ValueChanged<String> onInspect;

  @override
  Widget build(BuildContext context) => ListView(children: [
    Row(crossAxisAlignment: CrossAxisAlignment.end, children: [
      Expanded(child: TextField(
        controller: controller,
        onSubmitted: onInspect,
        decoration: const InputDecoration(labelText: 'Object ID', hintText: 'task, source, evidence, service…'),
      )),
      const SizedBox(width: 10),
      FilledButton(onPressed: () => onInspect(controller.text.trim()), child: const Text('Inspect')),
    ]),
    const SizedBox(height: 12),
    if (selectedObject.isEmpty)
      const Card(child: ListTile(
        leading: Icon(Icons.manage_search_outlined),
        title: Text('Select an object to inspect'),
        subtitle: Text('Identity • State • Owner • Version • Relations • Provenance • Evidence • History • Recovery'),
      ))
    else
      _InspectorCard(id: selectedObject),
  ]);
}

class _InspectorCard extends StatelessWidget {
  const _InspectorCard({required this.id});
  final String id;

  @override
  Widget build(BuildContext context) => Card(child: Column(children: [
    ListTile(
      leading: const Icon(Icons.inventory_2_outlined),
      title: Text(id),
      subtitle: const Text('Bounded inspection surface — no authority grant'),
    ),
    const _Detail('Identity', 'Observed from selected object reference'),
    const _Detail('State', 'UNKNOWN until object state is exposed'),
    const _Detail('Provenance', 'UNKNOWN until evidence lineage is exposed'),
    const _Detail('Recovery', 'Inspect-only; recovery remains controlled'),
  ]));
}

class _Simulation extends StatelessWidget {
  const _Simulation({required this.enabled, required this.onToggle});
  final bool enabled;
  final ValueChanged<bool> onToggle;

  @override
  Widget build(BuildContext context) => ListView(children: [
    SwitchListTile(
      value: enabled,
      onChanged: onToggle,
      title: const Text('Simulation / Dry Run'),
      subtitle: const Text('Prepare and inspect a lifecycle without treating preparation as authorization.'),
      secondary: const Icon(Icons.science_outlined),
    ),
    const _LifecycleCard(),
  ]);
}

class _BoundaryCard extends StatelessWidget {
  const _BoundaryCard();

  @override
  Widget build(BuildContext context) => const Card(child: Padding(
    padding: EdgeInsets.all(16),
    child: Wrap(spacing: 8, runSpacing: 8, children: [
      Chip(avatar: Icon(Icons.check, size: 16), label: Text('Observe')),
      Chip(avatar: Icon(Icons.check, size: 16), label: Text('Analyze')),
      Chip(avatar: Icon(Icons.check, size: 16), label: Text('Research')),
      Chip(avatar: Icon(Icons.check, size: 16), label: Text('Prepare')),
      Chip(avatar: Icon(Icons.lock_outline, size: 16), label: Text('Approve — human')),
      Chip(avatar: Icon(Icons.lock_outline, size: 16), label: Text('Authorize — human')),
      Chip(avatar: Icon(Icons.lock_outline, size: 16), label: Text('Release — human')),
    ]),
  ));
}

class _LifecycleCard extends StatelessWidget {
  const _LifecycleCard();

  @override
  Widget build(BuildContext context) => const Card(child: Padding(
    padding: EdgeInsets.all(16),
    child: Text('INTENT → VALIDATE → AUTHORIZE → EXECUTE → OBSERVE → EVIDENCE → COMPLETE'),
  ));
}

class _StateRow extends StatelessWidget {
  const _StateRow(this.name, this.state, this.detail);
  final String name;
  final String state;
  final String detail;

  @override
  Widget build(BuildContext context) => Card(child: ListTile(
    leading: const Icon(Icons.circle, size: 11),
    title: Text(name),
    subtitle: Text(detail),
    trailing: Text(state),
  ));
}

class _Detail extends StatelessWidget {
  const _Detail(this.name, this.value);
  final String name;
  final String value;

  @override
  Widget build(BuildContext context) => ListTile(dense: true, title: Text(name), subtitle: Text(value));
}

class _Metric extends StatelessWidget {
  const _Metric(this.label, this.value);
  final String label;
  final String value;

  @override
  Widget build(BuildContext context) => SizedBox(
    width: 190,
    child: Card(margin: EdgeInsets.zero, child: Padding(
      padding: const EdgeInsets.all(14),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Text(label, style: Theme.of(context).textTheme.bodySmall),
        const SizedBox(height: 5),
        Text(value, style: Theme.of(context).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w700)),
      ]),
    )),
  );
}
