import 'dart:async';

import 'package:flutter/material.dart';

import '../../api/api_connection_state.dart';
import '../../api/research_os_api_client.dart';
import '../../identity/owner_profile.dart';
import '../../identity/owner_profile_store.dart';
import '../../identity/owner_session_store.dart';

class HomePage extends StatefulWidget {
  const HomePage({required this.apiClient, super.key});

  final ResearchOSApiClient apiClient;

  @override
  State<HomePage> createState() => _HomePageState();
}

class _HomePageState extends State<HomePage> {
  static const _refreshInterval = Duration(seconds: 30);

  Timer? _refreshTimer;
  bool _loading = true;
  String? _error;
  Map<String, dynamic>? _health;
  Map<String, dynamic>? _providers;
  DateTime? _lastUpdated;

  @override
  void initState() {
    super.initState();
    _refresh();
    _refreshTimer = Timer.periodic(
      _refreshInterval,
      (_) => unawaited(_refresh(silent: true)),
    );
  }

  @override
  void dispose() {
    _refreshTimer?.cancel();
    super.dispose();
  }

  Future<void> _refresh({bool silent = false}) async {
    if (!silent && mounted) {
      setState(() {
        _loading = true;
        _error = null;
      });
    }
    try {
      final results = await Future.wait<Map<String, dynamic>>(
        <Future<Map<String, dynamic>>>[
          widget.apiClient.getHealth(),
          widget.apiClient.getProviders(),
        ],
      );
      if (!mounted) return;
      setState(() {
        _health = results[0];
        _providers = results[1];
        _lastUpdated = DateTime.now();
        _loading = false;
        _error = null;
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
    final providerCount = (_providers?['providers'] is List)
        ? (_providers!['providers'] as List).length
        : 0;
    final apiReady = _health?['status']?.toString() == 'ok';
    final version = _health?['version']?.toString() ?? 'unknown';

    return Scaffold(
      appBar: AppBar(
        title: const Text('Dashboard'),
        actions: <Widget>[
          if (_lastUpdated != null)
            Padding(
              padding: const EdgeInsets.only(right: 8),
              child: Center(
                child: Text(
                  'Updated ${_timeLabel(_lastUpdated!)}',
                  style: Theme.of(context).textTheme.bodySmall,
                ),
              ),
            ),
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
            ValueListenableBuilder<ApiConnectionSnapshot>(
              valueListenable: apiConnectionState,
              builder: (context, connection, _) {
                final connected =
                    connection.phase == ApiConnectionPhase.connected && apiReady;
                return _HeroPanel(
                  connected: connected,
                  connectionLabel: connection.label,
                  provider: activeProvider,
                  version: version,
                );
              },
            ),
            if (_loading) ...<Widget>[
              const SizedBox(height: 14),
              const LinearProgressIndicator(),
            ],
            if (_error != null) ...<Widget>[
              const SizedBox(height: 16),
              _ErrorCard(error: _error!, onRetry: _refresh),
            ],
            const SizedBox(height: 24),
            const _SectionHeader(
              title: 'System status',
              subtitle: 'Live health, provider and automatic API connection state',
            ),
            const SizedBox(height: 12),
            ValueListenableBuilder<ApiConnectionSnapshot>(
              valueListenable: apiConnectionState,
              builder: (context, connection, _) {
                final latency = connection.latency;
                final endpoint = connection.baseUrl ?? widget.apiClient.baseUrl;
                final source = connection.source ?? _endpointSource(endpoint);
                return LayoutBuilder(
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
                      mainAxisExtent: 152,
                      children: <Widget>[
                        _StatusCard(
                          icon: Icons.dns_outlined,
                          title: 'Local API',
                          value: apiReady ? 'Online' : connection.label,
                          detail: endpoint,
                          healthy: apiReady,
                        ),
                        _StatusCard(
                          icon: Icons.speed_outlined,
                          title: 'API Latency',
                          value: latency == null
                              ? '—'
                              : '${latency.inMilliseconds} ms',
                          detail: 'Source: $source',
                          healthy: latency != null,
                        ),
                        _StatusCard(
                          icon: Icons.smart_toy_outlined,
                          title: 'AI Provider',
                          value: activeProvider,
                          detail: '$providerCount provider(s) available',
                          healthy: activeProvider != 'unknown',
                        ),
                        _StatusCard(
                          icon: Icons.memory_outlined,
                          title: 'Memory',
                          value: _health?['memory'] == true ? 'Ready' : 'Unknown',
                          detail: 'Runtime $version',
                          healthy: _health?['memory'] == true,
                        ),
                      ],
                    );
                  },
                );
              },
            ),
            const SizedBox(height: 28),
            const _SectionHeader(
              title: 'Identity & privacy',
              subtitle: 'Owner identity is optional; private context stays outside public releases',
            ),
            const SizedBox(height: 12),
            ValueListenableBuilder<OwnerProfile?>(
              valueListenable: ownerProfileState,
              builder: (context, profile, _) {
                return ValueListenableBuilder<OwnerSession?>(
                  valueListenable: ownerSessionState,
                  builder: (context, session, __) {
                    return _IdentityCard(profile: profile, session: session);
                  },
                );
              },
            ),
            const SizedBox(height: 28),
            const _SectionHeader(
              title: 'Recent activity',
              subtitle: 'Current runtime events from this Research OS session',
            ),
            const SizedBox(height: 12),
            ValueListenableBuilder<ApiConnectionSnapshot>(
              valueListenable: apiConnectionState,
              builder: (context, connection, _) {
                return Card(
                  child: Column(
                    children: <Widget>[
                      _ActivityTile(
                        icon: Icons.cloud_done_outlined,
                        title: 'API ${connection.label}',
                        subtitle: connection.baseUrl ?? widget.apiClient.baseUrl,
                      ),
                      const Divider(height: 1),
                      _ActivityTile(
                        icon: Icons.smart_toy_outlined,
                        title: 'Provider $activeProvider',
                        subtitle: '$providerCount provider(s) discovered',
                      ),
                      const Divider(height: 1),
                      _ActivityTile(
                        icon: Icons.memory_outlined,
                        title: _health?['memory'] == true
                            ? 'Memory ready'
                            : 'Memory status unknown',
                        subtitle: 'Research OS API $version',
                      ),
                    ],
                  ),
                );
              },
            ),
            const SizedBox(height: 28),
            const _SectionHeader(
              title: 'Core areas',
              subtitle: 'Research OS features grouped around the local AI runtime',
            ),
            const SizedBox(height: 12),
            LayoutBuilder(
              builder: (context, constraints) {
                final columns = constraints.maxWidth >= 980
                    ? 3
                    : constraints.maxWidth >= 620
                        ? 2
                        : 1;
                final width =
                    (constraints.maxWidth - ((columns - 1) * 12)) / columns;
                return Wrap(
                  spacing: 12,
                  runSpacing: 12,
                  children: const <Widget>[
                    _WorkspaceCard(
                      Icons.auto_awesome_outlined,
                      'AI Workspace',
                      'Chat, providers and task runtime',
                    ),
                    _WorkspaceCard(
                      Icons.local_library_outlined,
                      'Knowledge',
                      'Library, memory and knowledge graph',
                    ),
                    _WorkspaceCard(
                      Icons.hub_outlined,
                      'API & Providers',
                      'Auto discovery, health, failover and routing',
                    ),
                    _WorkspaceCard(
                      Icons.security_outlined,
                      'Local System',
                      'Local API, storage, service and portable runtime',
                    ),
                    _WorkspaceCard(
                      Icons.monitor_heart_outlined,
                      'Monitoring',
                      'Health, latency and runtime visibility',
                    ),
                    _WorkspaceCard(
                      Icons.tune_outlined,
                      'Configuration',
                      'Endpoints, identity and application settings',
                    ),
                  ].map((card) => SizedBox(width: width, child: card)).toList(),
                );
              },
            ),
          ],
        ),
      ),
    );
  }

  static String _timeLabel(DateTime value) {
    final local = value.toLocal();
    final hour = local.hour.toString().padLeft(2, '0');
    final minute = local.minute.toString().padLeft(2, '0');
    final second = local.second.toString().padLeft(2, '0');
    return '$hour:$minute:$second';
  }

  static String _endpointSource(String endpoint) {
    final uri = Uri.tryParse(endpoint);
    final host = uri?.host ?? '';
    if (host == '127.0.0.1' || host == 'localhost' || host == '::1') {
      return 'local';
    }
    if (host == '10.0.2.2' || host == '10.0.3.2') return 'emulator';
    if (_isPrivateIpv4(host)) return 'lan';
    if (uri?.scheme == 'https') return 'cloud';
    return 'configured';
  }

  static bool _isPrivateIpv4(String host) {
    final parts = host.split('.');
    if (parts.length != 4) return false;
    final values = parts.map(int.tryParse).toList(growable: false);
    if (values.any((value) => value == null)) return false;
    final a = values[0]!;
    final b = values[1]!;
    return a == 10 ||
        (a == 172 && b >= 16 && b <= 31) ||
        (a == 192 && b == 168);
  }
}

class _HeroPanel extends StatelessWidget {
  const _HeroPanel({
    required this.connected,
    required this.connectionLabel,
    required this.provider,
    required this.version,
  });

  final bool connected;
  final String connectionLabel;
  final String provider;
  final String version;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Container(
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
            width: 56,
            height: 56,
            alignment: Alignment.center,
            decoration: BoxDecoration(
              color: scheme.primary,
              borderRadius: BorderRadius.circular(17),
            ),
            child: Text(
              'R',
              style: TextStyle(
                color: scheme.onPrimary,
                fontSize: 27,
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
                  style: Theme.of(context)
                      .textTheme
                      .headlineSmall
                      ?.copyWith(fontWeight: FontWeight.w800),
                ),
                const SizedBox(height: 4),
                Text(
                  '$provider • API $connectionLabel • v$version',
                  style: Theme.of(context).textTheme.bodyMedium,
                ),
              ],
            ),
          ),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
            decoration: BoxDecoration(
              color: scheme.surface.withValues(alpha: .78),
              borderRadius: BorderRadius.circular(999),
            ),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: <Widget>[
                Icon(
                  Icons.circle,
                  size: 9,
                  color: connected ? Colors.green : scheme.error,
                ),
                const SizedBox(width: 7),
                Text(
                  connected ? 'System ready' : connectionLabel,
                  style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 12),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _ErrorCard extends StatelessWidget {
  const _ErrorCard({required this.error, required this.onRetry});

  final String error;
  final Future<void> Function() onRetry;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Card(
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
                  Text(error),
                ],
              ),
            ),
            TextButton(onPressed: onRetry, child: const Text('Retry')),
          ],
        ),
      ),
    );
  }
}

class _IdentityCard extends StatelessWidget {
  const _IdentityCard({required this.profile, required this.session});

  final OwnerProfile? profile;
  final OwnerSession? session;

  @override
  Widget build(BuildContext context) {
    final verified = session != null && !session!.expired;
    return Card(
      child: ListTile(
        leading: Icon(
          verified ? Icons.verified_user_outlined : Icons.person_outline,
        ),
        title: Text(profile?.email ?? 'General AI profile'),
        subtitle: Text(
          profile == null
              ? 'No owner identity is attached to this device.'
              : verified
                  ? 'Verified owner session • private context remains local.'
                  : 'Local owner profile • cloud verification not active.',
        ),
        trailing: Chip(label: Text(verified ? 'Verified' : 'Local')),
      ),
    );
  }
}

class _ActivityTile extends StatelessWidget {
  const _ActivityTile({
    required this.icon,
    required this.title,
    required this.subtitle,
  });

  final IconData icon;
  final String title;
  final String subtitle;

  @override
  Widget build(BuildContext context) {
    return ListTile(
      leading: Icon(icon),
      title: Text(title),
      subtitle: Text(subtitle, maxLines: 1, overflow: TextOverflow.ellipsis),
      trailing: const Icon(Icons.chevron_right, size: 18),
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
        Text(
          title,
          style: Theme.of(context)
              .textTheme
              .titleLarge
              ?.copyWith(fontWeight: FontWeight.w800),
        ),
        const SizedBox(height: 3),
        Text(
          subtitle,
          style: Theme.of(context)
              .textTheme
              .bodyMedium
              ?.copyWith(color: Theme.of(context).colorScheme.onSurfaceVariant),
        ),
      ],
    );
  }
}

class _StatusCard extends StatelessWidget {
  const _StatusCard({
    required this.icon,
    required this.title,
    required this.value,
    required this.detail,
    required this.healthy,
  });

  final IconData icon;
  final String title;
  final String value;
  final String detail;
  final bool healthy;

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
                  decoration: BoxDecoration(
                    color: scheme.secondaryContainer,
                    borderRadius: BorderRadius.circular(10),
                  ),
                  child: Icon(icon, size: 20, color: scheme.onSecondaryContainer),
                ),
                const Spacer(),
                Icon(
                  Icons.circle,
                  size: 8,
                  color: healthy ? Colors.green : scheme.outline,
                ),
              ],
            ),
            const Spacer(),
            Text(
              title,
              style: Theme.of(context)
                  .textTheme
                  .labelMedium
                  ?.copyWith(color: scheme.onSurfaceVariant),
            ),
            const SizedBox(height: 2),
            Text(
              value,
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
              style: Theme.of(context)
                  .textTheme
                  .titleMedium
                  ?.copyWith(fontWeight: FontWeight.w800),
            ),
            Text(
              detail,
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
              style: Theme.of(context).textTheme.bodySmall,
            ),
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
              decoration: BoxDecoration(
                color: scheme.surfaceContainerHighest,
                borderRadius: BorderRadius.circular(13),
              ),
              child: Icon(icon, color: scheme.primary),
            ),
            const SizedBox(width: 14),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: <Widget>[
                  Text(title, style: const TextStyle(fontWeight: FontWeight.w800)),
                  const SizedBox(height: 4),
                  Text(
                    subtitle,
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                    style: Theme.of(context).textTheme.bodySmall,
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}
