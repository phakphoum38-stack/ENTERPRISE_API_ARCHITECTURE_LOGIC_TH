import 'dart:convert';

import 'package:flutter/material.dart';

import 'api/v3_api.dart';

class ResearchOSOperationalPage extends StatefulWidget {
  const ResearchOSOperationalPage({
    super.key,
    required this.label,
    required this.api,
  });

  final String label;
  final V3Api api;

  @override
  State<ResearchOSOperationalPage> createState() =>
      _ResearchOSOperationalPageState();
}

class _ResearchOSOperationalPageState
    extends State<ResearchOSOperationalPage> {
  late final TextEditingController _argumentController;
  Map<String, dynamic>? _result;
  Object? _error;
  bool _running = false;

  static const _toolByPage = <String, String>{
    'Files': 'workspace-files-list',
    'Repositories': 'workspace-repositories',
    'GitHub': 'github-status',
    'Drive': 'drive-status',
    'Runtime': 'runtime-status',
    'Installer': 'installer-status',
    'Backup': 'backups-list',
    'Restore': 'backups-list',
    'Shell': 'research-shell',
  };

  static const _descriptionByPage = <String, String>{
    'Files': 'Browse the confined DRIVE_VIRTUAL_CLOUD workspace.',
    'Repositories': 'Inspect repository mirrors and bundle evidence.',
    'GitHub': 'Inspect the governed local GitHub mirror.',
    'Drive': 'Inspect Research OS persistent Drive workspace status.',
    'Runtime': 'Inspect the active local Research OS service runtime.',
    'Installer': 'Inspect installed runtime and build metadata.',
    'Backup': 'List checksum-evidenced Research OS restore points.',
    'Restore': 'Review restore points. Restore mutation stays owner-gated.',
    'Shell': 'Run bounded Research OS diagnostic commands only.',
  };

  @override
  void initState() {
    super.initState();
    _argumentController = TextEditingController(
      text: switch (widget.label) {
        'Files' => '',
        'Shell' => 'help',
        _ => '',
      },
    );
    _run();
  }

  @override
  void dispose() {
    _argumentController.dispose();
    super.dispose();
  }

  Map<String, dynamic> _arguments() {
    final value = _argumentController.text.trim();
    return switch (widget.label) {
      'Files' => <String, dynamic>{'path': value},
      'Shell' => <String, dynamic>{'command': value.isEmpty ? 'help' : value},
      _ => <String, dynamic>{},
    };
  }

  Future<void> _run() async {
    final tool = _toolByPage[widget.label];
    if (tool == null || _running) return;
    setState(() {
      _running = true;
      _error = null;
    });
    try {
      final result = await widget.api.executeTool(tool, _arguments());
      if (!mounted) return;
      setState(() => _result = result);
    } catch (error) {
      if (!mounted) return;
      setState(() => _error = error);
    } finally {
      if (mounted) setState(() => _running = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final tool = _toolByPage[widget.label] ?? '-';
    final details = _descriptionByPage[widget.label] ??
        'Research OS governed operational surface.';
    return Column(
      children: [
        Padding(
          padding: const EdgeInsets.fromLTRB(20, 16, 20, 12),
          child: Row(
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(widget.label,
                        style: const TextStyle(
                            fontSize: 21, fontWeight: FontWeight.w800)),
                    Text(details,
                        style: const TextStyle(
                            color: Colors.white54, fontSize: 12)),
                  ],
                ),
              ),
              Chip(label: Text(tool)),
              const SizedBox(width: 8),
              FilledButton.tonalIcon(
                onPressed: _running ? null : _run,
                icon: const Icon(Icons.refresh),
                label: const Text('Run'),
              ),
            ],
          ),
        ),
        const Divider(height: 1),
        Expanded(
          child: ListView(
            padding: const EdgeInsets.all(20),
            children: [
              if (widget.label == 'Files' || widget.label == 'Shell')
                Card(
                  child: Padding(
                    padding: const EdgeInsets.all(16),
                    child: Row(
                      children: [
                        Expanded(
                          child: TextField(
                            controller: _argumentController,
                            onSubmitted: (_) => _run(),
                            decoration: InputDecoration(
                              labelText: widget.label == 'Files'
                                  ? 'Workspace relative path'
                                  : 'Research OS command',
                              hintText: widget.label == 'Files'
                                  ? 'github/repositories'
                                  : 'help | workspace | drive | repos | backups | runtime | installer',
                              border: const OutlineInputBorder(),
                            ),
                          ),
                        ),
                        const SizedBox(width: 10),
                        FilledButton(
                          onPressed: _running ? null : _run,
                          child: Text(widget.label == 'Files' ? 'Browse' : 'Execute'),
                        ),
                      ],
                    ),
                  ),
                ),
              if (widget.label == 'Restore')
                const Padding(
                  padding: EdgeInsets.only(bottom: 12),
                  child: Card(
                    child: ListTile(
                      leading: Icon(Icons.shield_outlined,
                          color: Color(0xFFFFB74D)),
                      title: Text('Owner Gate'),
                      subtitle: Text(
                          'This page verifies and lists restore points. Applying a restore is intentionally blocked until an approval-gated restore tool is selected.'),
                    ),
                  ),
                ),
              const SizedBox(height: 12),
              if (_running)
                const LinearProgressIndicator()
              else if (_error != null)
                Card(
                  child: ListTile(
                    leading: const Icon(Icons.error_outline,
                        color: Colors.redAccent),
                    title: const Text('Tool execution failed'),
                    subtitle: SelectableText('$_error'),
                  ),
                )
              else if (_result != null)
                _ResultCard(result: _result!)
              else
                const Card(
                  child: ListTile(
                    leading: Icon(Icons.hourglass_empty),
                    title: Text('Waiting for Research OS runtime'),
                  ),
                ),
              const SizedBox(height: 14),
              _ToolBoundaryCard(page: widget.label, tool: tool),
            ],
          ),
        ),
      ],
    );
  }
}

class _ResultCard extends StatelessWidget {
  const _ResultCard({required this.result});
  final Map<String, dynamic> result;

  @override
  Widget build(BuildContext context) {
    const encoder = JsonEncoder.withIndent('  ');
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Row(
              children: [
                Icon(Icons.check_circle_outline, color: Color(0xFF47E68A)),
                SizedBox(width: 8),
                Text('Live Research OS result',
                    style: TextStyle(fontWeight: FontWeight.w800)),
              ],
            ),
            const SizedBox(height: 12),
            SelectableText(
              encoder.convert(result),
              style: const TextStyle(fontFamily: 'monospace', fontSize: 12),
            ),
          ],
        ),
      ),
    );
  }
}

class _ToolBoundaryCard extends StatelessWidget {
  const _ToolBoundaryCard({required this.page, required this.tool});
  final String page;
  final String tool;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text('Tool Discovery & Governance',
                style: TextStyle(fontWeight: FontWeight.w800)),
            const SizedBox(height: 8),
            Text('Page: $page  →  Tool: $tool'),
            const SizedBox(height: 6),
            const Text(
              'Analysis → Research → Tool Match → Permission → Planning → Execution → Quality/Evidence',
              style: TextStyle(color: Colors.white60),
            ),
          ],
        ),
      ),
    );
  }
}
