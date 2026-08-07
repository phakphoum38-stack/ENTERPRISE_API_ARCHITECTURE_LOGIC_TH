import 'dart:async';

import 'package:flutter/material.dart';

import '../../api/research_os_api_client.dart';

class SystemMonitorPage extends StatefulWidget {
  const SystemMonitorPage({required this.apiClient, super.key});

  final ResearchOSApiClient apiClient;

  @override
  State<SystemMonitorPage> createState() => _SystemMonitorPageState();
}

class _SystemMonitorPageState extends State<SystemMonitorPage> {
  bool _loading = true;
  String? _error;
  Map<String, dynamic> _health = const <String, dynamic>{};
  Map<String, dynamic> _providers = const <String, dynamic>{};
  Map<String, dynamic> _github = const <String, dynamic>{};
  int _responseTimeMs = 0;
  DateTime? _lastCheckedAt;
  Timer? _timer;

  bool get _isLocalApi {
    final uri = Uri.tryParse(widget.apiClient.baseUrl);
    if (uri == null) return false;
    return uri.host == '127.0.0.1' ||
        uri.host == 'localhost' ||
        uri.host.startsWith('192.168.') ||
        uri.host.startsWith('10.') ||
        uri.host.startsWith('172.16.') ||
        uri.host.startsWith('172.17.') ||
        uri.host.startsWith('172.18.') ||
        uri.host.startsWith('172.19.') ||
        uri.host.startsWith('172.2') ||
        uri.host.startsWith('172.30.') ||
        uri.host.startsWith('172.31.');
  }

  @override
  void initState() {
    super.initState();
    _refresh();
    _timer = Timer.periodic(const Duration(seconds: 30), (_) {
      if (mounted && !_loading) _refresh(silent: true);
    });
  }

  @override
  void dispose() {
    _timer?.cancel();
    super.dispose();
  }

  Future<void> _refresh({bool silent = false}) async {
    if (!silent) {
      setState(() {
        _loading = true;
        _error = null;
      });
    }

    final stopwatch = Stopwatch()..start();
    try {
      final results = await Future.wait<Map<String, dynamic>>(<Future<Map<String, dynamic>>>[
        widget.apiClient.getHealth(),
        widget.apiClient.getProviders(),
        widget.apiClient.getGitHubDashboard(),
      ]);
      stopwatch.stop();
      if (!mounted) return;
      setState(() {
        _health = results[0];
        _providers = results[1];
        _github = results[2];
        _responseTimeMs = stopwatch.elapsedMilliseconds;
        _lastCheckedAt = DateTime.now();
        _loading = false;
        _error = null;
      });
    } on Object catch (error) {
      stopwatch.stop();
      if (!mounted) return;
      setState(() {
        _error = error.toString();
        _responseTimeMs = stopwatch.elapsedMilliseconds;
        _lastCheckedAt = DateTime.now();
        _loading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final workflows = _github['workflow_runs'];
    final latestWorkflow = workflows is List && workflows.isNotEmpty && workflows.first is Map
        ? Map<String, dynamic>.from(workflows.first as Map)
        : const <String, dynamic>{};

    return Scaffold(
      appBar: AppBar(
        title: const Text('System Monitor'),
        actions: <Widget>[
          IconButton(
            tooltip: 'รีเฟรชสถานะระบบ',
            onPressed: _loading ? null : _refresh,
            icon: const Icon(Icons.refresh),
          ),
        ],
      ),
      body: ListView(
        padding: const EdgeInsets.all(20),
        children: <Widget>[
          Text('ศูนย์ตรวจสอบระบบ', style: Theme.of(context).textTheme.headlineMedium),
          const SizedBox(height: 8),
          const Text('ตรวจ API, Provider, Memory, GitHub Actions และเวลาตอบสนองจากจุดเดียว'),
          const SizedBox(height: 12),
          Card(
            child: ListTile(
              leading: Icon(_isLocalApi ? Icons.computer_outlined : Icons.cloud_outlined),
              title: Text(_isLocalApi ? 'Local API' : 'Cloud API'),
              subtitle: SelectableText(widget.apiClient.baseUrl),
              trailing: Chip(label: Text(_isLocalApi ? 'Local-first' : 'Remote')),
            ),
          ),
          const SizedBox(height: 20),
          if (_loading) const LinearProgressIndicator(),
          if (_error != null)
            Card(
              child: ListTile(
                leading: const Icon(Icons.error_outline),
                title: const Text('ตรวจสอบระบบไม่สำเร็จ'),
                subtitle: Text(_error!),
                trailing: IconButton(onPressed: _refresh, icon: const Icon(Icons.refresh)),
              ),
            ),
          if (!_loading && _error == null)
            LayoutBuilder(
              builder: (context, constraints) {
                final width = constraints.maxWidth >= 900
                    ? (constraints.maxWidth - 36) / 4
                    : constraints.maxWidth >= 560
                        ? (constraints.maxWidth - 12) / 2
                        : constraints.maxWidth;
                return Wrap(
                  spacing: 12,
                  runSpacing: 12,
                  children: <Widget>[
                    _MonitorCard(
                      width: width,
                      title: 'API',
                      value: _health['status']?.toString() ?? 'unknown',
                      detail: '${_health['service'] ?? 'research-os-api'} • v${_health['version'] ?? '-'}',
                      icon: Icons.dns_outlined,
                    ),
                    _MonitorCard(
                      width: width,
                      title: 'Provider',
                      value: _providers['active']?.toString() ?? 'unknown',
                      detail: 'AI provider ที่กำลังใช้งาน',
                      icon: Icons.smart_toy_outlined,
                    ),
                    _MonitorCard(
                      width: width,
                      title: 'Memory',
                      value: _health['memory'] == true ? 'ready' : 'unavailable',
                      detail: _health['memory_commit'] == true
                          ? 'Memory + explicit commit ready'
                          : 'Knowledge memory service',
                      icon: Icons.memory_outlined,
                    ),
                    _MonitorCard(
                      width: width,
                      title: 'Response Time',
                      value: '$_responseTimeMs ms',
                      detail: _responseTimeMs <= 1000
                          ? 'ตอบสนองเร็ว'
                          : _responseTimeMs <= 5000
                              ? 'ตอบสนองปานกลาง'
                              : 'ตอบสนองช้า',
                      icon: Icons.speed_outlined,
                    ),
                  ],
                );
              },
            ),
          if (!_loading && _error == null) ...<Widget>[
            const SizedBox(height: 24),
            Text('GitHub Actions ล่าสุด', style: Theme.of(context).textTheme.titleLarge),
            const SizedBox(height: 8),
            Card(
              child: ListTile(
                leading: const Icon(Icons.account_tree_outlined),
                title: Text(latestWorkflow['name']?.toString() ?? 'ยังไม่มีข้อมูล Workflow'),
                subtitle: Text(
                  'สถานะ: ${latestWorkflow['status'] ?? 'unknown'} • ผลลัพธ์: ${latestWorkflow['conclusion'] ?? 'unknown'}',
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                ),
              ),
            ),
            const SizedBox(height: 12),
            Text(
              'ตรวจอัตโนมัติทุก 30 วินาที • ล่าสุด: ${_lastCheckedAt?.toLocal() ?? '-'}',
              style: Theme.of(context).textTheme.bodySmall,
            ),
          ],
        ],
      ),
    );
  }
}

class _MonitorCard extends StatelessWidget {
  const _MonitorCard({
    required this.width,
    required this.title,
    required this.value,
    required this.detail,
    required this.icon,
  });

  final double width;
  final String title;
  final String value;
  final String detail;
  final IconData icon;

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: width,
      child: Card(
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Row(
            children: <Widget>[
              Icon(icon, size: 30),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: <Widget>[
                    Text(title, maxLines: 1, overflow: TextOverflow.ellipsis),
                    Text(value, style: Theme.of(context).textTheme.titleLarge, maxLines: 1, overflow: TextOverflow.ellipsis),
                    Text(detail, maxLines: 2, overflow: TextOverflow.ellipsis),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
