import 'package:flutter/material.dart';

import '../../api/developer_access_api_client.dart';

class FlutterCodeToolPage extends StatefulWidget {
  const FlutterCodeToolPage({
    required this.client,
    required this.principal,
    super.key,
  });

  final DeveloperAccessApiClient client;
  final String principal;

  @override
  State<FlutterCodeToolPage> createState() => _FlutterCodeToolPageState();
}

class _FlutterCodeToolPageState extends State<FlutterCodeToolPage> {
  final _editor = TextEditingController();
  final _query = TextEditingController();
  String _project = 'research_os_flutter';
  String? _path;
  String _sha = '';
  String _diff = '';
  String _status = 'พร้อมใช้งาน';
  List<String> _projects = const ['research_os_flutter'];
  List<String> _files = const [];
  bool _busy = false;
  bool _changed = false;

  @override
  void initState() {
    super.initState();
    _loadProjects();
  }

  @override
  void dispose() {
    _editor.dispose();
    _query.dispose();
    super.dispose();
  }

  Future<void> _loadProjects() async {
    await _run(() async {
      final payload = await widget.client.getCodeProjects();
      final raw = payload['projects'];
      final projects = raw is Map
          ? raw.keys.map((value) => value.toString()).toList()
          : <String>['research_os_flutter'];
      if (projects.isNotEmpty && !projects.contains(_project)) {
        _project = projects.first;
      }
      _projects = projects.isEmpty ? const ['research_os_flutter'] : projects;
      await _loadFiles();
    });
  }

  Future<void> _loadFiles() async {
    final payload = await widget.client.getCodeFiles(
      project: _project,
      query: _query.text,
    );
    final raw = payload['items'];
    final files = raw is List
        ? raw.whereType<Map>().map((item) => item['path'].toString()).toList()
        : <String>[];
    setState(() {
      _files = files;
      if (_path != null && !_files.contains(_path)) {
        _path = null;
        _editor.clear();
        _sha = '';
      }
    });
  }

  Future<void> _readSelected() async {
    final path = _path;
    if (path == null || path.isEmpty) return;
    await _run(() async {
      final payload = await widget.client.readCodeFile(path, project: _project);
      setState(() {
        _editor.text = payload['content']?.toString() ?? '';
        _sha = payload['sha256']?.toString() ?? '';
        _diff = '';
        _changed = false;
        _status = 'อ่านไฟล์แล้ว — SHA ผูกกับเวอร์ชันที่อ่าน';
      });
    });
  }

  Future<void> _preview() async {
    final path = _path;
    if (path == null || path.isEmpty || _sha.isEmpty) return;
    await _run(() async {
      final payload = await widget.client.previewCodeChange(
        project: _project,
        path: path,
        originalSha256: _sha,
        content: _editor.text,
      );
      setState(() {
        _diff = payload['diff']?.toString() ?? '';
        _changed = payload['changed'] == true;
        _status = _changed ? 'Diff พร้อมตรวจสอบ — ยังไม่ได้ Apply' : 'ไม่มีการเปลี่ยนแปลง';
      });
    });
  }

  Future<void> _apply() async {
    final path = _path;
    if (path == null || path.isEmpty || _sha.isEmpty || !_changed) return;
    await _run(() async {
      final payload = await widget.client.applyCodeChange(
        project: _project,
        path: path,
        originalSha256: _sha,
        content: _editor.text,
      );
      final rolledBack = payload['rolled_back'] == true;
      setState(() {
        _status = rolledBack
            ? 'Validation ไม่ผ่าน — ระบบ Rollback แล้ว'
            : 'Apply สำเร็จ — Flutter analyze/test ผ่าน';
        _sha = payload['sha256']?.toString() ?? _sha;
        _changed = false;
        _diff = '';
      });
      if (!rolledBack) {
        await _readSelected();
      }
    });
  }

  Future<void> _run(Future<void> Function() action) async {
    if (_busy) return;
    setState(() => _busy = true);
    try {
      await action();
    } on DeveloperAccessApiException catch (error) {
      if (mounted) setState(() => _status = error.message);
    } catch (error) {
      if (mounted) setState(() => _status = 'เกิดข้อผิดพลาด: $error');
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Card(
      key: const Key('flutter-code-tool'),
      margin: const EdgeInsets.only(top: 18),
      child: Padding(
        padding: const EdgeInsets.all(18),
        child: SingleChildScrollView(
        key: const Key('flutter-code-tool-scroll'),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Row(
              children: [
                const Icon(Icons.code_outlined),
                const SizedBox(width: 10),
                const Expanded(
                  child: Text(
                    'Flutter Code Tool',
                    style: TextStyle(fontSize: 19, fontWeight: FontWeight.w800),
                  ),
                ),
                const Chip(label: Text('Owner Code Tool')),
              ],
            ),
            const SizedBox(height: 8),
            const Text(
              'เลือก Project → เลือก File → อ่าน Code → แก้ Code → Preview Diff → Apply Change → Flutter analyze/test → Evidence',
            ),
            const SizedBox(height: 14),
            Row(
              children: [
                Expanded(
                  child: DropdownButtonFormField<String>(
                    initialValue: _projects.contains(_project) ? _project : null,
                    decoration: const InputDecoration(
                      labelText: 'Project',
                      border: OutlineInputBorder(),
                    ),
                    items: _projects
                        .map((item) => DropdownMenuItem(value: item, child: Text(item)))
                        .toList(),
                    onChanged: _busy
                        ? null
                        : (value) async {
                            if (value == null) return;
                            setState(() {
                              _project = value;
                              _path = null;
                              _editor.clear();
                              _sha = '';
                              _diff = '';
                            });
                            await _loadFiles();
                          },
                  ),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: TextField(
                    controller: _query,
                    decoration: InputDecoration(
                      labelText: 'Filter files',
                      border: const OutlineInputBorder(),
                      suffixIcon: IconButton(
                        tooltip: 'Refresh files',
                        onPressed: _busy ? null : _loadFiles,
                        icon: const Icon(Icons.refresh),
                      ),
                    ),
                    onSubmitted: (_) => _loadFiles(),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 10),
            DropdownButtonFormField<String>(
              initialValue: _files.contains(_path) ? _path : null,
              decoration: const InputDecoration(
                labelText: 'File',
                border: OutlineInputBorder(),
              ),
              items: _files
                  .map((item) => DropdownMenuItem(value: item, child: Text(item)))
                  .toList(),
              onChanged: _busy
                  ? null
                  : (value) async {
                      setState(() => _path = value);
                      await _readSelected();
                    },
            ),
            const SizedBox(height: 12),
            TextField(
              controller: _editor,
              minLines: 16,
              maxLines: 28,
              expands: false,
              enabled: !_busy && _path != null,
              onChanged: (_) => setState(() => _changed = true),
              style: const TextStyle(fontFamily: 'monospace', fontSize: 13),
              decoration: const InputDecoration(
                labelText: 'Code',
                alignLabelWithHint: true,
                border: OutlineInputBorder(),
              ),
            ),
            const SizedBox(height: 10),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: [
                OutlinedButton.icon(
                  onPressed: _busy || _path == null ? null : _readSelected,
                  icon: const Icon(Icons.menu_book_outlined),
                  label: const Text('อ่าน Code'),
                ),
                FilledButton.icon(
                  onPressed: _busy || _path == null || _sha.isEmpty ? null : _preview,
                  icon: const Icon(Icons.compare_arrows_outlined),
                  label: const Text('Preview Diff'),
                ),
                FilledButton.icon(
                  onPressed: _busy || !_changed || _diff.isEmpty ? null : _apply,
                  icon: const Icon(Icons.save_outlined),
                  label: const Text('Apply Change'),
                ),
              ],
            ),
            const SizedBox(height: 10),
            Text(_status, key: const Key('flutter-code-tool-status')),
            if (_sha.isNotEmpty) ...[
              const SizedBox(height: 4),
              SelectableText(
                'Read SHA: $_sha',
                style: Theme.of(context).textTheme.bodySmall,
              ),
            ],
            if (_diff.isNotEmpty) ...[
              const SizedBox(height: 12),
              const Text('Preview Diff', style: TextStyle(fontWeight: FontWeight.w800)),
              const SizedBox(height: 6),
              Container(
                constraints: const BoxConstraints(maxHeight: 320),
                padding: const EdgeInsets.all(12),
                color: Theme.of(context).colorScheme.surfaceContainerHighest,
                child: SingleChildScrollView(
                  child: SelectableText(
                    _diff,
                    style: const TextStyle(fontFamily: 'monospace', fontSize: 12),
                  ),
                ),
              ),
            ],
            if (_busy) const Padding(
              padding: EdgeInsets.only(top: 10),
              child: LinearProgressIndicator(),
            ),
          ],
        ),
      ),
    ),
  );
  }
}
