import 'package:flutter/material.dart';

/// Futuristic ChatGPT-style navigation for the Research OS desktop shell.
/// Existing feature indices remain stable; staged items are visibly disabled
/// until their real workspace is implemented.
class ResearchOSSidebarV2 extends StatelessWidget {
  const ResearchOSSidebarV2({
    required this.expanded,
    required this.selectedIndex,
    required this.onToggle,
    required this.onSelected,
    super.key,
  });

  final bool expanded;
  final int selectedIndex;
  final VoidCallback onToggle;
  final ValueChanged<int> onSelected;

  static const compactWidth = 76.0;
  static const expandedWidth = 264.0;

  void _tap(BuildContext context, _Entry entry) {
    if (!entry.available) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('${entry.label} อยู่ในแผนงานถัดไป'),
          duration: const Duration(seconds: 2),
        ),
      );
      return;
    }
    onSelected(entry.index);
  }

  Widget _destination(BuildContext context, _Entry entry) {
    final scheme = Theme.of(context).colorScheme;
    final selected = entry.available && selectedIndex == entry.index;
    final foreground = entry.available
        ? (selected ? scheme.onSecondaryContainer : scheme.onSurfaceVariant)
        : scheme.onSurface.withValues(alpha: .38);

    return Padding(
      padding: EdgeInsets.symmetric(horizontal: expanded ? 10 : 8, vertical: 2),
      child: Material(
        color: selected ? scheme.secondaryContainer : Colors.transparent,
        borderRadius: BorderRadius.circular(13),
        child: InkWell(
          key: Key('v2-nav-${entry.keyName}'),
          borderRadius: BorderRadius.circular(13),
          onTap: () => _tap(context, entry),
          child: SizedBox(
            height: 43,
            child: Row(
              children: <Widget>[
                SizedBox(
                  width: expanded ? 44 : 58,
                  child: Icon(entry.icon, color: foreground, size: 21),
                ),
                if (expanded)
                  Expanded(
                    child: Text(
                      entry.label,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: TextStyle(
                        color: foreground,
                        fontWeight: selected ? FontWeight.w700 : FontWeight.w500,
                      ),
                    ),
                  ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _section(BuildContext context, String title) {
    if (!expanded) return const SizedBox(height: 8);
    return Padding(
      padding: const EdgeInsets.fromLTRB(18, 14, 18, 6),
      child: Text(
        title.toUpperCase(),
        style: Theme.of(context).textTheme.labelSmall?.copyWith(
              color: Theme.of(context).colorScheme.onSurfaceVariant,
              fontWeight: FontWeight.w800,
              letterSpacing: .8,
            ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    const workspace = <_Entry>[
      _Entry('search', 'Search', Icons.search_outlined, 0),
      _Entry('new-chat', 'New chat', Icons.add_comment_outlined, 1),
      _Entry('conversation', 'สนทนา AI', Icons.chat_bubble_outline, 1),
      _Entry('images', 'Images', Icons.image_outlined, 1, available: false),
      _Entry('library', 'Library', Icons.local_library_outlined, 3),
      _Entry('scheduled', 'Scheduled', Icons.schedule_outlined, 1, available: false),
      _Entry('plugins', 'Plugins', Icons.extension_outlined, 1, available: false),
      _Entry('projects', 'Projects', Icons.folder_outlined, 1, available: false),
    ];
    const account = <_Entry>[
      _Entry('pinned', 'Pinned', Icons.push_pin_outlined, 1, available: false),
      _Entry('recents', 'Recents', Icons.history_outlined, 1),
      _Entry('account', 'Account', Icons.account_circle_outlined, 9),
      _Entry('settings', 'Settings', Icons.settings_outlined, 9),
    ];

    return AnimatedContainer(
      key: const Key('research-os-sidebar-v2'),
      duration: const Duration(milliseconds: 220),
      curve: Curves.easeOutCubic,
      width: expanded ? expandedWidth : compactWidth,
      decoration: BoxDecoration(
        color: scheme.surface,
        border: Border(right: BorderSide(color: scheme.outlineVariant)),
      ),
      child: Column(
        children: <Widget>[
          SizedBox(
            height: 70,
            child: Padding(
              padding: EdgeInsets.symmetric(horizontal: expanded ? 14 : 8),
              child: Row(
                children: <Widget>[
                  const _ResearchMark(),
                  if (expanded) ...<Widget>[
                    const SizedBox(width: 10),
                    const Expanded(
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: <Widget>[
                          Text('Research OS', style: TextStyle(fontWeight: FontWeight.w800)),
                          Text('AI Operating Workspace', style: TextStyle(fontSize: 10.5)),
                        ],
                      ),
                    ),
                  ],
                  IconButton(
                    key: const Key('toggle-desktop-sidebar-v2'),
                    tooltip: expanded ? 'ย่อ Sidebar' : 'ขยาย Sidebar',
                    onPressed: onToggle,
                    icon: Icon(expanded ? Icons.chevron_left : Icons.chevron_right),
                  ),
                ],
              ),
            ),
          ),
          const Divider(height: 1),
          Expanded(
            child: ListView(
              padding: const EdgeInsets.symmetric(vertical: 6),
              children: <Widget>[
                _section(context, 'Workspace'),
                for (final entry in workspace) _destination(context, entry),
                _section(context, 'More'),
                _destination(context, const _Entry('more', 'More', Icons.more_horiz_outlined, 2)),
                _section(context, 'Account'),
                for (final entry in account) _destination(context, entry),
              ],
            ),
          ),
          Padding(
            padding: const EdgeInsets.fromLTRB(12, 6, 12, 12),
            child: Container(
              height: 42,
              decoration: BoxDecoration(
                color: scheme.surfaceContainerHighest,
                borderRadius: BorderRadius.circular(13),
              ),
              alignment: Alignment.center,
              child: expanded
                  ? Row(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: <Widget>[
                        Icon(Icons.shield_outlined, size: 17, color: scheme.primary),
                        const SizedBox(width: 8),
                        const Text('Local-first • secure', style: TextStyle(fontSize: 11)),
                      ],
                    )
                  : Icon(Icons.shield_outlined, size: 17, color: scheme.primary),
            ),
          ),
        ],
      ),
    );
  }
}

class _Entry {
  const _Entry(this.keyName, this.label, this.icon, this.index, {this.available = true});

  final String keyName;
  final String label;
  final IconData icon;
  final int index;
  final bool available;
}

class _ResearchMark extends StatelessWidget {
  const _ResearchMark();

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Container(
      width: 36,
      height: 36,
      alignment: Alignment.center,
      decoration: BoxDecoration(
        gradient: LinearGradient(colors: <Color>[scheme.primaryContainer, scheme.secondaryContainer]),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Text(
        'R',
        style: TextStyle(
          color: scheme.onPrimaryContainer,
          fontSize: 18,
          fontWeight: FontWeight.w900,
        ),
      ),
    );
  }
}
