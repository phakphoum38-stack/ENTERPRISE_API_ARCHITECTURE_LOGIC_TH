import 'package:flutter/material.dart';

import 'api/v3_api.dart';

class ResearchOSV3App extends StatelessWidget {
  const ResearchOSV3App({super.key, required this.api});

  final V3Api api;

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Research OS V3',
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
    final results = await Future.wait([
      widget.api.health(),
      widget.api.master(tasks: 30),
      widget.api.providers(),
    ]);
    return _V3Snapshot(
      health: results[0],
      master: results[1],
      providers: results[2],
    );
  }

  void _refresh() {
    setState(() => _snapshot = _loadSnapshot());
  }

  @override
  Widget build(BuildContext context) {
    final wide = MediaQuery.sizeOf(context).width >= 1100;
    const destinations = [
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
              selectedIndex: _selectedIndex,
              destinations: destinations,
              onDestinationSelected: (index) {
                setState(() => _selectedIndex = index);
              },
              leading: Padding(
                padding: const EdgeInsets.symmetric(vertical: 16),
                child: wide
                    ? const Text(
                        'Research OS V3',
                        style: TextStyle(fontWeight: FontWeight.w700),
                      )
                    : const Icon(Icons.auto_awesome),
              ),
            ),
            const VerticalDivider(width: 1),
            Expanded(
              child: switch (_selectedIndex) {
                0 => _HomePage(snapshot: _snapshot, onRefresh: _refresh),
                1 => const _ChatShell(),
                2 => const _FactoryPage(),
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
      title: 'V3 Control Center',
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
          if (value.hasError) {
            return _ConnectionError(error: value.error);
          }
          final data = value.data!;
          final capacity = data.master['maximum_leaf_capacity'];
          final scale = data.master['scale'];
          final providers = data.providerList;
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
                    label: 'Adaptive scale',
                    value: scale?.toString() ?? '-',
                    icon: Icons.memory,
                  ),
                  _MetricCard(
                    label: 'Leaf capacity',
                    value: _formatInteger(capacity),
                    icon: Icons.schema_outlined,
                  ),
                  _MetricCard(
                    label: 'Providers',
                    value: '${providers.length}',
                    icon: Icons.hub_outlined,
                  ),
                ],
              ),
              const SizedBox(height: 24),
              const Text(
                'Architecture',
                style: TextStyle(fontSize: 20, fontWeight: FontWeight.w700),
              ),
              const SizedBox(height: 12),
              const Card(
                child: Padding(
                  padding: EdgeInsets.all(20),
                  child: Text(
                    'Unified Master → Factory → Team → Tests → Release\n'
                    'Adaptive profiles: 1³ → 3³ → 6³ → 6⁶. '
                    'Maximum capacity is logical and never pre-spawned.',
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

class _ChatShell extends StatefulWidget {
  const _ChatShell();

  @override
  State<_ChatShell> createState() => _ChatShellState();
}

class _ChatShellState extends State<_ChatShell> {
  final _controller = TextEditingController();

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return _PageFrame(
      title: 'Chat',
      child: Row(
        children: [
          SizedBox(
            width: 220,
            child: ListView(
              padding: const EdgeInsets.all(12),
              children: [
                FilledButton.icon(
                  onPressed: () {},
                  icon: const Icon(Icons.add),
                  label: const Text('New chat'),
                ),
                const SizedBox(height: 16),
                const ListTile(
                  selected: true,
                  leading: Icon(Icons.chat_outlined),
                  title: Text('V3 conversation'),
                  subtitle: Text('Local-first shell'),
                ),
              ],
            ),
          ),
          const VerticalDivider(width: 1),
          Expanded(
            child: Column(
              children: [
                const Expanded(
                  child: Center(
                    child: Padding(
                      padding: EdgeInsets.all(32),
                      child: Text(
                        'Conversation execution will use the governed V3 '
                        'orchestrator and provider adapters. The desktop shell '
                        'never stores provider API keys.',
                        textAlign: TextAlign.center,
                      ),
                    ),
                  ),
                ),
                Padding(
                  padding: const EdgeInsets.all(16),
                  child: TextField(
                    controller: _controller,
                    decoration: const InputDecoration(
                      border: OutlineInputBorder(),
                      hintText: 'Message Research OS V3',
                      suffixIcon: Icon(Icons.send),
                    ),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _FactoryPage extends StatelessWidget {
  const _FactoryPage();

  @override
  Widget build(BuildContext context) {
    const stages = ['Master', 'Factory', 'Team', 'Tests', 'Release'];
    return _PageFrame(
      title: 'Adaptive Software Factory',
      child: ListView.separated(
        padding: const EdgeInsets.all(24),
        itemCount: stages.length,
        separatorBuilder: (_, __) => const Icon(Icons.arrow_downward),
        itemBuilder: (context, index) {
          return Card(
            child: ListTile(
              leading: CircleAvatar(child: Text('${index + 1}')),
              title: Text(stages[index]),
              subtitle: Text(
                index == 0
                    ? 'Chooses the smallest safe adaptive profile.'
                    : 'Receives governed work from the previous stage.',
              ),
            ),
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
          if (value.hasError) {
            return _ConnectionError(error: value.error);
          }
          final providers = value.data!.providerList;
          return ListView(
            padding: const EdgeInsets.all(24),
            children: [
              const Card(
                child: ListTile(
                  leading: Icon(Icons.key_off_outlined),
                  title: Text('Secrets stay outside the desktop app'),
                  subtitle: Text(
                    'Credentials are resolved by the V3 service. This screen '
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

class _PageFrame extends StatelessWidget {
  const _PageFrame({
    required this.title,
    required this.child,
    this.action,
  });

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
          'V3 local service is not ready.\n$error',
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
  });

  final Map<String, dynamic> health;
  final Map<String, dynamic> master;
  final Map<String, dynamic> providers;

  List<Map<String, dynamic>> get providerList {
    final value = providers['providers'];
    if (value is! List) {
      return const [];
    }
    return value
        .whereType<Map>()
        .map((item) => Map<String, dynamic>.from(item))
        .toList(growable: false);
  }
}

String _formatInteger(Object? value) {
  final number = switch (value) {
    int value => value,
    num value => value.toInt(),
    _ => int.tryParse(value?.toString() ?? ''),
  };
  if (number == null) {
    return '-';
  }
  final raw = number.toString();
  final buffer = StringBuffer();
  for (var index = 0; index < raw.length; index++) {
    if (index > 0 && (raw.length - index) % 3 == 0) {
      buffer.write(',');
    }
    buffer.write(raw[index]);
  }
  return buffer.toString();
}
