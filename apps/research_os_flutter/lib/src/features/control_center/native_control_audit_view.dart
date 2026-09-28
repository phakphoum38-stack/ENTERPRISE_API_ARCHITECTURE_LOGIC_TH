import 'dart:convert';

import 'package:flutter/material.dart';

class NativeControlAuditSnapshot {
  const NativeControlAuditSnapshot({
    required this.auditId,
    required this.observedAt,
    required this.status,
    required this.checks,
    required this.source,
  });

  final String auditId;
  final DateTime observedAt;
  final String status;
  final List<Map<String, String>> checks;
  final String source;

  Map<String, Object?> toJson() => <String, Object?>{
        'audit_id': auditId,
        'observed_at': observedAt.toUtc().toIso8601String(),
        'status': status,
        'source': source,
        'checks': checks,
      };
}

class NativeControlAuditView extends StatelessWidget {
  const NativeControlAuditView({
    required this.health,
    required this.brain,
    required this.skills,
    required this.providers,
    required this.agents,
    required this.agentReadiness,
    required this.orchestrations,
    required this.snapshots,
    required this.onRun,
    super.key,
  });

  final Map<String, dynamic>? health;
  final Map<String, dynamic>? brain;
  final Map<String, dynamic>? skills;
  final Map<String, dynamic>? providers;
  final Map<String, dynamic>? agents;
  final Map<String, dynamic>? agentReadiness;
  final Map<String, dynamic>? orchestrations;
  final List<NativeControlAuditSnapshot> snapshots;
  final VoidCallback onRun;

  NativeControlAuditSnapshot buildSnapshot() {
    final checks = <Map<String, String>>[
      _check('Runtime', health?['status']?.toString() == 'ok'),
      _check('Brain capacity', brain != null && brain!.isNotEmpty),
      _check('Brain skills', skills != null && skills!.isNotEmpty),
      _check('Providers', providers != null && providers!.isNotEmpty),
      _check('Agents', agents != null && agents!.isNotEmpty),
      _check(
        'Agent readiness',
        (agentReadiness?['status'] ?? agentReadiness?['readiness']) != null,
      ),
      _check('Workflow observation', _runs().isNotEmpty),
      _unavailable('Offline package audit'),
      _unavailable('Installed baseline'),
      _unavailable('Release authority decision'),
    ];
    final hasFail = checks.any((item) => item['state'] == 'FAIL');
    final hasDeferred = checks.any((item) => item['state'] == 'DEFERRED');
    final now = DateTime.now().toUtc();
    return NativeControlAuditSnapshot(
      auditId: 'audit-${now.millisecondsSinceEpoch}',
      observedAt: now,
      status: hasFail ? 'FAIL' : (hasDeferred ? 'DEFERRED' : 'PASS'),
      checks: checks,
      source: 'Native Control Center existing observation surfaces',
    );
  }

  List<Map<String, dynamic>> _runs() {
    final raw = orchestrations?['runs'] ?? orchestrations?['orchestrations'];
    if (raw is! List) return <Map<String, dynamic>>[];
    return raw.whereType<Map>().map(Map<String, dynamic>.from).toList();
  }

  Map<String, String> _check(String name, bool pass) => <String, String>{
        'check': name,
        'state': pass ? 'PASS' : 'FAIL',
        'detail': pass ? 'Observed' : 'Required observation unavailable',
      };

  Map<String, String> _unavailable(String name) => <String, String>{
        'check': name,
        'state': 'DEFERRED',
        'detail': 'Not exposed by the current read-only API surface',
      };

  @override
  Widget build(BuildContext context) {
    final latest = snapshots.isEmpty ? null : snapshots.first;
    return ListView(
      padding: const EdgeInsets.all(16),
      children: <Widget>[
        Card(
          child: ListTile(
            leading: const Icon(Icons.fact_check_outlined),
            title: const Text('Main Final Audit'),
            subtitle: const Text(
              'Read-only audit projection inside the existing Native Control Center. '
              'It does not grant authority or replace Final Gate.',
            ),
            trailing: FilledButton.icon(
              onPressed: onRun,
              icon: const Icon(Icons.play_arrow),
              label: const Text('Run Audit'),
            ),
          ),
        ),
        if (latest != null) ...<Widget>[
          Card(
            child: ListTile(
              leading: Icon(
                latest.status == 'PASS'
                    ? Icons.check_circle_outline
                    : latest.status == 'FAIL'
                        ? Icons.error_outline
                        : Icons.pending_outlined,
              ),
              title: Text('Latest: ${latest.status}'),
              subtitle: Text(
                '${latest.auditId} • ${latest.observedAt.toLocal()}',
              ),
            ),
          ),
          ...latest.checks.map(
            (item) => Card(
              child: ListTile(
                leading: Icon(
                  item['state'] == 'PASS'
                      ? Icons.check
                      : item['state'] == 'FAIL'
                          ? Icons.close
                          : Icons.pause_circle_outline,
                ),
                title: Text(item['check'] ?? 'Check'),
                subtitle: Text(item['detail'] ?? ''),
                trailing: Text(item['state'] ?? 'UNKNOWN'),
              ),
            ),
          ),
          OutlinedButton.icon(
            onPressed: () => _showExport(context, latest),
            icon: const Icon(Icons.ios_share_outlined),
            label: const Text('Export Audit JSON'),
          ),
        ] else
          const Card(
            child: ListTile(
              leading: Icon(Icons.info_outline),
              title: Text('No audit snapshot yet'),
              subtitle: Text(
                'Run Audit to capture an observation snapshot.',
              ),
            ),
          ),
        if (snapshots.length > 1) ...<Widget>[
          const SizedBox(height: 8),
          Text(
            'Audit History (${snapshots.length})',
            style: Theme.of(context).textTheme.titleMedium,
          ),
          ...snapshots.skip(1).map(
            (snapshot) => ListTile(
              title: Text(snapshot.auditId),
              subtitle: Text(
                '${snapshot.status} • ${snapshot.observedAt.toLocal()}',
              ),
            ),
          ),
        ],
      ],
    );
  }

  void _showExport(BuildContext context, NativeControlAuditSnapshot snapshot) {
    final value = const JsonEncoder.withIndent('  ').convert(snapshot.toJson());
    showDialog<void>(
      context: context,
      builder: (_) => AlertDialog(
        title: const Text('Audit JSON'),
        content: SizedBox(
          width: 700,
          child: SingleChildScrollView(child: SelectableText(value)),
        ),
        actions: <Widget>[
          TextButton(
            onPressed: () => Navigator.of(context).pop(),
            child: const Text('Close'),
          ),
        ],
      ),
    );
  }
}
