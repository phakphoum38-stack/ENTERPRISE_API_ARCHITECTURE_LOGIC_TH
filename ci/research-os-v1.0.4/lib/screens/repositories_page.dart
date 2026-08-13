import 'package:flutter/material.dart';

import '../models/repository_record.dart';
import '../models/system_snapshot.dart';
import '../services/repository_service.dart';
import '../widgets/page_scaffold.dart';
import '../widgets/section_card.dart';

class RepositoriesPage extends StatefulWidget {
  const RepositoriesPage({super.key, required this.snapshot});
  final SystemSnapshot? snapshot;

  @override
  State<RepositoriesPage> createState() => _RepositoriesPageState();
}

class _RepositoriesPageState extends State<RepositoriesPage> {
  final _service = RepositoryService();
  final _search = TextEditingController();
  List<RepositoryRecord> _repos = const [];
  bool _loading = false;

  @override
  void initState() {
    super.initState();
    _load();
  }

  @override
  void didUpdateWidget(covariant RepositoriesPage oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.snapshot?.rootPath != widget.snapshot?.rootPath) _load();
  }

  @override
  void dispose() {
    _search.dispose();
    super.dispose();
  }

  Future<void> _load() async {
    final root = widget.snapshot?.rootPath;
    if (root == null) return;
    setState(() => _loading = true);
    final repos = await _service.listRepositories(root);
    if (mounted) setState(() { _repos = repos; _loading = false; });
  }

  @override
  Widget build(BuildContext context) {
    final q = _search.text.trim().toLowerCase();
    final filtered = q.isEmpty ? _repos : _repos.where((r) => r.name.toLowerCase().contains(q)).toList();
    return PageScaffold(
      title: 'Repository Browser',
      subtitle: 'ดู source snapshots, full bundles และ bare mirror archives จาก Drive',
      actions: [
        SizedBox(width: 300, child: TextField(controller: _search, onChanged: (_) => setState(() {}), decoration: const InputDecoration(prefixIcon: Icon(Icons.search), hintText: 'ค้นหา repository', isDense: true))),
        const SizedBox(width: 8),
        IconButton.filledTonal(onPressed: _load, icon: const Icon(Icons.refresh)),
      ],
      child: widget.snapshot?.rootPath == null
          ? const SectionCard(child: Center(child: Text('ไม่พบ Drive Root')))
          : _loading
              ? const Center(child: CircularProgressIndicator())
              : ListView.separated(
                  itemCount: filtered.length,
                  separatorBuilder: (_, __) => const SizedBox(height: 9),
                  itemBuilder: (itemContext, index) {
                    final r = filtered[index];
                    return SectionCard(
                      child: Row(
                        children: [
                          const CircleAvatar(child: Icon(Icons.folder_copy_outlined)),
                          const SizedBox(width: 14),
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(r.name, style: const TextStyle(fontWeight: FontWeight.w700)),
                                const SizedBox(height: 4),
                                Text('${r.snapshotFiles} snapshot files • ${r.hasBundle ? _formatBytes(r.bundleBytes) : 'no bundle'}', style: const TextStyle(color: Colors.white60)),
                              ],
                            ),
                          ),
                          _Flag(label: 'BUNDLE', active: r.hasBundle),
                          const SizedBox(width: 6),
                          _Flag(label: 'MIRROR', active: r.hasMirrorArchive),
                          const SizedBox(width: 8),
                          IconButton(onPressed: () => _service.openRepository(r), tooltip: 'เปิดโฟลเดอร์', icon: const Icon(Icons.folder_open)),
                          IconButton(onPressed: r.hasBundle ? () async {
                            try {
                              final msg = await _service.verifyBundle(widget.snapshot!.rootPath!, r.name);
                              if (itemContext.mounted) {
                                ScaffoldMessenger.of(itemContext).showSnackBar(SnackBar(content: Text(msg)));
                              }
                            } catch (e) {
                              if (itemContext.mounted) {
                                ScaffoldMessenger.of(itemContext).showSnackBar(SnackBar(content: Text('$e')));
                              }
                            }
                          } : null, tooltip: 'Verify bundle', icon: const Icon(Icons.verified_outlined)),
                        ],
                      ),
                    );
                  },
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

class _Flag extends StatelessWidget {
  const _Flag({required this.label, required this.active});
  final String label;
  final bool active;
  @override
  Widget build(BuildContext context) {
    final color = active ? Colors.greenAccent : Colors.white30;
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 3),
      decoration: BoxDecoration(borderRadius: BorderRadius.circular(999), border: Border.all(color: color.withValues(alpha: .4))),
      child: Text(label, style: TextStyle(color: color, fontSize: 10, fontWeight: FontWeight.w700)),
    );
  }
}
