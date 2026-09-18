import 'package:flutter/material.dart';

import 'owner_api.dart';

class NativeControlCenterPage extends StatefulWidget {
  const NativeControlCenterPage({required this.api, this.onNavigate, super.key});
  final OwnerFriendApi api;
  final ValueChanged<int>? onNavigate;

  @override
  State<NativeControlCenterPage> createState() => _NativeControlCenterPageState();
}

class _NativeControlCenterPageState extends State<NativeControlCenterPage> {
  final _search = TextEditingController();
  final _inspector = TextEditingController();
  final _focus = FocusNode();
  Map<String, dynamic>? _status;
  String _objectId = '';
  bool _loading = false;
  final List<String> _activity = <String>[
    'Control Center opened',
    'Native control-plane shell ready',
  ];

  static const _commands = <String>[
    'Research',
    'Friend',
    'Runtime',
    'Evidence',
    'Failure Center',
    'System Map',
    'Universal Inspector',
  ];

  @override
  void initState() {
    super.initState();
    _load();
    // Keyboard focus is attached by Focus(autofocus: true) after the first frame.
  }

  @override
  void dispose() {
    _search.dispose();
    _inspector.dispose();
    _focus.dispose();
    super.dispose();
  }

  Future<void> _load() async {
    setState(() => _loading = true);
    try {
      final status = await widget.api.status();
      if (!mounted) return;
      setState(() {
        _status = status;
        _activity.insert(0, 'Runtime status observed');
      });
    } catch (error) {
      if (!mounted) return;
      setState(() => _activity.insert(0, 'Runtime observation failed: $error'));
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  void _runCommand(String command) {
    const routes = <String, int>{
      'Research': 1,
      'Runtime': 1,
      'Friend': 2,
      'Evidence': 4,
    };
    setState(() {
      _search.clear();
      _activity.insert(0, 'Command prepared: $command');
    });
    final route = routes[command];
    if (route != null) widget.onNavigate?.call(route);
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text('$command prepared — execution remains bounded by the control plane.')),
    );
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final query = _search.text.trim().toLowerCase();
    final commands = _commands.where((item) => item.toLowerCase().contains(query)).toList();
    final helper = _status?['helper_scheduler'] is Map
        ? Map<String, dynamic>.from(_status!['helper_scheduler'] as Map)
        : const <String, dynamic>{};
    final brain = _status?['brain_profiles'] is Map
        ? Map<String, dynamic>.from(_status!['brain_profiles'] as Map)
        : const <String, dynamic>{};
    final capabilities = (_status?['capabilities'] as List? ?? const <Object>[]).length;

    return Shortcuts(
      shortcuts: const <ShortcutActivator, Intent>{
        SingleActivator(LogicalKeyboardKey.keyK, control: true): _OpenCommandIntent(),
        SingleActivator(LogicalKeyboardKey.keyK, meta: true): _OpenCommandIntent(),
      },
      child: Actions(
        actions: <Type, Action<Intent>>{
          _OpenCommandIntent: CallbackAction<_OpenCommandIntent>(
            onInvoke: (_) {
              _focus.requestFocus();
              return null;
            },
          ),
        },
        child: Focus(
          autofocus: true,
          focusNode: _focus,
          child: LayoutBuilder(
            builder: (context, constraints) {
              final compact = constraints.maxWidth < 900;
              return ListView(
                padding: EdgeInsets.fromLTRB(compact ? 2 : 8, 2, compact ? 2 : 8, 24),
                children: [
                  Row(
                    children: [
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text('Control Center', style: theme.textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.w700)),
                            const SizedBox(height: 3),
                            Text('One native surface for control, state, intelligence, assurance and recovery.',
                                style: theme.textTheme.bodySmall?.copyWith(color: theme.colorScheme.onSurfaceVariant)),
                          ],
                        ),
                      ),
                      IconButton(
                        tooltip: 'Refresh runtime',
                        onPressed: _loading ? null : _load,
                        icon: _loading
                            ? const SizedBox.square(dimension: 18, child: CircularProgressIndicator(strokeWidth: 2))
                            : const Icon(Icons.refresh),
                      ),
                    ],
                  ),
                  const SizedBox(height: 14),
                  TextField(
                    controller: _search,
                    onChanged: (_) => setState(() {}),
                    onSubmitted: (value) {
                      if (commands.isNotEmpty) _runCommand(commands.first);
                    },
                    decoration: InputDecoration(
                      prefixIcon: const Icon(Icons.search),
                      suffixText: 'Ctrl/⌘ K',
                      hintText: 'Search command, navigate, inspect or ask Friend…',
                      border: OutlineInputBorder(borderRadius: BorderRadius.circular(14)),
                    ),
                  ),
                  if (query.isNotEmpty)
                    Card(
                      child: Column(
                        children: commands.isEmpty
                            ? [const ListTile(title: Text('No matching command'))]
                            : commands.take(8).map((command) => ListTile(
                                leading: const Icon(Icons.bolt_outlined),
                                title: Text(command),
                                subtitle: const Text('Prepare through the native command model'),
                                onTap: () => _runCommand(command),
                              )).toList(),
                      ),
                    ),
                  const SizedBox(height: 14),
                  _Section(title: 'System Map', icon: Icons.account_tree_outlined, child: _SystemMap(compact: compact)),
                  _Section(
                    title: 'Live Runtime',
                    icon: Icons.monitor_heart_outlined,
                    child: Wrap(
                      spacing: 10,
                      runSpacing: 10,
                      children: [
                        _MetricCard('Brain profiles', brain.length.toString()),
                        _MetricCard('Active workers', helper['max_active_workers']?.toString() ?? 'UNKNOWN'),
                        _MetricCard('Logical helpers', helper['max_logical_helpers']?.toString() ?? 'UNKNOWN'),
                        _MetricCard('Capabilities', capabilities.toString()),
                      ],
                    ),
                  ),
                  _Section(
                    title: 'Universal Activity',
                    icon: Icons.timeline_outlined,
                    child: Column(
                      children: _activity.take(12).map((event) => ListTile(
                        dense: true,
                        leading: const Icon(Icons.circle, size: 8),
                        title: Text(event),
                      )).toList(),
                    ),
                  ),
                  _Section(
                    title: 'Human Control Boundary',
                    icon: Icons.lock_outline,
                    child: Wrap(
                      spacing: 8,
                      runSpacing: 8,
                      children: const [
                        Chip(avatar: Icon(Icons.check, size: 16), label: Text('Observe')),
                        Chip(avatar: Icon(Icons.check, size: 16), label: Text('Analyze')),
                        Chip(avatar: Icon(Icons.check, size: 16), label: Text('Research')),
                        Chip(avatar: Icon(Icons.check, size: 16), label: Text('Prepare')),
                        Chip(avatar: Icon(Icons.lock_outline, size: 16), label: Text('Approve — human')),
                        Chip(avatar: Icon(Icons.lock_outline, size: 16), label: Text('Authorize — human')),
                        Chip(avatar: Icon(Icons.lock_outline, size: 16), label: Text('Release — human')),
                      ],
                    ),
                  ),
                  _Section(
                    title: 'Universal Inspector',
                    icon: Icons.manage_search_outlined,
                    child: Row(
                      crossAxisAlignment: CrossAxisAlignment.end,
                      children: [
                        Expanded(
                          child: TextField(
                            controller: _inspector,
                            decoration: const InputDecoration(labelText: 'Object ID', hintText: 'task, source, evidence, service…'),
                            onSubmitted: (value) => setState(() => _objectId = value.trim()),
                          ),
                        ),
                        const SizedBox(width: 10),
                        FilledButton(
                          onPressed: () => setState(() => _objectId = _inspector.text.trim()),
                          child: const Text('Inspect'),
                        ),
                      ],
                    ),
                  ),
                  if (_objectId.isNotEmpty)
                    Card(
                      child: ListTile(
                        leading: const Icon(Icons.policy_outlined),
                        title: Text(_objectId),
                        subtitle: const Text('Identity • State • Owner • Version • Relations • Provenance • Evidence • History • Recovery'),
                        trailing: const Icon(Icons.chevron_right),
                      ),
                    ),
                  const SizedBox(height: 6),
                  Text(
                    'Simulation and dry-run surfaces can be added without bypassing the command lifecycle: INTENT → VALIDATE → AUTHORIZE → EXECUTE → OBSERVE → EVIDENCE → COMPLETE.',
                    style: theme.textTheme.bodySmall?.copyWith(color: theme.colorScheme.onSurfaceVariant),
                  ),
                ],
              );
            },
          ),
        ),
      ),
    );
  }
}

class _OpenCommandIntent extends Intent {
  const _OpenCommandIntent();
}

class _Section extends StatelessWidget {
  const _Section({required this.title, required this.icon, required this.child});
  final String title;
  final IconData icon;
  final Widget child;

  @override
  Widget build(BuildContext context) => Card(
    margin: const EdgeInsets.only(bottom: 12),
    child: Padding(
      padding: const EdgeInsets.all(16),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Row(children: [
          Icon(icon, size: 19),
          const SizedBox(width: 8),
          Text(title, style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w700)),
        ]),
        const SizedBox(height: 12),
        child,
      ]),
    ),
  );
}

class _MetricCard extends StatelessWidget {
  const _MetricCard(this.label, this.value);
  final String label;
  final String value;

  @override
  Widget build(BuildContext context) => SizedBox(
    width: 190,
    child: Card(
      margin: EdgeInsets.zero,
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Text(label, style: Theme.of(context).textTheme.bodySmall),
          const SizedBox(height: 5),
          Text(value, style: Theme.of(context).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w700)),
        ]),
      ),
    ),
  );
}

class _SystemMap extends StatelessWidget {
  const _SystemMap({required this.compact});
  final bool compact;

  @override
  Widget build(BuildContext context) {
    final nodes = <String>['Mathematical Root', 'Universal Learning', 'Research', 'Friend', 'Platform', 'Runtime', 'Assurance', 'Reality'];
    return Wrap(
      alignment: WrapAlignment.center,
      spacing: compact ? 6 : 10,
      runSpacing: 8,
      children: nodes.map((node) => InputChip(
        label: Text(node),
        avatar: const Icon(Icons.circle, size: 9),
        onPressed: () => ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('$node selected — inspect relations from the same control surface.')),
        ),
      )).toList(),
    );
  }
}
