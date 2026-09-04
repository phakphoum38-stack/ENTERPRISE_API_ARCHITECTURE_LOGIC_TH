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
                    padding: EdgeInsets.fromLTRB(compact ? 12 : 24, compact ? 12 : 20, compact ? 12 : 24, compact ? 12 : 20),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.stretch,
                      children: [
                        _Header(teamCenter: teamCenter, status: status, compact: compact),
                        const SizedBox(height: 12),
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
    final theme = Theme.of(context);
    return Container(
      width: compact ? 64 : 204,
      margin: const EdgeInsets.all(12),
      padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 8),
      decoration: BoxDecoration(
        color: theme.colorScheme.surface.withValues(alpha: .72),
        borderRadius: BorderRadius.circular(18),
        border: Border.all(color: theme.colorScheme.outline.withValues(alpha: .10)),
      ),
      child: Column(
        children: [
          Container(
            width: 40,
            height: 40,
            alignment: Alignment.center,
            decoration: BoxDecoration(color: theme.colorScheme.primary.withValues(alpha: .12), borderRadius: BorderRadius.circular(12)),
            child: Icon(Icons.auto_awesome, color: theme.colorScheme.primary, size: 20),
          ),
          const SizedBox(height: 14),
          Expanded(
            child: ListView.builder(
              itemCount: FriendAppShell.items.length,
              itemBuilder: (context, i) {
                final item = FriendAppShell.items[i];
                final selected = i == index;
                return Padding(
                  padding: const EdgeInsets.symmetric(vertical: 2),
                  child: Tooltip(
                    message: compact ? item.label : '',
                    child: InkWell(
                      borderRadius: BorderRadius.circular(12),
                      onTap: () => onIndexChanged(i),
                      child: AnimatedContainer(
                        duration: const Duration(milliseconds: 160),
                        padding: EdgeInsets.symmetric(horizontal: compact ? 0 : 11, vertical: 10),
                        decoration: BoxDecoration(
                          color: selected ? theme.colorScheme.primary.withValues(alpha: .12) : Colors.transparent,
                          borderRadius: BorderRadius.circular(12),
                        ),
                        child: Row(
                          mainAxisAlignment: compact ? MainAxisAlignment.center : MainAxisAlignment.start,
                          children: [
                            Icon(item.icon, size: 20, color: selected ? theme.colorScheme.primary : theme.colorScheme.onSurfaceVariant),
                            if (!compact) ...[
                              const SizedBox(width: 10),
                              Expanded(child: Text(item.label, maxLines: 1, overflow: TextOverflow.ellipsis, style: TextStyle(fontSize: 13, fontWeight: selected ? FontWeight.w700 : FontWeight.w500))),
                            ],
                          ],
                        ),
                      ),
                    ),
                  ),
                );
              },
            ),
          ),
          Icon(Icons.settings_outlined, size: 19, color: theme.colorScheme.onSurfaceVariant),
        ],
      ),
    );
  }
}

class _Header extends StatelessWidget {
  const _Header({required this.teamCenter, required this.status, required this.compact});
  final Widget teamCenter;
  final Widget status;
  final bool compact;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Container(
      padding: EdgeInsets.symmetric(horizontal: compact ? 14 : 16, vertical: 12),
      decoration: BoxDecoration(
        color: theme.colorScheme.surface.withValues(alpha: .52),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: theme.colorScheme.outline.withValues(alpha: .08)),
      ),
      child: Row(
        children: [
          Expanded(
            child: Row(
              children: [
                Text('Friend', style: theme.textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w750)),
                if (!compact) ...[
                  const SizedBox(width: 10),
                  Container(width: 4, height: 4, decoration: BoxDecoration(color: theme.colorScheme.primary, shape: BoxShape.circle)),
                  const SizedBox(width: 8),
                  Text('Research workspace', style: theme.textTheme.bodySmall?.copyWith(color: theme.colorScheme.onSurfaceVariant)),
                ],
              ],
            ),
          ),
          if (!compact) ...[teamCenter, const SizedBox(width: 10)],
          status,
        ],
      ),
    );
  }
}
