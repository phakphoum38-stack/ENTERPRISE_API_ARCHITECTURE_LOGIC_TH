import 'package:flutter/material.dart';

enum RootClosureStatus { closed, repaired, verified, blocked, unknown }

class RootClosureNode {
  const RootClosureNode({
    required this.name,
    required this.status,
    required this.description,
  });

  final String name;
  final RootClosureStatus status;
  final String description;
}

class RootClosurePanel extends StatelessWidget {
  const RootClosurePanel({
    super.key,
    required this.runtimeObserved,
  });

  final bool runtimeObserved;

  List<RootClosureNode> get nodes => <RootClosureNode>[
        const RootClosureNode(
          name: 'SOURCE',
          status: RootClosureStatus.unknown,
          description: 'Authoritative repository/source identity must be bound.',
        ),
        const RootClosureNode(
          name: 'PROVENANCE',
          status: RootClosureStatus.unknown,
          description: 'Agent → run → PR → SHA lineage is not inferred from UI state.',
        ),
        const RootClosureNode(
          name: 'CHANGE',
          status: RootClosureStatus.unknown,
          description: 'Changed objects require exact-SHA correlation.',
        ),
        const RootClosureNode(
          name: 'SEMANTIC',
          status: RootClosureStatus.unknown,
          description: 'File → symbol → value → behavior semantics require evidence.',
        ),
        const RootClosureNode(
          name: 'CONSUMER',
          status: RootClosureStatus.unknown,
          description: 'Affected consumers and blast radius require lineage evidence.',
        ),
        const RootClosureNode(
          name: 'FAILURE',
          status: RootClosureStatus.unknown,
          description: 'Root versus cascade failure requires normalized CI evidence.',
        ),
        const RootClosureNode(
          name: 'REPAIR',
          status: RootClosureStatus.unknown,
          description: 'Repair must identify a bounded target and preserve authority.',
        ),
        const RootClosureNode(
          name: 'DIFF',
          status: RootClosureStatus.unknown,
          description: 'Semantic diff must explain what changed and why.',
        ),
        const RootClosureNode(
          name: 'REGRESSION',
          status: RootClosureStatus.unknown,
          description: 'Repair requires independent regression verification.',
        ),
        const RootClosureNode(
          name: 'GENERATED',
          status: RootClosureStatus.unknown,
          description: 'Generated artifacts require authoritative generation lineage.',
        ),
        const RootClosureNode(
          name: 'SUPERSEDED',
          status: RootClosureStatus.unknown,
          description: 'Superseded work must be traced before closure.',
        ),
        const RootClosureNode(
          name: 'DELETED',
          status: RootClosureStatus.unknown,
          description: 'Deleted implementations must be ruled out by lineage evidence.',
        ),
        const RootClosureNode(
          name: 'EVIDENCE',
          status: RootClosureStatus.unknown,
          description: 'Evidence must be fresh, bound, and independently verified.',
        ),
        const RootClosureNode(
          name: 'VERIFICATION',
          status: RootClosureStatus.unknown,
          description: 'Analyze/test/build results must bind to the same identity.',
        ),
        const RootClosureNode(
          name: 'AUTHORITY',
          status: RootClosureStatus.blocked,
          description: 'Approval, authorization, merge, and release remain external.',
        ),
      ];

  @override
  Widget build(BuildContext context) {
    final closed = nodes
        .where((node) => node.status == RootClosureStatus.closed)
        .length;
    final repaired = nodes
        .where((node) => node.status == RootClosureStatus.repaired)
        .length;
    final verified = nodes
        .where((node) => node.status == RootClosureStatus.verified)
        .length;
    final blocked = nodes
        .where((node) => node.status == RootClosureStatus.blocked)
        .length;
    final unknown = nodes
        .where((node) => node.status == RootClosureStatus.unknown)
        .length;

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: <Widget>[
            Row(
              children: <Widget>[
                const Icon(Icons.account_tree_outlined),
                const SizedBox(width: 10),
                Expanded(
                  child: Text(
                    'ROOT Closure Mesh',
                    style: Theme.of(context).textTheme.titleLarge?.copyWith(
                          fontWeight: FontWeight.w800,
                        ),
                  ),
                ),
                Chip(label: Text('CLOSED $closed/${nodes.length}')),
              ],
            ),
            const SizedBox(height: 6),
            const Text(
              'Canonical closure projection. UNKNOWN is preserved until source, lineage, '
              'repair, verification, and evidence are actually proven.',
            ),
            const SizedBox(height: 12),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: nodes
                  .map(
                    (node) => Tooltip(
                      message: node.description,
                      child: Chip(
                        avatar: Icon(_icon(node.status), size: 17),
                        label: Text(node.name),
                      ),
                    ),
                  )
                  .toList(),
            ),
            const SizedBox(height: 12),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: <Widget>[
                Text('REPAIRED $repaired'),
                Text('VERIFIED $verified'),
                Text('BLOCKED $blocked'),
                Text('UNKNOWN $unknown'),
              ],
            ),
            const Divider(height: 24),
            const Text(
              'Closure rule: CODE FIXED + DIFF CLOSED + EVIDENCE PROVEN + '
              'LINEAGE COMPLETE. Authority is never derived from observation.',
            ),
          ],
        ),
      ),
    );
  }

  IconData _icon(RootClosureStatus status) {
    switch (status) {
      case RootClosureStatus.closed:
        return Icons.check_circle_outline;
      case RootClosureStatus.repaired:
        return Icons.build_circle_outlined;
      case RootClosureStatus.verified:
        return Icons.verified_outlined;
      case RootClosureStatus.blocked:
        return Icons.lock_outline;
      case RootClosureStatus.unknown:
        return Icons.help_outline;
    }
  }
}
