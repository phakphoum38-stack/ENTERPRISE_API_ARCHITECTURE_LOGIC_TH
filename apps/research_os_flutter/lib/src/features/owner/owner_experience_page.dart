import 'package:flutter/material.dart';

import '../../api/research_os_api_client.dart';

class OwnerExperiencePage extends StatefulWidget {
  const OwnerExperiencePage({required this.apiClient, super.key});

  final ResearchOSApiClient apiClient;

  @override
  State<OwnerExperiencePage> createState() => _OwnerExperiencePageState();
}

class _OwnerExperiencePageState extends State<OwnerExperiencePage> {
  bool _loading = true;
  Map<String, dynamic> _auth = const <String, dynamic>{};
  Map<String, dynamic> _health = const <String, dynamic>{};
  Map<String, dynamic> _projects = const <String, dynamic>{};
  Map<String, dynamic> _workflows = const <String, dynamic>{};
  Map<String, dynamic> _agents = const <String, dynamic>{};
  Map<String, dynamic> _providers = const <String, dynamic>{};
  String? _error;

  @override
  void initState() {
    super.initState();
    _refresh();
  }

  Future<Map<String, dynamic>> _read(
    Future<Map<String, dynamic>> Function() operation,
    String label,
  ) async {
    try {
      return await operation();
    } on Object catch (error) {
      return <String, dynamic>{'__error': '$label: $error'};
    }
  }

  Future<void> _refresh() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final values = await Future.wait<Map<String, dynamic>>(<Future<Map<String, dynamic>>>[
        _read(widget.apiClient.getAuthStatus, 'Identity'),
        _read(widget.apiClient.getHealth, 'Health'),
        _read(widget.apiClient.getProjects, 'Projects'),
        _read(() => widget.apiClient.getOrchestrations(limit: 100), 'Workflows'),
        _read(widget.apiClient.getAgents, 'Agents'),
        _read(widget.apiClient.getProviders, 'Providers'),
      ]);
      if (!mounted) return;
      setState(() {
        _auth = values[0];
        _health = values[1];
        _projects = values[2];
        _workflows = values[3];
        _agents = values[4];
        _providers = values[5];
        final failures = values
            .where((item) => item['__error'] != null)
            .map((item) => item['__error'].toString())
            .toList(growable: false);
        _error = failures.isEmpty ? null : failures.join(' | ');
        _loading = false;
      });
    } on Object catch (error) {
      if (!mounted) return;
      setState(() {
        _loading = false;
        _error = error.toString();
      });
    }
  }

  bool get _isOwner {
    final role = (_auth['role'] ?? _auth['user']?['role'] ?? '').toString();
    return role.toLowerCase() == 'owner';
  }

  int _count(Map<String, dynamic> value, String key) {
    final raw = value[key];
    return raw is int ? raw : int.tryParse('$raw') ?? 0;
  }

  String _value(Map<String, dynamic> value, String key, String fallback) {
    final raw = value[key];
    final text = raw?.toString().trim() ?? '';
    return text.isEmpty ? fallback : text;
  }

  Widget _metric(String label, String value, IconData icon) {
    final scheme = Theme.of(context).colorScheme;
    return Card(
      child: ListTile(
        leading: Icon(icon, color: scheme.primary),
        title: Text(value, style: const TextStyle(fontWeight: FontWeight.w800)),
        subtitle: Text(label),
      ),
    );
  }

  Widget _section(String title, List<Widget> children) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: <Widget>[
            Text(title, style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w800)),
            const SizedBox(height: 12),
            ...children,
          ],
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final health = _value(_health, 'status', 'unknown');
    final projectCount = _count(_projects, 'count');
    final workflowCount = _count(_workflows, 'count');
    final agentCount = _count(_agents, 'count');
    final providerCount = _count(_providers, 'count');

    return Scaffold(
      appBar: AppBar(
        title: const Text('Owner Experience'),
        actions: <Widget>[
          IconButton(
            tooltip: 'Refresh',
            onPressed: _loading ? null : _refresh,
            icon: const Icon(Icons.refresh),
          ),
        ],
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : RefreshIndicator(
              onRefresh: _refresh,
              child: ListView(
                padding: const EdgeInsets.all(16),
                children: <Widget>[
                  if (_error != null)
                    Card(
                      child: ListTile(
                        leading: const Icon(Icons.warning_amber_outlined),
                        title: const Text('Some observations are unavailable'),
                        subtitle: Text(_error!),
                      ),
                    ),
                  _section(
                    'Owner Identity & Authority',
                    <Widget>[
                      ListTile(
                        contentPadding: EdgeInsets.zero,
                        leading: Icon(
                          _isOwner ? Icons.verified_user_outlined : Icons.person_outline,
                        ),
                        title: Text(
                          _isOwner ? 'OWNER session verified' : 'Owner session not verified',
                          style: const TextStyle(fontWeight: FontWeight.w800),
                        ),
                        subtitle: Text(
                          'Identity is derived from the authenticated server session. '
                          'Owner authority is unrestricted by resource or scope.',
                        ),
                      ),
                      const ListTile(
                        contentPadding: EdgeInsets.zero,
                        leading: Icon(Icons.lock_outline),
                        title: Text('Server authority boundary'),
                        subtitle: Text(
                          'This surface observes authority; it does not grant, approve, execute, merge, or release.',
                        ),
                      ),
                    ],
                  ),
                  _section(
                    'Platform State',
                    <Widget>[
                      Wrap(
                        spacing: 12,
                        runSpacing: 12,
                        children: <Widget>[
                          SizedBox(width: 210, child: _metric('API health', health, Icons.health_and_safety_outlined)),
                          SizedBox(width: 210, child: _metric('Projects configured', '$projectCount', Icons.folder_copy_outlined)),
                          SizedBox(width: 210, child: _metric('Workflow runs observed', '$workflowCount', Icons.account_tree_outlined)),
                          SizedBox(width: 210, child: _metric('Agents registered', '$agentCount', Icons.smart_toy_outlined)),
                          SizedBox(width: 210, child: _metric('Providers visible', '$providerCount', Icons.hub_outlined)),
                        ],
                      ),
                    ],
                  ),
                  _section(
                    'Shared Platform Boundaries',
                    <Widget>[
                      const ListTile(
                        contentPadding: EdgeInsets.zero,
                        leading: Icon(Icons.workspaces_outlined),
                        title: Text('Projects'),
                        subtitle: Text('Uses the existing ProjectRegistry and shared execution/evidence planes.'),
                      ),
                      const ListTile(
                        contentPadding: EdgeInsets.zero,
                        leading: Icon(Icons.account_tree_outlined),
                        title: Text('Workflows'),
                        subtitle: Text('Uses the existing Workflow Engine and orchestration APIs.'),
                      ),
                      const ListTile(
                        contentPadding: EdgeInsets.zero,
                        leading: Icon(Icons.fact_check_outlined),
                        title: Text('Evidence & Audit'),
                        subtitle: Text('Observations remain attributable to the existing evidence/audit plane.'),
                      ),
                      const ListTile(
                        contentPadding: EdgeInsets.zero,
                        leading: Icon(Icons.verified_outlined),
                        title: Text('Release'),
                        subtitle: Text('FINAL_GATE remains the single release authority.'),
                      ),
                    ],
                  ),
                  _section(
                    'Owner Special Boundary',
                    <Widget>[
                      const ListTile(
                        contentPadding: EdgeInsets.zero,
                        leading: Icon(Icons.desktop_windows_outlined),
                        title: Text('Owner Special / Friend'),
                        subtitle: Text(
                          'Existing owner_special runtime and Friend service remain separate boundaries. '
                          'This canonical surface does not duplicate or replace that runtime.',
                        ),
                      ),
                      const ListTile(
                        contentPadding: EdgeInsets.zero,
                        leading: Icon(Icons.security_outlined),
                        title: Text('Recovery & conflict policy'),
                        subtitle: Text(
                          'Existing lifecycle, resource-version conflict, stop/release/reconcile, and recovery controls remain authoritative.',
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),
    );
  }
}
