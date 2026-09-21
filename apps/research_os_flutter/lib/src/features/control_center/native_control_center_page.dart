import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../../api/research_os_api_client.dart';

class NativeControlCenterPage extends StatefulWidget {
  const NativeControlCenterPage({required this.apiClient, this.onNavigate, super.key});
  final ResearchOSApiClient apiClient;
  final ValueChanged<int>? onNavigate;

  @override
  State<NativeControlCenterPage> createState() => _NativeControlCenterPageState();
}

class _NativeControlCenterPageState extends State<NativeControlCenterPage>
    with TickerProviderStateMixin {
  late final TabController _tabs;
  late final AnimationController _pulse;
  final _command = TextEditingController();
  Timer? _timer;
  final _commandFocus = FocusNode();
  bool _loading = false;
  bool _simulation = false;
  Map<String, dynamic>? _health, _brain, _providers, _agents;
  final List<String> _activity = <String>[
    'Control Center initialized',
    'Human authority boundary active',
  ];

  static const _commands = <String>[
    'Refresh system', 'Open Home', 'Open Friend', 'Open Agents',
    'Open Library', 'Open Knowledge Graph', 'Open GitHub', 'Open Runtime',
    'Open Settings', 'Open Brain Skills', 'Open Evidence', 'Inspect object',
    'Show system map', 'Show failures', 'Show resources', 'Design Studio',
    'Simulation mode', 'Dry run', 'Replay',
  ];

  @override
  void initState() {
    super.initState();
    _tabs = TabController(length: 10, vsync: this);
    _pulse = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1400),
    )..repeat();
    _timer = Timer.periodic(const Duration(seconds: 20), (_) => _refresh());
    _refresh();
  }

  @override
  void dispose() {
    _timer?.cancel();
    _pulse.dispose();
    _tabs.dispose();
    _command.dispose();
    _commandFocus.dispose();
    super.dispose();
  }

  Future<void> _refresh() async {
    if (_loading) return;
    setState(() => _loading = true);
    try {
      final values = await Future.wait(<Future<Map<String, dynamic>>>[
        widget.apiClient.getHealth(),
        widget.apiClient.getBrainCapacity(),
        widget.apiClient.getProviders(),
        widget.apiClient.getAgents(),
      ]);
      if (!mounted) return;
      setState(() {
        _health = values[0];
        _brain = values[1];
        _providers = values[2];
        _agents = values[3];
        _activity.insert(0, 'Runtime state observed');
      });
    } catch (_) {
      if (!mounted) return;
      setState(() => _activity.insert(
            0,
            'Runtime observation unavailable; state remains UNKNOWN',
          ));
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  void _focusCommand() {
    _commandFocus.requestFocus();
    _command.selection = TextSelection.collapsed(offset: _command.text.length);
    setState(() {});
  }

  void _commandRun(String raw) {
    final value = raw.trim();
    if (value.isEmpty) return;
    _command.clear();
    if (value == 'Refresh system') {
      _refresh();
      return;
    }
    const navigation = <String, int>{
      'Open Home': 0,
      'Open Friend': 1,
      'Open Agents': 2,
      'Open Library': 3,
      'Open Knowledge Graph': 4,
      'Open GitHub': 5,
      'Open Runtime': 8,
      'Open Settings': 9,
      'Open Brain Skills': 11,
    };
    final destination = navigation[value];
    if (destination != null && widget.onNavigate != null) {
      widget.onNavigate!(destination);
      setState(() => _activity.insert(0, '$value navigated'));
      return;
    }
    if (value == 'Design Studio') {
      _tabs.index = 9;
      setState(() => _activity.insert(0, 'Design Studio opened'));
      return;
    }
    if (value == 'Simulation mode') {
      setState(() {
        _simulation = !_simulation;
        _activity.insert(
          0,
          _simulation ? 'Simulation mode enabled' : 'Live presentation restored',
        );
      });
      return;
    }
    final tab = <String, int>{
      'Show system map': 3,
      'Open Evidence': 4,
      'Inspect object': 5,
      'Show failures': 6,
      'Show resources': 7,
    }[value];
    if (tab != null) {
      _tabs.index = tab;
      setState(() => _activity.insert(0, '$value opened'));
      return;
    }
    setState(() => _activity.insert(
          0,
          '$value prepared; execution remains behind the authority boundary',
        ));
  }

  @override
  Widget build(BuildContext context) {
    final query = _command.text.trim().toLowerCase();
    final matches = _commands
        .where((item) => item.toLowerCase().contains(query))
        .take(8)
        .toList();
    final online = _health?['status']?.toString().toLowerCase() == 'ok';

    return CallbackShortcuts(
      bindings: <ShortcutActivator, VoidCallback>{
        const SingleActivator(LogicalKeyboardKey.keyK, control: true): _focusCommand,
        const SingleActivator(LogicalKeyboardKey.keyK, meta: true): _focusCommand,
        const SingleActivator(LogicalKeyboardKey.escape): () {
          _command.clear();
          FocusManager.instance.primaryFocus?.unfocus();
          setState(() {});
        },
      },
      child: Scaffold(
        appBar: AppBar(
        title: const Text('Research OS • Control Center'),
        actions: <Widget>[
          AnimatedBuilder(
            animation: _pulse,
            builder: (_, __) => Row(
              children: <Widget>[
                Transform.scale(
                  scale: online ? .85 + _pulse.value * .3 : 1,
                  child: Icon(
                    Icons.circle,
                    size: 11,
                    color: online
                        ? Theme.of(context).colorScheme.primary
                        : Theme.of(context).colorScheme.outline,
                  ),
                ),
                const SizedBox(width: 6),
                Text(online ? 'LIVE' : 'UNKNOWN'),
              ],
            ),
          ),
          const SizedBox(width: 10),
          FilterChip(
            selected: _simulation,
            avatar: const Icon(Icons.science_outlined, size: 17),
            label: Text(_simulation ? 'SIMULATION' : 'LIVE'),
            onSelected: (_) => _commandRun('Simulation mode'),
          ),
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
        ],
      ),
        body: Column(
          children: <Widget>[
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 12, 16, 8),
            child: TextField(
              focusNode: _commandFocus,
              controller: _command,
              onChanged: (_) => setState(() {}),
              onSubmitted: _commandRun,
              decoration: InputDecoration(
                prefixIcon: const Icon(Icons.search),
                hintText: 'Command, navigate, inspect, research…',
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
                    .map((item) => ListTile(
                          leading: const Icon(Icons.bolt_outlined),
                          title: Text(item),
                          onTap: () => _commandRun(item),
                        ))
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
              Tab(text: 'Failures', icon: Icon(Icons.warning_amber_outlined)),
              Tab(text: 'Resources', icon: Icon(Icons.memory_outlined)),
              Tab(text: 'Control', icon: Icon(Icons.lock_outline)),
              Tab(text: 'Design', icon: Icon(Icons.palette_outlined)),
            ],
          ),
          Expanded(
            child: AnimatedBuilder(
              animation: _tabs,
              builder: (context, _) => IndexedStack(
                index: _tabs.index,
                children: <Widget>[
                _Overview(
                  onNavigate: widget.onNavigate,
                  health: _health,
                  brain: _brain,
                  providers: _providers,
                  agents: _agents,
                  simulation: _simulation,
                  pulse: _pulse,
                ),
                _Activity(events: _activity),
                _JsonView(title: 'Observed system state', data: <String, dynamic>{
                  'health': _health ?? <String, dynamic>{},
                  'brain': _brain ?? <String, dynamic>{},
                  'providers': _providers ?? <String, dynamic>{},
                  'agents': _agents ?? <String, dynamic>{},
                }),
                _SystemMap(
                  health: _health,
                  brain: _brain,
                  providers: _providers,
                  agents: _agents,
                  pulse: _pulse,
                ),
                _JsonView(
                  title: 'Evidence / observation',
                  data: _health ?? <String, dynamic>{},
                ),
                _JsonView(
                  title: 'Universal Inspector',
                  data: <String, dynamic>{
                    'identity': 'control-center-runtime-observation',
                    'type': 'SYSTEM',
                    'state': _health == null ? 'UNKNOWN' : 'OBSERVED',
                    'owner': 'Research OS',
                    'version': 'current',
                    'provenance': 'Research OS API observation',
                    'authority': 'descriptive_only',
                  },
                ),
                const _UnknownCenter(
                  title: 'Failure Center',
                  icon: Icons.warning_amber_outlined,
                  message:
                      'No failure feed is exposed by the current API. UNKNOWN is preserved; failures are never invented.',
                ),
                const _UnknownCenter(
                  title: 'Resource Center',
                  icon: Icons.memory_outlined,
                  message:
                      'Runtime resource telemetry is not exposed by the current API. UNKNOWN is preserved.',
                ),
                const _ControlBoundary(),
                _DesignStudio(),
                ],
              ),
            ),
          ),
        ],
      ),
        ),
    );
  }
}

class _Overview extends StatelessWidget {
  const _Overview({
    required this.onNavigate,
    required this.health,
    required this.brain,
    required this.providers,
    required this.agents,
    required this.simulation,
    required this.pulse,
  });
  final ValueChanged<int>? onNavigate;
  final Map<String, dynamic>? health, brain, providers, agents;
  final bool simulation;
  final AnimationController pulse;

  @override
  Widget build(BuildContext context) {
    final status = health?['status']?.toString() ?? 'UNKNOWN';
    final values = <String, String>{
      'Runtime': status,
      'Capabilities': ((health?['capabilities'] as List?)?.length).toString(),
      'Brain skills': ((brain?['skills'] as List?)?.length).toString(),
      'Providers': ((providers?['providers'] as List?)?.length).toString(),
      'Agents': ((agents?['agents'] as List?)?.length).toString(),
    };
    return ListView(
      padding: const EdgeInsets.all(16),
      children: <Widget>[
        if (simulation)
          const Card(
            child: ListTile(
              leading: Icon(Icons.science_outlined),
              title: Text('SIMULATION'),
              subtitle: Text(
                'Commands are prepared only; live execution is not implied.',
              ),
            ),
          ),
        AnimatedBuilder(
          animation: pulse,
          builder: (_, __) => Card(
            child: ListTile(
              leading: Transform.scale(
                scale: status.toLowerCase() == 'ok' ? .9 + pulse.value * .2 : 1,
                child: Icon(
                  Icons.circle,
                  color: status.toLowerCase() == 'ok'
                      ? Theme.of(context).colorScheme.primary
                      : Theme.of(context).colorScheme.outline,
                ),
              ),
              title: Text(
                status.toLowerCase() == 'ok'
                    ? 'LIVE SYSTEM — runtime observed'
                    : 'SYSTEM STATE — waiting for runtime observation',
              ),
              trailing: Text(
                status.toLowerCase() == 'ok' ? 'OBSERVED' : 'UNKNOWN',
              ),
            ),
          ),
        ),
        const SizedBox(height: 12),
        Wrap(
          spacing: 12,
          runSpacing: 12,
          children: values.entries
              .map((entry) => SizedBox(
                    width: 190,
                    child: Card(
                      child: Padding(
                        padding: const EdgeInsets.all(16),
                        child: Row(
                          children: <Widget>[
                            const Icon(Icons.circle_outlined),
                            const SizedBox(width: 10),
                            Expanded(
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: <Widget>[
                                  Text(entry.key),
                                  const SizedBox(height: 4),
                                  Text(
                                    entry.value == 'null' ? 'UNKNOWN' : entry.value,
                                    style: Theme.of(context)
                                        .textTheme
                                        .titleLarge
                                        ?.copyWith(fontWeight: FontWeight.w800),
                                  ),
                                ],
                              ),
                            ),
                          ],
                        ),
                      ),
                    ),
                  ))
              .toList(),
        ),
        const SizedBox(height: 16),
        Card(
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Wrap(
              spacing: 10,
              runSpacing: 10,
              children: <Widget>[
                _QuickAction(
                  label: 'Friend',
                  icon: Icons.forum_outlined,
                  onPressed: onNavigate == null ? null : () => onNavigate!(1),
                ),
                _QuickAction(
                  label: 'Agents',
                  icon: Icons.smart_toy_outlined,
                  onPressed: onNavigate == null ? null : () => onNavigate!(2),
                ),
                _QuickAction(
                  label: 'Knowledge',
                  icon: Icons.account_tree_outlined,
                  onPressed: onNavigate == null ? null : () => onNavigate!(4),
                ),
                _QuickAction(
                  label: 'GitHub',
                  icon: Icons.code_outlined,
                  onPressed: onNavigate == null ? null : () => onNavigate!(5),
                ),
                _QuickAction(
                  label: 'Runtime',
                  icon: Icons.monitor_heart_outlined,
                  onPressed: onNavigate == null ? null : () => onNavigate!(8),
                ),
                _QuickAction(
                  label: 'Settings',
                  icon: Icons.settings_outlined,
                  onPressed: onNavigate == null ? null : () => onNavigate!(9),
                ),
              ],
            ),
          ),
        ),
        const SizedBox(height: 16),
        const Card(
          child: Padding(
            padding: EdgeInsets.all(16),
            child: Wrap(
              spacing: 6,
              runSpacing: 6,
              children: <Widget>[
                Chip(label: Text('INTENT')),
                Icon(Icons.arrow_forward, size: 15),
                Chip(label: Text('VALIDATE')),
                Icon(Icons.arrow_forward, size: 15),
                Chip(label: Text('PREPARE')),
                Icon(Icons.arrow_forward, size: 15),
                Chip(label: Text('AUTHORIZE')),
                Icon(Icons.arrow_forward, size: 15),
                Chip(label: Text('EXECUTE')),
                Icon(Icons.arrow_forward, size: 15),
                Chip(label: Text('OBSERVE')),
                Icon(Icons.arrow_forward, size: 15),
                Chip(label: Text('EVIDENCE')),
                Icon(Icons.arrow_forward, size: 15),
                Chip(label: Text('COMPLETE')),
                Icon(Icons.arrow_forward, size: 15),
                Chip(label: Text('RECOVER')),
              ],
            ),
          ),
        ),
      ],
    );
  }
}

class _Activity extends StatelessWidget {
  const _Activity({required this.events});
  final List<String> events;

  @override
  Widget build(BuildContext context) => ListView.builder(
        padding: const EdgeInsets.all(16),
        itemCount: events.length,
        itemBuilder: (_, index) => Card(
          child: ListTile(
            leading: const Icon(Icons.bolt_outlined),
            title: Text(events[index]),
          ),
        ),
      );
}

class _SystemMap extends StatelessWidget {
  const _SystemMap({
    required this.health,
    required this.brain,
    required this.providers,
    required this.agents,
    required this.pulse,
  });
  final Map<String, dynamic>? health, brain, providers, agents;
  final AnimationController pulse;

  @override
  Widget build(BuildContext context) {
    final nodes = <String, String>{
      'CORE': health == null ? 'UNKNOWN' : 'OBSERVED',
      'BRAIN': brain == null ? 'UNKNOWN' : 'OBSERVED',
      'PROVIDERS': providers == null ? 'UNKNOWN' : 'OBSERVED',
      'AGENTS': agents == null ? 'UNKNOWN' : 'OBSERVED',
      'ASSURANCE': 'UNKNOWN',
      'EXPERIENCE': 'ACTIVE',
    };
    return ListView(
      padding: const EdgeInsets.all(16),
      children: <Widget>[
        Card(
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: AnimatedBuilder(
              animation: pulse,
              builder: (_, __) => Wrap(
                alignment: WrapAlignment.center,
                spacing: 10,
                runSpacing: 10,
                children: nodes.entries
                    .map((entry) => AnimatedContainer(
                          duration: const Duration(milliseconds: 250),
                          width: 145 +
                              (entry.value == 'UNKNOWN' ? 0 : pulse.value * 5),
                          padding: const EdgeInsets.all(14),
                          decoration: BoxDecoration(
                            borderRadius: BorderRadius.circular(16),
                            border: Border.all(
                              color: entry.value == 'UNKNOWN'
                                  ? Theme.of(context).colorScheme.outline
                                  : Theme.of(context).colorScheme.primary,
                            ),
                          ),
                          child: Column(
                            children: <Widget>[
                              const Icon(Icons.hub_outlined),
                              const SizedBox(height: 6),
                              Text(entry.key,
                                  style: const TextStyle(
                                      fontWeight: FontWeight.w800)),
                              Text(entry.value),
                            ],
                          ),
                        ))
                    .toList(),
              ),
            ),
          ),
        ),
        const SizedBox(height: 12),
        const Text(
          'Descriptive map only. Missing telemetry remains UNKNOWN.',
        ),
      ],
    );
  }
}

class _UnknownCenter extends StatelessWidget {
  const _UnknownCenter({
    required this.title,
    required this.icon,
    required this.message,
  });
  final String title;
  final IconData icon;
  final String message;

  @override
  Widget build(BuildContext context) => Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 720),
          child: Card(
            child: Padding(
              padding: const EdgeInsets.all(24),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: <Widget>[
                  Icon(icon, size: 42),
                  const SizedBox(height: 12),
                  Text(title,
                      style: Theme.of(context).textTheme.headlineSmall),
                  const SizedBox(height: 8),
                  Text(message, textAlign: TextAlign.center),
                ],
              ),
            ),
          ),
        ),
      );
}

class _ControlBoundary extends StatelessWidget {
  const _ControlBoundary();

  @override
  Widget build(BuildContext context) => ListView(
        padding: const EdgeInsets.all(16),
        children: const <Widget>[
          Card(
            child: ListTile(
              leading: Icon(Icons.visibility_outlined),
              title: Text('Observe'),
              subtitle:
                  Text('Health, capabilities, brain, providers, agents'),
            ),
          ),
          Card(
            child: ListTile(
              leading: Icon(Icons.build_outlined),
              title: Text('Prepare'),
              subtitle: Text('Commands, navigation, inspection, simulation'),
            ),
          ),
          Card(
            child: ListTile(
              leading: Icon(Icons.lock_outline),
              title: Text('Human authority required'),
              subtitle:
                  Text('Approve • Authorize • Release • High-risk live action'),
            ),
          ),
          Card(
            child: ListTile(
              leading: Icon(Icons.history_outlined),
              title: Text('History boundary'),
              subtitle: Text(
                'No history rewrite, auto-merge, or authority derivation from observation.',
              ),
            ),
          ),
        ],
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
          Text(title,
              style: Theme.of(context)
                  .textTheme
                  .titleLarge
                  ?.copyWith(fontWeight: FontWeight.w700)),
          const SizedBox(height: 12),
          ...data.entries.map((entry) => Card(
                child: ListTile(
                  title: Text(entry.key),
                  subtitle: SelectableText(entry.value.toString()),
                ),
              )),
        ],
      );
}


class _QuickAction extends StatelessWidget {
  const _QuickAction({
    required this.label,
    required this.icon,
    required this.onPressed,
  });
  final String label;
  final IconData icon;
  final VoidCallback? onPressed;

  @override
  Widget build(BuildContext context) => OutlinedButton.icon(
        onPressed: onPressed,
        icon: Icon(icon),
        label: Text(label),
      );
}

class _DesignStudio extends StatefulWidget {
  @override
  State<_DesignStudio> createState() => _DesignStudioState();
}

class _DesignStudioState extends State<_DesignStudio> {
  int _selected = 0;
  bool _reducedMotion = false;
  bool _darkPreview = false;

  @override
  Widget build(BuildContext context) {
    final sections = <String>['Canvas', 'Tokens', 'Components', 'States', 'Motion', 'Accessibility'];
    return ListView(
      padding: const EdgeInsets.all(16),
      children: <Widget>[
        Card(
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Row(
              children: <Widget>[
                const Icon(Icons.palette_outlined, size: 30),
                const SizedBox(width: 12),
                Expanded(
                  child: Text(
                    'Native Design Studio',
                    style: Theme.of(context).textTheme.headlineSmall,
                  ),
                ),
                Switch(
                  value: _darkPreview,
                  onChanged: (value) => setState(() => _darkPreview = value),
                ),
                const Text('Preview'),
              ],
            ),
          ),
        ),
        const SizedBox(height: 12),
        SegmentedButton<int>(
          segments: List<DropdownMenuItem<int>>.empty().isEmpty
              ? sections.asMap().entries
                  .map((entry) => ButtonSegment<int>(
                        value: entry.key,
                        label: Text(entry.value),
                      ))
                  .toList()
              : const <ButtonSegment<int>>[],
          selected: <int>{_selected},
          onSelectionChanged: (values) => setState(() => _selected = values.first),
          multiSelectionEnabled: false,
        ),
        const SizedBox(height: 12),
        Card(
          child: Padding(
            padding: const EdgeInsets.all(18),
            child: _DesignSection(
              index: _selected,
              darkPreview: _darkPreview,
              reducedMotion: _reducedMotion,
              onReducedMotionChanged: (value) => setState(() => _reducedMotion = value),
            ),
          ),
        ),
      ],
    );
  }
}

class _DesignSection extends StatelessWidget {
  const _DesignSection({
    required this.index,
    required this.darkPreview,
    required this.reducedMotion,
    required this.onReducedMotionChanged,
  });
  final int index;
  final bool darkPreview;
  final bool reducedMotion;
  final ValueChanged<bool> onReducedMotionChanged;

  @override
  Widget build(BuildContext context) {
    switch (index) {
      case 0:
        return Container(
          height: 260,
          decoration: BoxDecoration(
            color: darkPreview ? Colors.black : Theme.of(context).colorScheme.surface,
            borderRadius: BorderRadius.circular(20),
            border: Border.all(color: Theme.of(context).colorScheme.outlineVariant),
          ),
          child: Center(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: <Widget>[
                Icon(Icons.grid_4x4, size: 42, color: Theme.of(context).colorScheme.primary),
                const SizedBox(height: 10),
                const Text('Native canvas / layout preview'),
                const SizedBox(height: 8),
                const Text('Grid • alignment • responsive • constraints'),
              ],
            ),
          ),
        );
      case 1:
        return Wrap(
          spacing: 10,
          runSpacing: 10,
          children: const <Widget>[
            Chip(label: Text('Brand')),
            Chip(label: Text('Surface')),
            Chip(label: Text('Background')),
            Chip(label: Text('Text')),
            Chip(label: Text('Interactive')),
            Chip(label: Text('Success')),
            Chip(label: Text('Warning')),
            Chip(label: Text('Error')),
            Chip(label: Text('Focus')),
            Chip(label: Text('Selection')),
          ],
        );
      case 2:
        return Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: <Widget>[
            const Text('State-complete components'),
            const SizedBox(height: 12),
            Wrap(
              spacing: 10,
              runSpacing: 10,
              children: <Widget>[
                FilledButton(onPressed: () {}, child: const Text('Primary')),
                OutlinedButton(onPressed: () {}, child: const Text('Secondary')),
                const Chip(label: Text('Loading')),
                const Chip(label: Text('Error')),
                const Chip(label: Text('Offline')),
              ],
            ),
          ],
        );
      case 3:
        return const Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: <Widget>[
            Text('State coverage'),
            SizedBox(height: 10),
            Text('Default → Loading → Empty → Error → Offline → Degraded → Recovery'),
          ],
        );
      case 4:
        return Row(
          children: <Widget>[
            Expanded(
              child: Text(
                reducedMotion
                    ? 'Reduced motion: enabled. Non-essential animation is suppressed.'
                    : 'Motion follows state transitions and remains descriptive.',
              ),
            ),
            Switch(value: reducedMotion, onChanged: onReducedMotionChanged),
          ],
        );
      default:
        return const Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: <Widget>[
            Text('Accessibility'),
            SizedBox(height: 10),
            Text('Contrast • keyboard • focus • semantics • reduced motion • responsive layout'),
          ],
        );
    }
  }
}
