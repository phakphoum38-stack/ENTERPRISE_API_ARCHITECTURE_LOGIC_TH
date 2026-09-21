import 'dart:convert';

import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

class FileCodeWorkspace extends StatefulWidget {
  const FileCodeWorkspace({super.key});

  @override
  State<FileCodeWorkspace> createState() => _FileCodeWorkspaceState();
}

class _FileCodeWorkspaceState extends State<FileCodeWorkspace> {
  final _path = TextEditingController();
  final _content = TextEditingController();
  String _kind = 'TEXT';
  String? _fingerprint;
  String? _error;
  bool _readOnly = true;

  static const _extensions = <String>{
    'py', 'dart', 'js', 'ts', 'tsx', 'jsx', 'json', 'yaml', 'yml',
    'md', 'txt', 'toml', 'xml', 'html', 'css', 'sh', 'ps1',
  };

  @override
  void dispose() {
    _path.dispose();
    _content.dispose();
    super.dispose();
  }

  String _detectKind(String path) {
    final name = path.split(RegExp(r'[/\\]')).last;
    final dot = name.lastIndexOf('.');
    if (dot < 0) return 'TEXT';
    final ext = name.substring(dot + 1).toLowerCase();
    if (ext == 'md') return 'MARKDOWN';
    if (ext == 'txt') return 'TEXT';
    if (ext == 'json' || ext == 'yaml' || ext == 'yml' || ext == 'toml') {
      return 'DATA';
    }
    return 'CODE';
  }

  Future<void> _openFile() async {
    setState(() {
      _error = null;
      _fingerprint = null;
    });
    final result = await FilePicker.platform.pickFiles(
      type: FileType.custom,
      allowedExtensions: _extensions.toList(),
      withData: true,
    );
    if (result == null || result.files.isEmpty) return;
    final file = result.files.single;
    final bytes = file.bytes;
    if (bytes == null) {
      setState(() => _error = 'File bytes are unavailable on this platform.');
      return;
    }
    final content = utf8.decode(bytes, allowMalformed: true);
    setState(() {
      _path.text = file.path ?? file.name;
      _content.text = content;
      _kind = _detectKind(file.name);
      _fingerprint = _localFingerprint(bytes);
      _readOnly = true;
    });
  }

  String _localFingerprint(List<int> bytes) {
    // A deterministic local preview fingerprint; it is not a Git object SHA
    // or artifact SHA-256 and never substitutes for evidence.
    var h = 0xcbf29ce484222325;
    for (final byte in bytes) {
      h ^= byte;
      h = (h * 0x100000001b3) & 0xffffffffffffffff;
    }
    return h.toRadixString(16).padLeft(16, '0');
  }

  void _clear() {
    setState(() {
      _path.clear();
      _content.clear();
      _kind = 'TEXT';
      _sha256 = null;
      _error = null;
      _readOnly = true;
    });
  }

  @override
  Widget build(BuildContext context) {
    final lineCount = _content.text.isEmpty ? 0 : '\n'.allMatches(_content.text).length + 1;
    return ListView(
      padding: const EdgeInsets.all(16),
      children: <Widget>[
        Card(
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: <Widget>[
                Row(
                  children: <Widget>[
                    const Icon(Icons.folder_code_outlined, size: 30),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Text(
                        'Files / Code',
                        style: Theme.of(context).textTheme.headlineSmall,
                      ),
                    ),
                    OutlinedButton.icon(
                      onPressed: _openFile,
                      icon: const Icon(Icons.file_open_outlined),
                      label: const Text('Open file'),
                    ),
                    const SizedBox(width: 8),
                    IconButton(
                      tooltip: 'Clear workspace',
                      onPressed: _content.text.isEmpty ? null : _clear,
                      icon: const Icon(Icons.clear),
                    ),
                  ],
                ),
                const SizedBox(height: 12),
                Text(
                  'Read source locally without changing repository history. '
                  'Supported: code, Markdown and text. No write-back or authority is implied.',
                  style: Theme.of(context).textTheme.bodyMedium,
                ),
                const SizedBox(height: 12),
                TextField(
                  controller: _path,
                  decoration: const InputDecoration(
                    labelText: 'File path / name',
                    prefixIcon: Icon(Icons.route_outlined),
                    border: OutlineInputBorder(),
                  ),
                  onChanged: (value) => setState(() => _kind = _detectKind(value)),
                ),
                const SizedBox(height: 10),
                Wrap(
                  spacing: 8,
                  runSpacing: 8,
                  children: <Widget>[
                    Chip(label: Text(_kind)),
                    if (_content.text.isNotEmpty) Chip(label: Text('$lineCount lines')),
                    if (_fingerprint != null)
                      Chip(
                        avatar: const Icon(Icons.fingerprint, size: 17),
                        label: Text('local fingerprint: $_fingerprint'),
                      ),
                  ],
                ),
              ],
            ),
          ),
        ),
        if (_error != null)
          Card(
            child: ListTile(
              leading: const Icon(Icons.error_outline),
              title: const Text('File could not be opened'),
              subtitle: Text(_error!),
            ),
          ),
        const SizedBox(height: 12),
        Card(
          child: Padding(
            padding: const EdgeInsets.all(12),
            child: Column(
              children: <Widget>[
                Row(
                  children: <Widget>[
                    const Icon(Icons.code),
                    const SizedBox(width: 8),
                    const Expanded(child: Text('Source buffer')),
                    Switch(
                      value: _readOnly,
                      onChanged: (value) => setState(() => _readOnly = value),
                    ),
                    Text(_readOnly ? 'READ-ONLY' : 'EDIT BUFFER'),
                  ],
                ),
                const Divider(),
                TextField(
                  controller: _content,
                  readOnly: _readOnly,
                  maxLines: 24,
                  minLines: 12,
                  onChanged: (_) => setState(() => _sha256 = null),
                  style: const TextStyle(
                    fontFamily: 'monospace',
                    fontSize: 13,
                    height: 1.45,
                  ),
                  decoration: const InputDecoration(
                    hintText: 'Open a .py/.dart/.md/.txt file…',
                    border: InputBorder.none,
                    alignLabelWithHint: true,
                  ),
                ),
              ],
            ),
          ),
        ),
        const SizedBox(height: 12),
        Card(
          child: ListTile(
            leading: const Icon(Icons.shield_outlined),
            title: const Text('Authority boundary'),
            subtitle: const Text(
              'This workspace observes or prepares content only. '
              'Repository writes, repair, merge and release remain outside this viewer.',
            ),
          ),
        ),
      ],
    );
  }
}
