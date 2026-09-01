import 'package:flutter/material.dart';

import '../../api/research_os_api_client.dart';

class DesignStudioPanel extends StatefulWidget {
  const DesignStudioPanel({super.key, required this.apiClient});
  final ResearchOSApiClient apiClient;

  @override
  State<DesignStudioPanel> createState() => _DesignStudioPanelState();
}

class _DesignStudioPanelState extends State<DesignStudioPanel> {
  bool _loading = true;
  String? _error;
  Map<String, dynamic> _capacity = const {};
  List<dynamic> _agents = const [];
  List<dynamic> _skills = const [];

  @override
  void initState() {
    super.initState();
    _refresh();
  }

  Future<void> _refresh() async {
    setState(() { _loading = true; _error = null; });
    try {
      final results = await Future.wait<dynamic>([
        widget.apiClient.getBrainCapacity(),
        widget.apiClient.getAgents(),
        widget.apiClient.getBrainSkills(),
      ]);
      if (!mounted) return;
      setState(() {
        _capacity = results[0] as Map<String, dynamic>;
        _agents = results[1] as List<dynamic>;
        _skills = results[2] as List<dynamic>;
        _loading = false;
      });
    } catch (error) {
      if (!mounted) return;
      setState(() { _error = error.toString(); _loading = false; });
    }
  }

  String _capacityText() => (_capacity['maximum_leaf_capacity'] ?? _capacity['capacity'] ?? '46,656').toString();
  String _scaleText() => (_capacity['scale'] ?? '6^6').toString();

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: EdgeInsets.zero,
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Row(children: [
            const Icon(Icons.design_services_outlined),
            const SizedBox(width: 10),
            const Expanded(child: Text('Design Studio', style: TextStyle(fontSize: 20, fontWeight: FontWeight.w700))),
            IconButton(onPressed: _loading ? null : _refresh, icon: const Icon(Icons.refresh)),
          ]),
          const SizedBox(height: 6),
          const Text('Design according to agents, skills, policy and evidence.'),
          const SizedBox(height: 18),
          if (_loading) const LinearProgressIndicator()
          else if (_error != null) Text(_error!, style: TextStyle(color: Theme.of(context).colorScheme.error))
          else ...[
            Wrap(spacing: 8, runSpacing: 8, children: [
              Chip(label: Text('${_scaleText()} READY')),
              Chip(label: Text('${_capacityText()} logical capacity')),
              Chip(label: Text('${_agents.length} agents')),
              Chip(label: Text('${_skills.length} skills')),
            ]),
            const SizedBox(height: 18),
            const _StepTile(number: '1', title: 'Registry & Policy', detail: 'Read agent registry, skills and permission boundary.'),
            const _StepTile(number: '2', title: 'Build Design System', detail: 'Compose UI from available capabilities and evidence.'),
            const _StepTile(number: '3', title: 'Accessibility & Status', detail: 'Check readable states, permissions and runtime readiness.'),
            const _StepTile(number: '4', title: 'Implementation Handoff', detail: 'Prepare evidence-backed handoff; no external write without explicit execution.'),
            const SizedBox(height: 12),
            const Divider(),
            const SizedBox(height: 8),
            const Text('Evidence', style: TextStyle(fontWeight: FontWeight.w700)),
            const SizedBox(height: 8),
            const _EvidenceRow(icon: Icons.check_circle_outline, title: 'Design created', detail: 'Friend Workspace Design Studio'),
            const _EvidenceRow(icon: Icons.smart_toy_outlined, title: 'GUI Designer', detail: 'Agent role ready'),
            _EvidenceRow(icon: Icons.hub_outlined, title: _scaleText(), detail: '${_capacityText()} logical capacity'),
            const _EvidenceRow(icon: Icons.rule_outlined, title: 'Permission boundary', detail: 'Explicit execution required for writes'),
          ],
        ]),
      ),
    );
  }
}

class _StepTile extends StatelessWidget {
  const _StepTile({required this.number, required this.title, required this.detail});
  final String number, title, detail;
  @override
  Widget build(BuildContext context) => ListTile(
    contentPadding: EdgeInsets.zero,
    leading: CircleAvatar(radius: 15, child: Text(number)),
    title: Text(title, style: const TextStyle(fontWeight: FontWeight.w600)),
    subtitle: Text(detail),
  );
}

class _EvidenceRow extends StatelessWidget {
  const _EvidenceRow({required this.icon, required this.title, required this.detail});
  final IconData icon;
  final String title, detail;
  @override
  Widget build(BuildContext context) => ListTile(
    contentPadding: EdgeInsets.zero,
    dense: true,
    leading: Icon(icon, size: 20),
    title: Text(title),
    subtitle: Text(detail),
  );
}
