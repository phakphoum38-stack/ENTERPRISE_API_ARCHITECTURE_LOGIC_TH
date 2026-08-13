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
  bool _mutating = false;

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
    'Backup': 'List restore points and run a verified backup tool through the Owner Gate.',
    'Restore': 'Review restore points and run a verified restore tool through the Owner Gate.',
    'Shell': 'Run bounded Research OS diagnostic commands only.',
  };

  @override
  void initState() {
    super.initState();
    _argumentController = TextEditingController(
      text: switch (widget.label) {
        'Files' => '',
        'Shell' => 'help',
        'Restore' => '',
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

  Map<String, dynamic> _unwrap(Map<String, dynamic> response) {
    final result = response['result'];
    return result is Map ? Map<String, dynamic>.from(result) : response;
  }

  List<Map<String, dynamic>> _mapList(dynamic value) {
    if (value is! List) return const <Map<String, dynamic>>[];
    return value
        .whereType<Map>()
        .map((item) => Map<String, dynamic>.from(item))
        .toList();
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

  Future<bool> _confirm(String title, String message) async {
    return await showDialog<bool>(
          context: context,
          builder: (dialogContext) => AlertDialog(
            title: Text(title),
            content: Text(message),
            actions: [
              TextButton(
                onPressed: () => Navigator.pop(dialogContext, false),
                child: const Text('Cancel'),
              ),
              FilledButton(
                onPressed: () => Navigator.pop(dialogContext, true),
                child: const Text('Approve & Run'),
              ),
            ],
          ),
        ) ??
        false;
  }

  Future<void> _runGovernedMutation(String capability) async {
    if (_mutating) return;
    setState(() {
      _mutating = true;
      _error = null;
    });
    try {
      final catalogResponse =
          await widget.api.executeTool('drive-tools-list', const {});
      final catalog = _unwrap(catalogResponse);
      final packages = _mapList(catalog['packages']);
      Map<String, dynamic>? selected;
      for (final package in packages) {
        final name = package['name']?.toString().toLowerCase() ?? '';
        if (name.contains(capability)) {
          selected = package;
          break;
        }
      }
      if (selected == null) {
        throw StateError(
          'No checksum-governed $capability tool package is configured in the Research OS Drive tool mirror.',
        );
      }

      final packageName = selected['name']?.toString() ?? '';
      final backupName = _argumentController.text.trim();
      if (capability == 'restore' && backupName.isEmpty) {
        throw StateError('Enter a restore-point filename before running restore.');
      }
      if (!mounted) return;
      final approved = await _confirm(
        capability == 'backup' ? 'Create Backup' : 'Restore Research OS',
        'Run verified package "$packageName" through the V3 Owner Gate? '
        'Research OS will record the governed tool result as evidence.',
      );
      if (!approved) return;

      final arguments = <String, dynamic>{'action': capability};
      if (capability == 'restore') arguments['backup'] = backupName;
      final response = await widget.api.executeTool(
        'drive-tool-execute',
        <String, dynamic>{
          'name': packageName,
          'arguments': arguments,
        },
        approved: true,
      );
      if (!mounted) return;
      setState(() => _result = response);
      await _run();
    } catch (error) {
      if (!mounted) return;
      setState(() => _error = error);
    } finally {
      if (mounted) setState(() => _mutating = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final tool = _toolByPage[widget.label] ?? '-';
    final details = _descriptionByPage[widget.label] ??
        'Research OS governed operational surface.';
    final inputPage = widget.label == 'Files' ||
        widget.label == 'Shell' ||
        widget.label == 'Restore';
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
                label: const Text('Refresh'),
              ),
              if (widget.label == 'Backup') ...[
                const SizedBox(width: 8),
                FilledButton.icon(
                  onPressed:
                      _mutating ? null : () => _runGovernedMutation('backup'),
                  icon: const Icon(Icons.backup_outlined),
                  label: const Text('Create Backup'),
                ),
              ],
              if (widget.label == 'Restore') ...[
                const SizedBox(width: 8),
                FilledButton.icon(
                  onPressed:
                      _mutating ? null : () => _runGovernedMutation('restore'),
                  icon: const Icon(Icons.restore),
                  label: const Text('Restore'),
                ),
              ],
            ],
          ),
        ),
        const Divider(height: 1),
        Expanded(
          child: ListView(
            padding: const EdgeInsets.all(20),
            children: [
              if (inputPage)
                Card(
                  child: Padding(
                    padding: const EdgeInsets.all(16),
                    child: Row(
                      children: [
                        Expanded(
                          child: TextField(
                            controller: _argumentController,
                            onSubmitted: (_) {
                              if (widget.label != 'Restore') _run();
                            },
                            decoration: InputDecoration(
                              labelText: switch (widget.label) {
                                'Files' => 'Workspace relative path',
                                'Shell' => 'Research OS command',
                                _ => 'Restore-point filename',
                              },
                              hintText: switch (widget.label) {
                                'Files' => 'github/repositories',
                                'Shell' =>
                                  'help | workspace | drive | repos | backups | runtime | installer',
                                _ => 'ResearchOS-backup.zip',
                              },
                              border: const OutlineInputBorder(),
                            ),
                          ),
                        ),
                        if (widget.label != 'Restore') ...[
                          const SizedBox(width: 10),
                          FilledButton(
                            onPressed: _running ? null : _run,
                            child: Text(widget.label == 'Files'
                                ? 'Browse'
                                : 'Execute'),
                          ),
                        ],
                      ],
                    ),
                  ),
                ),
              if (widget.label == 'Backup' || widget.label == 'Restore')
                const Padding(
                  padding: EdgeInsets.only(top: 12, bottom: 12),
                  child: Card(
                    child: ListTile(
                      leading: Icon(Icons.shield_outlined,
                          color: Color(0xFFFFB74D)),
                      title: Text('Owner Gate + checksum verification'),
                      subtitle: Text(
                        'Backup/Restore mutation is executed only through a verified Drive tool package and explicit owner approval. Missing packages fail closed.',
                      ),
                    ),
                  ),
                ),
              const SizedBox(height: 12),
              if (_running || _mutating)
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
