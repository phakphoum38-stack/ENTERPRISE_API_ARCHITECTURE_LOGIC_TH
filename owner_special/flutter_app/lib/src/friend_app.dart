import 'package:flutter/material.dart';

import 'owner_api.dart';

class OwnerFriendApp extends StatefulWidget {
  const OwnerFriendApp({required this.api, this.startup, this.startupError, super.key});
  final OwnerFriendApi api;
  final Map<String, dynamic>? startup;
  final String? startupError;

  @override
  State<OwnerFriendApp> createState() => _OwnerFriendAppState();
}

class _OwnerFriendAppState extends State<OwnerFriendApp> {
  int _index = 0;

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      title: 'Research OS Owner Special',
      theme: ThemeData(useMaterial3: true, colorSchemeSeed: Colors.indigo),
      home: Scaffold(
        appBar: AppBar(
          title: const Text('Research OS • Owner Special • Friend Complete V1.3'),
          actions: <Widget>[Padding(padding: const EdgeInsets.symmetric(horizontal: 16), child: Center(child: Text(widget.startupError == null ? 'Friend Service: connected' : 'Friend Service: offline')))],
        ),
        body: Row(children: <Widget>[
          NavigationRail(
            selectedIndex: _index,
            onDestinationSelected: (value) => setState(() => _index = value),
            labelType: NavigationRailLabelType.all,
            destinations: const <NavigationRailDestination>[
              NavigationRailDestination(icon: Icon(Icons.forum_outlined), selectedIcon: Icon(Icons.forum), label: Text('Friend')),
              NavigationRailDestination(icon: Icon(Icons.psychology_outlined), selectedIcon: Icon(Icons.psychology), label: Text('Capabilities')),
              NavigationRailDestination(icon: Icon(Icons.memory_outlined), selectedIcon: Icon(Icons.memory), label: Text('Memory')),
              NavigationRailDestination(icon: Icon(Icons.settings_outlined), selectedIcon: Icon(Icons.settings), label: Text('Provider')),
            ],
          ),
          const VerticalDivider(width: 1),
          Expanded(child: <Widget>[_FriendChatPage(api: widget.api), _CapabilitiesPage(api: widget.api, startup: widget.startup), _MemoryPage(api: widget.api), _ProviderPage(api: widget.api)][_index]),
        ]),
      ),
    );
  }
}

class _FriendChatPage extends StatefulWidget {
  const _FriendChatPage({required this.api});
  final OwnerFriendApi api;
  @override
  State<_FriendChatPage> createState() => _FriendChatPageState();
}

class _FriendChatPageState extends State<_FriendChatPage> {
  final _controller = TextEditingController();
  bool _busy = false;
  bool _turboMillion = true;
  String _answer = 'Friend Runtime พร้อมรับงาน';
  String _scale = '-';
  int _capacity = 0;
  int _activeWorkers = 0;
  int _batches = 0;
  String _factory = '-';

  @override
  void dispose() { _controller.dispose(); super.dispose(); }

  Future<void> _send() async {
    final text = _controller.text.trim();
    if (text.isEmpty || _busy) return;
    setState(() => _busy = true);
    try {
      final response = await widget.api.chat(text, complexity: 6, risk: 3, parallelism: 8, helperBudget: _turboMillion ? 1000000 : 0, requestedSkills: const <String>['analysis', 'planning', 'memory', 'quality']);
      final decision = Map<String, dynamic>.from(response['decision'] as Map);
      final helpers = Map<String, dynamic>.from(response['helpers'] as Map? ?? const <String, dynamic>{});
      final factory = Map<String, dynamic>.from(response['factory'] as Map);
      setState(() {
        _answer = response['text']?.toString() ?? '';
        _scale = decision['scale']?.toString() ?? '-';
        _capacity = (decision['capacity'] as num?)?.toInt() ?? 0;
        _activeWorkers = (helpers['active_workers'] as num?)?.toInt() ?? 0;
        _batches = (helpers['batches'] as num?)?.toInt() ?? 0;
        _factory = (factory['stages'] as List? ?? const <Object>[]).join(' → ');
      });
    } catch (error) {
      setState(() => _answer = 'Friend Service error: $error');
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.all(24),
      child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: <Widget>[
        Wrap(spacing: 12, runSpacing: 8, children: <Widget>[
          FilterChip(key: const Key('turbo-million'), selected: _turboMillion, onSelected: (value) => setState(() => _turboMillion = value), label: const Text('Turbo Helpers 1,000,000')),
          Chip(label: Text('Brain scale: $_scale')),
          Chip(label: Text('Logical capacity: $_capacity')),
          Chip(label: Text('Active workers: $_activeWorkers')),
          Chip(label: Text('Batches: $_batches')),
          Chip(label: Text('Factory: $_factory')),
        ]),
        const SizedBox(height: 20),
        Expanded(child: Card(child: Padding(padding: const EdgeInsets.all(20), child: SelectableText(_answer, key: const Key('friend-answer'))))),
        const SizedBox(height: 16),
        Row(children: <Widget>[
          Expanded(child: TextField(key: const Key('friend-input'), controller: _controller, onSubmitted: (_) => _send(), decoration: const InputDecoration(border: OutlineInputBorder(), hintText: 'คุยกับเพื่อนของเรา…'))),
          const SizedBox(width: 12),
          FilledButton.icon(key: const Key('friend-send'), onPressed: _busy ? null : _send, icon: _busy ? const SizedBox.square(dimension: 18, child: CircularProgressIndicator(strokeWidth: 2)) : const Icon(Icons.send), label: const Text('ส่ง')),
        ]),
      ]),
    );
  }
}

class _CapabilitiesPage extends StatelessWidget {
  const _CapabilitiesPage({required this.api, this.startup});
  final OwnerFriendApi api;
  final Map<String, dynamic>? startup;
  @override
  Widget build(BuildContext context) {
    return FutureBuilder<Map<String, dynamic>>(
      future: startup?['status'] is Map ? Future<Map<String, dynamic>>.value(Map<String, dynamic>.from(startup!['status'] as Map)) : api.status(),
      builder: (context, snapshot) {
        if (!snapshot.hasData) return const Center(child: CircularProgressIndicator());
        final status = snapshot.data!;
        final profiles = Map<String, dynamic>.from(status['brain_profiles'] as Map? ?? const <String, dynamic>{});
        final helper = Map<String, dynamic>.from(status['helper_scheduler'] as Map? ?? const <String, dynamic>{});
        final capabilities = (status['capabilities'] as List? ?? const <Object>[]).map((item) => item.toString()).toList();
        return ListView(padding: const EdgeInsets.all(24), children: <Widget>[
          Text('Friend Complete Architecture', style: Theme.of(context).textTheme.headlineSmall),
          const SizedBox(height: 16),
          Text('Brain: ${profiles.entries.map((entry) => '${entry.key}=${entry.value}').join(' • ')}'),
          Text('Helpers: logical ${helper['max_logical_helpers'] ?? '-'} • active ${helper['max_active_workers'] ?? '-'}'),
          const SizedBox(height: 16),
          Wrap(spacing: 8, runSpacing: 8, children: capabilities.map((name) => Chip(label: Text(name))).toList()),
        ]);
      },
    );
  }
}

class _MemoryPage extends StatelessWidget {
  const _MemoryPage({required this.api});
  final OwnerFriendApi api;
  @override
  Widget build(BuildContext context) {
    return FutureBuilder<Map<String, dynamic>>(
      future: api.memory(),
      builder: (context, snapshot) {
        if (!snapshot.hasData) return const Center(child: CircularProgressIndicator());
        final items = snapshot.data!['items'] as List? ?? const <Object>[];
        if (items.isEmpty) return const Center(child: Text('ยังไม่มีความจำใน profile/session นี้'));
        return ListView.builder(padding: const EdgeInsets.all(24), itemCount: items.length, itemBuilder: (context, index) {
          final item = Map<String, dynamic>.from(items[index] as Map);
          return ListTile(title: Text(item['kind']?.toString() ?? ''), subtitle: Text(item['text']?.toString() ?? ''));
        });
      },
    );
  }
}

class _ProviderPage extends StatefulWidget {
  const _ProviderPage({required this.api});
  final OwnerFriendApi api;
  @override
  State<_ProviderPage> createState() => _ProviderPageState();
}

class _ProviderPageState extends State<_ProviderPage> {
  final _baseUrl = TextEditingController();
  final _model = TextEditingController();
  final _apiKey = TextEditingController();
  Map<String, dynamic>? _status;
  String _message = '';
  bool _busy = false;

  @override
  void initState() { super.initState(); _load(); }
  @override
  void dispose() { _baseUrl.dispose(); _model.dispose(); _apiKey.dispose(); super.dispose(); }

  Future<void> _load() async {
    try {
      final status = await widget.api.providerStatus();
      if (!mounted) return;
      setState(() {
        _status = status;
        _baseUrl.text = status['base_url']?.toString() ?? '';
        _model.text = status['model']?.toString() ?? '';
      });
    } catch (error) { if (mounted) setState(() => _message = '$error'); }
  }

  Future<void> _saveAndTest() async {
    if (_busy) return;
    setState(() { _busy = true; _message = ''; });
    try {
      final saved = await widget.api.configureProvider(baseUrl: _baseUrl.text.trim(), model: _model.text.trim(), apiKey: _apiKey.text.trim().isEmpty ? null : _apiKey.text.trim());
      _apiKey.clear();
      final tested = await widget.api.testProvider();
      if (!mounted) return;
      setState(() { _status = saved; _message = tested['connected'] == true ? 'Provider connected' : 'Provider test failed: ${tested['error'] ?? 'unknown'}'; });
    } catch (error) { if (mounted) setState(() => _message = '$error'); }
    finally { if (mounted) setState(() => _busy = false); }
  }

  @override
  Widget build(BuildContext context) {
    final credentialPresent = _status?['credential_present'] == true;
    return ListView(padding: const EdgeInsets.all(24), children: <Widget>[
      Text('OpenAI-compatible Provider', style: Theme.of(context).textTheme.headlineSmall),
      const SizedBox(height: 8),
      Text('Credential: ${credentialPresent ? 'stored securely' : 'not configured'} • backend: ${_status?['secret_backend'] ?? '-'}'),
      const SizedBox(height: 20),
      TextField(key: const Key('provider-base-url'), controller: _baseUrl, decoration: const InputDecoration(labelText: 'Base URL', border: OutlineInputBorder())),
      const SizedBox(height: 12),
      TextField(key: const Key('provider-model'), controller: _model, decoration: const InputDecoration(labelText: 'Model', border: OutlineInputBorder())),
      const SizedBox(height: 12),
      TextField(key: const Key('provider-api-key'), controller: _apiKey, obscureText: true, decoration: const InputDecoration(labelText: 'API key (leave blank to keep existing)', border: OutlineInputBorder())),
      const SizedBox(height: 16),
      FilledButton.icon(key: const Key('provider-save-test'), onPressed: _busy ? null : _saveAndTest, icon: const Icon(Icons.link), label: const Text('Save & Test Connection')),
      if (_message.isNotEmpty) Padding(padding: const EdgeInsets.only(top: 16), child: SelectableText(_message, key: const Key('provider-message'))),
    ]);
  }
}
