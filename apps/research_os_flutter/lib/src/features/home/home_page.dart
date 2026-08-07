import 'package:flutter/material.dart';

import '../../api/research_os_api_client.dart';

class HomePage extends StatefulWidget {
  const HomePage({
    required this.apiClient,
    super.key,
  });

  final ResearchOSApiClient apiClient;

  @override
  State<HomePage> createState() => _HomePageState();
}

class _HomePageState extends State<HomePage> {
  bool _loading = true;
  String? _error;
  Map<String, dynamic>? _health;
  Map<String, dynamic>? _providers;

  @override
  void initState() {
    super.initState();
    _refresh();
  }

  Future<void> _refresh() async {
    setState(() {
      _loading = true;
      _error = null;
    });

    try {
      final results = await Future.wait<Map<String, dynamic>>(
        <Future<Map<String, dynamic>>>[
          widget.apiClient.getHealth(),
          widget.apiClient.getProviders(),
        ],
      );
      if (!mounted) return;
      setState(() {
        _health = results[0];
        _providers = results[1];
        _loading = false;
      });
    } on Object catch (error) {
      if (!mounted) return;
      setState(() {
        _error = error.toString();
        _loading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final activeProvider = _providers?['active']?.toString() ?? 'unknown';
    final apiStatus = _health?['status']?.toString() ?? 'offline';

    return Scaffold(
      appBar: AppBar(
        title: const Text('Research OS Home'),
        actions: <Widget>[
          IconButton(
            tooltip: 'Refresh',
            onPressed: _loading ? null : _refresh,
            icon: const Icon(Icons.refresh),
          ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: _refresh,
        child: ListView(
          padding: const EdgeInsets.all(20),
          children: <Widget>[
            Text(
              'บ้านของเรา',
              style: Theme.of(context).textTheme.headlineMedium,
            ),
            const SizedBox(height: 8),
            Text(
              'ศูนย์กลางสำหรับ Gemini, AI Memory, Knowledge และ GitHub',
              style: Theme.of(context).textTheme.bodyLarge,
            ),
            const SizedBox(height: 24),
            if (_loading) const LinearProgressIndicator(),
            if (_error != null)
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: <Widget>[
                      Text(
                        'เชื่อมต่อ Research OS API ไม่สำเร็จ',
                        style: Theme.of(context).textTheme.titleMedium,
                      ),
                      const SizedBox(height: 8),
                      Text(_error!),
                      const SizedBox(height: 12),
                      FilledButton.icon(
                        onPressed: _refresh,
                        icon: const Icon(Icons.refresh),
                        label: const Text('ลองใหม่'),
                      ),
                    ],
                  ),
                ),
              ),
            const SizedBox(height: 16),
            LayoutBuilder(
              builder: (context, constraints) {
                final columns = constraints.maxWidth >= 900
                    ? 3
                    : constraints.maxWidth >= 560
                        ? 2
                        : 1;
                return GridView.count(
                  crossAxisCount: columns,
                  shrinkWrap: true,
                  physics: const NeverScrollableScrollPhysics(),
                  mainAxisSpacing: 12,
                  crossAxisSpacing: 12,
                  mainAxisExtent: 104,
                  children: <Widget>[
                    _StatusCard(
                      icon: Icons.monitor_heart_outlined,
                      title: 'API Health',
                      value: apiStatus,
                    ),
                    _StatusCard(
                      icon: Icons.smart_toy_outlined,
                      title: 'Active Provider',
                      value: activeProvider,
                    ),
                    _StatusCard(
                      icon: Icons.memory_outlined,
                      title: 'AI Memory',
                      value: _health?['memory'] == true ? 'ready' : 'unknown',
                    ),
                  ],
                );
              },
            ),
            const SizedBox(height: 24),
            Text(
              'พื้นที่ทำงาน',
              style: Theme.of(context).textTheme.titleLarge,
            ),
            const SizedBox(height: 12),
            const _FeatureTile(
              icon: Icons.chat_bubble_outline,
              title: 'AI Chat',
              subtitle: 'สนทนากับ Gemini ผ่าน Research OS API',
            ),
            const _FeatureTile(
              icon: Icons.manage_search,
              title: 'AI Memory',
              subtitle: 'ค้นหาและใช้ความรู้จาก Research Artifacts',
            ),
            const _FeatureTile(
              icon: Icons.local_library_outlined,
              title: 'Library',
              subtitle: 'เปิดดูและค้นหาความรู้ใน Research OS',
            ),
            const _FeatureTile(
              icon: Icons.account_tree_outlined,
              title: 'GitHub Dashboard',
              subtitle: 'Workflow, commits, pull requests และ releases',
            ),
          ],
        ),
      ),
    );
  }
}

class _StatusCard extends StatelessWidget {
  const _StatusCard({
    required this.icon,
    required this.title,
    required this.value,
  });

  final IconData icon;
  final String title;
  final String value;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Row(
          children: <Widget>[
            Icon(icon, size: 32),
            const SizedBox(width: 14),
            Expanded(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                crossAxisAlignment: CrossAxisAlignment.start,
                children: <Widget>[
                  Text(
                    title,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: Theme.of(context).textTheme.labelLarge,
                  ),
                  const SizedBox(height: 2),
                  Text(
                    value,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: Theme.of(context).textTheme.titleMedium,
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _FeatureTile extends StatelessWidget {
  const _FeatureTile({
    required this.icon,
    required this.title,
    required this.subtitle,
  });

  final IconData icon;
  final String title;
  final String subtitle;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: ListTile(
        leading: Icon(icon),
        title: Text(title),
        subtitle: Text(subtitle),
        trailing: const Icon(Icons.chevron_right),
      ),
    );
  }
}
