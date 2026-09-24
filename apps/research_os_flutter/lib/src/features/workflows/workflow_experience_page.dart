import 'package:flutter/material.dart';

import '../../api/research_os_api_client.dart';
import '../../ui/enterprise_components.dart';

class WorkflowExperiencePage extends StatefulWidget {
  const WorkflowExperiencePage({required this.apiClient, super.key});
  final ResearchOSApiClient apiClient;

  @override
  State<WorkflowExperiencePage> createState() => _WorkflowExperiencePageState();
}

class _WorkflowExperiencePageState extends State<WorkflowExperiencePage> {
  bool _loading = true;
  bool _loadingTimeline = false;
  String? _error;
  List<Map<String, dynamic>> _runs = const [];
  Map<String, dynamic>? _selectedRun;
  List<Map<String, dynamic>> _timeline = const [];

  @override
  void initState() {
    super.initState();
    _loadRuns();
  }

  Future<void> _loadRuns() async {
    if (mounted) setState(() { _loading = true; _error = null; });
    try {
      final payload = await widget.apiClient.getOrchestrations(limit: 100);
      final raw = payload['runs'];
      final runs = raw is List ? raw.whereType<Map>().map(_map).toList() : <Map<String, dynamic>>[];
      if (!mounted) return;
      setState(() {
        _runs = runs;
        _loading = false;
        if (_selectedRun != null) {
          final id = _selectedRun!['run_id']?.toString() ?? '';
          _selectedRun = runs.where((run) => (run['run_id']?.toString() ?? '') == id).firstOrNull;
        }
      });
    } catch (error) {
      if (mounted) setState(() { _loading = false; _error = error.toString(); });
    }
  }

  Future<void> _selectRun(Map<String, dynamic> run) async {
    final id = run['run_id']?.toString() ?? '';
    if (id.isEmpty) return;
    setState(() { _selectedRun = run; _loadingTimeline = true; _timeline = const []; });
    try {
      final payload = await widget.apiClient.getOrchestrationTimeline(id);
      final raw = payload['events'];
      final events = raw is List ? raw.whereType<Map>().map(_map).take(256).toList() : <Map<String, dynamic>>[];
      if (mounted) setState(() => _timeline = events);
    } catch (error) {
      if (mounted) setState(() => _error = error.toString());
    } finally {
      if (mounted) setState(() => _loadingTimeline = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final selected = _selectedRun;
    final selectedSteps = selected?['steps'] is List
        ? (selected!['steps'] as List).whereType<Map>().map(_map).toList()
        : const <Map<String, dynamic>>[];
    return ListView(
      padding: const EdgeInsets.fromLTRB(24, 22, 24, 32),
      children: [
        const EnterprisePageHeader(
          icon: Icons.account_tree_outlined,
          title: 'Workflow Experience',
          subtitle: 'Canonical orchestration workspace: lifecycle, runs, steps, timeline and recovery state',
        ),
        const SizedBox(height: 18),
        EnterpriseSection(
          title: 'Workflow lifecycle',
          subtitle: 'Observed from the existing orchestration API; this surface does not become an execution authority.',
          child: Wrap(
            spacing: 8,
            runSpacing: 8,
            children: const [
              _LifecycleChip('INTENT'), _LifecycleChip('VALIDATE'), _LifecycleChip('PREPARE'),
              _LifecycleChip('AUTHORIZE'), _LifecycleChip('EXECUTE'), _LifecycleChip('OBSERVE'),
              _LifecycleChip('EVIDENCE'), _LifecycleChip('COMPLETE'), _LifecycleChip('RECOVER'),
            ],
          ),
        ),
        const SizedBox(height: 18),
        EnterpriseSection(
          title: 'Run workspace',
          subtitle: 'Existing Workflow Engine runs are observed through /v1/agents/orchestrations.',
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Row(
                children: [
                  Expanded(child: Text(_loading ? 'Loading workflow runs...' : _runs.length.toString() + ' run(s) observed', key: const Key('workflow-run-count'))),
                  IconButton(
                    key: const Key('refresh-workflows'),
                    tooltip: 'Refresh workflow runs',
                    onPressed: _loading ? null : _loadRuns,
                    icon: const Icon(Icons.refresh),
                  ),
                ],
              ),
              if (_loading) const LinearProgressIndicator(),
              if (_error != null)
                ListTile(
                  key: const Key('workflow-error'),
                  leading: const Icon(Icons.error_outline),
                  title: const Text('Workflow API warning'),
                  subtitle: Text(_error!),
                ),
              if (!_loading && _runs.isEmpty)
                const ListTile(
                  key: Key('workflow-empty'),
                  leading: Icon(Icons.inbox_outlined),
                  title: Text('No workflow runs observed'),
                  subtitle: Text('UNKNOWN remains UNKNOWN; this page does not synthesize runs.'),
                ),
              ..._runs.map(_runTile),
            ],
          ),
        ),
        const SizedBox(height: 18),
        EnterpriseSection(
          title: 'Selected run',
          subtitle: selected == null ? 'Select a run to inspect its existing timeline.' : 'Read-only observation of ' + (selected['run_id']?.toString() ?? '') + '.',
          child: selected == null
              ? const ListTile(
                  key: Key('workflow-no-selection'),
                  leading: Icon(Icons.touch_app_outlined),
                  title: Text('No run selected'),
                )
              : Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    ListTile(
                      key: const Key('workflow-selected-run'),
                      leading: const Icon(Icons.route_outlined),
                      title: Text(selected['objective']?.toString() ?? 'Untitled workflow'),
                      subtitle: Text('Run ' + (selected['run_id']?.toString() ?? '-') + ' • status ' + (selected['status']?.toString() ?? 'UNKNOWN')),
                    ),
                    if (selectedSteps.isNotEmpty) ...[
                      const Divider(),
                      const Padding(
                        padding: EdgeInsets.only(bottom: 8),
                        child: Text('Steps', style: TextStyle(fontWeight: FontWeight.w800)),
                      ),
                      ...selectedSteps.map((step) => ListTile(
                            dense: true,
                            leading: const Icon(Icons.subdirectory_arrow_right),
                            title: Text(step['step_id']?.toString() ?? 'step'),
                            subtitle: Text(step['objective']?.toString() ?? ''),
                            trailing: Chip(label: Text(step['status']?.toString() ?? 'UNKNOWN')),
                          )),
                    ],
                    const Divider(),
                    if (_loadingTimeline) const LinearProgressIndicator(),
                    if (!_loadingTimeline && _timeline.isEmpty)
                      const ListTile(
                        key: Key('workflow-timeline-empty'),
                        leading: Icon(Icons.timeline_outlined),
                        title: Text('No timeline events observed'),
                      ),
                    ..._timeline.map((event) => ListTile(
                          dense: true,
                          leading: const Icon(Icons.circle_outlined, size: 16),
                          title: Text(event['event_type']?.toString() ?? 'event'),
                          subtitle: Text('run status: ' + (event['run_status']?.toString() ?? 'UNKNOWN') + ' • step: ' + (event['step_id']?.toString() ?? '-')),
                        )),
                  ],
                ),
        ),
      ],
    );
  }

  Widget _runTile(Map<String, dynamic> run) {
    final id = run['run_id']?.toString() ?? '';
    final selected = _selectedRun?['run_id'] == run['run_id'];
    return Card(
      key: Key('workflow-run-' + id),
      margin: const EdgeInsets.only(top: 8),
      child: ListTile(
        selected: selected,
        leading: const Icon(Icons.account_tree_outlined),
        title: Text(run['objective']?.toString() ?? 'Untitled workflow'),
        subtitle: Text('Run ' + id + ' • ' + (run['status']?.toString() ?? 'UNKNOWN')),
        trailing: const Icon(Icons.chevron_right),
        onTap: () => _selectRun(run),
      ),
    );
  }

  static Map<String, dynamic> _map(Map<dynamic, dynamic> value) =>
      value.map((key, value) => MapEntry(key.toString(), value));
}

class _LifecycleChip extends StatelessWidget {
  const _LifecycleChip(this.label);
  final String label;

  @override
  Widget build(BuildContext context) => Chip(key: Key('workflow-lifecycle-' + label), label: Text(label));
}
