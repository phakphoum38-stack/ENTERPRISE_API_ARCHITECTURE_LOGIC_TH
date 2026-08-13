import 'dart:io';

import 'package:flutter/material.dart';

import '../models/system_snapshot.dart';
import '../services/repository_service.dart';
import '../widgets/page_scaffold.dart';
import '../widgets/section_card.dart';

class RestorePage extends StatefulWidget {
  const RestorePage({super.key, required this.snapshot});
  final SystemSnapshot? snapshot;

  @override
  State<RestorePage> createState() => _RestorePageState();
}

class _RestorePageState extends State<RestorePage> {
  final _service = RepositoryService();
  List<String> _bundles = const [];
  bool _busy = false;

  @override
  void initState() {
    super.initState();
    _load();
  }

  @override
  void didUpdateWidget(covariant RestorePage oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.snapshot?.rootPath != widget.snapshot?.rootPath) _load();
  }

  Future<void> _load() async {
    final root = widget.snapshot?.rootPath;
    if (root == null) return;
    final dir = Directory('$root\\github\\bundles\\full');
    if (!await dir.exists()) return;
    final names = <String>[];
    await for (final entity in dir.list(followLinks: false)) {
      if (entity is File && entity.path.toLowerCase().endsWith('.bundle')) {
        names.add(entity.path.split(Platform.pathSeparator).last.replaceFirst(RegExp(r'\.bundle$', caseSensitive: false), ''));
      }
    }
    names.sort((a, b) => a.toLowerCase().compareTo(b.toLowerCase()));
    if (mounted) setState(() => _bundles = names);
  }

  Future<void> _restore(String name) async {
    final root = widget.snapshot?.rootPath;
    if (root == null) return;
    final ok = await showDialog<bool>(context: context, builder: (context) => AlertDialog(title: const Text('Restore repository?'), content: Text('จะ clone $name.bundle ไปยัง %LOCALAPPDATA%\\ResearchOS\\restore-workspace โดยไม่แก้ข้อมูลต้นฉบับใน Drive'), actions: [TextButton(onPressed: () => Navigator.pop(context, false), child: const Text('ยกเลิก')), FilledButton(onPressed: () => Navigator.pop(context, true), child: const Text('Restore'))]));
    if (ok != true) return;
    setState(() => _busy = true);
    try {
      await _service.verifyBundle(root, name);
      final destination = await _service.restoreBundle(root, name);
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Restore สำเร็จ: $destination')));
      await Process.start('explorer.exe', [destination], runInShell: true);
    } catch (e) {
      if (context.mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Restore ไม่สำเร็จ: $e')));
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return PageScaffold(
      title: 'Backup / Restore Center',
      subtitle: 'ตรวจ bundle ก่อน clone คืน • ไม่เขียนทับ repository ต้นฉบับ',
      actions: [IconButton.filledTonal(onPressed: _busy ? null : _load, icon: const Icon(Icons.refresh))],
      child: _bundles.isEmpty
          ? const SectionCard(child: Center(child: Text('ยังไม่มี full bundle สำหรับ Restore')))
          : ListView.separated(
              itemCount: _bundles.length,
              separatorBuilder: (_, __) => const SizedBox(height: 9),
              itemBuilder: (itemContext, index) {
                final name = _bundles[index];
                return SectionCard(child: Row(children: [const Icon(Icons.inventory_2_outlined), const SizedBox(width: 12), Expanded(child: Text('$name.bundle', style: const TextStyle(fontWeight: FontWeight.w700))), OutlinedButton.icon(onPressed: _busy ? null : () async {
                  try {
                    final msg = await _service.verifyBundle(widget.snapshot!.rootPath!, name);
                    if (itemContext.mounted) {
                      ScaffoldMessenger.of(itemContext).showSnackBar(SnackBar(content: Text(msg)));
                    }
                  } catch (e) {
                    if (itemContext.mounted) {
                      ScaffoldMessenger.of(itemContext).showSnackBar(SnackBar(content: Text('$e')));
                    }
                  }
                }, icon: const Icon(Icons.verified_outlined), label: const Text('Verify')), const SizedBox(width: 8), FilledButton.icon(onPressed: _busy ? null : () => _restore(name), icon: const Icon(Icons.restore), label: const Text('Restore'))]));
              },
            ),
    );
  }
}
