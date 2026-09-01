import 'package:flutter/material.dart';

import '../../api/research_os_api_client.dart';

class AgentRuntimeBridge extends StatefulWidget {
  const AgentRuntimeBridge({required this.apiClient, super.key});

  final ResearchOSApiClient apiClient;

  @override
  State<AgentRuntimeBridge> createState() => _AgentRuntimeBridgeState();
}

class _AgentRuntimeBridgeState extends State<AgentRuntimeBridge> {
  final TextEditingController _objectiveController = TextEditingController();
  bool _busy = false;
  String? _runId;
  String? _status;
  String? _error;

  @override
  void dispose() {
    _objectiveController.dispose();
    super.dispose();
  }

  Future<void> _plan() async {
    final objective = _objectiveController.text.trim();
    if (objective.isEmpty || _busy) return;

    setState(() {
      _busy = true;
      _error = null;
      _status = 'Creating an Agent Mesh plan…';
    });
    try {
      final response = await widget.apiClient.createOrchestration(
        objective: objective,
        steps: <Map<String, Object?>>[
          <String, Object?>{
            'step_id': 'understand',
            'objective': 'Understand the request and available context.',
            'requested_agent': 'auto',
            'max_attempts': 2,
          },
          <String, Object?>{
            'step_id': 'plan',
            'objective': 'Plan the smallest evidence-backed implementation path.',
            'requested_agent': 'auto',
            'max_attempts': 2,
          },
          <String, Object?>{
            'step_id': 'verify',
            'objective': 'Verify the result and record runtime evidence.',
            'requested_agent': 'auto',
            'max_attempts': 2,
          },
        ],
      );
      final runId = (response['run_id'] ?? response['id'] ?? '').toString();
      if (!mounted) return;
      setState(() {
        _runId = runId.isEmpty ? null : runId;
        _status = runId.isEmpty
            ? 'Plan created; run id was not returned.'
            : 'Plan created • waiting for explicit execution.';
      });
    } on Object catch (error) {
      if (mounted) setState(() => _error = error.toString());
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _execute() async {
    final runId = _runId;
    if (runId == null || _busy) return;
    setState(() {
      _busy = true;
      _error = null;
      _status = 'Executing approved Agent Mesh run…';
    });
    try {
      final response = await widget.apiClient.executeOrchestration(
        runId,
        confirmed: true,
      );
      final status = (response['status'] ?? 'execution requested').toString();
      if (mounted) setState(() => _status = 'Run $status • $runId');
    } on Object catch (error) {
      if (mounted) setState(() => _error = error.toString());
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: EdgeInsets.zero,
      child: Padding(
        padding: const EdgeInsets.fromLTRB(14, 10, 14, 12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: <Widget>[
            Row(
              children: <Widget>[
                const Icon(Icons.hub_outlined, size: 20),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    'Agent Mesh Runtime',
                    style: Theme.of(context).textTheme.titleSmall?.copyWith(fontWeight: FontWeight.w800),
                  ),
                ),
                if (_runId != null)
                  Chip(
                    avatar: const Icon(Icons.route_outlined, size: 16),
                    label: Text(_runId!.length > 12 ? '${_runId!.substring(0, 12)}…' : _runId!),
                  ),
              ],
            ),
            const SizedBox(height: 4),
            const Text('Plan first. Execute only through an explicit user action.'),
            const SizedBox(height: 10),
            TextField(
              controller: _objectiveController,
              enabled: !_busy,
              minLines: 1,
              maxLines: 3,
              textInputAction: TextInputAction.done,
              onSubmitted: (_) => _plan(),
              decoration: const InputDecoration(
                labelText: 'Objective',
                hintText: 'เช่น ตรวจสอบและปรับปรุง workflow นี้',
                border: OutlineInputBorder(),
                isDense: true,
              ),
            ),
            const SizedBox(height: 10),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: <Widget>[
                FilledButton.icon(
                  onPressed: _busy ? null : _plan,
                  icon: const Icon(Icons.account_tree_outlined),
                  label: const Text('Plan with Agent Mesh'),
                ),
                OutlinedButton.icon(
                  onPressed: _runId == null || _busy ? null : _execute,
                  icon: const Icon(Icons.play_arrow_outlined),
                  label: const Text('Explicit Execute'),
                ),
              ],
            ),
            if (_busy) ...<Widget>[
              const SizedBox(height: 10),
              const LinearProgressIndicator(),
            ],
            if (_status != null) ...<Widget>[
              const SizedBox(height: 8),
              Text(_status!),
            ],
            if (_error != null) ...<Widget>[
              const SizedBox(height: 8),
              Text(_error!, style: TextStyle(color: Theme.of(context).colorScheme.error)),
            ],
          ],
        ),
      ),
    );
  }
}
