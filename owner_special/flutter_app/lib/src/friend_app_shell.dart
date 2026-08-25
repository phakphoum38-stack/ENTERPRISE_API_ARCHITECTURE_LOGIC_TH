import 'package:flutter/material.dart';

class FriendAppShell extends StatelessWidget {
  const FriendAppShell({required this.index, required this.onIndexChanged, required this.pages, required this.teamCenter, required this.status, super.key});
  final int index;
  final ValueChanged<int> onIndexChanged;
  final List<Widget> pages;
  final Widget teamCenter;
  final Widget status;

  static const items = <({IconData icon, String label})>[
    (icon: Icons.dashboard_outlined, label: 'Dashboard'),
    (icon: Icons.chat_bubble_outline, label: 'Friend Chat'),
    (icon: Icons.auto_awesome_outlined, label: 'Skills & Tools'),
    (icon: Icons.smart_toy_outlined, label: 'Agents'),
    (icon: Icons.memory_outlined, label: 'Memory'),
    (icon: Icons.fact_check_outlined, label: 'Evidence'),
    (icon: Icons.settings_outlined, label: 'Settings'),
  ];

  @override
  Widget build(BuildContext context) {
    final safeIndex = index.clamp(0, pages.length - 1).toInt();
    return Material(
      color: Theme.of(context).scaffoldBackgroundColor,
      child: SafeArea(
        child: LayoutBuilder(
          builder: (context, constraints) {
            final compact = constraints.maxWidth < 1000;
            return Row(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                _Sidebar(index: safeIndex, onIndexChanged: onIndexChanged, compact: compact),
                Expanded(
                  child: Padding(
                    padding: EdgeInsets.fromLTRB(compact ? 12 : 36, compact ? 12 : 28, compact ? 12 : 36, compact ? 12 : 28),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.stretch,
                      children: [
                        _Header(teamCenter: teamCenter, status: status, compact: compact),
                        const SizedBox(height: 18),
                        Expanded(child: pages[safeIndex]),
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
    final primary = theme.colorScheme.primary;
    return Container(
      width: compact ? 76 : 238,
      margin: EdgeInsets.fromLTRB(compact ? 8 : 0, 0, compact ? 8 : 0, 0),
      padding: EdgeInsets.fromLTRB(compact ? 8 : 18, 22, compact ? 8 : 18, 18),
      decoration: BoxDecoration(
        color: theme.colorScheme.surface,
        border: Border(right: BorderSide(color: theme.dividerColor.withValues(alpha: .45))),
      ),
      child: Column(
        crossAxisAlignment: compact ? CrossAxisAlignment.center : CrossAxisAlignment.stretch,
        children: [
          if (compact)
            Icon(Icons.hub_outlined, color: primary, size: 30)
          else ...[
            Text('RESEARCH OS', style: theme.textTheme.titleMedium?.copyWith(letterSpacing: 1.2)),
            const SizedBox(height: 4),
            Text('Friend Runtime v3.4', style: theme.textTheme.bodySmall),
          ],
          const SizedBox(height: 32),
          Expanded(
            child: ListView.builder(
              itemCount: FriendAppShell.items.length,
              itemBuilder: (context, i) {
                final item = FriendAppShell.items[i];
                final selected = i == index;
                final child = Container(
                  height: 42,
                  padding: EdgeInsets.symmetric(horizontal: compact ? 0 : 16),
                  alignment: compact ? Alignment.center : Alignment.centerLeft,
                  decoration: BoxDecoration(
                    color: selected ? primary.withValues(alpha: .14) : Colors.transparent,
                    borderRadius: BorderRadius.circular(9),
                  ),
                  child: Row(
                    mainAxisAlignment: compact ? MainAxisAlignment.center : MainAxisAlignment.start,
                    children: [
                      Icon(item.icon, size: 19, color: selected ? primary : theme.colorScheme.onSurfaceVariant),
                      if (!compact) ...[
                        const SizedBox(width: 12),
                        Expanded(child: Text(item.label, maxLines: 1, overflow: TextOverflow.ellipsis, style: theme.textTheme.bodyMedium?.copyWith(fontWeight: selected ? FontWeight.w600 : FontWeight.w400))),
                      ],
                    ],
                  ),
                );
                return Padding(
                  padding: const EdgeInsets.only(bottom: 6),
                  child: InkWell(borderRadius: BorderRadius.circular(9), onTap: () => onIndexChanged(i), child: child),
                );
              },
            ),
          ),
          _EngineCard(compact: compact),
        ],
      ),
    );
  }
}

class _EngineCard extends StatelessWidget {
  const _EngineCard({required this.compact});
  final bool compact;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final semantic = theme.extension<FriendSemanticColors>()!;
    return Container(
      padding: EdgeInsets.all(compact ? 10 : 16),
      decoration: BoxDecoration(color: theme.colorScheme.surfaceContainerHighest, borderRadius: BorderRadius.circular(10)),
      child: compact
          ? Icon(Icons.bolt, color: semantic.success)
          : Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Text('6^6 Engine', style: theme.textTheme.bodyMedium?.copyWith(fontWeight: FontWeight.w600)),
              const SizedBox(height: 3),
              Row(children: [Text('READY', style: theme.textTheme.bodySmall?.copyWith(color: semantic.success, fontWeight: FontWeight.w700)), const Spacer(), Expanded(child: Text('46,656 logical capacity', maxLines: 1, overflow: TextOverflow.ellipsis, textAlign: TextAlign.end, style: theme.textTheme.bodySmall))]),
            ]),
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
    return Wrap(
      alignment: WrapAlignment.spaceBetween,
      crossAxisAlignment: WrapCrossAlignment.center,
      spacing: 12,
      runSpacing: 12,
      children: [
        if (!compact) teamCenter,
        status,
        if (compact) ConstrainedBox(constraints: const BoxConstraints(maxWidth: 220), child: teamCenter),
      ],
    );
  }
}
