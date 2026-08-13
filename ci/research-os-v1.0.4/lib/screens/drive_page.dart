import 'package:flutter/material.dart';

import '../models/system_snapshot.dart';
import '../widgets/page_scaffold.dart';
import '../widgets/section_card.dart';

class DrivePage extends StatelessWidget {
  const DrivePage({super.key, required this.snapshot, required this.onInstall, required this.onOpenRoot, required this.onRefresh});
  final SystemSnapshot? snapshot;
  final VoidCallback onInstall;
  final VoidCallback onOpenRoot;
  final VoidCallback onRefresh;

  @override
  Widget build(BuildContext context) {
    final s = snapshot;
    return PageScaffold(
      title: 'Drive Root',
      subtitle: 'Google Drive เป็น persistent data root ของ Research OS',
      actions: [IconButton.filledTonal(onPressed: onRefresh, icon: const Icon(Icons.refresh))],
      child: ListView(
        children: [
          SectionCard(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('Root Path', style: Theme.of(context).textTheme.labelLarge?.copyWith(color: Colors.white60)),
                const SizedBox(height: 8),
                SelectableText(s?.rootPath ?? 'ไม่พบ DRIVE_VIRTUAL_CLOUD', style: Theme.of(context).textTheme.titleMedium?.copyWith(fontFamily: 'Consolas')),
                const SizedBox(height: 16),
                Wrap(spacing: 10, runSpacing: 10, children: [
                  FilledButton.icon(onPressed: onInstall, icon: const Icon(Icons.build_circle_outlined), label: const Text('Install / Repair Bootstrap')),
                  FilledButton.tonalIcon(onPressed: s?.rootReady == true ? onOpenRoot : null, icon: const Icon(Icons.folder_open), label: const Text('เปิด Root')),
                ]),
              ],
            ),
          ),
          const SizedBox(height: 12),
          SectionCard(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('Expected Structure', style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w700)),
                const SizedBox(height: 12),
                const SelectableText('''DRIVE_VIRTUAL_CLOUD\\
├─ research-os\\
├─ github\\
│  ├─ repositories\\
│  ├─ mirrors\\bare\\
│  ├─ bundles\\full\\
│  ├─ sync\\
│  └─ restore\\
├─ backup\\
├─ logs\\
├─ runtime\\
└─ system\\''', style: TextStyle(fontFamily: 'Consolas', height: 1.5, color: Colors.white70)),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
