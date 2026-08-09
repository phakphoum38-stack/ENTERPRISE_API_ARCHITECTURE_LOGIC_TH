import 'package:flutter/material.dart';

import '../../api/research_os_api_client.dart';
import '../../ui/enterprise_components.dart';

class BrainInspectorPanel extends StatefulWidget {
  const BrainInspectorPanel({required this.apiClient, super.key});

  final ResearchOSApiClient apiClient;

  @override
  State<BrainInspectorPanel> createState() => _BrainInspectorPanelState();
}

class _BrainInspectorPanelState extends State<BrainInspectorPanel> {
  final TextEditingController _objective = TextEditingController();
  bool _loading = false;
  bool _planning = false;
  String? _error;
  Map<String, dynamic>? _health;
  Map<String, dynamic>? _plan;
  List<Map<String, dynamic>> _capabilities = const [];
  List<Map<String, dynamic>> _skills = const [];
  List<Map<String, dynamic>> _tools = const [];

  @override
  void initState() {
    super.initState();
    _load();
  }

  @override
  void dispose() {
    _objective.dispose();
    super.dispose();
  }

  Future<void> _load() async {
    if (_loading) return;
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final health = await widget.apiClient.getIntelligenceHealth();
      final capabilities = await widget.apiClient.getIntelligenceCapabilities();
      final skills = await widget.apiClient.getIntelligenceSkills();
      final tools = await widget.apiClient.getIntelligenceTools();
      if (!mounted) return;
      setState(() {
        _health = health;
        _capabilities = _mapList(capabilities['capabilities']);
        _skills = _mapList(skills['skills']);
        _tools = _mapList(tools['tools']);
      });
    } catch (error) {
      if (mounted) setState(() => _error = error.toString());
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _previewPlan() async {
    final objective = _objective.text.trim();
    if (objective.isEmpty || _planning) return;
    setState(() {
      _planning = true;
      _error = null;
    });
    try {
      final payload = await widget.apiClient.planIntelligence(
        objective,
        sessionId: 'agent-center-brain-inspector',
        context: const <String, Object?>{'surface': 'agent_center'},
      );
      if (mounted) setState(() => _plan = payload);
    } catch (error) {
      if (mounted) setState(() => _error = error.toString());
    } finally {
      if (mounted) setState(() => _planning = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final health = _health ?? const <String, dynamic>{};
    final counts = health['counts'] is Map
        ? _map(health['counts'] as Map)
        : const <String, dynamic>{};
    final ready = health['ready'] == true;
    final shownCapabilities = _capabilities.take(18).toList();

    return EnterpriseSection(
      title: 'AI Brain Inspector',
      subtitle:
          'Read-only view of Brain health, capabilities, skills, tools และ plan preview — ไม่มี execute หรือ permission grant',
      child: Column(
        key: const Key('brain-inspector'),
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Row(
            children: [
              Icon(
                ready ? Icons.psychology_alt_outlined : Icons.psychology_outlined,
              ),
              const SizedBox(width: 10),
              Expanded(
                child: Text(
                  _health == null
                      ? 'Brain status not loaded'
                      : ready
                          ? 'Brain runtime ready'
                          : 'Brain runtime degraded / incomplete',
                ),
              ),
              Chip(
                key: const Key('brain-ready-state'),
                label: Text(_health == null ? 'unknown' : (ready ? 'ready' : 'not ready')),
              ),
              const SizedBox(width: 8),
              IconButton(
                key: const Key('brain-inspector-refresh'),
                tooltip: 'Refresh AI Brain Inspector',
                onPressed: _loading ? null : _load,
                icon: const Icon(Icons.refresh),
              ),
            ],
          ),
          if (_loading) const LinearProgressIndicator(),
          if (_error != null)
            ListTile(
              key: const Key('brain-inspector-error'),
              leading: const Icon(Icons.warning_amber_outlined),
              title: const Text('Brain Inspector API warning'),
              subtitle: Text(_error!),
            ),
          const SizedBox(height: 8),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: [
              _metric('Agents', counts['operational_agents_ready'], counts['operational_agents']),
              _metric('Brain Team', counts['brain_agents_ready'], counts['brain_agents']),
              _metric('Skills', counts['skills_ready'], counts['skills']),
              _metric('Tools', counts['tools_ready'], counts['tools']),
              _metric('Mutating tools', counts['mutating_tools_ready'], null),
            ],
          ),
          const SizedBox(height: 14),
          Text('Capabilities', style: Theme.of(context).textTheme.titleSmall),
          const SizedBox(height: 8),
          if (_capabilities.isEmpty && !_loading)
            const Text('No capability catalog loaded.')
          else
            Wrap(
              spacing: 7,
              runSpacing: 7,
              children: shownCapabilities.map((item) {
                final id = '${item['capability'] ?? 'unknown'}';
                final routable = item['routable'] == true;
                final skill = item['skill_supported'] == true;
                final executable = item['executable'] == true;
                return Tooltip(
                  message:
                      'routable=$routable • skill=$skill • executable=$executable',
                  child: Chip(
                    key: Key('brain-capability-${_safeKey(id)}'),
                    avatar: Icon(
                      executable
                          ? Icons.play_circle_outline
                          : skill
                              ? Icons.extension_outlined
                              : routable
                                  ? Icons.route_outlined
                                  : Icons.help_outline,
                      size: 16,
                    ),
                    label: Text(id),
                  ),
                );
              }).toList(),
            ),
          if (_capabilities.length > shownCapabilities.length)
            Padding(
              padding: const EdgeInsets.only(top: 6),
              child: Text(
                '+${_capabilities.length - shownCapabilities.length} more capabilities',
                style: Theme.of(context).textTheme.bodySmall,
              ),
            ),
          const SizedBox(height: 14),
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Expanded(
                child: _contractList(
                  context,
                  title: 'Ready skills',
                  count: _skills.length,
                  items: _skills
                      .take(8)
                      .map((item) => '${item['skill_id'] ?? item['name'] ?? 'skill'}')
                      .toList(),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: _contractList(
                  context,
                  title: 'Ready tools',
                  count: _tools.length,
                  items: _tools
                      .take(8)
                      .map((item) => '${item['tool_id'] ?? item['name'] ?? 'tool'}')
                      .toList(),
                ),
              ),
            ],
          ),
          const Divider(height: 28),
          Text('Read-only plan preview', style: Theme.of(context).textTheme.titleSmall),
          const SizedBox(height: 8),
          Row(
            children: [
              Expanded(
                child: TextField(
                  key: const Key('brain-plan-objective'),
                  controller: _objective,
                  decoration: const InputDecoration(
                    prefixIcon: Icon(Icons.account_tree_outlined),
                    labelText: 'Goal for Brain plan preview',
                    helperText: 'Planning only — tools are not executed.',
                  ),
                  onSubmitted: (_) => _previewPlan(),
                ),
              ),
              const SizedBox(width: 10),
              FilledButton.icon(
                key: const Key('brain-plan-preview'),
                onPressed: _planning ? null : _previewPlan,
                icon: const Icon(Icons.visibility_outlined),
                label: const Text('Preview plan'),
              ),
            ],
          ),
          if (_planning) const LinearProgressIndicator(),
          if (_plan != null) ...[
            const SizedBox(height: 12),
            _planPreview(context, _plan!),
          ],
          const SizedBox(height: 10),
          const ListTile(
            key: Key('brain-inspector-safety'),
            dense: true,
            leading: Icon(Icons.shield_outlined),
            title: Text('Inspector is read-only'),
            subtitle: Text(
              'No hidden chain-of-thought, direct adapter access, permission grant, release, deploy, or production bypass is exposed here.',
            ),
          ),
        ],
      ),
    );
  }

  Widget _metric(String label, Object? ready, Object? total) {
    final value = total == null ? '${ready ?? '-'}' : '${ready ?? '-'}/${total ?? '-'}';
    return Chip(label: Text('$label $value'));
  }

  Widget _contractList(
    BuildContext context, {
    required String title,
    required int count,
    required List<String> items,
  }) {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        border: Border.all(color: Theme.of(context).dividerColor),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text('$title • $count', style: Theme.of(context).textTheme.labelLarge),
          const SizedBox(height: 6),
          if (items.isEmpty)
            const Text('None ready')
          else
            ...items.map(
              (item) => Padding(
                padding: const EdgeInsets.symmetric(vertical: 2),
                child: Text('• $item', maxLines: 1, overflow: TextOverflow.ellipsis),
              ),
            ),
        ],
      ),
    );
  }

  Widget _planPreview(BuildContext context, Map<String, dynamic> payload) {
    final result = payload['result'] is Map
        ? _map(payload['result'] as Map)
        : const <String, dynamic>{};
    final plan = result['plan'] is Map
        ? _map(result['plan'] as Map)
        : const <String, dynamic>{};
    final required = plan['required_capabilities'] is List
        ? (plan['required_capabilities'] as List).map((value) => '$value').toList()
        : const <String>[];
    final blocked = plan['blocked_reasons'] is List
        ? (plan['blocked_reasons'] as List).map((value) => '$value').toList()
        : const <String>[];
    return Card(
      key: const Key('brain-plan-result'),
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const Icon(Icons.fact_check_outlined),
                const SizedBox(width: 8),
                const Expanded(child: Text('Brain plan preview')),
                Chip(label: Text(payload['execution_performed'] == true ? 'executed' : 'read-only')),
              ],
            ),
            Text('Goal: ${plan['goal'] ?? _objective.text.trim()}'),
            const SizedBox(height: 6),
            Text(
              required.isEmpty
                  ? 'Required capabilities: none detected'
                  : 'Required capabilities: ${required.join(', ')}',
            ),
            if (blocked.isNotEmpty) ...[
              const SizedBox(height: 6),
              Text('Blocked: ${blocked.join(' • ')}'),
            ],
            const SizedBox(height: 6),
            Text(
              'No execution performed by this preview.',
              style: Theme.of(context).textTheme.bodySmall,
            ),
          ],
        ),
      ),
    );
  }

  static List<Map<String, dynamic>> _mapList(Object? value) => value is List
      ? value.whereType<Map>().map(_map).toList()
      : <Map<String, dynamic>>[];

  static Map<String, dynamic> _map(Map<dynamic, dynamic> value) =>
      value.map((key, value) => MapEntry(key.toString(), value));

  static String _safeKey(String value) => value
      .toLowerCase()
      .replaceAll(RegExp(r'[^a-z0-9_.-]+'), '-');
}
