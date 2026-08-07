import 'package:flutter/material.dart';

import '../../api/research_os_api_client.dart';

class LibraryPage extends StatefulWidget {
  const LibraryPage({required this.apiClient, super.key});

  final ResearchOSApiClient apiClient;

  @override
  State<LibraryPage> createState() => _LibraryPageState();
}

class _LibraryPageState extends State<LibraryPage> {
  final TextEditingController _searchController = TextEditingController();
  bool _loading = true;
  String? _error;
  List<Map<String, dynamic>> _items = const <Map<String, dynamic>>[];

  @override
  void initState() {
    super.initState();
    _loadArtifacts();
  }

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  Future<void> _loadArtifacts() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final payload = await widget.apiClient.getKnowledgeArtifacts();
      final raw = payload['artifacts'];
      if (!mounted) return;
      setState(() {
        _items = raw is List
            ? raw.whereType<Map<String, dynamic>>().toList(growable: false)
            : const <Map<String, dynamic>>[];
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

  Future<void> _search() async {
    final query = _searchController.text.trim();
    if (query.isEmpty) {
      await _loadArtifacts();
      return;
    }
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final payload = await widget.apiClient.searchMemory(query);
      final raw = payload['results'] ?? payload['hits'];
      if (!mounted) return;
      setState(() {
        _items = raw is List
            ? raw.whereType<Map<String, dynamic>>().toList(growable: false)
            : const <Map<String, dynamic>>[];
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
    final query = _searchController.text.trim();
    return RefreshIndicator(
      onRefresh: _loadArtifacts,
      child: ListView(
        padding: const EdgeInsets.fromLTRB(24, 24, 24, 40),
        children: <Widget>[
          _PageHeading(
            icon: Icons.local_library_outlined,
            title: 'Knowledge Library',
            subtitle: 'ค้นหาและเปิดดู Research Artifacts และ Memory จากศูนย์กลางเดียว',
            action: IconButton(
              tooltip: 'Refresh',
              onPressed: _loading ? null : _loadArtifacts,
              icon: const Icon(Icons.refresh),
            ),
          ),
          const SizedBox(height: 20),
          Card(
            child: Padding(
              padding: const EdgeInsets.all(18),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: <Widget>[
                  Text('Search knowledge', style: Theme.of(context).textTheme.titleMedium),
                  const SizedBox(height: 12),
                  SearchBar(
                    controller: _searchController,
                    hintText: 'ค้นหา เช่น API, Gemini, Architecture, Memory',
                    leading: const Icon(Icons.search),
                    trailing: <Widget>[
                      if (query.isNotEmpty)
                        IconButton(
                          tooltip: 'ล้างคำค้น',
                          onPressed: _loading
                              ? null
                              : () {
                                  _searchController.clear();
                                  _loadArtifacts();
                                },
                          icon: const Icon(Icons.close),
                        ),
                      IconButton(
                        tooltip: 'ค้นหา',
                        onPressed: _loading ? null : _search,
                        icon: const Icon(Icons.arrow_forward),
                      ),
                    ],
                    onSubmitted: (_) => _search(),
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 20),
          Row(
            children: <Widget>[
              Expanded(
                child: Text('Knowledge results', style: Theme.of(context).textTheme.titleLarge),
              ),
              Chip(label: Text('${_items.length} items')),
            ],
          ),
          const SizedBox(height: 10),
          if (_loading) const LinearProgressIndicator(),
          if (_error != null)
            Card(
              child: ListTile(
                leading: const Icon(Icons.error_outline),
                title: const Text('โหลด Knowledge ไม่สำเร็จ'),
                subtitle: Text(_error!),
                trailing: IconButton(onPressed: _loadArtifacts, icon: const Icon(Icons.refresh)),
              ),
            ),
          if (!_loading && _error == null && _items.isEmpty)
            const Card(
              child: Padding(
                padding: EdgeInsets.all(28),
                child: Column(
                  children: <Widget>[
                    Icon(Icons.menu_book_outlined, size: 38),
                    SizedBox(height: 10),
                    Text('ยังไม่พบความรู้ใน Library'),
                  ],
                ),
              ),
            ),
          for (final item in _items) _ArtifactCard(item: item),
        ],
      ),
    );
  }
}

class _PageHeading extends StatelessWidget {
  const _PageHeading({required this.icon, required this.title, required this.subtitle, required this.action});
  final IconData icon;
  final String title;
  final String subtitle;
  final Widget action;

  @override
  Widget build(BuildContext context) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: <Widget>[
        Container(
          width: 46,
          height: 46,
          alignment: Alignment.center,
          decoration: BoxDecoration(
            color: Theme.of(context).colorScheme.primaryContainer,
            borderRadius: BorderRadius.circular(14),
          ),
          child: Icon(icon),
        ),
        const SizedBox(width: 14),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: <Widget>[
              Text(title, style: Theme.of(context).textTheme.headlineSmall),
              const SizedBox(height: 4),
              Text(subtitle, style: Theme.of(context).textTheme.bodyMedium),
            ],
          ),
        ),
        action,
      ],
    );
  }
}

class _ArtifactCard extends StatelessWidget {
  const _ArtifactCard({required this.item});
  final Map<String, dynamic> item;

  @override
  Widget build(BuildContext context) {
    final artifact = item['artifact'];
    final source = artifact is Map<String, dynamic> ? artifact : item;
    final title = source['title']?.toString() ?? source['artifact_id']?.toString() ?? 'Untitled artifact';
    final status = source['status']?.toString() ?? 'unknown';
    final path = source['path']?.toString() ?? '';
    final excerpt = item['excerpt']?.toString();

    return Card(
      margin: const EdgeInsets.only(bottom: 10),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: <Widget>[
            const Icon(Icons.article_outlined, size: 28),
            const SizedBox(width: 14),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: <Widget>[
                  Row(
                    children: <Widget>[
                      Expanded(child: Text(title, style: Theme.of(context).textTheme.titleMedium)),
                      Chip(label: Text(status)),
                    ],
                  ),
                  if (path.isNotEmpty) Text(path, style: Theme.of(context).textTheme.bodySmall),
                  if (excerpt != null && excerpt.isNotEmpty) ...<Widget>[
                    const SizedBox(height: 8),
                    Text(excerpt, maxLines: 3, overflow: TextOverflow.ellipsis),
                  ],
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}
