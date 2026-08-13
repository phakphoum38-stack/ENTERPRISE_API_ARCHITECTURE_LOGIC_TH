import 'package:flutter/material.dart';

import '../models/drive_entry.dart';
import '../models/system_snapshot.dart';
import '../services/drive_file_service.dart';
import '../widgets/page_scaffold.dart';
import '../widgets/section_card.dart';

class FilesPage extends StatefulWidget {
  const FilesPage({super.key, required this.snapshot});
  final SystemSnapshot? snapshot;

  @override
  State<FilesPage> createState() => _FilesPageState();
}

class _FilesPageState extends State<FilesPage> {
  final _service = DriveFileService();
  final _search = TextEditingController();
  String? _currentPath;
  List<DriveEntry> _entries = const [];
  bool _loading = false;

  @override
  void initState() {
    super.initState();
    _reset();
  }

  @override
  void didUpdateWidget(covariant FilesPage oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.snapshot?.rootPath != widget.snapshot?.rootPath) _reset();
  }

  @override
  void dispose() {
    _search.dispose();
    super.dispose();
  }

  Future<void> _reset() async {
    final root = widget.snapshot?.rootPath;
    if (root == null) return;
    _currentPath = root;
    await _load();
  }

  Future<void> _load() async {
    final path = _currentPath;
    if (path == null) return;
    setState(() => _loading = true);
    final entries = await _service.list(path);
    if (mounted) setState(() { _entries = entries; _loading = false; });
  }

  Future<void> _enter(DriveEntry entry) async {
    if (!entry.isDirectory) {
      await _service.open(entry);
      return;
    }
    setState(() => _currentPath = entry.path);
    await _load();
  }

  Future<void> _up() async {
    final root = widget.snapshot?.rootPath;
    final current = _currentPath;
    if (root == null || current == null || current.toLowerCase() == root.toLowerCase()) return;
    final separator = current.lastIndexOf('\\');
    if (separator <= 2) return;
    final parent = current.substring(0, separator);
    if (!parent.toLowerCase().startsWith(root.toLowerCase())) return;
    setState(() => _currentPath = parent);
    await _load();
  }

  @override
  Widget build(BuildContext context) {
    final q = _search.text.trim().toLowerCase();
    final filtered = q.isEmpty ? _entries : _entries.where((e) => e.name.toLowerCase().contains(q)).toList();
    return PageScaffold(
      title: 'Drive File Browser',
      subtitle: _currentPath ?? 'ไม่พบ Drive Root',
      actions: [
        SizedBox(width: 280, child: TextField(controller: _search, onChanged: (_) => setState(() {}), decoration: const InputDecoration(prefixIcon: Icon(Icons.search), hintText: 'ค้นหาในโฟลเดอร์นี้', isDense: true))),
        const SizedBox(width: 8),
        IconButton.filledTonal(onPressed: _up, tooltip: 'ขึ้นหนึ่งระดับ', icon: const Icon(Icons.arrow_upward)),
        const SizedBox(width: 6),
        IconButton.filledTonal(onPressed: _load, tooltip: 'Refresh', icon: const Icon(Icons.refresh)),
      ],
      child: widget.snapshot?.rootPath == null
          ? const SectionCard(child: Center(child: Text('ไม่พบ DRIVE_VIRTUAL_CLOUD')))
          : _loading
              ? const Center(child: CircularProgressIndicator())
              : SectionCard(
                  padding: EdgeInsets.zero,
                  child: ListView.separated(
                    itemCount: filtered.length,
                    separatorBuilder: (_, __) => const Divider(height: 1),
                    itemBuilder: (context, index) {
                      final entry = filtered[index];
                      return ListTile(
                        leading: Icon(entry.isDirectory ? Icons.folder_outlined : Icons.insert_drive_file_outlined),
                        title: Text(entry.name),
                        subtitle: Text(entry.isDirectory ? 'Folder' : _formatBytes(entry.sizeBytes)),
                        trailing: Text(entry.modifiedAt == null ? '' : entry.modifiedAt!.toLocal().toString().substring(0, 16), style: const TextStyle(color: Colors.white38, fontSize: 11)),
                        onTap: () => _enter(entry),
                        onLongPress: () => _service.open(entry),
                      );
                    },
                  ),
                ),
    );
  }

  String _formatBytes(int bytes) {
    if (bytes >= 1024 * 1024 * 1024) return '${(bytes / (1024 * 1024 * 1024)).toStringAsFixed(1)} GB';
    if (bytes >= 1024 * 1024) return '${(bytes / (1024 * 1024)).toStringAsFixed(1)} MB';
    if (bytes >= 1024) return '${(bytes / 1024).toStringAsFixed(1)} KB';
    return '$bytes B';
  }
}
