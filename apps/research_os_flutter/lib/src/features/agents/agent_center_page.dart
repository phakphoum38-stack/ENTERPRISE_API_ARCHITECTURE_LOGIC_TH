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
  List<Map<String, dynamic>> _runs = const <Map<String, dynamic>>[];
  List<Map<String, dynamic>> _agents = const <Map<String, dynamic>>[];
  final Set<String> _busyRuns = <String>{};

  @override
  void initState() {
    super.initState();
    _loadRuns();
  }

  Future<void> _loadRuns() async {
    if (mounted) {
      setState(() {
        _loading = true;
        _error = null;
      });
    }
    try {
      final payload = await widget.apiClient.getOrchestrations();
      final rawRuns = payload['runs'];
      final runs = rawRuns is List
          ? rawRuns.whereType<Map>().map(_stringKeyed).toList()
          : <Map<String, dynamic>>[];
      if (!mounted) return;
      setState(() {
        _runs = runs;
        _loading = false;
      });
    } catch (error) {
      if (!mounted) return;
      setState(() {
        _loading = false;
        _error = error.toString();
      });
    }
  }

  Future<void> _loadHealth() async {
    setState(() => _loadingHealth = true);
    try {
      final payload = await widget.apiClient.getAgents();
      final raw = payload['agents'];
      final agents = raw is List
          ? raw.whereType<Map>().map(_stringKeyed).toList()
          : <Map<String, dynamic>>[];
      if (!mounted) return;
      setState(() => _agents = agents);
    } catch (error) {
      if (!mounted) return;
      setState(() => _error = error.toString());
    } finally {
      if (mounted) setState(() => _loadingHealth = false);
    }
  }

  Future<void> _createOrchestration() async {
    final draft = await showDialog<_OrchestrationDraft>(
      context: context,
      builder: (context) => const _CreateOrchestrationDialog(),
    );
    if (draft == null || !mounted) return;
    setState(() {
      _creating = true;
      _error = null;
    });
    try {
      await widget.apiClient.createOrchestration(
        objective: draft.objective,
        steps: draft.steps,
      );
      await _loadRuns();
    } catch (error) {
      if (!mounted) return;
      setState(() => _error = error.toString());
    } finally {
      if (mounted) setState(() => _creating = false);
    }
  }

  Future<void> _action(String runId, String action) async {
    setState(() => _busyRuns.add(runId));
    try {
      switch (action) {
        case 'confirm':
          await widget.apiClient.confirmOrchestration(runId);
        case 'retry':
          await widget.apiClient.retryOrchestration(runId);
        case 'cancel':
          await widget.apiClient.cancelOrchestration(runId);
        case 'execute':
        case 'resume':
          await widget.apiClient.executeOrchestration(runId);
      }
      await _loadRuns();
    } catch (error) {
      if (!mounted) return;
      setState(() => _error = error.toString());
    } finally {
      if (mounted) setState(() => _busyRuns.remove(runId));
    }
  }

  Future<void> _showTimeline(String runId) async {
    try {
      final payload = await widget.apiClient.getOrchestrationTimeline(runId);
      final raw = payload['events'];
      final events = raw is List
          ? raw.whereType<Map>().map(_stringKeyed).toList()
          : <Map<String, dynamic>>[];
      if (!mounted) return;
      await showDialog<void>(
        context: context,
        builder: (context) => AlertDialog(
          title: Text('Run timeline • ${_shortId(runId)}'),
          content: SizedBox(
            width: 620,
            child: events.isEmpty
                ? const Text('No timeline events yet.')
                : ListView.separated(
                    shrinkWrap: true,
                    itemCount: events.length,
                    separatorBuilder: (_, __) => const Divider(height: 1),
                    itemBuilder: (context, index) {
                      final event = events[index];
                      return ListTile(
                        dense: true,
                        leading: const Icon(Icons.circle_outlined, size: 16),
                        title: Text((event['event_type'] ?? 'event').toString()),
                        subtitle: Text(
                          'status: ${(event['run_status'] ?? 'unknown')} • step: ${(event['step_id'] ?? '-')}',
                        ),
                      );
                    },
                  ),
          ),
          actions: <Widget>[
            TextButton(onPressed: () => Navigator.pop(context), child: const Text('Close')),
          ],
        ),
      );
    } catch (error) {
      if (!mounted) return;
      setState(() => _error = error.toString());
    }
  }

  @override
  Widget build(BuildContext context) {
    final approvals = _runs
        .where((run) => run['status']?.toString() == 'awaiting_confirmation')
        .toList();

    return ListView(
      padding: const EdgeInsets.fromLTRB(24, 22, 24, 32),
      children: <Widget>[
        const EnterprisePageHeader(
          icon: Icons.smart_toy_outlined,
          title: 'Agent Center V2',
          subtitle:
              'Orchestration graph, live timeline, approvals, health, retry/cancel/resume และ workspace context ในศูนย์กลางเดียว',
        ),
        const SizedBox(height: 20),
        EnterpriseSection(
          title: 'Workspace',
          subtitle: 'ขอบเขต context และ artifact สำหรับ orchestration ใหม่',
          child: Row(
            children: <Widget>[
              const Icon(Icons.workspaces_outline),
              const SizedBox(width: 12),
              DropdownButton<String>(
                key: const Key('workspace-selector'),
                value: _workspace,
                items: const <DropdownMenuItem<String>>[
                  DropdownMenuItem(value: 'default', child: Text('Default workspace')),
                  DropdownMenuItem(value: 'research', child: Text('Research workspace')),
                  DropdownMenuItem(value: 'operations', child: Text('Operations workspace')),
                ],
                onChanged: (value) => setState(() => _workspace = value ?? 'default'),
              ),
              const Spacer(),
              Text('Active: $_workspace'),
            ],
          ),
        ),
        const SizedBox(height: 20),
        EnterpriseSection(
          title: 'Approval inbox',
          subtitle: 'งานเขียนข้อมูลจะหยุดรอการยืนยันที่นี่',
          child: approvals.isEmpty
              ? const ListTile(
                  leading: Icon(Icons.verified_outlined),
                  title: Text('No approvals waiting'),
                  subtitle: Text('Write-capable actions will appear here before execution.'),
                )
              : Column(
                  children: approvals.map((run) {
                    final id = (run['run_id'] ?? '').toString();
                    return ListTile(
                      key: Key('approval-$id'),
                      leading: const Icon(Icons.approval_outlined),
                      title: Text((run['objective'] ?? 'Approval required').toString()),
                      subtitle: Text('Run ${_shortId(id)}'),
                      trailing: FilledButton(
                        key: Key('confirm-$id'),
                        onPressed: _busyRuns.contains(id) ? null : () => _action(id, 'confirm'),
                        child: const Text('Approve'),
                      ),
                    );
                  }).toList(),
                ),
        ),
        const SizedBox(height: 20),
        EnterpriseSection(
          title: 'Multi-Agent orchestration',
          subtitle: 'Dependency graph, execution state และ run controls',
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: <Widget>[
              Row(
                children: <Widget>[
                  Expanded(
                    child: Text(_loading
                        ? 'กำลังโหลด orchestration...'
                        : '${_runs.length} orchestration run(s)'),
                  ),
                  FilledButton.icon(
                    key: const Key('create-orchestration-button'),
                    onPressed: _creating ? null : _createOrchestration,
                    icon: const Icon(Icons.add),
                    label: const Text('Create orchestration'),
                  ),
                  IconButton(
                    tooltip: 'Refresh',
                    onPressed: _loading ? null : _loadRuns,
                    icon: const Icon(Icons.refresh),
                  ),
                ],
              ),
              if (_loading) const LinearProgressIndicator(),
              if (_error != null)
                ListTile(
                  leading: const Icon(Icons.error_outline),
                  title: const Text('Agent Center API warning'),
                  subtitle: Text(_error!),
                ),
              if (!_loading && _runs.isEmpty)
                const Card(
                  child: ListTile(
                    leading: Icon(Icons.hub_outlined),
                    title: Text('No orchestration runs yet'),
                    subtitle: Text('กด Create orchestration เพื่อสร้างแผนงาน Multi-Agent ใหม่จากหน้านี้'),
                  ),
                ),
              ..._runs.map(_buildRunCard),
            ],
          ),
        ),
        const SizedBox(height: 20),
        EnterpriseSection(
          title: 'Agent health & capabilities',
          subtitle: 'Readiness ของ core agents และ V2 Completion Crew',
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: <Widget>[
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
                const ListTile(
                  leading: Icon(Icons.health_and_safety_outlined),
                  title: Text('Health data not loaded'),
                  subtitle: Text('กด Refresh health เพื่ออ่าน readiness จาก Agent Registry จริง'),
                ),
              ..._agents.map((agent) {
                final health = agent['health'] is Map
                    ? _stringKeyed(agent['health'] as Map)
                    : <String, dynamic>{};
                final ready = health['ready'] == true;
                return ListTile(
                  leading: Icon(ready ? Icons.check_circle_outline : Icons.error_outline),
                  title: Text((agent['name'] ?? agent['agent_id'] ?? 'Agent').toString()),
                  subtitle: Text(
                    '${(agent['capabilities'] is List ? (agent['capabilities'] as List).join(' • ') : '')}\n${(agent['permission_profile'] ?? 'standard')}',
                  ),
                  isThreeLine: true,
                  trailing: Chip(label: Text((health['status'] ?? 'unknown').toString())),
                );
              }),
            ],
          ),
        ),
      ],
    );
  }

  Widget _buildRunCard(Map<String, dynamic> run) {
    final runId = (run['run_id'] ?? '').toString();
    final status = (run['status'] ?? 'unknown').toString();
    final objective = (run['objective'] ?? 'Untitled orchestration').toString();
    final steps = run['steps'] is List ? run['steps'] as List : const <dynamic>[];
    final busy = _busyRuns.contains(runId);

    return Card(
      margin: const EdgeInsets.only(top: 10),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: <Widget>[
            Row(
              children: <Widget>[
                Expanded(
                  child: Text(objective,
                      style: Theme.of(context)
                          .textTheme
                          .titleMedium
                          ?.copyWith(fontWeight: FontWeight.w700)),
                ),
                Chip(label: Text(status)),
              ],
            ),
            Text('Run ${_shortId(runId)}'),
            const SizedBox(height: 10),
            ...steps.whereType<Map>().map((raw) {
              final step = _stringKeyed(raw);
              final stepId = (step['step_id'] ?? 'step').toString();
              final agent = (step['requested_agent'] ?? 'auto').toString();
              final stepStatus = (step['status'] ?? 'planned').toString();
              final depends = step['depends_on'] is List
                  ? (step['depends_on'] as List).join(', ')
                  : '';
              return Row(
                children: <Widget>[
                  const Icon(Icons.account_tree_outlined, size: 18),
                  const SizedBox(width: 8),
                  Expanded(child: Text('$stepId → $agent${depends.isEmpty ? '' : ' • depends: $depends'}')),
                  Chip(label: Text(stepStatus)),
                ],
              );
            }),
            const SizedBox(height: 10),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: <Widget>[
                OutlinedButton.icon(
                  key: Key('execute-$runId'),
                  onPressed: busy || runId.isEmpty ? null : () => _action(runId, 'execute'),
                  icon: const Icon(Icons.play_arrow),
                  label: const Text('Execute'),
                ),
                OutlinedButton.icon(
                  key: Key('timeline-$runId'),
                  onPressed: busy || runId.isEmpty ? null : () => _showTimeline(runId),
                  icon: const Icon(Icons.timeline),
                  label: const Text('Timeline'),
                ),
                if (status == 'failed')
                  OutlinedButton.icon(
                    key: Key('retry-$runId'),
                    onPressed: busy ? null : () => _action(runId, 'retry'),
                    icon: const Icon(Icons.replay),
                    label: const Text('Retry'),
                  ),
                if (status == 'interrupted' || status == 'blocked')
                  OutlinedButton.icon(
                    key: Key('resume-$runId'),
                    onPressed: busy ? null : () => _action(runId, 'resume'),
                    icon: const Icon(Icons.resume),
                    label: const Text('Resume'),
                  ),
                if (!{'completed', 'failed', 'cancelled'}.contains(status))
                  TextButton.icon(
                    key: Key('cancel-$runId'),
                    onPressed: busy ? null : () => _action(runId, 'cancel'),
                    icon: const Icon(Icons.cancel_outlined),
                    label: const Text('Cancel'),
                  ),
                if (status == 'awaiting_confirmation')
                  FilledButton.icon(
                    key: Key('confirm-$runId'),
                    onPressed: busy ? null : () => _action(runId, 'confirm'),
                    icon: const Icon(Icons.verified_outlined),
                    label: const Text('Confirm'),
                  ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  static Map<String, dynamic> _stringKeyed(Map<dynamic, dynamic> value) =>
      value.map((key, value) => MapEntry(key.toString(), value));

  static String _shortId(String value) =>
      value.length <= 8 ? value : value.substring(0, 8);
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

  static const _agentIds = <String>[
    'research',
    'developer',
    'document',
    'github',
    'google_workspace',
    'shift',
    'v2_workspace_engineer',
    'v2_agent_center_engineer',
    'v2_api_compat_engineer',
    'v2_reliability_release_engineer',
  ];

  @override
  void dispose() {
    _objective.dispose();
    _firstStep.dispose();
    _secondStep.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: const Text('Create orchestration'),
      content: SizedBox(
        width: 560,
        child: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: <Widget>[
              TextField(
                key: const Key('orchestration-objective'),
                controller: _objective,
                decoration: const InputDecoration(labelText: 'Objective'),
              ),
              const SizedBox(height: 12),
              _stepEditor(
                controller: _firstStep,
                key: const Key('orchestration-step-1'),
                value: _firstAgent,
                onAgentChanged: (value) => setState(() => _firstAgent = value ?? 'research'),
              ),
              const SizedBox(height: 12),
              _stepEditor(
                controller: _secondStep,
                key: const Key('orchestration-step-2'),
                value: _secondAgent,
                onAgentChanged: (value) => setState(() => _secondAgent = value ?? 'document'),
              ),
            ],
          ),
        ),
      ),
      actions: <Widget>[
        TextButton(onPressed: () => Navigator.pop(context), child: const Text('Cancel')),
        FilledButton(
          key: const Key('submit-orchestration'),
          onPressed: _submit,
          child: const Text('Create'),
        ),
      ],
    );
  }

  Widget _stepEditor({
    required TextEditingController controller,
    required Key key,
    required String value,
    required ValueChanged<String?> onAgentChanged,
  }) {
    return Row(
      children: <Widget>[
        Expanded(
          child: TextField(
            key: key,
            controller: controller,
            decoration: const InputDecoration(labelText: 'Step objective'),
          ),
        ),
        const SizedBox(width: 10),
        DropdownButton<String>(
          value: value,
          items: _agentIds
              .map((id) => DropdownMenuItem<String>(value: id, child: Text(id)))
              .toList(),
          onChanged: onAgentChanged,
        ),
      ],
    );
  }

  void _submit() {
    final objective = _objective.text.trim();
    final first = _firstStep.text.trim();
    final second = _secondStep.text.trim();
    if (objective.isEmpty || first.isEmpty || second.isEmpty) return;
    Navigator.pop(
      context,
      _OrchestrationDraft(
        objective,
        <Map<String, Object?>>[
          <String, Object?>{
            'step_id': 'step-1',
            'objective': first,
            'requested_agent': _firstAgent,
          },
          <String, Object?>{
            'step_id': 'step-2',
            'objective': second,
            'requested_agent': _secondAgent,
            'depends_on': <String>['step-1'],
          },
        ],
      ),
    );
  }
}

class _OrchestrationDraft {
  const _OrchestrationDraft(this.objective, this.steps);

  final String objective;
  final List<Map<String, Object?>> steps;
}
