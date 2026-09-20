import 'package:flutter/material.dart';

import 'package:research_os_contracts/research_os_contracts.dart';

import 'owner_api.dart';

class NativeCoreWorkspacePage extends StatefulWidget {
  const NativeCoreWorkspacePage({required this.api, this.runtimeCapability, this.onNavigate, super.key});
  final OwnerFriendApi api;
  final RuntimeStatusCapability? runtimeCapability;
  final ValueChanged<int>? onNavigate;

  @override
  State<NativeCoreWorkspacePage> createState() => _NativeCoreWorkspacePageState();
}

class _NativeCoreWorkspacePageState extends State<NativeCoreWorkspacePage>
    with SingleTickerProviderStateMixin {
  late final TabController _tabs;
  final _command = TextEditingController();
  final _inspector = TextEditingController();
  final _targetSha = TextEditingController();
  Map<String, dynamic>? _status;
  bool _loading = false;
  bool _simulation = true;
  String _selectedObject = '';
  final List<String> _events = <String>[
    'Control Center initialized',
    'Human authority boundary active',
  ];
  int _livePulse = 0;

  static const commands = <_CommandDefinition>[
    _CommandDefinition(id: 'CMD-GENERATE-ORCHESTRATOR', label: 'Run Generate Orchestrator', target: 'generate-orchestrator.yml', risk: 'LOW', defaultMode: 'SIMULATION', description: 'Resolve the canonical workflow binding and prepare a workflow_dispatch preview.', keywords: 'generate orchestrator workflow actions build'),
    _CommandDefinition(id: 'CMD-INSPECT-EVIDENCE', label: 'Inspect Evidence', target: 'evidence', risk: 'LOW', defaultMode: 'SIMULATION', description: 'Open the evidence projection without fabricating missing lineage.', keywords: 'inspect evidence provenance lineage hash'),
  ];
  static const _navigationCommands = <String>[
    'Open Research', 'Open Friend', 'Open Runtime', 'Open Evidence',
    'Inspect object', 'Simulation mode',
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
    _targetSha.dispose();
    super.dispose();
  }

  Future<void> _load() async {
    setState(() => _loading = true);
    try {
      final status = await (widget.runtimeCapability ?? _OwnerRuntimeCapability(widget.api)).runtimeStatus();
      if (!mounted) return;
      setState(() {
        _status = status;
        _livePulse++;
        _events.insert(0, 'Runtime status observed');
      });
    } catch (error) {
      if (!mounted) return;
      setState(() => _events.insert(0, 'Runtime observation unavailable: ${error.toString()}'));
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  void _runCommand(String value) {
    final command = value.trim();
    if (command.isEmpty) return;
    _command.clear();
    _CommandDefinition? workflow;
    for (final item in commands) {
      if (item.label == command) {
        workflow = item;
        break;
      }
    }
    if (workflow != null) {
      _showCommandPreview(workflow);
      return;
    }
    if (command == 'Refresh Runtime') {
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

  Future<void> _showCommandPreview(_CommandDefinition command) async {
    final selectedMode = await showDialog<String>(
      context: context,
      builder: (context) => _CommandPreviewDialog(
        command: command,
        initialMode: command.defaultMode == 'LIVE' && !_simulation ? 'LIVE' : 'SIMULATION',
        targetShaController: _targetSha,
      ),
    );
    if (!mounted || selectedMode == null) return;
    setState(() {
      _simulation = selectedMode != 'LIVE';
      _events.insert(
        0,
        selectedMode == 'LIVE'
            ? '${command.id} authorization boundary reached; execution remains human-controlled'
            : '${command.id} prepared in simulation',
      );
    });
  }

  String _commandSubtitle(String label) {
    for (final command in commands) {
      if (command.label == label) {
        return '${command.id} • ${command.target} • risk ${command.risk} • default ${command.defaultMode}';
      }
    }
    return 'Prepared through the native control lifecycle';
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final query = _command.text.trim().toLowerCase();
    final workflowMatches = commands.where((item) =>
        item.label.toLowerCase().contains(query) ||
        item.id.toLowerCase().contains(query) ||
        item.target.toLowerCase().contains(query) ||
        item.keywords.toLowerCase().contains(query),
      );
    final matches = <String>[
      ...workflowMatches.map((item) => item.label),
      ..._navigationCommands.where((item) => item.toLowerCase().contains(query)),
      'Refresh Runtime',
    ].toSet().take(8).toList();

    return Material(
      child: SizedBox.expand(
        child: Column(
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
                            subtitle: Text(_commandSubtitle(item)),
                            onTap: () => _runCommand(item),
                          )).toList(),
                ),
              ),
            const SizedBox(height: 8),
            AnimatedContainer(
              duration: const Duration(milliseconds: 320),
              curve: Curves.easeOutCubic,
              height: _loading ? 3 : 1,
              decoration: BoxDecoration(
                color: _loading ? theme.colorScheme.primary : theme.colorScheme.outlineVariant,
                borderRadius: BorderRadius.circular(99),
              ),
              child: _loading ? const LinearProgressIndicator(minHeight: 3) : null,
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
              _Overview(key: ValueKey('overview-$_livePulse'), status: _status, simulation: _simulation),
              _Activity(events: _events),
              _StateView(status: _status),
              _EvidenceView(status: _status),
              _Inspector(controller: _inspector, selectedObject: _selectedObject, onInspect: (id) {
                setState(() {
                  _selectedObject = id;
                  _events.insert(0, 'Inspector opened: $id');
                });
              }),
              _Simulation(enabled: _simulation, onToggle: (value) => setState(() {
                _simulation = value;
                _events.insert(0, value ? 'Simulation mode enabled' : 'Simulation mode disabled');
              })),
            ])),
          ],
        ),
      ),
    );
  }
}

class _Overview extends StatelessWidget {
  const _Overview({super.key, required this.status, required this.simulation});
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
      const SizedBox(height: 12),
      _LiveSystemCard(online: status != null),
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
      title: AnimatedSwitcher(
        duration: const Duration(milliseconds: 240),
        child: Text(events[index], key: ValueKey(events[index])),
      ),
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

class _LiveSystemCard extends StatefulWidget {
  const _LiveSystemCard({required this.online});
  final bool online;

  @override
  State<_LiveSystemCard> createState() => _LiveSystemCardState();
}

class _LiveSystemCardState extends State<_LiveSystemCard>
    with SingleTickerProviderStateMixin {
  late final AnimationController _controller;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1500),
    )..repeat(reverse: true);
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final color = widget.online
        ? theme.colorScheme.primary
        : theme.colorScheme.outline;
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Row(
          children: [
            AnimatedBuilder(
              animation: _controller,
              builder: (context, child) => Opacity(
                opacity: widget.online ? .45 + (_controller.value * .55) : 1,
                child: Container(
                  width: 12,
                  height: 12,
                  decoration: BoxDecoration(
                    color: color,
                    shape: BoxShape.circle,
                    boxShadow: widget.online
                        ? [BoxShadow(color: color.withValues(alpha: .28), blurRadius: 10)]
                        : const [],
                  ),
                ),
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Text(
                widget.online ? 'LIVE SYSTEM — runtime observed' : 'SYSTEM STATE — waiting for runtime observation',
                style: theme.textTheme.titleSmall?.copyWith(fontWeight: FontWeight.w700),
              ),
            ),
            Text(
              widget.online ? 'LIVE' : 'UNKNOWN',
              style: theme.textTheme.labelMedium?.copyWith(
                color: color,
                fontWeight: FontWeight.w800,
              ),
            ),
          ],
        ),
      ),
    );
  }
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


final class _CommandDefinition {
  const _CommandDefinition({required this.id, required this.label, required this.target, required this.risk, required this.defaultMode, required this.description, required this.keywords});
  final String id;
  final String label;
  final String target;
  final String risk;
  final String defaultMode;
  final String description;
  final String keywords;
}

final class _CommandPreviewDialog extends StatefulWidget {
  const _CommandPreviewDialog({required this.command, required this.initialMode, required this.targetShaController});
  final _CommandDefinition command;
  final String initialMode;
  final TextEditingController targetShaController;
  @override State<_CommandPreviewDialog> createState() => _CommandPreviewDialogState();
}

class _CommandPreviewDialogState extends State<_CommandPreviewDialog> {
  late String _mode;
  bool _humanAuthorized = false;
  @override
  void initState() {
    super.initState();
    _mode = widget.initialMode;
  }
  bool get _shaValid => RegExp(r'^[0-9a-f]{64}$').hasMatch(widget.targetShaController.text.trim());
  @override
  Widget build(BuildContext context) {
    final live = _mode == 'LIVE';
    return AlertDialog(
      title: Row(children: [const Icon(Icons.bolt_outlined), const SizedBox(width: 10), Expanded(child: Text(widget.command.label))]),
      content: SizedBox(
        width: 620,
        child: SingleChildScrollView(
          child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
            Text(widget.command.description),
            const SizedBox(height: 16),
            Wrap(spacing: 8, runSpacing: 8, children: [
              Chip(label: Text(widget.command.id)),
              Chip(label: Text('Target: ${widget.command.target}')),
              Chip(label: Text('Risk: ${widget.command.risk}')),
            ]),
            const SizedBox(height: 14),
            SegmentedButton<String>(
              segments: const [
                ButtonSegment(value: 'SIMULATION', label: Text('SIMULATION'), icon: Icon(Icons.science_outlined)),
                ButtonSegment(value: 'LIVE', label: Text('LIVE'), icon: Icon(Icons.lock_outline)),
              ],
              selected: {_mode},
              onSelectionChanged: (value) => setState(() => _mode = value.first),
            ),
            const SizedBox(height: 14),
            TextField(
              controller: widget.targetShaController,
              onChanged: (_) => setState(() {}),
              decoration: InputDecoration(
                labelText: 'Exact target SHA-256',
                hintText: '64 lowercase hexadecimal characters',
                errorText: widget.targetShaController.text.isEmpty || _shaValid ? null : 'Must be exactly 64 lowercase hexadecimal characters',
                prefixIcon: const Icon(Icons.fingerprint),
              ),
            ),
            const SizedBox(height: 12),
            Card(child: ListTile(
              leading: Icon(live ? Icons.warning_amber_outlined : Icons.science_outlined),
              title: Text(live ? 'Human authorization required' : 'No live execution'),
              subtitle: Text(live ? 'Preview reaches the authorization boundary only. The UI does not self-authorize, merge, release, or dispatch a real workflow.' : 'Prepared for inspection only. Simulation is not execution.'),
            )),
            if (live) ...[
              CheckboxListTile(
                value: _humanAuthorized,
                onChanged: (value) => setState(() => _humanAuthorized = value ?? false),
                title: const Text('I explicitly authorize the LIVE execution boundary'),
                subtitle: const Text('Authorization is a human decision and is never inferred from observation or confidence.'),
                controlAffinity: ListTileControlAffinity.leading,
              ),
              const Text('LIVE dispatch is intentionally not invoked from this UI surface yet; no real GitHub Actions run will be started by this preview.'),
            ],
          ]),
        ),
      ),
      actions: [
        TextButton(onPressed: () => Navigator.of(context).pop(), child: const Text('Cancel')),
        FilledButton.icon(
          onPressed: _shaValid ? () => Navigator.of(context).pop(_mode) : null,
          icon: Icon(live && _humanAuthorized ? Icons.lock_open : Icons.play_arrow),
          label: Text(live ? (_humanAuthorized ? 'Authorize Boundary' : 'Review LIVE') : 'Prepare Simulation'),
        ),
      ],
    );
  }
}

final class _OwnerRuntimeCapability implements RuntimeStatusCapability {
  const _OwnerRuntimeCapability(this.api);
  final OwnerFriendApi api;
  @override
  Future<Map<String, dynamic>> runtimeStatus() => api.status();
}
