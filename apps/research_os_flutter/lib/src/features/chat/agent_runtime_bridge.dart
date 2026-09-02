import 'dart:async';

import 'package:flutter/material.dart';

import '../../api/research_os_api_client.dart';
import 'runtime_models.dart';

class AgentRuntimeBridge extends StatefulWidget {
  const AgentRuntimeBridge({required this.apiClient, super.key});

  final ResearchOSApiClient apiClient;

  @override
  State<AgentRuntimeBridge> createState() => _AgentRuntimeBridgeState();
}

class _AgentRuntimeBridgeState extends State<AgentRuntimeBridge> {
  final TextEditingController _objectiveController = TextEditingController();
  Timer? _evidenceTimer;
  bool _busy = false;
  bool _loadingEvidence = false;
  OrchestrationRun? _run;
  RuntimeEvidence _evidence = const RuntimeEvidence(state: RuntimeState.idle);
  String? _statusMessage;
  String? _error;

  @override
  void dispose() {
    _evidenceTimer?.cancel();
    _objectiveController.dispose();
    super.dispose();
  }

  Future<void> _plan() async {
    final objective = _objectiveController.text.trim();
    if (objective.isEmpty || _busy) return;
    _evidenceTimer?.cancel();
    setState(() {
      _busy = true;
      _error = null;
      _run = null;
      _evidence = const RuntimeEvidence(state: RuntimeState.idle);
      _statusMessage = 'Creating an Agent Mesh plan…';
    });
    try {
      final response = await widget.apiClient.createOrchestration(
        objective: objective,
        steps: <Map<String, Object?>>[
          <String, Object?>{'step_id': 'understand', 'objective': 'Understand the request and available context.', 'requested_agent': 'auto', 'max_attempts': 2},
          <String, Object?>{'step_id': 'plan', 'objective': 'Plan the smallest evidence-backed implementation path.', 'requested_agent': 'auto', 'max_attempts': 2},
          <String, Object?>{'step_id': 'verify', 'objective': 'Verify the result and record runtime evidence.', 'requested_agent': 'auto', 'max_attempts': 2},
        ],
      );
      final run = OrchestrationRun.fromResponse(response);
      if (!mounted) return;
      setState(() {
        _run = run;
        _statusMessage = run.hasId
            ? 'Run planned • waiting for explicit execution.'
            : 'Plan created; run id was not returned.';
      });
      if (run.hasId) await _loadEvidence(preservePlannedState: true);
    } on Object catch (error) {
      if (mounted) setState(() => _error = error.toString());
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _execute() async {
    final run = _run;
    if (run == null || !run.hasId || _busy) return;
    setState(() {
      _busy = true;
      _error = null;
      _statusMessage = 'Executing approved Agent Mesh run…';
    });
    try {
      final response = await widget.apiClient.executeOrchestration(run.id, confirmed: true);
      final executedRun = OrchestrationRun.fromResponse(response);
      if (mounted) {
        setState(() {
          _run = OrchestrationRun(
            id: executedRun.id.isEmpty ? run.id : executedRun.id,
            objective: executedRun.objective.isEmpty ? run.objective : executedRun.objective,
            state: executedRun.state == RuntimeState.unknown ? RuntimeState.executing : executedRun.state,
            steps: executedRun.steps.isEmpty ? run.steps : executedRun.steps,
          );
          _statusMessage = 'Run ${_run!.state.wireName} • ${_run!.id}';
        });
      }
      await _loadEvidence();
      if (!mounted || !_evidence.state.isTerminal) _startEvidencePolling(run.id);
    } on Object catch (error) {
      if (mounted) setState(() => _error = error.toString());
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  void _startEvidencePolling(String runId) {
    _evidenceTimer?.cancel();
    var attempts = 0;
    _evidenceTimer = Timer.periodic(const Duration(milliseconds: 1500), (timer) async {
      if (_run?.id != runId) {
        timer.cancel();
        _evidenceTimer = null;
        return;
      }
      attempts += 1;
      await _loadEvidence();
      if (attempts >= 20 || _evidence.state.isTerminal) {
        timer.cancel();
        _evidenceTimer = null;
      }
    });
  }

  Future<void> _loadEvidence({bool preservePlannedState = false}) async {
    final run = _run;
    if (run == null || !run.hasId || _loadingEvidence) return;
    setState(() => _loadingEvidence = true);
    try {
      final response = await widget.apiClient.getOrchestrationTimeline(run.id);
      final evidence = RuntimeEvidence.fromResponse(response);
      if (!mounted) return;
      setState(() {
        _evidence = evidence;
        if (evidence.state != RuntimeState.unknown && !(preservePlannedState && evidence.state == RuntimeState.planned)) {
          _run = OrchestrationRun(id: run.id, objective: run.objective, state: evidence.state, steps: run.steps);
        }
        if (preservePlannedState && run.state == RuntimeState.planned && evidence.state == RuntimeState.planned) {
          _statusMessage = 'Run planned • waiting for explicit execution.';
        } else if (evidence.state != RuntimeState.unknown) {
          _statusMessage = 'Run ${evidence.state.wireName} • ${run.id}';
        }
      });
    } on Object catch (error) {
      if (mounted) setState(() => _error = 'Evidence refresh failed: $error');
    } finally {
      if (mounted) setState(() => _loadingEvidence = false);
    }
  }

  String _eventValue(Map<String, dynamic> item, List<String> keys) {
    for (final key in keys) {
      final value = item[key];
      if (value != null && value.toString().trim().isNotEmpty) return value.toString();
    }
    return '';
  }

  Widget _evidenceView() {
    final events = _evidence.events;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: <Widget>[
        const Divider(height: 22),
        Row(
          children: <Widget>[
            const Icon(Icons.fact_check_outlined, size: 19),
            const SizedBox(width: 8),
            const Expanded(child: Text('Runtime Evidence', style: TextStyle(fontWeight: FontWeight.w800))),
            IconButton(
              tooltip: 'Refresh evidence',
              onPressed: _loadingEvidence ? null : _loadEvidence,
              icon: _loadingEvidence
                  ? const SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2))
                  : const Icon(Icons.refresh, size: 19),
            ),
          ],
        ),
        if (_evidence.state != RuntimeState.idle && _evidence.state != RuntimeState.unknown)
          Chip(avatar: const Icon(Icons.circle, size: 10), label: Text(_evidence.state.wireName)),
        if (_evidence.raw.isEmpty) const Text('Execute a planned run to collect runtime evidence.'),
        if (events.isEmpty && _evidence.raw.isNotEmpty)
          const Padding(padding: EdgeInsets.only(top: 6), child: Text('Timeline is available; no event list was returned by the runtime.')),
        if (events.isNotEmpty)
          ...events.take(8).map(
                (item) => ListTile(
                  dense: true,
                  contentPadding: EdgeInsets.zero,
                  leading: Icon(_evidence.state.isTerminal ? Icons.check_circle_outline : Icons.radio_button_checked, size: 18),
                  title: Text(_eventValue(item, const <String>['title', 'name', 'step_id', 'event', 'event_type', 'type'])),
                  subtitle: Text(_eventValue(item, const <String>['status', 'run_status', 'state', 'detail', 'message', 'objective'])),
                ),
              ),
        const SizedBox(height: 4),
        const Text('Permission boundary: runtime writes remain behind the explicit execution path.', style: TextStyle(fontSize: 12)),
      ],
    );
  }

  @override
  Widget build(BuildContext context) {
    final run = _run;
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
                Expanded(child: Text('Agent Mesh Runtime', style: Theme.of(context).textTheme.titleSmall?.copyWith(fontWeight: FontWeight.w800))),
                if (run != null && run.hasId)
                  Chip(
                    avatar: const Icon(Icons.route_outlined, size: 16),
                    label: Text(run.id.length > 12 ? '${run.id.substring(0, 12)}…' : run.id),
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
              decoration: const InputDecoration(labelText: 'Objective', hintText: 'เช่น ตรวจสอบและปรับปรุง workflow นี้', border: OutlineInputBorder(), isDense: true),
            ),
            const SizedBox(height: 10),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: <Widget>[
                FilledButton.icon(onPressed: _busy ? null : _plan, icon: const Icon(Icons.account_tree_outlined), label: const Text('Plan with Agent Mesh')),
                OutlinedButton.icon(onPressed: run == null || !run.hasId || _busy ? null : _execute, icon: const Icon(Icons.play_arrow_outlined), label: const Text('Explicit Execute')),
              ],
            ),
            if (_busy) ...<Widget>[const SizedBox(height: 10), const LinearProgressIndicator()],
            if (_statusMessage != null) ...<Widget>[const SizedBox(height: 8), Text(_statusMessage!)],
            if (_error != null) ...<Widget>[const SizedBox(height: 8), Text(_error!, style: const TextStyle(color: Colors.red))],
            _evidenceView(),
          ],
        ),
      ),
    );
  }
}
