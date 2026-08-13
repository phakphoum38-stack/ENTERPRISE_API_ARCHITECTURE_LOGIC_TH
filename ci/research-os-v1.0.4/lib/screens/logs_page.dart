import 'package:flutter/material.dart';

import '../models/system_snapshot.dart';
import '../widgets/page_scaffold.dart';
import '../widgets/section_card.dart';

class LogsPage extends StatelessWidget {
  const LogsPage({super.key, required this.snapshot, required this.onRefresh, required this.onOpenLogs});
  final SystemSnapshot? snapshot;
  final VoidCallback onRefresh;
  final VoidCallback onOpenLogs;

  @override
  Widget build(BuildContext context) {
    final lines = snapshot?.lastLogLines ?? const <String>[];
    return PageScaffold(
      title: 'Logs & Diagnostics',
      subtitle: 'ดู Mirror Worker log และสถานะพื้นฐานแบบ read-only',
      actions: [OutlinedButton.icon(onPressed: onOpenLogs, icon: const Icon(Icons.folder_open), label: const Text('เปิด Logs')), const SizedBox(width: 8), IconButton.filledTonal(onPressed: onRefresh, icon: const Icon(Icons.refresh))],
      child: SectionCard(
        padding: EdgeInsets.zero,
        child: lines.isEmpty
            ? const Center(child: Text('ยังไม่มี log'))
            : ListView.builder(
                padding: const EdgeInsets.all(18),
                itemCount: lines.length,
                itemBuilder: (context, index) => Padding(
                  padding: const EdgeInsets.symmetric(vertical: 2),
                  child: SelectableText(lines[index], style: const TextStyle(fontFamily: 'Consolas', fontSize: 12.5, height: 1.45, color: Colors.white70)),
                ),
              ),
      ),
    );
  }
}
