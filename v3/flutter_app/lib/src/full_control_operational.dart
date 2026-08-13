import 'dart:convert';

import 'package:flutter/material.dart';

import 'api/v3_api.dart';

Map<String, dynamic> _result(Map<String, dynamic> response) {
  final value = response['result'];
  if (value is Map) return Map<String, dynamic>.from(value);
  return response;
}

List<Map<String, dynamic>> _maps(dynamic value) {
  if (value is! List) return const <Map<String, dynamic>>[];
  return value.whereType<Map>().map((item) => Map<String, dynamic>.from(item)).toList();
}

int _int(dynamic value) {
  if (value is int) return value;
  if (value is num) return value.toInt();
  return int.tryParse(value?.toString() ?? '') ?? 0;
}

String _bytes(int bytes) {
  if (bytes >= 1024 * 1024 * 1024) return '${(bytes / (1024 * 1024 * 1024)).toStringAsFixed(1)} GB';
  if (bytes >= 1024 * 1024) return '${(bytes / (1024 * 1024)).toStringAsFixed(1)} MB';
  if (bytes >= 1024) return '${(bytes / 1024).toStringAsFixed(1)} KB';
  return '$bytes B';
}

String _hash(dynamic value) {
  final text = value?.toString() ?? '-';
  return text.length > 12 ? '${text.substring(0, 12)}…' : text;
}

void _snack(BuildContext context, String text) {
  ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(text)));
}

Future<bool> _confirm(BuildContext context, String title, String body) async {
  return await showDialog<bool>(
        context: context,
        builder: (dialogContext) => AlertDialog(
          title: Text(title),
          content: Text(body),
          actions: [
            TextButton(onPressed: () => Navigator.pop(dialogContext, false), child: const Text('Cancel')),
            FilledButton(onPressed: () => Navigator.pop(dialogContext, true), child: const Text('Confirm')),
          ],
        ),
      ) ??
      false;
}

class _Frame extends StatelessWidget {
  const _Frame({required this.title, required this.subtitle, required this.child, this.actions = const []});
  final String title;
  final String subtitle;
  final Widget child;
  final List<Widget> actions;

  @override
  Widget build(BuildContext context) {
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
                    Text(title, style: const TextStyle(fontSize: 20, fontWeight: FontWeight.w800)),
                    const SizedBox(height: 3),
                    Text(subtitle, style: const TextStyle(color: Colors.white54, fontSize: 12)),
                  ],
                ),
              ),
              ...actions,
            ],
          ),
        ),
        const Divider(height: 1),
        Expanded(child: Padding(padding: const EdgeInsets.all(16), child: child)),
      ],
    );
  }
}

class _Card extends StatelessWidget {
  const _Card({required this.child, this.padding = const EdgeInsets.all(14)});
  final Widget child;
  final EdgeInsets padding;

  @override
  Widget build(BuildContext context) {
    return Card(child: Padding(padding: padding, child: child));
  }
}

class _Error extends StatelessWidget {
  const _Error(this.message, {this.icon = Icons.warning_amber_rounded});
  final String message;
  final IconData icon;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 48, color: Colors.orangeAccent),
          const SizedBox(height: 10),
          Text(message, textAlign: TextAlign.center, style: const TextStyle(color: Colors.white60)),
        ],
      ),
    );
  }
}

class FullFilesPage extends StatefulWidget {
  const FullFilesPage({super.key, required this.api});
  final V3Api api;

  @override
  State<FullFilesPage> createState() => _FullFilesPageState();
}

class _FullFilesPageState extends State<FullFilesPage> {
  String _path = '';
  String? _root;
  String? _error;
  bool _loading = true;
  List<Map<String, dynamic>> _entries = [];

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() => _loading = true);
    try {
      final data = _result(await widget.api.executeTool('workspace-files-list', {'path': _path}));
      if (!mounted) return;
      setState(() {
        _root = data['root']?.toString();
        _path = data['path']?.toString() ?? _path;
        _entries = _maps(data['entries']);
        _error = null;
      });
    } catch (error) {
      if (mounted) setState(() => _error = error.toString());
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _open(Map<String, dynamic> item) async {
    final path = item['path']?.toString() ?? '';
    if (item['directory'] == true) {
      setState(() => _path = path);
      await _load();
      return;
    }
    try {
      final data = _result(await widget.api.executeTool('workspace-file-read', {'path': path}));
      if (!mounted) return;
      await showDialog<void>(
        context: context,
        builder: (dialogContext) => AlertDialog(
          title: Text(path),
          content: SizedBox(
            width: 820,
            height: 520,
            child: SingleChildScrollView(
              child: SelectableText(data['text']?.toString() ?? '', style: const TextStyle(fontFamily: 'Consolas', fontSize: 12)),
            ),
          ),
          actions: [TextButton(onPressed: () => Navigator.pop(dialogContext), child: const Text('Close'))],
        ),
      );
    } catch (error) {
      if (mounted) _snack(context, 'Preview failed: $error');
    }
  }

  Future<void> _up() async {
    if (_path.isEmpty) return;
    final parts = _path.split('/').where((part) => part.isNotEmpty).toList();
    if (parts.isNotEmpty) parts.removeLast();
    _path = parts.join('/');
    await _load();
  }

  @override
  Widget build(BuildContext context) {
    return _Frame(
      title: 'Files',
      subtitle: _root == null ? 'Governed DRIVE_VIRTUAL_CLOUD browser' : '$_root${_path.isEmpty ? '' : ' / $_path'}',
      actions: [
        IconButton.filledTonal(onPressed: _path.isEmpty ? null : _up, icon: const Icon(Icons.arrow_upward)),
        const SizedBox(width: 6),
        IconButton.filledTonal(onPressed: _load, icon: const Icon(Icons.refresh)),
      ],
      child: _loading
          ? const Center(child: CircularProgressIndicator())
          : _error != null
              ? _Error(_error!, icon: Icons.cloud_off)
              : _Card(
                  padding: EdgeInsets.zero,
                  child: ListView.separated(
                    itemCount: _entries.length,
                    separatorBuilder: (_, __) => const Divider(height: 1),
                    itemBuilder: (context, index) {
                      final item = _entries[index];
                      final dir = item['directory'] == true;
                      return ListTile(
                        leading: Icon(dir ? Icons.folder_outlined : Icons.description_outlined),
                        title: Text(item['name']?.toString() ?? '-'),
                        subtitle: Text(dir ? 'Folder' : _bytes(_int(item['size']))),
                        trailing: Icon(dir ? Icons.chevron_right : Icons.visibility_outlined),
                        onTap: () => _open(item),
                      );
                    },
                  ),
                ),
    );
  }
}

class FullRepositoriesPage extends StatefulWidget {
  const FullRepositoriesPage({super.key, required this.api});
  final V3Api api;

  @override
  State<FullRepositoriesPage> createState() => _FullRepositoriesPageState();
}

class _FullRepositoriesPageState extends State<FullRepositoriesPage> {
  List<Map<String, dynamic>> _items = [];
  String? _error;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    try {
      final data = _result(await widget.api.executeTool('workspace-repositories', const {}));
      if (!mounted) return;
      setState(() {
        _items = _maps(data['repositories']);
        _error = null;
      });
    } catch (error) {
      if (mounted) setState(() => _error = error.toString());
    }
  }

  @override
  Widget build(BuildContext context) {
    return _Frame(
      title: 'Repositories',
      subtitle: 'Drive snapshots + bundle SHA-256 evidence',
      actions: [IconButton.filledTonal(onPressed: _load, icon: const Icon(Icons.refresh))],
      child: _error != null
          ? _Error(_error!, icon: Icons.inventory_2_outlined)
          : ListView.separated(
              itemCount: _items.length,
              separatorBuilder: (_, __) => const SizedBox(height: 8),
              itemBuilder: (context, index) {
                final repo = _items[index];
                final bundleRaw = repo['bundle'];
                final bundle = bundleRaw is Map ? Map<String, dynamic>.from(bundleRaw) : null;
                return _Card(
                  child: ListTile(
                    contentPadding: EdgeInsets.zero,
                    leading: const CircleAvatar(child: Icon(Icons.folder_copy_outlined)),
                    title: Text('${repo['owner'] ?? '-'}/${repo['name'] ?? '-'}'),
                    subtitle: Text(
                      '${repo['files'] ?? 0} files · ${repo['path'] ?? ''}\n'
                      '${bundle == null ? 'Bundle not found' : 'Bundle ${_bytes(_int(bundle['size']))} · SHA ${_hash(bundle['sha256'])}'}',
                    ),
                    isThreeLine: true,
                  ),
                );
              },
            ),
    );
  }
}

class FullStatusToolPage extends StatefulWidget {
  const FullStatusToolPage({
    super.key,
    required this.api,
    required this.title,
    required this.subtitle,
    required this.tool,
    required this.icon,
  });

  final V3Api api;
  final String title;
  final String subtitle;
  final String tool;
  final IconData icon;

  @override
  State<FullStatusToolPage> createState() => _FullStatusToolPageState();
}

class _FullStatusToolPageState extends State<FullStatusToolPage> {
  Map<String, dynamic>? _data;
  String? _error;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    try {
      final data = _result(await widget.api.executeTool(widget.tool, const {}));
      if (!mounted) return;
      setState(() {
        _data = data;
        _error = null;
      });
    } catch (error) {
      if (mounted) setState(() => _error = error.toString());
    }
  }

  @override
  Widget build(BuildContext context) {
    return _Frame(
      title: widget.title,
      subtitle: widget.subtitle,
      actions: [IconButton.filledTonal(onPressed: _load, icon: const Icon(Icons.refresh))],
      child: _error != null
          ? _Error(_error!, icon: widget.icon)
          : _data == null
              ? const Center(child: CircularProgressIndicator())
              : ListView(
                  children: [
                    _Card(
                      child: Row(
                        children: [
                          CircleAvatar(child: Icon(widget.icon)),
                          const SizedBox(width: 12),
                          Expanded(child: Text('${widget.title} is connected to V3 Tool Registry.', style: const TextStyle(fontWeight: FontWeight.w700))),
                        ],
                      ),
                    ),
                    const SizedBox(height: 10),
                    _Card(
                      child: SelectableText(
                        const JsonEncoder.withIndent('  ').convert(_data),
                        style: const TextStyle(fontFamily: 'Consolas', fontSize: 12, height: 1.4),
                      ),
                    ),
                  ],
                ),
    );
  }
}

class FullBackupPage extends StatefulWidget {
  const FullBackupPage({super.key, required this.api});
  final V3Api api;

  @override
  State<FullBackupPage> createState() => _FullBackupPageState();
}

class _FullBackupPageState extends State<FullBackupPage> {
  List<Map<String, dynamic>> _backups = [];
  List<Map<String, dynamic>> _packages = [];
  bool _busy = false;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    try {
      final values = await Future.wait([
        widget.api.executeTool('backups-list', const {}),
        widget.api.executeTool('drive-tools-list', const {}),
      ]);
      if (!mounted) return;
      setState(() {
        _backups = _maps(_result(values[0])['backups']);
        _packages = _maps(_result(values[1])['packages']);
      });
    } catch (error) {
      if (mounted) _snack(context, 'Backup inventory failed: $error');
    }
  }

  Map<String, dynamic>? _matchingPackage(String keyword) {
    for (final item in _packages) {
      if ((item['name']?.toString().toLowerCase() ?? '').contains(keyword)) return item;
    }
    return null;
  }

  Future<void> _create() async {
    final package = _matchingPackage('backup');
    if (package == null) {
      _snack(context, 'No checksum-governed backup package is configured in Drive.');
      return;
    }
    if (!await _confirm(context, 'Create backup', 'Run verified package ${package['name']} with owner approval?')) return;
    setState(() => _busy = true);
    try {
      final response = await widget.api.executeTool(
        'drive-tool-execute',
        {'name': package['name'], 'arguments': const {'action': 'backup'}},
        approved: true,
      );
      if (mounted) _snack(context, 'Backup: ${const JsonEncoder.withIndent('  ').convert(response)}');
      await _load();
    } catch (error) {
      if (mounted) _snack(context, 'Backup failed: $error');
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return _Frame(
      title: 'Backup',
      subtitle: 'Restore-point inventory + approval-gated checksum-verified backup tool',
      actions: [FilledButton.icon(onPressed: _busy ? null : _create, icon: const Icon(Icons.backup_outlined), label: const Text('Create Backup'))],
      child: ListView.separated(
        itemCount: _backups.length,
        separatorBuilder: (_, __) => const SizedBox(height: 8),
        itemBuilder: (context, index) {
          final item = _backups[index];
          return _Card(
            child: ListTile(
              contentPadding: EdgeInsets.zero,
              leading: const Icon(Icons.archive_outlined),
              title: Text(item['name']?.toString() ?? '-'),
              subtitle: Text('${_bytes(_int(item['size']))} · SHA ${_hash(item['sha256'])}\n${item['path'] ?? ''}'),
              isThreeLine: true,
            ),
          );
        },
      ),
    );
  }
}

class FullRestorePage extends StatefulWidget {
  const FullRestorePage({super.key, required this.api});
  final V3Api api;

  @override
  State<FullRestorePage> createState() => _FullRestorePageState();
}

class _FullRestorePageState extends State<FullRestorePage> {
  List<Map<String, dynamic>> _backups = [];
  List<Map<String, dynamic>> _packages = [];

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    try {
      final values = await Future.wait([
        widget.api.executeTool('backups-list', const {}),
        widget.api.executeTool('drive-tools-list', const {}),
      ]);
      if (!mounted) return;
      setState(() {
        _backups = _maps(_result(values[0])['backups']);
        _packages = _maps(_result(values[1])['packages']);
      });
    } catch (error) {
      if (mounted) _snack(context, 'Restore inventory failed: $error');
    }
  }

  Map<String, dynamic>? get _restorePackage {
    for (final item in _packages) {
      if ((item['name']?.toString().toLowerCase() ?? '').contains('restore')) return item;
    }
    return null;
  }

  Future<void> _restore(Map<String, dynamic> backup) async {
    final package = _restorePackage;
    if (package == null) {
      _snack(context, 'No checksum-governed restore package is configured in Drive.');
      return;
    }
    final name = backup['name']?.toString() ?? '';
    if (!await _confirm(context, 'Restore backup', 'Run ${package['name']} for $name with owner approval?')) return;
    try {
      final response = await widget.api.executeTool(
        'drive-tool-execute',
        {'name': package['name'], 'arguments': {'action': 'restore', 'backup': name}},
        approved: true,
      );
      if (mounted) _snack(context, 'Restore: ${const JsonEncoder.withIndent('  ').convert(response)}');
    } catch (error) {
      if (mounted) _snack(context, 'Restore failed: $error');
    }
  }

  @override
  Widget build(BuildContext context) {
    return _Frame(
      title: 'Restore',
      subtitle: 'Restore points + owner-approved verified restore tool execution',
      actions: [IconButton.filledTonal(onPressed: _load, icon: const Icon(Icons.refresh))],
      child: ListView.separated(
        itemCount: _backups.length,
        separatorBuilder: (_, __) => const SizedBox(height: 8),
        itemBuilder: (context, index) {
          final item = _backups[index];
          return _Card(
            child: Row(
              children: [
                const Icon(Icons.settings_backup_restore_outlined),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(item['name']?.toString() ?? '-', style: const TextStyle(fontWeight: FontWeight.w700)),
                      Text('${_bytes(_int(item['size']))} · ${item['path'] ?? ''}', style: const TextStyle(color: Colors.white54, fontSize: 12)),
                    ],
                  ),
                ),
                FilledButton.tonalIcon(onPressed: () => _restore(item), icon: const Icon(Icons.restore), label: const Text('Restore')),
              ],
            ),
          );
        },
      ),
    );
  }
}

class FullShellPage extends StatefulWidget {
  const FullShellPage({super.key, required this.api});
  final V3Api api;

  @override
  State<FullShellPage> createState() => _FullShellPageState();
}

class _FullShellPageState extends State<FullShellPage> {
  final _controller = TextEditingController(text: 'help');
  String _output = 'Research OS diagnostic console. Type help.';
  bool _busy = false;

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  Future<void> _run() async {
    final command = _controller.text.trim();
    if (command.isEmpty || _busy) return;
    setState(() => _busy = true);
    try {
      final data = _result(await widget.api.executeTool('research-shell', {'command': command}));
      if (mounted) setState(() => _output = const JsonEncoder.withIndent('  ').convert(data));
    } catch (error) {
      if (mounted) setState(() => _output = 'Error: $error');
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return _Frame(
      title: 'Shell',
      subtitle: 'Bounded Research OS diagnostic console · arbitrary OS shell is disabled',
      child: Column(
        children: [
          _Card(
            child: Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _controller,
                    onSubmitted: (_) => _run(),
                    decoration: const InputDecoration(prefixIcon: Icon(Icons.terminal), labelText: 'Research OS command'),
                  ),
                ),
                const SizedBox(width: 8),
                FilledButton.icon(onPressed: _busy ? null : _run, icon: const Icon(Icons.play_arrow), label: const Text('Run Command')),
              ],
            ),
          ),
          const SizedBox(height: 10),
          Expanded(
            child: _Card(
              child: SingleChildScrollView(
                child: SelectableText(_output, style: const TextStyle(fontFamily: 'Consolas', fontSize: 12, height: 1.45)),
              ),
            ),
          ),
        ],
      ),
    );
  }
}
