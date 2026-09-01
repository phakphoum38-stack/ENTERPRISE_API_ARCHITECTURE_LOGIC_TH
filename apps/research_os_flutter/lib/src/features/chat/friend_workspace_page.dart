import 'package:flutter/material.dart';

import '../../api/research_os_api_client.dart';
import 'chat_page.dart';

class FriendWorkspacePage extends StatefulWidget {
  const FriendWorkspacePage({required this.apiClient, super.key});

  final ResearchOSApiClient apiClient;

  @override
  State<FriendWorkspacePage> createState() => _FriendWorkspacePageState();
}

class _FriendWorkspacePageState extends State<FriendWorkspacePage> {
  bool _loading = false;
  String? _error;
  Map<String, dynamic>? _capacity;
  Map<String, dynamic>? _agents;
  Map<String, dynamic>? _readiness;
  Map<String, dynamic>? _runs;

  Future<void> _refreshInspector() async {
    if (_loading) return;
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final results = await Future.wait<Map<String, dynamic>>(<Future<Map<String, dynamic>>>[
        widget.apiClient.getBrainCapacity(),
        widget.apiClient.getAgents(),
        widget.apiClient.getAgentReadiness(),
        widget.apiClient.getOrchestrations(limit: 5),
      ]);
      if (!mounted) return;
      setState(() {
        _capacity = results[0];
        _agents = results[1];
        _readiness = results[2];
        _runs = results[3];
      });
    } on Object catch (error) {
      if (mounted) setState(() => _error = error.toString());
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  int? _capacityValue() {
    final value = _capacity?['maximum_leaf_capacity'] ?? _capacity?['capacity'];
    return value is num ? value.toInt() : int.tryParse('$value');
  }

  String _scaleValue() => (_capacity?['scale'] ?? '6^6').toString();

  int _listLength(Map<String, dynamic>? payload, String key) {
    final value = payload?[key];
    return value is List ? value.length : 0;
  }

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, constraints) {
        final wide = constraints.maxWidth >= 1100;
        if (!wide) return ChatPage(apiClient: widget.apiClient);

        return Row(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: <Widget>[
            Expanded(child: ChatPage(apiClient: widget.apiClient)),
            const SizedBox(width: 14),
            SizedBox(
              width: 360,
              child: _ContextInspector(
                loading: _loading,
                error: _error,
                scale: _scaleValue(),
                capacity: _capacityValue(),
                agents: _listLength(_agents, 'agents'),
                readyAgents: _listLength(_readiness, 'agents'),
                runs: _listLength(_runs, 'runs'),
                onRefresh: _refreshInspector,
              ),
            ),
          ],
        );
      },
    );
  }
}

class _ContextInspector extends StatelessWidget {
  const _ContextInspector({
    required this.loading,
    required this.error,
    required this.scale,
    required this.capacity,
    required this.agents,
    required this.readyAgents,
    required this.runs,
    required this.onRefresh,
  });

  final bool loading;
  final String? error;
  final String scale;
  final int? capacity;
  final int agents;
  final int readyAgents;
  final int runs;
  final VoidCallback onRefresh;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final runtimeReady = capacity != null;
    return Container(
      decoration: BoxDecoration(
        color: scheme.surface,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: Theme.of(context).dividerColor),
      ),
      child: ListView(
        padding: const EdgeInsets.all(18),
        children: <Widget>[
          Row(
            children: <Widget>[
              Expanded(
                child: Text(
                  'Context Inspector',
                  style: Theme.of(context).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w800),
                ),
              ),
              IconButton(
                tooltip: 'Refresh runtime context',
                onPressed: loading ? null : onRefresh,
                icon: loading
                    ? const SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2))
                    : const Icon(Icons.refresh),
              ),
            ],
          ),
          const SizedBox(height: 4),
          Text('Visible intent, agents, permissions and evidence', style: Theme.of(context).textTheme.bodySmall),
          const SizedBox(height: 18),
          const _InspectorLabel('Current intent'),
          const _InspectorValue('build + verify'),
          const SizedBox(height: 14),
          const _InspectorLabel('Agent Mesh'),
          _InspectorValue(agents == 0 ? 'Not loaded' : '$readyAgents / $agents ready'),
          const SizedBox(height: 14),
          const _InspectorLabel('Skills & Tools'),
          const _InspectorValue('Registry-backed capability routing'),
          const SizedBox(height: 14),
          const _InspectorLabel('Selected agents'),
          const Wrap(
            spacing: 8,
            runSpacing: 8,
            children: <Widget>[
              Chip(label: Text('GUI Designer')),
              Chip(label: Text('Developer')),
            ],
          ),
          const SizedBox(height: 14),
          const _InspectorLabel('Memory & Evidence'),
          const _InspectorValue('Local-first • evidence-aware'),
          const SizedBox(height: 14),
          const _InspectorLabel('Permission boundary'),
          const _InspectorValue('Writes require an explicit execution path; external actions remain credential-scoped.'),
          const SizedBox(height: 18),
          Card(
            margin: EdgeInsets.zero,
            child: Padding(
              padding: const EdgeInsets.all(14),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: <Widget>[
                  Row(
                    children: <Widget>[
                      const Icon(Icons.hub_outlined),
                      const SizedBox(width: 8),
                      Expanded(
                        child: Text(
                          '$scale ORCHESTRATOR',
                          style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w800),
                        ),
                      ),
                      Chip(label: Text(runtimeReady ? 'READY' : 'CHECK')),
                    ],
                  ),
                  const SizedBox(height: 8),
                  Text(capacity == null ? 'Runtime capacity not loaded' : '$capacity logical capacity'),
                  const SizedBox(height: 4),
                  Text('$runs recent orchestration runs'),
                ],
              ),
            ),
          ),
          const SizedBox(height: 14),
          const _InspectorLabel('Evidence'),
          const _EvidenceRow(
            icon: Icons.design_services_outlined,
            title: 'Design created',
            detail: 'GUI Designer • implementation handoff',
          ),
          const _EvidenceRow(
            icon: Icons.fact_check_outlined,
            title: 'Regression',
            detail: 'Runtime result appears after verification',
          ),
          if (error != null) ...<Widget>[
            const SizedBox(height: 12),
            Text(error!, style: TextStyle(color: scheme.error)),
          ],
        ],
      ),
    );
  }
}

class _InspectorLabel extends StatelessWidget {
  const _InspectorLabel(this.text);
  final String text;

  @override
  Widget build(BuildContext context) {
    return Text(text, style: Theme.of(context).textTheme.labelLarge?.copyWith(fontWeight: FontWeight.w700));
  }
}

class _InspectorValue extends StatelessWidget {
  const _InspectorValue(this.text);
  final String text;

  @override
  Widget build(BuildContext context) {
    return Padding(padding: const EdgeInsets.only(top: 4), child: Text(text));
  }
}

class _EvidenceRow extends StatelessWidget {
  const _EvidenceRow({required this.icon, required this.title, required this.detail});
  final IconData icon;
  final String title;
  final String detail;

  @override
  Widget build(BuildContext context) {
    return ListTile(
      contentPadding: EdgeInsets.zero,
      leading: Icon(icon),
      title: Text(title),
      subtitle: Text(detail),
    );
  }
}
