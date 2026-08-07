import 'package:flutter/material.dart';

import '../../api/research_os_api_client.dart';

class KnowledgeGraphPage extends StatefulWidget {
  const KnowledgeGraphPage({required this.apiClient, super.key});

  final ResearchOSApiClient apiClient;

  @override
  State<KnowledgeGraphPage> createState() => _KnowledgeGraphPageState();
}

class _KnowledgeGraphPageState extends State<KnowledgeGraphPage> {
  bool _loading = true;
  String? _error;
  List<Map<String, dynamic>> _nodes = const <Map<String, dynamic>>[];
  List<Map<String, dynamic>> _edges = const <Map<String, dynamic>>[];

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final payload = await widget.apiClient.getKnowledgeGraph();
      if (!mounted) return;
      setState(() {
        _nodes = _mapList(payload['nodes']);
        _edges = _mapList(payload['edges']);
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

  List<Map<String, dynamic>> _mapList(Object? value) {
    if (value is! List) return const <Map<String, dynamic>>[];
    return value
        .whereType<Map>()
        .map((item) => Map<String, dynamic>.from(item))
        .toList();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('แผนผังความรู้'),
        actions: <Widget>[
          IconButton(
            tooltip: 'รีเฟรชแผนผัง',
            onPressed: _loading ? null : _load,
            icon: const Icon(Icons.refresh),
          ),
        ],
      ),
      body: ListView(
        padding: const EdgeInsets.all(20),
        children: <Widget>[
          Text(
            'Knowledge Graph',
            key: const Key('knowledge-graph-heading'),
            style: Theme.of(context).textTheme.headlineMedium,
          ),
          const SizedBox(height: 8),
          Text(
            'ดูโหนดความรู้และความสัมพันธ์ระหว่าง Research Artifacts',
            style: Theme.of(context).textTheme.bodyLarge,
          ),
          const SizedBox(height: 20),
          if (_loading) const LinearProgressIndicator(),
          if (_error != null)
            Card(
              child: ListTile(
                leading: const Icon(Icons.error_outline),
                title: const Text('โหลดแผนผังไม่สำเร็จ'),
                subtitle: Text(_error!),
                trailing: IconButton(
                  onPressed: _load,
                  icon: const Icon(Icons.refresh),
                ),
              ),
            ),
          if (!_loading && _error == null) ...<Widget>[
            LayoutBuilder(
              builder: (context, constraints) {
                final width = constraints.maxWidth >= 520
                    ? (constraints.maxWidth - 12) / 2
                    : constraints.maxWidth;
                return Wrap(
                  spacing: 12,
                  runSpacing: 12,
                  children: <Widget>[
                    _CountCard(
                      width: width,
                      label: 'Knowledge Nodes',
                      value: _nodes.length,
                      icon: Icons.hub_outlined,
                    ),
                    _CountCard(
                      width: width,
                      label: 'Relationships',
                      value: _edges.length,
                      icon: Icons.link,
                    ),
                  ],
                );
              },
            ),
            const SizedBox(height: 24),
            Text('โหนดความรู้', style: Theme.of(context).textTheme.titleLarge),
            const SizedBox(height: 8),
            if (_nodes.isEmpty)
              const Card(child: ListTile(title: Text('ยังไม่มีโหนดความรู้'))),
            ..._nodes.map(
              (node) => Card(
                child: ListTile(
                  leading: const CircleAvatar(
                    child: Icon(Icons.description_outlined),
                  ),
                  title: Text(
                    node['title']?.toString().isNotEmpty == true
                        ? node['title'].toString()
                        : node['id']?.toString() ?? 'Unknown',
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                  ),
                  subtitle: Text(
                    '${node['id'] ?? ''}\nสถานะ: ${node['status'] ?? 'unknown'}',
                  ),
                  isThreeLine: true,
                ),
              ),
            ),
            const SizedBox(height: 20),
            Text('ความสัมพันธ์', style: Theme.of(context).textTheme.titleLarge),
            const SizedBox(height: 8),
            if (_edges.isEmpty)
              const Card(child: ListTile(title: Text('ยังไม่มีความสัมพันธ์'))),
            ..._edges.map(
              (edge) => Card(
                child: ListTile(
                  leading: const Icon(Icons.arrow_forward),
                  title: Text(
                    '${edge['source'] ?? '?'} → ${edge['target'] ?? '?'}',
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                  ),
                  subtitle: Text('ประเภท: ${edge['relation'] ?? 'related'}'),
                ),
              ),
            ),
          ],
        ],
      ),
    );
  }
}

class _CountCard extends StatelessWidget {
  const _CountCard({
    required this.width,
    required this.label,
    required this.value,
    required this.icon,
  });

  final double width;
  final String label;
  final int value;
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
                  mainAxisSize: MainAxisSize.min,
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: <Widget>[
                    Text(
                      label,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                    Text(
                      '$value',
                      style: Theme.of(context).textTheme.headlineSmall,
                    ),
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
