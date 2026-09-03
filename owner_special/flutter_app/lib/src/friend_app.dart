import 'package:flutter/material.dart';

import 'friend_app_shell.dart';
import 'friend_module_shell.dart';
import 'friend_theme.dart';
import 'launch_desk_page.dart';
import 'owner_api.dart';
import 'team_center.dart';

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
  TeamRecord _currentTeam = const TeamRecord(id: 'research', name: 'Research Team');

  void _onTeamChanged(TeamRecord team) => setState(() => _currentTeam = team);

  @override
  Widget build(BuildContext context) {
    final pages = <Widget>[
      _FriendChatPage(api: widget.api, team: _currentTeam),
      LaunchDeskPage(api: widget.api),
      _CapabilitiesPage(api: widget.api, startup: widget.startup),
      _MemoryPage(api: widget.api),
      _ProviderPage(api: widget.api),
      _TeamPage(team: _currentTeam),
    ];

    return MaterialApp(
      debugShowCheckedModeBanner: false,
      title: 'Friend',
      theme: FriendTheme.build(),
      home: FriendAppShell(
        index: _index,
        onIndexChanged: (value) => setState(() => _index = value),
        pages: pages,
        teamCenter: ConstrainedBox(constraints: const BoxConstraints(maxWidth: 420), child: TeamCenter(onChanged: _onTeamChanged)),
        status: _StatusPill(connected: widget.startupError == null),
      ),
    );
  }
}

class _StatusPill extends StatelessWidget {
  const _StatusPill({required this.connected});
  final bool connected;
  @override
  Widget build(BuildContext context) {
    final color = connected ? const Color(0xFF34D399) : const Color(0xFFF59E0B);
    return Container(padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8), decoration: BoxDecoration(color: color.withValues(alpha: .12), borderRadius: BorderRadius.circular(999)), child: Row(mainAxisSize: MainAxisSize.min, children: [Container(width: 7, height: 7, decoration: BoxDecoration(color: color, shape: BoxShape.circle)), const SizedBox(width: 8), Text(connected ? 'Friend Service connected' : 'Friend Service offline')]));
  }
}

class _TeamPage extends StatelessWidget {
  const _TeamPage({required this.team});
  final TeamRecord team;
  @override
  Widget build(BuildContext context) => FriendModuleShell(title: 'Team Workspace', child: ListView(children: [Card(child: ListTile(leading: const Icon(Icons.groups_outlined), title: Text(team.name), subtitle: Text('Team ID: ${team.id}'))), const SizedBox(height: 16), const Wrap(spacing: 8, runSpacing: 8, children: [Chip(label: Text('Chat')), Chip(label: Text('Agents')), Chip(label: Text('Memory')), Chip(label: Text('Files')), Chip(label: Text('Tasks'))])]);
}

class _FriendChatPage extends StatefulWidget {
  const _FriendChatPage({required this.api, required this.team});
  final OwnerFriendApi api;
  final TeamRecord team;
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
      setState(() { _answer = response['text']?.toString() ?? ''; _scale = decision['scale']?.toString() ?? '-'; _capacity = (decision['capacity'] as num?)?.toInt() ?? 0; _activeWorkers = (helpers['active_workers'] as num?)?.toInt() ?? 0; _batches = (helpers['batches'] as num?)?.toInt() ?? 0; _factory = (factory['stages'] as List? ?? const <Object>[]).join(' → '); });
    } catch (error) { setState(() => _answer = 'Friend Service error: $error'); }
    finally { if (mounted) setState(() => _busy = false); }
  }
  @override
  Widget build(BuildContext context) => FriendModuleShell(title: 'Friend Workspace', child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [Text('Team: ${widget.team.name}', style: Theme.of(context).textTheme.titleMedium), const SizedBox(height: 12), SizedBox(height: 48, child: SingleChildScrollView(scrollDirection: Axis.horizontal, child: Row(children: [FilterChip(key: const Key('turbo-million'), selected: _turboMillion, onSelected: (value) => setState(() => _turboMillion = value), label: const Text('Turbo Helpers 1,000,000')), const SizedBox(width: 12), Chip(label: Text('Brain scale: $_scale')), const SizedBox(width: 12), Chip(label: Text('Logical capacity: $_capacity')), const SizedBox(width: 12), Chip(label: Text('Active workers: $_activeWorkers')), const SizedBox(width: 12), Chip(label: Text('Batches: $_batches')), const SizedBox(width: 12), Chip(label: Text('Factory: $_factory'))])), const SizedBox(height: 20), Expanded(child: Container(padding: const EdgeInsets.all(20), decoration: BoxDecoration(color: Theme.of(context).colorScheme.surface, borderRadius: BorderRadius.circular(18)), child: SelectableText(_answer, key: const Key('friend-answer')))), const SizedBox(height: 16), Row(children: [Expanded(child: TextField(key: const Key('friend-input'), controller: _controller, onSubmitted: (_) => _send(), decoration: const InputDecoration(hintText: 'คุยกับเพื่อนของเรา…'))), const SizedBox(width: 12), FilledButton.icon(key: const Key('friend-send'), onPressed: _busy ? null : _send, icon: _busy ? const SizedBox.square(dimension: 18, child: CircularProgressIndicator(strokeWidth: 2)) : const Icon(Icons.arrow_upward), label: const Text('ส่ง'))])]));
}

class _CapabilitiesPage extends StatelessWidget {
  const _CapabilitiesPage({required this.api, this.startup});
  final OwnerFriendApi api;
  final Map<String, dynamic>? startup;
  @override
  Widget build(BuildContext context) => FriendModuleShell(title: 'Capabilities', child: FutureBuilder<Map<String, dynamic>>(future: startup?['status'] is Map ? Future<Map<String, dynamic>>.value(Map<String, dynamic>.from(startup!['status'] as Map)) : api.status(), builder: (context, snapshot) { if (!snapshot.hasData) return const Center(child: CircularProgressIndicator()); final status = snapshot.data!; final profiles = Map<String, dynamic>.from(status['brain_profiles'] as Map? ?? const <String, dynamic>{}); final helper = Map<String, dynamic>.from(status['helper_scheduler'] as Map? ?? const <String, dynamic>{}); final capabilities = (status['capabilities'] as List? ?? const <Object>[]).map((item) => item.toString()).toList(); return ListView(children: [Text('Brain: ${profiles.entries.map((entry) => '${entry.key}=${entry.value}').join(' • ')}'), Text('Helpers: logical ${helper['max_logical_helpers'] ?? '-'} • active ${helper['max_active_workers'] ?? '-'}'), const SizedBox(height: 16), Wrap(spacing: 8, runSpacing: 8, children: capabilities.map((name) => Chip(label: Text(name))).toList())]); }));
}

class _MemoryPage extends StatelessWidget {
  const _MemoryPage({required this.api});
  final OwnerFriendApi api;
  @override
  Widget build(BuildContext context) => FriendModuleShell(title: 'Memory', child: FutureBuilder<Map<String, dynamic>>(future: api.memory(), builder: (context, snapshot) { if (!snapshot.hasData) return const Center(child: CircularProgressIndicator()); final items = snapshot.data!['items'] as List? ?? const <Object>[]; if (items.isEmpty) return const Center(child: Text('ยังไม่มีความจำใน profile/session นี้')); return ListView.builder(itemCount: items.length, itemBuilder: (context, index) { final item = Map<String, dynamic>.from(items[index] as Map); return ListTile(title: Text(item['kind']?.toString() ?? ''), subtitle: Text(item['text']?.toString() ?? '')); }); }));
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
  Future<void> _load() async { try { final status = await widget.api.providerStatus(); if (!mounted) return; setState(() { _status = status; _baseUrl.text = status['base_url']?.toString() ?? ''; _model.text = status['model']?.toString() ?? ''; }); } catch (error) { if (mounted) setState(() => _message = '$error'); } }
  Future<void> _saveAndTest() async { if (_busy) return; setState(() { _busy = true; _message = ''; }); try { final saved = await widget.api.configureProvider(baseUrl: _baseUrl.text.trim(), model: _model.text.trim(), apiKey: _apiKey.text.trim().isEmpty ? null : _apiKey.text.trim()); _apiKey.clear(); final tested = await widget.api.testProvider(); final refreshed = await widget.api.providerStatus(); if (!mounted) return; setState(() { _status = refreshed; final connected = tested['connected'] == true; final stored = refreshed['credential_present'] == true; _message = connected && stored ? 'Provider connected • API key stored securely' : connected ? 'Provider connected • credential status unavailable' : 'Provider test failed: ${tested['error'] ?? 'unknown'}'; }); assert(saved.isNotEmpty); } catch (error) { if (mounted) setState(() => _message = '$error'); } finally { if (mounted) setState(() => _busy = false); } }
  @override
  Widget build(BuildContext context) { final credentialPresent = _status?['credential_present'] == true; return FriendModuleShell(title: 'Provider', child: ListView(children: [Text('Credential: ${credentialPresent ? 'stored securely' : 'not configured'} • backend: ${_status?['secret_backend'] ?? '-'}'), const SizedBox(height: 20), TextField(key: const Key('provider-base-url'), controller: _baseUrl, decoration: const InputDecoration(labelText: 'Base URL')), const SizedBox(height: 12), TextField(key: const Key('provider-model'), controller: _model, decoration: const InputDecoration(labelText: 'Model')), const SizedBox(height: 12), TextField(key: const Key('provider-api-key'), controller: _apiKey, obscureText: true, decoration: InputDecoration(labelText: credentialPresent ? 'API key (stored securely — leave blank to keep it)' : 'API key (enter once to store securely)', hintText: credentialPresent ? 'Stored securely; no need to enter it again' : null)), const SizedBox(height: 8), Text(credentialPresent ? 'The key is cleared from the field after saving and remains server-side in the secure credential backend.' : 'Enter the key here only. It will be stored server-side and never displayed again.', style: Theme.of(context).textTheme.bodySmall), const SizedBox(height: 16), FilledButton.icon(key: const Key('provider-save-test'), onPressed: _busy ? null : _saveAndTest, icon: _busy ? const SizedBox.square(dimension: 18, child: CircularProgressIndicator(strokeWidth: 2)) : const Icon(Icons.link), label: Text(_busy ? 'Testing...' : 'Save & Test Connection')), if (_message.isNotEmpty) Padding(padding: const EdgeInsets.only(top: 16), child: SelectableText(_message, key: const Key('provider-message')))])); }
}
