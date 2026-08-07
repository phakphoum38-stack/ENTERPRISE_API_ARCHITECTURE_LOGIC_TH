import 'package:flutter/material.dart';

import '../../api/research_os_api_client.dart';

class HomePage extends StatefulWidget {
  const HomePage({required this.apiClient, super.key});

  final ResearchOSApiClient apiClient;

  @override
  State<HomePage> createState() => _HomePageState();
}

class _HomePageState extends State<HomePage> {
  bool _loading = true;
  String? _error;
  Map<String, dynamic>? _health;
  Map<String, dynamic>? _providers;

  @override
  void initState() {
    super.initState();
    _refresh();
  }

  Future<void> _refresh() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final results = await Future.wait<Map<String, dynamic>>(<Future<Map<String, dynamic>>>[
        widget.apiClient.getHealth(),
        widget.apiClient.getProviders(),
      ]);
      if (!mounted) return;
      setState(() {
        _health = results[0];
        _providers = results[1];
        _loading = false;
      });
    } on Object catch (error) {
      if (!mounted) return;
      setState(() {
        _error = error.toString();
        _loading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final activeProvider = _providers?['active']?.toString() ?? 'unknown';
    final apiReady = _health?['status']?.toString() == 'ok';

    return Scaffold(
      appBar: AppBar(
        title: const Text('Overview'),
        actions: <Widget>[
          IconButton(
            tooltip: 'Refresh dashboard',
            onPressed: _loading ? null : _refresh,
            icon: const Icon(Icons.refresh),
          ),
          const SizedBox(width: 8),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: _refresh,
        child: ListView(
          padding: const EdgeInsets.fromLTRB(24, 18, 24, 32),
          children: <Widget>[
            Container(
              padding: const EdgeInsets.all(24),
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  colors: <Color>[
                    scheme.primaryContainer,
                    scheme.primaryContainer.withValues(alpha: .58),
                  ],
                ),
                borderRadius: BorderRadius.circular(20),
              ),
              child: Row(
                children: <Widget>[
                  Container(
                    width: 54,
                    height: 54,
                    alignment: Alignment.center,
                    decoration: BoxDecoration(
                      color: scheme.primary,
                      borderRadius: BorderRadius.circular(16),
                    ),
                    child: Text(
                      'R',
                      style: TextStyle(
                        color: scheme.onPrimary,
                        fontSize: 26,
                        fontWeight: FontWeight.w900,
                      ),
                    ),
                  ),
                  const SizedBox(width: 18),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: <Widget>[
                        Text(
                          'Research OS',
                          style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                                fontWeight: FontWeight.w800,
                              ),
                        ),
                        const SizedBox(height: 4),
                        Text(
                          'AI • Memory • Knowledge • Agents • Workspace',
                          style: Theme.of(context).textTheme.bodyMedium,
                        ),
                      ],
                    ),
                  ),
                  _HealthBadge(ready: apiReady),
                ],
              ),
            ),
            if (_loading) ...<Widget>[
              const SizedBox(height: 14),
              const LinearProgressIndicator(),
            ],
            if (_error != null) ...<Widget>[
              const SizedBox(height: 16),
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(18),
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: <Widget>[
                      Icon(Icons.error_outline, color: scheme.error),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: <Widget>[
                            const Text(
                              'Research OS API unavailable',
                              style: TextStyle(fontWeight: FontWeight.w700),
                            ),
                            const SizedBox(height: 6),
                            Text(_error!),
                          ],
                        ),
                      ),
                      TextButton(onPressed: _refresh, child: const Text('Retry')),
                    ],
                  ),
                ),
              ),
            ],
            const SizedBox(height: 24),
            _SectionHeader(
              title: 'System status',
              subtitle: 'Current health of the local Research OS workspace',
            ),
            const SizedBox(height: 12),
            LayoutBuilder(
              builder: (context, constraints) {
                final columns = constraints.maxWidth >= 1050
                    ? 4
                    : constraints.maxWidth >= 650
                        ? 2
                        : 1;
                return GridView.count(
                  crossAxisCount: columns,
                  shrinkWrap: true,
                  physics: const NeverScrollableScrollPhysics(),
                  mainAxisSpacing: 12,
                  crossAxisSpacing: 12,
                  mainAxisExtent: 140,
                  children: <Widget>[
                    _StatusCard(
                      icon: Icons.dns_outlined,
                      title: 'Local API',
                      value: apiReady ? 'Online' : 'Offline',
                      detail: _health?['version']?.toString() ?? 'Research OS API',
                    ),
                    _StatusCard(
                      icon: Icons.smart_toy_outlined,
                      title: 'AI Provider',
                      value: activeProvider,
                      detail: 'Active inference provider',
                    ),
                    _StatusCard(
                      icon: Icons.memory_outlined,
                      title: 'Memory',
                      value: _health?['memory'] == true ? 'Ready' : 'Unknown',
                      detail: 'Local knowledge memory',
                    ),
                    _StatusCard(
                      icon: Icons.apps_outlined,
                      title: 'Workspace',
                      value: _health?['google_workspace'] == true ? 'Available' : 'Not ready',
                      detail: 'Google Workspace connector',
                    ),
                  ],
                );
              },
            ),
            const SizedBox(height: 28),
            _SectionHeader(
              title: 'Workspaces',
              subtitle: 'Core areas are grouped by purpose instead of one long menu',
            ),
            const SizedBox(height: 12),
            LayoutBuilder(
              builder: (context, constraints) {
                final columns = constraints.maxWidth >= 980 ? 3 : constraints.maxWidth >= 620 ? 2 : 1;
                final width = (constraints.maxWidth - ((columns - 1) * 12)) / columns;
                return Wrap(
                  spacing: 12,
                  runSpacing: 12,
                  children: const <Widget>[
                    _WorkspaceCard(Icons.auto_awesome_outlined, 'AI & Agents', 'Chat, specialist agents and task runtime'),
                    _WorkspaceCard(Icons.local_library_outlined, 'Knowledge', 'Library, memory and knowledge graph'),
                    _WorkspaceCard(Icons.link_outlined, 'Connections', 'GitHub and Google Workspace integrations'),
                    _WorkspaceCard(Icons.security_outlined, 'Local System', 'Windows Service, API, storage and backup'),
                    _WorkspaceCard(Icons.monitor_heart_outlined, 'Monitoring', 'Health, runtime and system visibility'),
                    _WorkspaceCard(Icons.tune_outlined, 'Configuration', 'Providers, endpoints and application settings'),
                  ].map((card) => SizedBox(width: width, child: card)).toList(),
                );
              },
            ),
          ],
        ),
      ),
    );
  }
}

class _SectionHeader extends StatelessWidget {
  const _SectionHeader({required this.title, required this.subtitle});
  final String title;
  final String subtitle;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: <Widget>[
        Text(title, style: Theme.of(context).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w800)),
        const SizedBox(height: 3),
        Text(subtitle, style: Theme.of(context).textTheme.bodyMedium?.copyWith(color: Theme.of(context).colorScheme.onSurfaceVariant)),
      ],
    );
  }
}

class _HealthBadge extends StatelessWidget {
  const _HealthBadge({required this.ready});
  final bool ready;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      decoration: BoxDecoration(
        color: scheme.surface.withValues(alpha: .75),
        borderRadius: BorderRadius.circular(999),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: <Widget>[
          Icon(Icons.circle, size: 9, color: ready ? Colors.green : scheme.error),
          const SizedBox(width: 7),
          Text(ready ? 'System ready' : 'API offline', style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 12)),
        ],
      ),
    );
  }
}

class _StatusCard extends StatelessWidget {
  const _StatusCard({required this.icon, required this.title, required this.value, required this.detail});
  final IconData icon;
  final String title;
  final String value;
  final String detail;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: <Widget>[
            Row(
              children: <Widget>[
                Container(
                  width: 36,
                  height: 36,
                  alignment: Alignment.center,
                  decoration: BoxDecoration(color: scheme.secondaryContainer, borderRadius: BorderRadius.circular(10)),
                  child: Icon(icon, size: 20, color: scheme.onSecondaryContainer),
                ),
                const Spacer(),
                Icon(Icons.circle, size: 8, color: scheme.primary),
              ],
            ),
            const Spacer(),
            Text(title, style: Theme.of(context).textTheme.labelMedium?.copyWith(color: scheme.onSurfaceVariant)),
            const SizedBox(height: 2),
            Text(value, maxLines: 1, overflow: TextOverflow.ellipsis, style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w800)),
            Text(detail, maxLines: 1, overflow: TextOverflow.ellipsis, style: Theme.of(context).textTheme.bodySmall),
          ],
        ),
      ),
    );
  }
}

class _WorkspaceCard extends StatelessWidget {
  const _WorkspaceCard(this.icon, this.title, this.subtitle);
  final IconData icon;
  final String title;
  final String subtitle;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(18),
        child: Row(
          children: <Widget>[
            Container(
              width: 44,
              height: 44,
              alignment: Alignment.center,
              decoration: BoxDecoration(color: scheme.surfaceContainerHighest, borderRadius: BorderRadius.circular(13)),
              child: Icon(icon, color: scheme.primary),
            ),
            const SizedBox(width: 14),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: <Widget>[
                  Text(title, style: const TextStyle(fontWeight: FontWeight.w800)),
                  const SizedBox(height: 4),
                  Text(subtitle, maxLines: 2, overflow: TextOverflow.ellipsis, style: Theme.of(context).textTheme.bodySmall),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}
