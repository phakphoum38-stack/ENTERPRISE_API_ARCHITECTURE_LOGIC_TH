import 'package:flutter/material.dart';

class MissionControlDesktopPage extends StatelessWidget {
  const MissionControlDesktopPage({this.projection, super.key});

  final Map<String, dynamic>? projection;

  static const _allowedStatuses = <String>{
    'PASSED',
    'FAILED',
    'PENDING',
    'UNKNOWN',
    'BLOCKED',
    'READY_FOR_FINAL_GATE',
    'VERIFIED',
    'INVALID',
    'CONFLICT',
    'STALE',
  };

  @override
  Widget build(BuildContext context) {
    final data = projection == null ? const <String, dynamic>{} : Map<String, dynamic>.from(projection!);
    final readOnly = data['read_only'] == true;
    final owner = data['owner_id']?.toString();
    final summary = data['state_summary'] is Map
        ? Map<String, dynamic>.from(data['state_summary'] as Map)
        : const <String, dynamic>{};
    final panels = data['panels'] is List ? List<Object?>.from(data['panels'] as List) : const <Object?>[];
    final truncation = data['truncation'] is Map
        ? Map<String, dynamic>.from(data['truncation'] as Map)
        : const <String, dynamic>{};

    return LayoutBuilder(
      builder: (context, constraints) {
        final compact = constraints.maxWidth < 900;
        return ListView(
          padding: EdgeInsets.fromLTRB(compact ? 2 : 8, 2, compact ? 2 : 8, 20),
          children: [
            _PageHeader(owner: owner, readOnly: readOnly, compact: compact),
            const SizedBox(height: 14),
            _StateSummary(summary: summary),
            const SizedBox(height: 14),
            if (panels.isEmpty)
              const _EmptyProjectionState()
            else
              ...panels.whereType<Map>().map((panel) => _PanelCard(panel: Map<String, dynamic>.from(panel))),
            if (truncation.isNotEmpty) ...[
              const SizedBox(height: 4),
              _TruncationNotice(value: truncation),
            ],
          ],
        );
      },
    );
  }

  static String safeStatus(Object? value) {
    final status = value?.toString() ?? 'UNKNOWN';
    return _allowedStatuses.contains(status) ? status : 'UNKNOWN';
  }
}

class _PageHeader extends StatelessWidget {
  const _PageHeader({required this.owner, required this.readOnly, required this.compact});
  final String? owner;
  final bool readOnly;
  final bool compact;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text('Mission Control', style: theme.textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.w700)),
              const SizedBox(height: 3),
              Text(
                owner == null || owner!.isEmpty ? 'Waiting for a validated Phase 4I projection' : 'Owner: $owner',
                style: theme.textTheme.bodySmall?.copyWith(color: theme.colorScheme.onSurfaceVariant),
              ),
            ],
          ),
        ),
        if (!compact) const SizedBox(width: 12),
        _ReadOnlyBadge(enabled: readOnly),
      ],
    );
  }
}

class _ReadOnlyBadge extends StatelessWidget {
  const _ReadOnlyBadge({required this.enabled});
  final bool enabled;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final label = enabled ? 'READ ONLY' : 'INVALID PROJECTION';
    return Container(
      key: const Key('mission-control-read-only'),
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 7),
      decoration: BoxDecoration(
        color: theme.colorScheme.surfaceContainerLow,
        borderRadius: BorderRadius.circular(999),
        border: Border.all(color: theme.colorScheme.outline.withValues(alpha: .10)),
      ),
      child: Row(mainAxisSize: MainAxisSize.min, children: [
        Icon(enabled ? Icons.lock_outline : Icons.warning_amber_outlined, size: 15),
        const SizedBox(width: 6),
        Text(label, style: theme.textTheme.labelSmall?.copyWith(fontWeight: FontWeight.w700)),
      ]),
    );
  }
}

class _StateSummary extends StatelessWidget {
  const _StateSummary({required this.summary});
  final Map<String, dynamic> summary;

  @override
  Widget build(BuildContext context) {
    final gate = MissionControlDesktopPage.safeStatus(summary['gate_status']);
    final build = MissionControlDesktopPage.safeStatus(summary['build_identity_status']);
    return Wrap(
      spacing: 10,
      runSpacing: 10,
      children: [
        _StatusCard(title: 'Authoritative Gate', value: gate),
        _StatusCard(title: 'Build / Release Identity', value: build),
        const _StatusCard(title: 'Execution Authority', value: 'NONE'),
      ],
    );
  }
}

class _StatusCard extends StatelessWidget {
  const _StatusCard({required this.title, required this.value});
  final String title;
  final String value;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return SizedBox(
      width: 230,
      child: Card(
        child: Padding(
          padding: const EdgeInsets.all(14),
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text(title, style: theme.textTheme.labelMedium?.copyWith(color: theme.colorScheme.onSurfaceVariant)),
            const SizedBox(height: 8),
            Text(value, key: Key('mission-status-$value'), style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w700)),
          ]),
        ),
      ),
    );
  }
}

class _PanelCard extends StatelessWidget {
  const _PanelCard({required this.panel});
  final Map<String, dynamic> panel;

  @override
  Widget build(BuildContext context) {
    final type = panel['type']?.toString() ?? 'text';
    final title = panel['title']?.toString() ?? panel['id']?.toString() ?? 'Panel';
    return Card(
      key: Key('mission-panel-${panel['id'] ?? title}'),
      margin: const EdgeInsets.only(bottom: 12),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Text(title, style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w700)),
          const SizedBox(height: 10),
          _PanelBody(type: type, panel: panel),
        ]),
      ),
    );
  }
}

class _PanelBody extends StatelessWidget {
  const _PanelBody({required this.type, required this.panel});
  final String type;
  final Map<String, dynamic> panel;

  @override
  Widget build(BuildContext context) {
    switch (type) {
      case 'metric':
        return Text(panel['value']?.toString() ?? 'UNKNOWN', style: Theme.of(context).textTheme.headlineSmall);
      case 'status':
        return _StatusLine(value: MissionControlDesktopPage.safeStatus(panel['value']));
      case 'table':
        return _BoundedList(values: panel['rows']);
      case 'timeline':
        return _BoundedList(values: panel['steps']);
      case 'capability-health':
        return _BoundedList(values: panel['items']);
      case 'text':
      default:
        return SelectableText(panel['value']?.toString() ?? 'UNKNOWN');
    }
  }
}

class _StatusLine extends StatelessWidget {
  const _StatusLine({required this.value});
  final String value;

  @override
  Widget build(BuildContext context) => Row(mainAxisSize: MainAxisSize.min, children: [
        const Icon(Icons.circle, size: 9),
        const SizedBox(width: 8),
        Text(value, key: Key('mission-panel-status-$value'), style: const TextStyle(fontWeight: FontWeight.w700)),
      ]);
}

class _BoundedList extends StatelessWidget {
  const _BoundedList({required this.values});
  final Object? values;

  @override
  Widget build(BuildContext context) {
    if (values is! List || values.isEmpty) return const Text('No data available');
    final items = (values as List).take(100).toList(growable: false);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: items.map((item) => Padding(
        padding: const EdgeInsets.symmetric(vertical: 4),
        child: Text(item is Map ? item.values.map((value) => value.toString()).join(' • ') : item.toString()),
      )).toList(growable: false),
    );
  }
}

class _TruncationNotice extends StatelessWidget {
  const _TruncationNotice({required this.value});
  final Map<String, dynamic> value;

  @override
  Widget build(BuildContext context) => Card(
        key: const Key('mission-control-truncation'),
        child: ListTile(
          leading: const Icon(Icons.data_array_outlined),
          title: const Text('Some source data is truncated'),
          subtitle: Text(value.entries.map((entry) => '${entry.key}: ${entry.value}').join(' • ')),
        ),
      );
}

class _EmptyProjectionState extends StatelessWidget {
  const _EmptyProjectionState();

  @override
  Widget build(BuildContext context) => Card(
        key: const Key('mission-control-empty'),
        child: const Padding(
          padding: EdgeInsets.all(28),
          child: Column(children: [
            Icon(Icons.dashboard_outlined, size: 34),
            SizedBox(height: 10),
            Text('Mission Control is waiting for validated state.'),
            SizedBox(height: 4),
            Text('No execution action is available from this surface.'),
          ]),
        ),
      );
}
