import 'package:flutter/material.dart';

class FriendAppShell extends StatelessWidget {
  const FriendAppShell({required this.index, required this.onIndexChanged, required this.pages, required this.teamCenter, required this.status, super.key});
  final int index;
  final ValueChanged<int> onIndexChanged;
  final List<Widget> pages;
  final Widget teamCenter;
  final Widget status;

  static const items = <({IconData icon, String label})>[
    (icon: Icons.chat_bubble_outline, label: 'Friend'),
    (icon: Icons.rocket_launch_outlined, label: 'Launch Desk'),
    (icon: Icons.auto_awesome_outlined, label: 'Capabilities'),
    (icon: Icons.memory_outlined, label: 'Memory'),
    (icon: Icons.tune_outlined, label: 'Provider'),
    (icon: Icons.groups_outlined, label: 'Team'),
  ];

  @override
  Widget build(BuildContext context) {
    return Material(
      color: Theme.of(context).scaffoldBackgroundColor,
      child: SafeArea(
        child: LayoutBuilder(
          builder: (context, constraints) {
            final compact = constraints.maxWidth < 900;
            return Row(
              children: [
                _Sidebar(index: index, onIndexChanged: onIndexChanged, compact: compact),
                Expanded(
                  child: Padding(
                    padding: EdgeInsets.all(compact ? 12 : 20),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.stretch,
                      children: [
                        _Header(teamCenter: teamCenter, status: status),
                        const SizedBox(height: 16),
                        Expanded(child: pages[index]),
                      ],
                    ),
                  ),
                ),
              ],
            );
          },
        ),
      ),
    );
  }
}

class _Sidebar extends StatelessWidget {
  const _Sidebar({required this.index, required this.onIndexChanged, required this.compact});
  final int index;
  final ValueChanged<int> onIndexChanged;
  final bool compact;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: compact ? 76 : 220,
      margin: const EdgeInsets.all(12),
      padding: const EdgeInsets.symmetric(vertical: 14, horizontal: 10),
      decoration: BoxDecoration(
        color: Theme.of(context).colorScheme.surface,
        borderRadius: BorderRadius.circular(22),
        border: Border.all(color: Theme.of(context).dividerColor.withValues(alpha: .08)),
      ),
      child: Column(
        children: [
          Container(
            width: 44,
            height: 44,
            alignment: Alignment.center,
            decoration: BoxDecoration(color: Theme.of(context).colorScheme.primary.withValues(alpha: .14), borderRadius: BorderRadius.circular(14)),
            child: Icon(Icons.hub_outlined, color: Theme.of(context).colorScheme.primary),
          ),
          const SizedBox(height: 18),
          Expanded(
            child: ListView.builder(
              itemCount: FriendAppShell.items.length,
              itemBuilder: (context, i) {
                final item = FriendAppShell.items[i];
                final selected = i == index;
                return Padding(
                  padding: const EdgeInsets.symmetric(vertical: 4),
                  child: InkWell(
                    borderRadius: BorderRadius.circular(14),
                    onTap: () => onIndexChanged(i),
                    child: AnimatedContainer(
                      duration: const Duration(milliseconds: 160),
                      padding: EdgeInsets.symmetric(horizontal: compact ? 0 : 12, vertical: 12),
                      decoration: BoxDecoration(
                        color: selected ? Theme.of(context).colorScheme.primary.withValues(alpha: .13) : Colors.transparent,
                        borderRadius: BorderRadius.circular(14),
                      ),
                      child: Row(
                        mainAxisAlignment: compact ? MainAxisAlignment.center : MainAxisAlignment.start,
                        children: [
                          Icon(item.icon, color: selected ? Theme.of(context).colorScheme.primary : null),
                          if (!compact) ...[
                            const SizedBox(width: 10),
                            Expanded(
                              child: Text(
                                item.label,
                                maxLines: 1,
                                overflow: TextOverflow.ellipsis,
                                style: TextStyle(fontWeight: selected ? FontWeight.w700 : FontWeight.w500),
                              ),
                            ),
                          ],
                        ],
                      ),
                    ),
                  ),
                );
              },
            ),
          ),
          const Icon(Icons.settings_outlined, size: 20),
        ],
      ),
    );
  }
}

class _Header extends StatelessWidget {
  const _Header({required this.teamCenter, required this.status});
  final Widget teamCenter;
  final Widget status;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: Theme.of(context).colorScheme.surface,
        borderRadius: BorderRadius.circular(22),
        border: Border.all(color: Theme.of(context).dividerColor.withValues(alpha: .08)),
      ),
      child: Wrap(
        alignment: WrapAlignment.spaceBetween,
        crossAxisAlignment: WrapCrossAlignment.center,
        spacing: 16,
        runSpacing: 12,
        children: [
          const Column(crossAxisAlignment: CrossAxisAlignment.start, children: [Text('Friend', style: TextStyle(fontSize: 22, fontWeight: FontWeight.w800)), SizedBox(height: 3), Text('Adaptive application workspace')]),
          teamCenter,
          status,
        ],
      ),
    );
  }
}
