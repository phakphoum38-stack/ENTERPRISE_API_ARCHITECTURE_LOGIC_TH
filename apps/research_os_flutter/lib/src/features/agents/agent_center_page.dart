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
  static const _agents = <_AgentView>[
    _AgentView('Research Agent', Icons.psychology_outlined,
        'Research • Synthesis • Memory • Knowledge',
        'memory.read • knowledge.read/write'),
    _AgentView('Document Agent', Icons.description_outlined,
        'PDF • Word • Excel • PowerPoint • Markdown',
        'documents.read • knowledge.write'),
    _AgentView('GitHub Agent', Icons.account_tree_outlined,
        'Repository • Commit • PR • Issues • Workflows', 'github.read'),
    _AgentView('Google Workspace Agent', Icons.apps_outlined,
        'Drive • Docs • Sheets • Calendar • Gmail • Workspace',
        'google.read • write with confirmation'),
    _AgentView('Shift Agent', Icons.calendar_view_week_outlined,
        'Roster • Replacement • Leave • Conflict • Calendar Sync',
        'sheets.read • calendar write with confirmation'),
  ];

  bool _loading = true;
  bool _creating = false;
  String? _error;
  List<Map<String, dynamic>> _runs = const <Map<String, dynamic>>[];
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
          ? rawRuns.whereType<Map>().map((item) {
              return item.map((key, value) => MapEntry(key.toString(), value));
            }).toList()
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

  Future<void> _runAction(String runId, {required bool confirm}) async {
    setState(() => _busyRuns.add(runId));
    try {
      if (confirm) {
        await widget.apiClient.confirmOrchestration(runId);
      } else {
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

  @override
  Widget build(BuildContext context) {
    return ListView(
      padding: const EdgeInsets.fromLTRB(24, 22, 24, 32),
      children: <Widget>[
        const EnterprisePageHeader(
          icon: Icons.smart_toy_outlined,
          title: 'Agent Center',
          subtitle:
              'จัดการผู้ช่วยเฉพาะทาง, routing, orchestration, task queue, events และสิทธิ์การทำงานจากศูนย์กลางเดียว',
        ),
        const SizedBox(height: 24),
        const EnterpriseSection(
          title: 'Runtime overview',
          subtitle: 'สถานะของ Agent Runtime 1.0',
          child: Wrap(
            spacing: 12,
            runSpacing: 12,
            children: <Widget>[
              SizedBox(
                  width: 230,
                  child: EnterpriseStatusTile(
                      icon: Icons.route_outlined,
                      title: 'Router',
                      value: 'Capability based',
                      caption: 'Research fallback')),
              SizedBox(
                  width: 230,
                  child: EnterpriseStatusTile(
                      icon: Icons.queue_outlined,
                      title: 'Task Queue',
                      value: 'Active',
                      caption: 'Local runtime')),
              SizedBox(
                  width: 230,
                  child: EnterpriseStatusTile(
                      icon: Icons.swap_horiz,
                      title: 'Event Bus',
                      value: 'Active',
                      caption: 'Runtime events')),
              SizedBox(
                  width: 230,
                  child: EnterpriseStatusTile(
                      icon: Icons.memory_outlined,
                      title: 'Shared Context',
                      value: 'Local-first',
                      caption: 'ResearchOSData/agents')),
            ],
          ),
        ),
        const SizedBox(height: 28),
        EnterpriseSection(
          title: 'Multi-Agent orchestration',
          subtitle:
              'สร้างและติดตาม dependency chain, execution state และ confirmation gate จาก runtime จริง',
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: <Widget>[
              Row(
                children: <Widget>[
                  Expanded(
                    child: Text(
                      _loading
                          ? 'กำลังโหลด orchestration...'
                          : '${_runs.length} orchestration run(s)',
                      style: Theme.of(context).textTheme.titleSmall,
                    ),
                  ),
                  FilledButton.icon(
                    key: const Key('create-orchestration-button'),
                    onPressed: _creating ? null : _createOrchestration,
                    icon: _creating
                        ? const SizedBox(
                            width: 16,
                            height: 16,
                            child: CircularProgressIndicator(strokeWidth: 2),
                          )
                        : const Icon(Icons.add),
                    label: const Text('Create orchestration'),
                  ),
                  const SizedBox(width: 8),
                  IconButton(
                    tooltip: 'Refresh orchestrations',
                    onPressed: _loading ? null : _loadRuns,
                    icon: const Icon(Icons.refresh),
                  ),
                ],
              ),
              if (_loading) ...<Widget>[
                const SizedBox(height: 10),
                const LinearProgressIndicator(),
              ],
              if (_error != null) ...<Widget>[
                const SizedBox(height: 10),
                Card(
                  child: ListTile(
                    leading: const Icon(Icons.error_outline),
                    title: const Text('Orchestrator API unavailable'),
                    subtitle: Text(_error!),
                    trailing: TextButton(
                      onPressed: _loadRuns,
                      child: const Text('Retry'),
                    ),
                  ),
                ),
              ],
              if (!_loading && _error == null && _runs.isEmpty) ...<Widget>[
                const SizedBox(height: 10),
                const Card(
                  child: ListTile(
                    leading: Icon(Icons.hub_outlined),
                    title: Text('No orchestration runs yet'),
                    subtitle: Text(
                        'กด Create orchestration เพื่อสร้างแผนงาน Multi-Agent ใหม่จากหน้านี้'),
                  ),
                ),
              ],
              ..._runs.map(_buildRunCard),
            ],
          ),
        ),
        const SizedBox(height: 28),
        EnterpriseSection(
          title: 'Registered agents',
          subtitle:
              'Agent ทุกตัวใช้ permission model และ confirmation policy ชุดเดียวกัน',
          child: LayoutBuilder(
            builder: (context, constraints) {
              final columns = constraints.maxWidth >= 1050
                  ? 3
                  : constraints.maxWidth >= 650
                      ? 2
                      : 1;
              final width =
                  (constraints.maxWidth - (columns - 1) * 12) / columns;
              return Wrap(
                spacing: 12,
                runSpacing: 12,
                children: _agents
                    .map((agent) => SizedBox(
                          width: width,
                          child: Card(
                            child: Padding(
                              padding: const EdgeInsets.all(18),
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: <Widget>[
                                  Row(children: <Widget>[
                                    Container(
                                      width: 40,
                                      height: 40,
                                      alignment: Alignment.center,
                                      decoration: BoxDecoration(
                                        color: Theme.of(context)
                                            .colorScheme
                                            .secondaryContainer,
                                        borderRadius: BorderRadius.circular(12),
                                      ),
                                      child: Icon(agent.icon),
                                    ),
                                    const SizedBox(width: 12),
                                    Expanded(
                                        child: Text(agent.name,
                                            style: Theme.of(context)
                                                .textTheme
                                                .titleMedium
                                                ?.copyWith(
                                                    fontWeight:
                                                        FontWeight.w700))),
                                    const Chip(label: Text('Ready')),
                                  ]),
                                  const SizedBox(height: 14),
                                  Text(agent.capabilities),
                                  const SizedBox(height: 12),
                                  const Divider(height: 1),
                                  const SizedBox(height: 10),
                                  Text('Permissions',
                                      style: Theme.of(context)
                                          .textTheme
                                          .labelMedium),
                                  const SizedBox(height: 3),
                                  Text(agent.permissions,
                                      style: Theme.of(context)
                                          .textTheme
                                          .bodySmall),
                                ],
                              ),
                            ),
                          ),
                        ))
                    .toList(),
              );
            },
          ),
        ),
        const SizedBox(height: 28),
        const EnterpriseSection(
          title: 'Governance',
          subtitle: 'กติกากลางสำหรับ Agent ทุกตัว',
          child: Column(
            children: <Widget>[
              Card(
                  child: ListTile(
                      leading: Icon(Icons.verified_user_outlined),
                      title: Text('Write actions require confirmation'),
                      subtitle: Text(
                          'งานที่แก้ Calendar, Google Workspace หรือข้อมูลภายนอกจะหยุดรอการยืนยันก่อน Execute'))),
              SizedBox(height: 8),
              Card(
                  child: ListTile(
                      leading: Icon(Icons.storage_outlined),
                      title: Text('Shared Context แบบ Local-first'),
                      subtitle: Text(
                          'Context ของ Agent อยู่ใต้ ResearchOSData/agents และไม่บังคับพึ่ง Cloud'))),
              SizedBox(height: 8),
              Card(
                  child: ListTile(
                      leading: Icon(Icons.account_tree_outlined),
                      title: Text('Dependency-aware orchestration'),
                      subtitle: Text(
                          'Agent ถัดไปจะทำงานเมื่อ dependency สำเร็จ และรับ dependency results เป็น context โดยอัตโนมัติ'))),
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

    return Padding(
      padding: const EdgeInsets.only(top: 10),
      child: Card(
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
              const SizedBox(height: 4),
              Text('Run ${_shortId(runId)}',
                  style: Theme.of(context).textTheme.bodySmall),
              const SizedBox(height: 12),
              ...steps.whereType<Map>().map((step) {
                final stepId = (step['step_id'] ?? 'step').toString();
                final agent = (step['requested_agent'] ?? 'auto').toString();
                final stepStatus = (step['status'] ?? 'planned').toString();
                final dependsOn = step['depends_on'] is List
                    ? (step['depends_on'] as List).join(', ')
                    : '';
                return ListTile(
                  dense: true,
                  contentPadding: EdgeInsets.zero,
                  leading: const Icon(Icons.subdirectory_arrow_right),
                  title: Text('$stepId • $agent'),
                  subtitle: Text(dependsOn.isEmpty
                      ? 'No dependency'
                      : 'Depends on: $dependsOn'),
                  trailing: Chip(label: Text(stepStatus)),
                );
              }),
              const SizedBox(height: 8),
              Wrap(
                spacing: 8,
                runSpacing: 8,
                children: <Widget>[
                  OutlinedButton.icon(
                    key: Key('execute-$runId'),
                    onPressed: busy || runId.isEmpty
                        ? null
                        : () => _runAction(runId, confirm: false),
                    icon: const Icon(Icons.play_arrow),
                    label: const Text('Execute'),
                  ),
                  if (status == 'awaiting_confirmation')
                    FilledButton.icon(
                      key: Key('confirm-$runId'),
                      onPressed: busy || runId.isEmpty
                          ? null
                          : () => _runAction(runId, confirm: true),
                      icon: const Icon(Icons.verified_outlined),
                      label: const Text('Confirm'),
                    ),
                  if (busy)
                    const Padding(
                      padding: EdgeInsets.all(8),
                      child: SizedBox(
                        width: 18,
                        height: 18,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      ),
                    ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }

  static String _shortId(String value) {
    if (value.length <= 8) return value;
    return value.substring(0, 8);
  }
}

class _CreateOrchestrationDialog extends StatefulWidget {
  const _CreateOrchestrationDialog();

  @override
  State<_CreateOrchestrationDialog> createState() =>
      _CreateOrchestrationDialogState();
}

class _CreateOrchestrationDialogState
    extends State<_CreateOrchestrationDialog> {
  final _objective = TextEditingController();
  final _firstStep = TextEditingController();
  final _secondStep = TextEditingController();
  String _firstAgent = 'research';
  String _secondAgent = 'document';

  static const _agentIds = <String>[
    'research',
    'document',
    'github',
    'google_workspace',
    'shift',
  ];

  @override
  void dispose() {
    _objective.dispose();
    _firstStep.dispose();
    _secondStep.dispose();
    super.dispose();
  }

  void _submit() {
    final objective = _objective.text.trim();
    final first = _firstStep.text.trim();
    final second = _secondStep.text.trim();
    if (objective.isEmpty || first.isEmpty) return;

    final steps = <Map<String, Object?>>[
      <String, Object?>{
        'step_id': 'step-1',
        'objective': first,
        'requested_agent': _firstAgent,
      },
      if (second.isNotEmpty)
        <String, Object?>{
          'step_id': 'step-2',
          'objective': second,
          'requested_agent': _secondAgent,
          'depends_on': <String>['step-1'],
        },
    ];
    Navigator.of(context).pop(_OrchestrationDraft(objective, steps));
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
                decoration: const InputDecoration(
                  labelText: 'Overall objective',
                  hintText: 'เช่น วิเคราะห์เอกสารและสรุปเป็นองค์ความรู้',
                ),
              ),
              const SizedBox(height: 14),
              TextField(
                key: const Key('orchestration-step-1'),
                controller: _firstStep,
                decoration: const InputDecoration(labelText: 'Step 1 objective'),
              ),
              const SizedBox(height: 8),
              DropdownButtonFormField<String>(
                key: const Key('orchestration-agent-1'),
                initialValue: _firstAgent,
                decoration: const InputDecoration(labelText: 'Step 1 agent'),
                items: _agentIds
                    .map((value) => DropdownMenuItem(
                          value: value,
                          child: Text(value),
                        ))
                    .toList(),
                onChanged: (value) {
                  if (value != null) setState(() => _firstAgent = value);
                },
              ),
              const SizedBox(height: 14),
              TextField(
                key: const Key('orchestration-step-2'),
                controller: _secondStep,
                decoration: const InputDecoration(
                  labelText: 'Step 2 objective (optional)',
                  helperText: 'Step 2 จะขึ้นกับผลจาก Step 1 อัตโนมัติ',
                ),
              ),
              const SizedBox(height: 8),
              DropdownButtonFormField<String>(
                key: const Key('orchestration-agent-2'),
                initialValue: _secondAgent,
                decoration: const InputDecoration(labelText: 'Step 2 agent'),
                items: _agentIds
                    .map((value) => DropdownMenuItem(
                          value: value,
                          child: Text(value),
                        ))
                    .toList(),
                onChanged: (value) {
                  if (value != null) setState(() => _secondAgent = value);
                },
              ),
            ],
          ),
        ),
      ),
      actions: <Widget>[
        TextButton(
          onPressed: () => Navigator.of(context).pop(),
          child: const Text('Cancel'),
        ),
        FilledButton(
          key: const Key('submit-orchestration'),
          onPressed: _submit,
          child: const Text('Create'),
        ),
      ],
    );
  }
}

class _OrchestrationDraft {
  const _OrchestrationDraft(this.objective, this.steps);

  final String objective;
  final List<Map<String, Object?>> steps;
}

class _AgentView {
  const _AgentView(this.name, this.icon, this.capabilities, this.permissions);
  final String name;
  final IconData icon;
  final String capabilities;
  final String permissions;
}
