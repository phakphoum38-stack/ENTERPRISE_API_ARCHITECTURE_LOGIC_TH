import 'package:flutter/material.dart';

import '../models/system_snapshot.dart';
import '../widgets/page_scaffold.dart';
import '../widgets/section_card.dart';
import '../widgets/status_card.dart';

class SyncPage extends StatelessWidget {
  const SyncPage({
    super.key,
    required this.snapshot,
    required this.onStart,
    required this.onStop,
    required this.onLogin,
    required this.onOpenBundles,
    required this.onOpenMirrors,
  });

  final SystemSnapshot? snapshot;
  final VoidCallback onStart;
  final VoidCallback onStop;
  final VoidCallback onLogin;
  final VoidCallback onOpenBundles;
  final VoidCallback onOpenMirrors;

  @override
  Widget build(BuildContext context) {
    final s = snapshot;
    return PageScaffold(
      title: 'GitHub Sync & Mirror',
      subtitle: 'Full-history bundles + bare mirror archives + repository snapshots',
      child: ListView(
        children: [
          Wrap(
            spacing: 12,
            runSpacing: 12,
            children: [
              SizedBox(width: 300, child: StatusCard(title: 'Git', value: s?.gitAvailable == true ? 'Ready' : 'Missing', icon: Icons.terminal, good: s?.gitAvailable)),
              SizedBox(width: 300, child: StatusCard(title: 'GitHub Auth', value: s?.githubAuthenticated == true ? 'Connected' : 'Not connected', icon: Icons.hub, good: s?.githubAuthenticated)),
              SizedBox(width: 300, child: StatusCard(title: 'Worker', value: s?.workerState ?? 'Unknown', icon: Icons.memory, good: s?.workerInstalled)),
            ],
          ),
          const SizedBox(height: 14),
          SectionCard(
            child: Wrap(
              spacing: 10,
              runSpacing: 10,
              children: [
                FilledButton.icon(onPressed: onStart, icon: const Icon(Icons.play_arrow), label: const Text('Start Sync')),
                FilledButton.tonalIcon(onPressed: onStop, icon: const Icon(Icons.stop), label: const Text('Stop Worker')),
                OutlinedButton.icon(onPressed: onLogin, icon: const Icon(Icons.login), label: const Text('GitHub Login')),
                OutlinedButton.icon(onPressed: onOpenBundles, icon: const Icon(Icons.inventory_2_outlined), label: Text('Bundles (${s?.bundleCount ?? 0})')),
                OutlinedButton.icon(onPressed: onOpenMirrors, icon: const Icon(Icons.archive_outlined), label: Text('Mirrors (${s?.mirrorCount ?? 0})')),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
