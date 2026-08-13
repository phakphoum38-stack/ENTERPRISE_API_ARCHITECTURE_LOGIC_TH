import 'package:flutter/material.dart';

import '../models/system_snapshot.dart';
import '../widgets/page_scaffold.dart';
import '../widgets/section_card.dart';
import '../widgets/status_card.dart';

class OverviewPage extends StatelessWidget {
  const OverviewPage({
    super.key,
    required this.snapshot,
    required this.onInstall,
    required this.onSync,
    required this.onOpenRoot,
    required this.onNavigate,
  });

  final SystemSnapshot? snapshot;
  final VoidCallback onInstall;
  final VoidCallback onSync;
  final VoidCallback onOpenRoot;
  final ValueChanged<int> onNavigate;

  @override
  Widget build(BuildContext context) {
    final s = snapshot;
    return PageScaffold(
      title: 'Research OS Control Center',
      subtitle: 'One Truth สำหรับ Drive, GitHub, AI Providers, Backup และ Restore',
      actions: [
        FilledButton.icon(onPressed: onSync, icon: const Icon(Icons.sync), label: const Text('Sync ตอนนี้')),
      ],
      child: LayoutBuilder(
        builder: (context, constraints) {
          final columns = constraints.maxWidth >= 1200 ? 4 : constraints.maxWidth >= 760 ? 2 : 1;
          final width = (constraints.maxWidth - ((columns - 1) * 12)) / columns;
          final cards = [
            SizedBox(width: width, child: StatusCard(title: 'Drive Root', value: s?.rootPath ?? 'ไม่พบ', subtitle: s?.installed == true ? 'Bootstrap installed' : 'ยังไม่ได้ฝัง Bootstrap', icon: Icons.cloud_done_outlined, good: s?.rootReady, onTap: onOpenRoot)),
            SizedBox(width: width, child: StatusCard(title: 'GitHub', value: s?.githubAuthenticated == true ? 'Authenticated' : 'ต้องเชื่อมต่อ', subtitle: s?.ghAvailable == true ? 'GitHub CLI พร้อม' : 'ไม่พบ gh', icon: Icons.hub_outlined, good: s?.githubAuthenticated, onTap: () => onNavigate(6))),
            SizedBox(width: width, child: StatusCard(title: 'Mirror Worker', value: s?.workerState ?? 'กำลังตรวจสอบ', subtitle: '${s?.bundleCount ?? 0} bundles • ${s?.mirrorCount ?? 0} mirrors', icon: Icons.memory_outlined, good: s?.workerInstalled, onTap: () => onNavigate(6))),
            SizedBox(width: width, child: StatusCard(title: 'Repositories', value: '${s?.repositoryCount ?? 0}', subtitle: 'Drive repository snapshots', icon: Icons.folder_copy_outlined, good: (s?.repositoryCount ?? 0) > 0, onTap: () => onNavigate(2))),
          ];

          return SingleChildScrollView(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Wrap(spacing: 12, runSpacing: 12, children: cards),
                const SizedBox(height: 16),
                SectionCard(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          const Icon(Icons.bolt_outlined),
                          const SizedBox(width: 10),
                          Text('Quick Actions', style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w700)),
                        ],
                      ),
                      const SizedBox(height: 16),
                      Wrap(
                        spacing: 10,
                        runSpacing: 10,
                        children: [
                          FilledButton.tonalIcon(onPressed: onInstall, icon: const Icon(Icons.build_circle_outlined), label: const Text('Install / Repair Root')),
                          FilledButton.tonalIcon(onPressed: () => onNavigate(1), icon: const Icon(Icons.smart_toy_outlined), label: const Text('เปิด AI Chat')),
                          FilledButton.tonalIcon(onPressed: () => onNavigate(3), icon: const Icon(Icons.folder_outlined), label: const Text('เปิด Drive Files')),
                          FilledButton.tonalIcon(onPressed: () => onNavigate(4), icon: const Icon(Icons.key_outlined), label: const Text('API Providers')),
                          FilledButton.tonalIcon(onPressed: () => onNavigate(7), icon: const Icon(Icons.restore), label: const Text('Restore Center')),
                          FilledButton.tonalIcon(onPressed: () => onNavigate(8), icon: const Icon(Icons.terminal), label: const Text('Diagnostics')),
                        ],
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 16),
                SectionCard(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text('Recent Activity', style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w700)),
                      const SizedBox(height: 12),
                      if (s == null || s.lastLogLines.isEmpty)
                        const Text('ยังไม่มี log จาก Mirror Worker', style: TextStyle(color: Colors.white54))
                      else
                        ...s.lastLogLines.reversed.take(8).map((line) => Padding(
                              padding: const EdgeInsets.symmetric(vertical: 4),
                              child: Text(line, maxLines: 1, overflow: TextOverflow.ellipsis, style: const TextStyle(fontFamily: 'Consolas', color: Colors.white70)),
                            )),
                    ],
                  ),
                ),
              ],
            ),
          );
        },
      ),
    );
  }
}
