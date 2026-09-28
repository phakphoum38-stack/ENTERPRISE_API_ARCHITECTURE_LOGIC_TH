import 'package:flutter/material.dart';

import '../../api/research_os_api_client.dart';

class ProjectExperiencePage extends StatefulWidget {
  const ProjectExperiencePage({required this.apiClient, super.key});
  final ResearchOSApiClient apiClient;
  @override
  State<ProjectExperiencePage> createState() => _ProjectExperiencePageState();
}

class _ProjectExperiencePageState extends State<ProjectExperiencePage> {
  bool _loading = true;
  String? _error;
  Map<String, dynamic>? _snapshot;

  @override
  void initState() {
    super.initState();
    _refresh();
  }

  Future<void> _refresh() async {
    setState(() { _loading = true; _error = null; });
    try {
      final result = await widget.apiClient.getProjects();
      if (!mounted) return;
      setState(() { _snapshot = result; _loading = false; });
    } on Object catch (error) {
      if (!mounted) return;
      setState(() { _error = error.toString(); _loading = false; });
    }
  }

  @override
  Widget build(BuildContext context) {
    final projects = (_snapshot?['projects'] as List?) ?? const <dynamic>[];
    final supported = _snapshot?['supported_project_contexts']?.toString() ?? '—';
    final configured = _snapshot?['configured_count']?.toString() ?? '—';
    final authority = _snapshot?['release_authority']?.toString() ?? '—';
    final scheme = Theme.of(context).colorScheme;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Projects'),
        actions: <Widget>[
          IconButton(tooltip: 'Refresh projects', onPressed: _loading ? null : _refresh, icon: const Icon(Icons.refresh)),
          const SizedBox(width: 8),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: _refresh,
        child: ListView(
          padding: const EdgeInsets.fromLTRB(24, 18, 24, 32),
          children: <Widget>[
            Card(
              child: Padding(
                padding: const EdgeInsets.all(20),
                child: Wrap(
                  spacing: 28,
                  runSpacing: 18,
                  children: <Widget>[
                    _Metric('Configured', configured, 'ProjectRegistry'),
                    _Metric('Supported', supported, 'shared platform contexts'),
                    _Metric('Scale proof', '10 / 20 / 50 / 100', 'existing execution proof'),
                    _Metric('Release', authority, 'single release authority'),
                  ],
                ),
              ),
            ),
            if (_loading) ...<Widget>[const SizedBox(height: 14), const LinearProgressIndicator()],
            if (_error != null) ...<Widget>[
              const SizedBox(height: 16),
              Card(
                child: ListTile(
                  leading: Icon(Icons.error_outline, color: scheme.error),
                  title: const Text('Project Registry unavailable'),
                  subtitle: Text(_error!),
                  trailing: TextButton(onPressed: _refresh, child: const Text('Retry')),
                ),
              ),
            ],
            const SizedBox(height: 24),
            Text('Project Registry', style: Theme.of(context).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w800)),
            const SizedBox(height: 6),
            Text(
              'Project identity and configuration are displayed from the existing shared registry. Execution, authorization, queueing and evidence remain owned by the existing platform.',
              style: Theme.of(context).textTheme.bodyMedium?.copyWith(color: scheme.onSurfaceVariant),
            ),
            const SizedBox(height: 14),
            if (projects.isEmpty && !_loading)
              const Card(child: Padding(padding: EdgeInsets.all(20), child: Text('No configured projects were returned by the registry.')))
            else
              ...projects.map((raw) {
                final project = raw is Map ? raw : const <String, dynamic>{};
                final capabilities = (project['capabilities'] as List?)?.map((item) => item.toString()).toList() ?? const <String>[];
                return Card(
                  margin: const EdgeInsets.only(bottom: 12),
                  child: ExpansionTile(
                    leading: CircleAvatar(child: Text(project['project_id']?.toString().replaceFirst('project-', '') ?? '?')),
                    title: Text(project['display_name']?.toString() ?? 'Unnamed project', style: const TextStyle(fontWeight: FontWeight.w800)),
                    subtitle: Text('${project['project_id'] ?? 'unknown'} • v${project['version'] ?? 'unknown'}'),
                    childrenPadding: const EdgeInsets.fromLTRB(20, 0, 20, 18),
                    children: <Widget>[
                      _DetailRow('Capabilities', capabilities.join(', ')),
                      _DetailRow('Authorization', project['authorization_policy']?.toString() ?? '—'),
                      _DetailRow('Workflow', project['workflow_profile']?.toString() ?? '—'),
                      _DetailRow('Evidence namespace', project['evidence_namespace']?.toString() ?? '—'),
                      _DetailRow('Resource policy', project['resource_policy']?.toString() ?? '—'),
                      _DetailRow('Queue', project['queue_namespace']?.toString() ?? '—'),
                      _DetailRow('Evidence ledger', project['evidence_ledger']?.toString() ?? '—'),
                      _DetailRow('Release authority', project['release_authority']?.toString() ?? '—'),
                    ],
                  ),
                );
              }),
          ],
        ),
      ),
    );
  }
}

class _Metric extends StatelessWidget {
  const _Metric(this.label, this.value, this.detail);
  final String label;
  final String value;
  final String detail;
  @override
  Widget build(BuildContext context) => SizedBox(
    width: 190,
    child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: <Widget>[
      Text(label, style: Theme.of(context).textTheme.labelMedium),
      const SizedBox(height: 4),
      Text(value, style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w800)),
      const SizedBox(height: 2),
      Text(detail, style: Theme.of(context).textTheme.bodySmall),
    ]),
  );
}

class _DetailRow extends StatelessWidget {
  const _DetailRow(this.label, this.value);
  final String label;
  final String value;
  @override
  Widget build(BuildContext context) => Padding(
    padding: const EdgeInsets.only(top: 8),
    child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: <Widget>[
      SizedBox(width: 150, child: Text(label, style: const TextStyle(fontWeight: FontWeight.w700))),
      Expanded(child: Text(value)),
    ]),
  );
}
