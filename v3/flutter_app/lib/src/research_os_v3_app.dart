import 'package:flutter/material.dart';

import 'api/v3_api.dart';
import 'chat/chat_page.dart';

class ResearchOSV3App extends StatelessWidget {
  const ResearchOSV3App({super.key, required this.api});

  final V3Api api;

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Research OS V3.2',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: const Color(0xFF3157D5)),
        useMaterial3: true,
      ),
      home: V3AppShell(api: api),
    );
  }
}

class V3AppShell extends StatefulWidget {
  const V3AppShell({super.key, required this.api});

  final V3Api api;

  @override
  State<V3AppShell> createState() => _V3AppShellState();
}

class _V3AppShellState extends State<V3AppShell> {
  int _selectedIndex = 0;
  late Future<_V3Snapshot> _snapshot;

  @override
  void initState() {
    super.initState();
    _snapshot = _loadSnapshot();
  }

  Future<_V3Snapshot> _loadSnapshot() async {
    final results = await Future.wait<Map<String, dynamic>>([
      widget.api.health(),
      widget.api.master(tasks: 30),
      widget.api.providers(),
      widget.api.skills(),
      widget.api.tools(),
      widget.api.agents(),
      widget.api.memory(limit: 20),
      widget.api.factoryPlan(tasks: 30),
    ]);
    return _V3Snapshot(
      health: results[0],
      master: results[1],
      providers: results[2],
      skills: results[3],
      tools: results[4],
      agents: results[5],
      memory: results[6],
      factory: results[7],
    );
  }

  void _refresh() {
    setState(() => _snapshot = _loadSnapshot());
  }

  @override
  Widget build(BuildContext context) {
    final wide = MediaQuery.sizeOf(context).width >= 1180;
    const destinations = <NavigationRailDestination>[
      NavigationRailDestination(
        icon: Icon(Icons.home_outlined),
        selectedIcon: Icon(Icons.home),
        label: Text('Home'),
      ),
      NavigationRailDestination(
        icon: Icon(Icons.chat_bubble_outline),
        selectedIcon: Icon(Icons.chat_bubble),
        label: Text('Chat'),
      ),
      NavigationRailDestination(
        icon: Icon(Icons.groups_outlined),
        selectedIcon: Icon(Icons.groups),
        label: Text('Agents'),
      ),
      NavigationRailDestination(
        icon: Icon(Icons.psychology_outlined),
        selectedIcon: Icon(Icons.psychology),
        label: Text('Memory'),
      ),
      NavigationRailDestination(
        icon: Icon(Icons.extension_outlined),
        selectedIcon: Icon(Icons.extension),
        label: Text('Skills'),
      ),
      NavigationRailDestination(
        icon: Icon(Icons.build_outlined),
        selectedIcon: Icon(Icons.build),
        label: Text('Tools'),
      ),
      NavigationRailDestination(
        icon: Icon(Icons.account_tree_outlined),
        selectedIcon: Icon(Icons.account_tree),
        label: Text('Factory'),
      ),
      NavigationRailDestination(
        icon: Icon(Icons.hub_outlined),
        selectedIcon: Icon(Icons.hub),
        label: Text('Providers'),
      ),
    ];

    return Scaffold(
      body: SafeArea(
        child: Row(
          children: [
            NavigationRail(
              extended: wide,
              minExtendedWidth: 210,
              selectedIndex: _selectedIndex,
              destinations: destinations,
              onDestinationSelected: (index) {
                setState(() => _selectedIndex = index);
              },
              leading: Padding(
                padding: const EdgeInsets.symmetric(vertical: 16),
                child: wide
                    ? const Column(
                        mainAxisSize: MainAxisSize.min,
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            'Research OS V3.2',
                            style: TextStyle(fontWeight: FontWeight.w800),
                          ),
                          SizedBox(height: 2),
                          Text('Unified 10x10'),
                        ],
                      )
                    : const Icon(Icons.auto_awesome),
              ),
            ),
            const VerticalDivider(width: 1),
            Expanded(
              child: switch (_selectedIndex) {
                0 => _HomePage(snapshot: _snapshot, onRefresh: _refresh),
                1 => V3ChatPage(api: widget.api),
                2 => _AgentsPage(
                    api: widget.api,
                    snapshot: _snapshot,
                    onRefresh: _refresh,
                  ),
                3 => _MemoryPage(api: widget.api),
                4 => _SkillsPage(snapshot: _snapshot, onRefresh: _refresh),
                5 => _ToolsPage(
                    api: widget.api,
                    snapshot: _snapshot,
                    onRefresh: _refresh,
                  ),
                6 => _FactoryPage(snapshot: _snapshot, onRefresh: _refresh),
                _ => _ProvidersPage(snapshot: _snapshot, onRefresh: _refresh),
              },
            ),
          ],
        ),
      ),
    );
  }
}

class _HomePage extends StatelessWidget {
  const _HomePage({required this.snapshot, required this.onRefresh});

  final Future<_V3Snapshot> snapshot;
  final VoidCallback onRefresh;

  @override
  Widget build(BuildContext context) {
    return _PageFrame(
      title: 'Full System Control Center',
      action: IconButton(
        tooltip: 'Refresh',
        onPressed: onRefresh,
        icon: const Icon(Icons.refresh),
      ),
      child: FutureBuilder<_V3Snapshot>(
        future: snapshot,
        builder: (context, value) {
          if (value.connectionState != ConnectionState.done) {
            return const Center(child: CircularProgressIndicator());
          }
          if (value.hasError) return _ConnectionError(error: value.error);
          final data = value.data!;
          final maximumScale = data.health['maximum_scale']?.toString() ?? '-';
          final maximumCapacity = data.health['maximum_logical_capacity'];
          return ListView(
            padding: const EdgeInsets.all(24),
            children: [
              Wrap(
                spacing: 16,
                runSpacing: 16,
                children: [
                  _MetricCard(
                    label: 'Local service',
                    value: data.health['status']?.toString() ?? 'unknown',
                    icon: Icons.dns_outlined,
                  ),
                  _MetricCard(
                    label: 'Maximum logical scale',
                    value: maximumScale,
                    icon: Icons.memory,
                  ),
                  _MetricCard(
                    label: 'Logical capacity',
                    value: _formatInteger(maximumCapacity),
                    icon: Icons.schema_outlined,
                  ),
                  _MetricCard(
                    label: 'Active scale',
                    value: data.master['scale']?.toString() ?? '-',
                    icon: Icons.tune,
                  ),
                  _MetricCard(
                    label: 'Skills',
                    value: '${data.skillList.length}',
                    icon: Icons.extension_outlined,
                  ),
                  _MetricCard(
                    label: 'Tools',
                    value: '${data.toolList.length}',
                    icon: Icons.build_outlined,
                  ),
                  _MetricCard(
                    label: 'Agents',
                    value: '${data.agentList.length}',
                    icon: Icons.groups_outlined,
                  ),
                  _MetricCard(
                    label: 'Providers',
                    value: '${data.providerList.length}',
                    icon: Icons.hub_outlined,
                  ),
                ],
              ),
              const SizedBox(height: 24),
              const Text(
                'Unified architecture',
                style: TextStyle(fontSize: 20, fontWeight: FontWeight.w700),
              ),
              const SizedBox(height: 12),
              const Card(
                child: Padding(
                  padding: EdgeInsets.all(20),
                  child: Text(
                    'Unified Master → Brain → Skills / Tools / Agents / Memory '
                    '→ Provider → Factory → Team → Tests → Release\n\n'
                    'Adaptive profiles scale from 1³ through 10¹⁰. The 10^10 '
                    'value is logical planning capacity; real execution remains '
                    'bounded and governed.',
                  ),
                ),
              ),
            ],
          );
        },
      ),
    );
  }
}

class _AgentsPage extends StatefulWidget {
  const _AgentsPage({
    required this.api,
    required this.snapshot,
    required this.onRefresh,
  });

  final V3Api api;
  final Future<_V3Snapshot> snapshot;
  final VoidCallback onRefresh;

  @override
  State<_AgentsPage> createState() => _AgentsPageState();
}

class _AgentsPageState extends State<_AgentsPage> {
  String? _running;
  String? _result;

  Future<void> _run(String name) async {
    setState(() {
      _running = name;
      _result = null;
    });
    try {
      final response = await widget.api.runAgent(
        name,
        'Report your current Research OS V3.2 role and readiness.',
      );
      if (mounted) {
        setState(() => _result = response['text']?.toString() ?? response.toString());
      }
    } catch (error) {
      if (mounted) setState(() => _result = error.toString());
    } finally {
      if (mounted) setState(() => _running = null);
    }
  }

  @override
  Widget build(BuildContext context) {
    return _PageFrame(
      title: 'Agents',
      action: IconButton(
        tooltip: 'Refresh',
        onPressed: widget.onRefresh,
        icon: const Icon(Icons.refresh),
      ),
      child: FutureBuilder<_V3Snapshot>(
        future: widget.snapshot,
        builder: (context, value) {
          if (value.connectionState != ConnectionState.done) {
            return const Center(child: CircularProgressIndicator());
          }
          if (value.hasError) return _ConnectionError(error: value.error);
          final agents = value.data!.agentList;
          return ListView(
            padding: const EdgeInsets.all(24),
            children: [
              for (final agent in agents)
                Card(
                  child: ListTile(
                    leading: const Icon(Icons.smart_toy_outlined),
                    title: Text(agent['name']?.toString() ?? 'agent'),
                    subtitle: Text(
                      '${agent['role'] ?? ''}\n${agent['description'] ?? ''}',
                    ),
                    isThreeLine: true,
                    trailing: FilledButton(
                      onPressed: _running == null
                          ? () => _run(agent['name']?.toString() ?? '')
                          : null,
                      child: Text(_running == agent['name'] ? 'Running' : 'Run'),
                    ),
                  ),
                ),
              if (_result != null) ...[
                const SizedBox(height: 12),
                Card(
                  child: Padding(
                    padding: const EdgeInsets.all(16),
                    child: SelectableText(_result!),
                  ),
                ),
              ],
            ],
          );
        },
      ),
    );
  }
}

class _MemoryPage extends StatefulWidget {
  const _MemoryPage({required this.api});
  final V3Api api;

  @override
  State<_MemoryPage> createState() => _MemoryPageState();
}

class _MemoryPageState extends State<_MemoryPage> {
  final TextEditingController _controller = TextEditingController();
  late Future<Map<String, dynamic>> _memory;
  bool _saving = false;

  @override
  void initState() {
    super.initState();
    _memory = widget.api.memory(limit: 50);
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  void _refresh() {
    setState(() => _memory = widget.api.memory(limit: 50));
  }

  Future<void> _save() async {
    final text = _controller.text.trim();
    if (text.isEmpty || _saving) return;
    setState(() => _saving = true);
    try {
      await widget.api.addMemory(text, tags: const ['desktop']);
      _controller.clear();
      _refresh();
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return _PageFrame(
      title: 'Memory',
      action: IconButton(
        tooltip: 'Refresh',
        onPressed: _refresh,
        icon: const Icon(Icons.refresh),
      ),
      child: Column(
        children: [
          Padding(
            padding: const EdgeInsets.all(20),
            child: Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _controller,
                    decoration: const InputDecoration(
                      border: OutlineInputBorder(),
                      labelText: 'Add user-scoped memory',
                    ),
                  ),
                ),
                const SizedBox(width: 12),
                FilledButton.icon(
                  onPressed: _saving ? null : _save,
                  icon: const Icon(Icons.save_outlined),
                  label: const Text('Save'),
                ),
              ],
            ),
          ),
          Expanded(
            child: FutureBuilder<Map<String, dynamic>>(
              future: _memory,
              builder: (context, value) {
                if (value.connectionState != ConnectionState.done) {
                  return const Center(child: CircularProgressIndicator());
                }
                if (value.hasError) return _ConnectionError(error: value.error);
                final records = _mapList(value.data?['memory']);
                if (records.isEmpty) {
                  return const Center(child: Text('No local memory records yet.'));
                }
                return ListView.builder(
                  padding: const EdgeInsets.fromLTRB(24, 0, 24, 24),
                  itemCount: records.length,
                  itemBuilder: (context, index) {
                    final record = records[index];
                    return Card(
                      child: ListTile(
                        leading: const Icon(Icons.notes),
                        title: Text(record['text']?.toString() ?? ''),
                        subtitle: Text(record['created_at']?.toString() ?? ''),
                      ),
                    );
                  },
                );
              },
            ),
          ),
        ],
      ),
    );
  }
}

class _SkillsPage extends StatelessWidget {
  const _SkillsPage({required this.snapshot, required this.onRefresh});
  final Future<_V3Snapshot> snapshot;
  final VoidCallback onRefresh;

  @override
  Widget build(BuildContext context) {
    return _CatalogPage(
      title: 'Skills',
      snapshot: snapshot,
      onRefresh: onRefresh,
      items: (data) => data.skillList,
      icon: Icons.extension_outlined,
      subtitle: (item) =>
          '${item['origin'] ?? ''} · ${item['runtime_mode'] ?? ''}\n${item['description'] ?? ''}',
    );
  }
}

class _ToolsPage extends StatefulWidget {
  const _ToolsPage({
    required this.api,
    required this.snapshot,
    required this.onRefresh,
  });

  final V3Api api;
  final Future<_V3Snapshot> snapshot;
  final VoidCallback onRefresh;

  @override
  State<_ToolsPage> createState() => _ToolsPageState();
}

class _ToolsPageState extends State<_ToolsPage> {
  String? _result;
  String? _running;

  Future<void> _runEcho() async {
    setState(() {
      _running = 'echo';
      _result = null;
    });
    try {
      final response = await widget.api.executeTool(
        'echo',
        <String, dynamic>{'text': 'Research OS V3.2 tool probe'},
      );
      if (mounted) setState(() => _result = response.toString());
    } catch (error) {
      if (mounted) setState(() => _result = error.toString());
    } finally {
      if (mounted) setState(() => _running = null);
    }
  }

  @override
  Widget build(BuildContext context) {
    return _PageFrame(
      title: 'Tools',
      action: IconButton(
        tooltip: 'Refresh',
        onPressed: widget.onRefresh,
        icon: const Icon(Icons.refresh),
      ),
      child: FutureBuilder<_V3Snapshot>(
        future: widget.snapshot,
        builder: (context, value) {
          if (value.connectionState != ConnectionState.done) {
            return const Center(child: CircularProgressIndicator());
          }
          if (value.hasError) return _ConnectionError(error: value.error);
          final tools = value.data!.toolList;
          return ListView(
            padding: const EdgeInsets.all(24),
            children: [
              const Card(
                child: ListTile(
                  leading: Icon(Icons.gpp_good_outlined),
                  title: Text('Governed execution boundary'),
                  subtitle: Text(
                    'Write-capable tools require explicit approval. Model text '
                    'alone is never treated as proof of tool execution.',
                  ),
                ),
              ),
              const SizedBox(height: 12),
              for (final tool in tools)
                Card(
                  child: ListTile(
                    leading: const Icon(Icons.build_outlined),
                    title: Text(tool['name']?.toString() ?? 'tool'),
                    subtitle: Text(
                      '${tool['risk'] ?? ''} · approval=${tool['approval_required']}\n'
                      '${tool['description'] ?? ''}',
                    ),
                    isThreeLine: true,
                    trailing: tool['name'] == 'echo'
                        ? FilledButton(
                            onPressed: _running == null ? _runEcho : null,
                            child: Text(_running == 'echo' ? 'Running' : 'Probe'),
                          )
                        : null,
                  ),
                ),
              if (_result != null)
                Card(
                  child: Padding(
                    padding: const EdgeInsets.all(16),
                    child: SelectableText(_result!),
                  ),
                ),
            ],
          );
        },
      ),
    );
  }
}

class _FactoryPage extends StatelessWidget {
  const _FactoryPage({required this.snapshot, required this.onRefresh});
  final Future<_V3Snapshot> snapshot;
  final VoidCallback onRefresh;

  @override
  Widget build(BuildContext context) {
    return _PageFrame(
      title: 'Adaptive Software Factory',
      action: IconButton(
        tooltip: 'Refresh',
        onPressed: onRefresh,
        icon: const Icon(Icons.refresh),
      ),
      child: FutureBuilder<_V3Snapshot>(
        future: snapshot,
        builder: (context, value) {
          if (value.connectionState != ConnectionState.done) {
            return const Center(child: CircularProgressIndicator());
          }
          if (value.hasError) return _ConnectionError(error: value.error);
          final factory = value.data!.factory;
          final stages = (factory['stage_order'] is List)
              ? List<Object?>.from(factory['stage_order'] as List)
              : const <Object?>[];
          return ListView(
            padding: const EdgeInsets.all(24),
            children: [
              Wrap(
                spacing: 16,
                runSpacing: 16,
                children: [
                  _MetricCard(
                    label: 'Selected scale',
                    value: factory['scale']?.toString() ?? '-',
                    icon: Icons.tune,
                  ),
                  _MetricCard(
                    label: 'Leaf capacity',
                    value: _formatInteger(factory['maximum_leaf_capacity']),
                    icon: Icons.schema_outlined,
                  ),
                ],
              ),
              const SizedBox(height: 20),
              for (var index = 0; index < stages.length; index++) ...[
                Card(
                  child: ListTile(
                    leading: CircleAvatar(child: Text('${index + 1}')),
                    title: Text(stages[index].toString()),
                    subtitle: const Text('Governed stage under the Unified Master.'),
                  ),
                ),
                if (index != stages.length - 1)
                  const Center(child: Icon(Icons.arrow_downward)),
              ],
            ],
          );
        },
      ),
    );
  }
}

class _ProvidersPage extends StatelessWidget {
  const _ProvidersPage({required this.snapshot, required this.onRefresh});
  final Future<_V3Snapshot> snapshot;
  final VoidCallback onRefresh;

  @override
  Widget build(BuildContext context) {
    return _PageFrame(
      title: 'Providers',
      action: IconButton(
        tooltip: 'Refresh',
        onPressed: onRefresh,
        icon: const Icon(Icons.refresh),
      ),
      child: FutureBuilder<_V3Snapshot>(
        future: snapshot,
        builder: (context, value) {
          if (value.connectionState != ConnectionState.done) {
            return const Center(child: CircularProgressIndicator());
          }
          if (value.hasError) return _ConnectionError(error: value.error);
          final providers = value.data!.providerList;
          return ListView(
            padding: const EdgeInsets.all(24),
            children: [
              const Card(
                child: ListTile(
                  leading: Icon(Icons.key_off_outlined),
                  title: Text('Secrets stay outside the desktop app'),
                  subtitle: Text(
                    'Credentials are resolved by the V3.2 service. This screen '
                    'shows safe provider status only.',
                  ),
                ),
              ),
              const SizedBox(height: 12),
              for (final provider in providers)
                Card(
                  child: ListTile(
                    leading: Icon(
                      provider['ready'] == true
                          ? Icons.check_circle_outline
                          : Icons.pause_circle_outline,
                    ),
                    title: Text(provider['name']?.toString() ?? 'provider'),
                    subtitle: Text(
                      'ready=${provider['ready']} · '
                      'connected=${provider['connected']} · '
                      'secret_exposed=${provider['secret_exposed']}',
                    ),
                  ),
                ),
            ],
          );
        },
      ),
    );
  }
}

class _CatalogPage extends StatelessWidget {
  const _CatalogPage({
    required this.title,
    required this.snapshot,
    required this.onRefresh,
    required this.items,
    required this.icon,
    required this.subtitle,
  });

  final String title;
  final Future<_V3Snapshot> snapshot;
  final VoidCallback onRefresh;
  final List<Map<String, dynamic>> Function(_V3Snapshot) items;
  final IconData icon;
  final String Function(Map<String, dynamic>) subtitle;

  @override
  Widget build(BuildContext context) {
    return _PageFrame(
      title: title,
      action: IconButton(
        tooltip: 'Refresh',
        onPressed: onRefresh,
        icon: const Icon(Icons.refresh),
      ),
      child: FutureBuilder<_V3Snapshot>(
        future: snapshot,
        builder: (context, value) {
          if (value.connectionState != ConnectionState.done) {
            return const Center(child: CircularProgressIndicator());
          }
          if (value.hasError) return _ConnectionError(error: value.error);
          final rows = items(value.data!);
          return ListView.builder(
            padding: const EdgeInsets.all(24),
            itemCount: rows.length,
            itemBuilder: (context, index) {
              final item = rows[index];
              return Card(
                child: ListTile(
                  leading: Icon(icon),
                  title: Text(item['name']?.toString() ?? '-'),
                  subtitle: Text(subtitle(item)),
                  isThreeLine: true,
                ),
              );
            },
          );
        },
      ),
    );
  }
}

class _PageFrame extends StatelessWidget {
  const _PageFrame({required this.title, required this.child, this.action});

  final String title;
  final Widget child;
  final Widget? action;

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Material(
          color: Theme.of(context).colorScheme.surface,
          child: SizedBox(
            height: 64,
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 24),
              child: Row(
                children: [
                  Expanded(
                    child: Text(
                      title,
                      style: Theme.of(context).textTheme.titleLarge,
                    ),
                  ),
                  if (action != null) action!,
                ],
              ),
            ),
          ),
        ),
        const Divider(height: 1),
        Expanded(child: child),
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
      width: 220,
      child: Card(
        child: Padding(
          padding: const EdgeInsets.all(20),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Icon(icon),
              const SizedBox(height: 18),
              Text(label, style: Theme.of(context).textTheme.labelLarge),
              const SizedBox(height: 6),
              Text(value, style: Theme.of(context).textTheme.headlineSmall),
            ],
          ),
        ),
      ),
    );
  }
}

class _ConnectionError extends StatelessWidget {
  const _ConnectionError({required this.error});
  final Object? error;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Text(
          'V3.2 local service is not ready.\n$error',
          textAlign: TextAlign.center,
        ),
      ),
    );
  }
}

class _V3Snapshot {
  const _V3Snapshot({
    required this.health,
    required this.master,
    required this.providers,
    required this.skills,
    required this.tools,
    required this.agents,
    required this.memory,
    required this.factory,
  });

  final Map<String, dynamic> health;
  final Map<String, dynamic> master;
  final Map<String, dynamic> providers;
  final Map<String, dynamic> skills;
  final Map<String, dynamic> tools;
  final Map<String, dynamic> agents;
  final Map<String, dynamic> memory;
  final Map<String, dynamic> factory;

  List<Map<String, dynamic>> get providerList => _mapList(providers['providers']);
  List<Map<String, dynamic>> get skillList => _mapList(skills['skills']);
  List<Map<String, dynamic>> get toolList => _mapList(tools['tools']);
  List<Map<String, dynamic>> get agentList => _mapList(agents['agents']);
}

List<Map<String, dynamic>> _mapList(Object? value) {
  if (value is! List) return const <Map<String, dynamic>>[];
  return value
      .whereType<Map>()
      .map((item) => Map<String, dynamic>.from(item))
      .toList(growable: false);
}

String _formatInteger(Object? value) {
  final number = switch (value) {
    int value => value,
    num value => value.toInt(),
    _ => int.tryParse(value?.toString() ?? ''),
  };
  if (number == null) return '-';
  final raw = number.toString();
  final buffer = StringBuffer();
  for (var index = 0; index < raw.length; index++) {
    if (index > 0 && (raw.length - index) % 3 == 0) buffer.write(',');
    buffer.write(raw[index]);
  }
  return buffer.toString();
}
