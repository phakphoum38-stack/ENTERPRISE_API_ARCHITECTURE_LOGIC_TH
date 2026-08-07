import 'package:flutter/material.dart';

import '../../api/research_os_api_client.dart';

class LibraryPage extends StatefulWidget {
  const LibraryPage({
    required this.apiClient,
    super.key,
  });

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
    return Scaffold(
      appBar: AppBar(
        title: const Text('ห้องสมุดความรู้'),
        actions: <Widget>[
          IconButton(
            tooltip: 'Refresh',
            onPressed: _loading ? null : _loadArtifacts,
            icon: const Icon(Icons.refresh),
          ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: _loadArtifacts,
        child: ListView(
          padding: const EdgeInsets.all(20),
          children: <Widget>[
            Text(
              'Research OS Library',
              style: Theme.of(context).textTheme.headlineMedium,
            ),
            const SizedBox(height: 8),
            Text(
              'ค้นหาและเปิดดูความรู้จาก Research Artifacts',
              style: Theme.of(context).textTheme.bodyLarge,
            ),
            const SizedBox(height: 20),
            SearchBar(
              controller: _searchController,
              hintText: 'ค้นหาความรู้ เช่น API, Gemini, Architecture',
              leading: const Icon(Icons.search),
              trailing: <Widget>[
                IconButton(
                  tooltip: 'ค้นหา',
                  onPressed: _loading ? null : _search,
                  icon: const Icon(Icons.arrow_forward),
                ),
              ],
              onSubmitted: (_) => _search(),
            ),
            const SizedBox(height: 16),
            if (_loading) const LinearProgressIndicator(),
            if (_error != null)
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Text(_error!),
                ),
              ),
            if (!_loading && _error == null && _items.isEmpty)
              const Card(
                child: Padding(
                  padding: EdgeInsets.all(20),
                  child: Text('ยังไม่พบความรู้ในห้องสมุด'),
                ),
              ),
            for (final item in _items) _ArtifactCard(item: item),
          ],
        ),
      ),
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
    final title = source['title']?.toString() ??
        source['artifact_id']?.toString() ??
        'Untitled artifact';
    final status = source['status']?.toString() ?? 'unknown';
    final path = source['path']?.toString() ?? '';
    final excerpt = item['excerpt']?.toString();

    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: ListTile(
        leading: const Icon(Icons.menu_book_outlined),
        title: Text(title),
        subtitle: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: <Widget>[
            const SizedBox(height: 4),
            Text('สถานะ: $status'),
            if (path.isNotEmpty) Text(path),
            if (excerpt != null && excerpt.isNotEmpty) ...<Widget>[
              const SizedBox(height: 6),
              Text(
                excerpt,
                maxLines: 3,
                overflow: TextOverflow.ellipsis,
              ),
            ],
          ],
        ),
        trailing: const Icon(Icons.chevron_right),
      ),
    );
  }
}
