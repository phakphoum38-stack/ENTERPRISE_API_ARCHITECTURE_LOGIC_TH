import 'package:flutter/material.dart';

import 'v5_capability.dart';
import 'v5_workspace_route.dart';

class ResearchOSAdaptiveNavigation extends StatelessWidget {
  const ResearchOSAdaptiveNavigation({
    required this.level,
    required this.selected,
    required this.onSelected,
    this.compact = false,
    super.key,
  });

  final ResearchOSUserLevel level;
  final ResearchOSWorkspace selected;
  final ValueChanged<ResearchOSWorkspace> onSelected;
  final bool compact;

  @override
  Widget build(BuildContext context) {
    final routes = const ResearchOSWorkspaceRoutes().visibleFor(level);
    final grouped = <String, List<ResearchOSWorkspaceRoute>>{
      'Work': <ResearchOSWorkspaceRoute>[],
      'Knowledge': <ResearchOSWorkspaceRoute>[],
      'System': <ResearchOSWorkspaceRoute>[],
    };

    for (final route in routes) {
      final group = switch (route.workspace) {
        ResearchOSWorkspace.friend ||
        ResearchOSWorkspace.research ||
        ResearchOSWorkspace.developer ||
        ResearchOSWorkspace.brain ||
        ResearchOSWorkspace.factory => 'Work',
        ResearchOSWorkspace.memory ||
        ResearchOSWorkspace.library ||
        ResearchOSWorkspace.evidence => 'Knowledge',
        ResearchOSWorkspace.identity ||
        ResearchOSWorkspace.owner ||
        ResearchOSWorkspace.settings => 'System',
      };
      grouped[group]!.add(route);
    }

    return ListView(
      padding: const EdgeInsets.symmetric(vertical: 10),
      children: <Widget>[
        for (final entry in grouped.entries)
          if (entry.value.isNotEmpty) ...<Widget>[
            if (!compact)
              Padding(
                padding: const EdgeInsets.fromLTRB(18, 12, 18, 6),
                child: Text(
                  entry.key.toUpperCase(),
                  style: Theme.of(context).textTheme.labelSmall?.copyWith(
                        fontWeight: FontWeight.w700,
                        letterSpacing: .7,
                      ),
                ),
              ),
            for (final route in entry.value)
              Padding(
                padding: EdgeInsets.symmetric(horizontal: compact ? 8 : 10, vertical: 2),
                child: Tooltip(
                  message: compact ? route.label : '',
                  child: ListTile(
                    dense: true,
                    selected: selected == route.workspace,
                    leading: Icon(route.icon),
                    title: compact ? null : Text(route.label),
                    horizontalTitleGap: compact ? 0 : 10,
                    contentPadding: EdgeInsets.symmetric(horizontal: compact ? 12 : 10),
                    onTap: () => onSelected(route.workspace),
                  ),
                ),
              ),
          ],
      ],
    );
  }
}
