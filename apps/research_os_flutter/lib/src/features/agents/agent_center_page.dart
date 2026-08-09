import 'package:flutter/material.dart';

import '../../api/research_os_api_client.dart';
import '../../ui/enterprise_components.dart';

class AgentCenterPage extends StatefulWidget {
  const AgentCenterPage({required this.apiClient, super.key});

  final ResearchOSApiClient apiClient;

  @override
  State<AgentCenterPage> createState() => _AgentCenterPageState();
}

class _AgentCenterPageState extends State<AgentCenterPage> {
  bool _loading = true;
  bool _creating = false;
  bool _loadingHealth = false;
  String? _error;
  String _workspace = 'default';
  List<Map<String, dynamic>> _runs = const [];
  List<Map<String, dynamic>> _agents = const [];
  final Set<String> _busyRuns = <String>{};

  @override
  void initState() {
    super.initState();
    _loadRuns();
  }

  Future<void> _loadRuns() async {
    if (mounted) setState(() { _loading = true; _error = null; });
    try {
      final payload = await widget.apiClient.getOrchestrations();
      final raw = payload['runs'];
      final runs = raw is List ? raw.whereType<Map>().map(_map).toList() : <Map<String, dynamic>>[];
      if (mounted) setState(() { _runs = runs; _loading = false; });
    } catch (error) {
      if (mounted) setState(() { _loading = false; _error = error.toString(); });
    }
  }

  Future<void> _loadHealth() async {
    setState(() => _loadingHealth = true);
    try {
      final payload = await widget.apiClient.getAgents();
      final raw = payload['agents'];
      final agents = raw is List ? raw.whereType<Map>().map(_map).toList() : <Map<String, dynamic>>[];
      if (mounted) setState(() => _agents = agents);
    } catch (error) {
      if (mounted) setState(() => _error = error.toString());
    } finally {
      if (mounted) setState(() => _loadingHealth = false);
    }
  }

  Future<void> _createOrchestration() async {
    final draft = await showDialog<_OrchestrationDraft>(
      context: context,
      builder: (_) => const _CreateOrchestrationDialog(),
    );
    if (draft == null || !mounted) return;
    setState(() { _creating = true; _error = null; });
    try {
      await widget.apiClient.createOrchestration(objective: draft.objective, steps: draft.steps);
      await _loadRuns();
    } catch (error) {
      if (mounted) setState(() => _error = error.toString());
    } finally {
      if (mounted) setState(() => _creating = false);
    }
  }

  Future<void> _action(String runId, String action) async {
    setState(() => _busyRuns.add(runId));
    try {
      if (action == 'confirm') {
        await widget.apiClient.confirmOrchestration(runId);
      } else if (action == 'retry') {
        await widget.apiClient.retryOrchestration(runId);
      } else if (action == 'cancel') {
        await widget.apiClient.cancelOrchestration(runId);
      } else {
        await widget.apiClient.executeOrchestration(runId);
      }
      await _loadRuns();
    } catch (error) {
      if (mounted) setState(() => _error = error.toString());
    } finally {
      if (mounted) setState(() => _busyRuns.remove(runId));
    }
  }

  Future<void> _showTimeline(String runId) async {
    try {
      final payload = await widget.apiClient.getOrchestrationTimeline(runId);
      final raw = payload['events'];
      final events = raw is List ? raw.whereType<Map>().map(_map).toList() : <Map<String, dynamic>>[];
      if (!mounted) return;
      await showDialog<void>(
        context: context,
        builder: (context) => AlertDialog(
          title: Text('Run timeline • ${_shortId(runId)}'),
          content: SizedBox(
            width: 620,
            child: events.isEmpty
                ? const Text('No timeline events yet.')
                : ListView.builder(
                    shrinkWrap: true,
                    itemCount: events.length,
                    itemBuilder: (_, index) {
                      final event = events[index];
                      return ListTile(
                        dense: true,
                        leading: const Icon(Icons.circle_outlined, size: 16),
                        title: Text((event['event_type'] ?? 'event').toString()),
                        subtitle: Text('status: ${event['run_status'] ?? 'unknown'} • step: ${event['step_id'] ?? '-'}'),
                      );
                    },
                  ),
          ),
          actions: [TextButton(onPressed: () => Navigator.pop(context), child: const Text('Close'))],
        ),
      );
    } catch (error) {
      if (mounted) setState(() => _error = error.toString());
    }
  }

  @override
  Widget build(BuildContext context) {
    final approvals = _runs.where((run) => run['status'] == 'awaiting_confirmation').toList();
    return ListView(
      padding: const EdgeInsets.fromLTRB(24, 22, 24, 32),
      children: [
        const EnterprisePageHeader(
          icon: Icons.smart_toy_outlined,
          title: 'Agent Center V2',
          subtitle: 'Orchestration graph, live timeline, approvals, retry/cancel/resume, health และ workspace context',
        ),
        const SizedBox(height: 20),
        EnterpriseSection(
          title: 'Workspace',
          subtitle: 'ขอบเขต context และ artifacts ของงาน',
          child: Row(children: [
            const Icon(Icons.workspaces_outline),
            const SizedBox(width: 12),
            DropdownButton<String>(
              key: const Key('workspace-selector'),
              value: _workspace,
              items: const [
                DropdownMenuItem(value: 'default', child: Text('Default workspace')),
                DropdownMenuItem(value: 'research', child: Text('Research workspace')),
                DropdownMenuItem(value: 'operations', child: Text('Operations workspace')),
              ],
              onChanged: (value) => setState(() => _workspace = value ?? 'default'),
            ),
            const Spacer(),
            Text('Active: $_workspace'),
          ]),
        ),
        const SizedBox(height: 20),
        EnterpriseSection(
          title: 'Approval inbox',
          subtitle: 'Write-capable actions ต้องยืนยันก่อน execute',
          child: approvals.isEmpty
              ? const ListTile(
                  leading: Icon(Icons.verified_outlined),
                  title: Text('No approvals waiting'),
                  subtitle: Text('งานที่ต้องยืนยันจะปรากฏที่นี่'),
                )
              : Column(children: approvals.map((run) {
                  final id = '${run['run_id'] ?? ''}';
                  return ListTile(
                    key: Key('approval-$id'),
                    leading: const Icon(Icons.approval_outlined),
                    title: Text('${run['objective'] ?? 'Approval required'}'),
                    trailing: FilledButton(
                      key: Key('confirm-$id'),
                      onPressed: _busyRuns.contains(id) ? null : () => _action(id, 'confirm'),
                      child: const Text('Approve'),
                    ),
                  );
                }).toList()),
        ),
        const SizedBox(height: 20),
        EnterpriseSection(
          title: 'Multi-Agent orchestration',
          subtitle: 'Dependency graph, status และ run controls',
          child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
            Row(children: [
              Expanded(child: Text(_loading ? 'กำลังโหลด orchestration...' : '${_runs.length} orchestration run(s)')),
              FilledButton.icon(
                key: const Key('create-orchestration-button'),
                onPressed: _creating ? null : _createOrchestration,
                icon: const Icon(Icons.add),
                label: const Text('Create orchestration'),
              ),
              IconButton(onPressed: _loading ? null : _loadRuns, icon: const Icon(Icons.refresh)),
            ]),
            if (_loading) const LinearProgressIndicator(),
            if (_error != null) ListTile(leading: const Icon(Icons.error_outline), title: const Text('Agent Center API warning'), subtitle: Text(_error!)),
            if (!_loading && _runs.isEmpty)
              const Card(child: ListTile(
                leading: Icon(Icons.hub_outlined),
                title: Text('No orchestration runs yet'),
                subtitle: Text('กด Create orchestration เพื่อสร้างแผนงาน Multi-Agent ใหม่จากหน้านี้'),
              )),
            ..._runs.map(_runCard),
          ]),
        ),
        const SizedBox(height: 20),
        EnterpriseSection(
          title: 'Agent health & capabilities',
          subtitle: 'Readiness ของ core agents และ V2 Completion Crew',
          child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
            Align(
              alignment: Alignment.centerRight,
              child: OutlinedButton.icon(
                key: const Key('load-agent-health'),
                onPressed: _loadingHealth ? null : _loadHealth,
                icon: const Icon(Icons.monitor_heart_outlined),
                label: const Text('Refresh health'),
              ),
            ),
            if (_loadingHealth) const LinearProgressIndicator(),
            if (_agents.isEmpty && !_loadingHealth)
              const ListTile(title: Text('Health data not loaded'), subtitle: Text('กด Refresh health เพื่ออ่าน Agent Registry จริง')),
            ..._agents.map((agent) {
              final health = agent['health'] is Map ? _map(agent['health'] as Map) : <String, dynamic>{};
              return ListTile(
                leading: Icon(health['ready'] == true ? Icons.check_circle_outline : Icons.error_outline),
                title: Text('${agent['name'] ?? agent['agent_id'] ?? 'Agent'}'),
                subtitle: Text('${agent['permission_profile'] ?? 'standard'}'),
                trailing: Chip(label: Text('${health['status'] ?? 'unknown'}')),
              );
            }),
          ]),
        ),
      ],
    );
  }

  Widget _runCard(Map<String, dynamic> run) {
    final id = '${run['run_id'] ?? ''}';
    final status = '${run['status'] ?? 'unknown'}';
    final steps = run['steps'] is List ? run['steps'] as List : const [];
    final busy = _busyRuns.contains(id);
    return Card(
      margin: const EdgeInsets.only(top: 10),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Row(children: [Expanded(child: Text('${run['objective'] ?? 'Untitled orchestration'}')), Chip(label: Text(status))]),
          Text('Run ${_shortId(id)}'),
          const SizedBox(height: 8),
          ...steps.whereType<Map>().map((raw) {
            final step = _map(raw);
            final deps = step['depends_on'] is List ? (step['depends_on'] as List).join(', ') : '';
            return ListTile(
              dense: true,
              leading: const Icon(Icons.account_tree_outlined),
              title: Text('${step['step_id'] ?? 'step'} → ${step['requested_agent'] ?? 'auto'}'),
              subtitle: Text(deps.isEmpty ? 'No dependency' : 'Depends on: $deps'),
              trailing: Chip(label: Text('${step['status'] ?? 'planned'}')),
            );
          }),
          Wrap(spacing: 8, runSpacing: 8, children: [
            OutlinedButton.icon(
              key: Key('execute-$id'),
              onPressed: busy ? null : () => _action(id, 'execute'),
              icon: const Icon(Icons.play_arrow),
              label: const Text('Execute'),
            ),
            OutlinedButton.icon(
              key: Key('timeline-$id'),
              onPressed: busy ? null : () => _showTimeline(id),
              icon: const Icon(Icons.timeline),
              label: const Text('Timeline'),
            ),
            if (status == 'failed') OutlinedButton(key: Key('retry-$id'), onPressed: busy ? null : () => _action(id, 'retry'), child: const Text('Retry')),
            if (status == 'interrupted' || status == 'blocked') OutlinedButton(key: Key('resume-$id'), onPressed: busy ? null : () => _action(id, 'resume'), child: const Text('Resume')),
            if (!{'completed', 'failed', 'cancelled'}.contains(status)) TextButton(key: Key('cancel-$id'), onPressed: busy ? null : () => _action(id, 'cancel'), child: const Text('Cancel')),
            if (status == 'awaiting_confirmation') FilledButton(key: Key('confirm-$id'), onPressed: busy ? null : () => _action(id, 'confirm'), child: const Text('Confirm')),
          ]),
        ]),
      ),
    );
  }

  static Map<String, dynamic> _map(Map<dynamic, dynamic> value) => value.map((key, value) => MapEntry(key.toString(), value));
  static String _shortId(String value) => value.length <= 8 ? value : value.substring(0, 8);
}

class _CreateOrchestrationDialog extends StatefulWidget {
  const _CreateOrchestrationDialog();
  @override
  State<_CreateOrchestrationDialog> createState() => _CreateOrchestrationDialogState();
}

class _CreateOrchestrationDialogState extends State<_CreateOrchestrationDialog> {
  final _objective = TextEditingController();
  final _firstStep = TextEditingController();
  final _secondStep = TextEditingController();
  String _firstAgent = 'research';
  String _secondAgent = 'document';

  static const _agentIds = [
    'research', 'developer', 'document', 'github', 'google_workspace', 'shift',
    'v2_workspace_engineer', 'v2_agent_center_engineer', 'v2_api_compat_engineer', 'v2_reliability_release_engineer',
  ];

  @override
  void dispose() {
    _objective.dispose(); _firstStep.dispose(); _secondStep.dispose(); super.dispose();
  }

  @override
  Widget build(BuildContext context) => AlertDialog(
    title: const Text('Create orchestration'),
    content: SizedBox(
      width: 560,
      child: Column(mainAxisSize: MainAxisSize.min, children: [
        TextField(key: const Key('orchestration-objective'), controller: _objective, decoration: const InputDecoration(labelText: 'Objective')),
        const SizedBox(height: 12),
        _step(_firstStep, const Key('orchestration-step-1'), _firstAgent, (v) => setState(() => _firstAgent = v ?? 'research')),
        const SizedBox(height: 12),
        _step(_secondStep, const Key('orchestration-step-2'), _secondAgent, (v) => setState(() => _secondAgent = v ?? 'document')),
      ]),
    ),
    actions: [
      TextButton(onPressed: () => Navigator.pop(context), child: const Text('Cancel')),
      FilledButton(key: const Key('submit-orchestration'), onPressed: _submit, child: const Text('Create')),
    ],
  );

  Widget _step(TextEditingController controller, Key key, String value, ValueChanged<String?> changed) => Row(children: [
    Expanded(child: TextField(key: key, controller: controller, decoration: const InputDecoration(labelText: 'Step objective'))),
    const SizedBox(width: 10),
    DropdownButton<String>(value: value, items: _agentIds.map((id) => DropdownMenuItem(value: id, child: Text(id))).toList(), onChanged: changed),
  ]);

  void _submit() {
    final objective = _objective.text.trim();
    final first = _firstStep.text.trim();
    final second = _secondStep.text.trim();
    if (objective.isEmpty || first.isEmpty || second.isEmpty) return;
    Navigator.pop(context, _OrchestrationDraft(objective, [
      {'step_id': 'step-1', 'objective': first, 'requested_agent': _firstAgent},
      {'step_id': 'step-2', 'objective': second, 'requested_agent': _secondAgent, 'depends_on': <String>['step-1']},
    ]));
  }
}

class _OrchestrationDraft {
  const _OrchestrationDraft(this.objective, this.steps);
  final String objective;
  final List<Map<String, Object?>> steps;
}
