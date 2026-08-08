import 'package:flutter/material.dart';

import '../../api/research_os_api_client.dart';
import '../../ui/enterprise_components.dart';

class MemoryInspectorPage extends StatefulWidget {
  const MemoryInspectorPage({required this.apiClient, super.key});

  final ResearchOSApiClient apiClient;

  @override
  State<MemoryInspectorPage> createState() => _MemoryInspectorPageState();
}

class _MemoryInspectorPageState extends State<MemoryInspectorPage> {
  final TextEditingController _searchController = TextEditingController();
  List<Map<String, dynamic>> _records = const <Map<String, dynamic>>[];
  bool _loading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _load();
  }

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  Future<void> _load() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final query = _searchController.text.trim();
      final response = query.isEmpty
          ? await widget.apiClient.getRuntimeMemory()
          : await widget.apiClient.searchRuntimeMemory(query);
      final raw = query.isEmpty ? response['records'] : response['hits'];
      final records = <Map<String, dynamic>>[];
      if (raw is List) {
        for (final item in raw) {
          if (item is Map) {
            final map = Map<String, dynamic>.from(item);
            final nested = map['record'];
            if (nested is Map) {
              records.add(Map<String, dynamic>.from(nested));
            } else {
              records.add(map);
            }
          }
        }
      }
      if (!mounted) return;
      setState(() => _records = records);
    } on Object catch (error) {
      if (!mounted) return;
      setState(() => _error = error.toString());
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _delete(Map<String, dynamic> record) async {
    final id = record['id']?.toString() ?? '';
    if (id.isEmpty) return;
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('ลบ Memory นี้?'),
        content: const Text(
          'รายการนี้จะถูกลบออกจาก Runtime Memory ในเครื่อง และจะไม่ถูกส่งขึ้น Cloud อัตโนมัติ',
        ),
        actions: <Widget>[
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('ยกเลิก'),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(context, true),
            child: const Text('ลบ'),
          ),
        ],
      ),
    );
    if (confirmed != true) return;
    try {
      await widget.apiClient.deleteRuntimeMemory(id);
      await _load();
    } on Object catch (error) {
      if (mounted) setState(() => _error = error.toString());
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Memory Inspector')),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(20),
          child: Column(
            children: <Widget>[
              EnterprisePageHeader(
                title: 'Memory Inspector',
                subtitle: 'ดู ค้นหา และลบ Runtime Memory ที่เก็บแบบ local-first',
                icon: Icons.memory_outlined,
                actions: <Widget>[
                  IconButton(
                    tooltip: 'รีเฟรช',
                    onPressed: _loading ? null : _load,
                    icon: const Icon(Icons.refresh),
                  ),
                ],
              ),
              const SizedBox(height: 14),
              TextField(
                key: const Key('memory-inspector-search'),
                controller: _searchController,
                textInputAction: TextInputAction.search,
                onSubmitted: (_) => _load(),
                decoration: InputDecoration(
                  hintText: 'ค้นหา Memory…',
                  prefixIcon: const Icon(Icons.search),
                  suffixIcon: IconButton(
                    tooltip: 'ค้นหา',
                    onPressed: _loading ? null : _load,
                    icon: const Icon(Icons.arrow_forward),
                  ),
                  border: const OutlineInputBorder(),
                ),
              ),
              if (_error != null) ...<Widget>[
                const SizedBox(height: 10),
                Card(
                  child: ListTile(
                    leading: const Icon(Icons.error_outline),
                    title: const Text('Memory status'),
                    subtitle: Text(_error!),
                  ),
                ),
              ],
              const SizedBox(height: 12),
              Expanded(
                child: _loading
                    ? const Center(child: CircularProgressIndicator())
                    : _records.isEmpty
                        ? const Center(
                            child: Text('ยังไม่มี Runtime Memory ที่ตรงกับรายการนี้'),
                          )
                        : ListView.separated(
                            itemCount: _records.length,
                            separatorBuilder: (_, __) => const SizedBox(height: 8),
                            itemBuilder: (context, index) {
                              final record = _records[index];
                              final title = record['title']?.toString().trim();
                              final content = record['content']?.toString() ?? '';
                              final type = record['type']?.toString() ?? 'memory';
                              final source = record['source']?.toString() ?? 'unknown';
                              final provider = record['provider']?.toString();
                              final tags = record['tags'];
                              return Card(
                                key: Key('memory-record-${record['id']}'),
                                child: Padding(
                                  padding: const EdgeInsets.all(14),
                                  child: Column(
                                    crossAxisAlignment: CrossAxisAlignment.start,
                                    children: <Widget>[
                                      Row(
                                        children: <Widget>[
                                          Chip(label: Text(type)),
                                          const SizedBox(width: 8),
                                          Expanded(
                                            child: Text(
                                              title == null || title.isEmpty ? 'Memory' : title,
                                              style: Theme.of(context).textTheme.titleMedium,
                                            ),
                                          ),
                                          IconButton(
                                            tooltip: 'ลบ Memory',
                                            onPressed: () => _delete(record),
                                            icon: const Icon(Icons.delete_outline),
                                          ),
                                        ],
                                      ),
                                      const SizedBox(height: 6),
                                      SelectableText(content),
                                      const SizedBox(height: 10),
                                      Wrap(
                                        spacing: 6,
                                        runSpacing: 6,
                                        children: <Widget>[
                                          Chip(label: Text('source: $source')),
                                          if (provider != null && provider.isNotEmpty)
                                            Chip(label: Text('provider: $provider')),
                                          if (tags is List)
                                            ...tags.map(
                                              (tag) => Chip(label: Text('#${tag.toString()}')),
                                            ),
                                        ],
                                      ),
                                    ],
                                  ),
                                ),
                              );
                            },
                          ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
