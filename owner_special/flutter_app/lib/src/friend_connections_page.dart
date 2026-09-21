import 'package:flutter/material.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

import 'friend_module_shell.dart';
import 'owner_api.dart';

class FriendConnectionsPage extends StatefulWidget {
  const FriendConnectionsPage({required this.api, super.key});
  final OwnerFriendApi api;

  @override
  State<FriendConnectionsPage> createState() => _FriendConnectionsPageState();
}

class _FriendConnectionsPageState extends State<FriendConnectionsPage> {
  static const _storage = FlutterSecureStorage();
  final _apiUrl = TextEditingController(text: 'http://127.0.0.1:8787');
  List<Map<String, dynamic>> _connections = <Map<String, dynamic>>[];
  String _selected = 'default';
  String _message = '';
  bool _busy = false;

  @override
  void initState() {
    super.initState();
    _load();
  }

  @override
  void dispose() {
    _apiUrl.dispose();
    super.dispose();
  }

  Future<void> _load() async {
    setState(() => _busy = true);
    try {
      final savedUrl = await _storage.read(key: 'research_os_api_url');
      if (savedUrl != null && savedUrl.trim().isNotEmpty) {
        _apiUrl.text = savedUrl.trim();
        if (widget.api is HttpOwnerFriendApi) {
          (widget.api as HttpOwnerFriendApi).setResearchOsBaseUrl(savedUrl.trim());
        }
      }
      final rows = await widget.api.friendConnections();
      if (!mounted) return;
      setState(() => _connections = rows);
    } catch (error) {
      if (mounted) setState(() => _message = error.toString());
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<String?> _password(String id) =>
      _storage.read(key: 'friend.connection.$id.password');

  Future<void> _saveApiUrl() async {
    final value = _apiUrl.text.trim().replaceFirst(RegExp(r'/+$'), '');
    if (value.isEmpty) return;
    await _storage.write(key: 'research_os_api_url', value: value);
    if (widget.api is HttpOwnerFriendApi) {
      (widget.api as HttpOwnerFriendApi).setResearchOsBaseUrl(value);
    }
    if (mounted) {
      setState(() => _message = 'Research OS API URL saved locally');
    }
  }

  Future<void> _saveConnection({
    String? id,
    required String name,
    required String username,
    required String password,
    required String transport,
    required String endpoint,
    required bool locked,
  }) async {
    final connectionId = (id ?? name.toLowerCase().replaceAll(RegExp(r'[^a-z0-9._-]+'), '-'))
        .replaceAll(RegExp(r'^-+|-+$'), '');
    if (connectionId.isEmpty) throw const FormatException('Connection name/id is required');
    final result = await widget.api.saveFriendConnection(<String, dynamic>{
      'id': connectionId,
      'name': name,
      'username': username,
      'transport': transport,
      'endpoint': endpoint,
      'locked': locked,
      'enabled': true,
    });
    if (password.isNotEmpty) {
      await _storage.write(key: 'friend.connection.$connectionId.password', value: password);
    }
    widget.api.setFriendConnection(connectionId, password: password.isEmpty ? await _password(connectionId) : password);
    if (!mounted) return;
    setState(() {
      _selected = connectionId;
      _message = 'Saved ${result['connection']?['name'] ?? connectionId} • password stays in secure storage';
    });
    await _load();
  }

  Future<void> _test(String id) async {
    setState(() {
      _busy = true;
      _message = 'Testing $id…';
    });
    try {
      final password = await _password(id);
      final result = await widget.api.testFriendConnection(id, password: password);
      widget.api.setFriendConnection(id, password: password);
      if (!mounted) return;
      setState(() => _message = 'TEST: ${result['status'] ?? 'UNKNOWN'} • ${result['transport'] ?? '-'}');
    } catch (error) {
      if (mounted) setState(() => _message = 'TEST FAILED: $error');
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _showEditor([Map<String, dynamic>? current]) async {
    final name = TextEditingController(text: current?['name']?.toString() ?? '');
    final username = TextEditingController(text: current?['username']?.toString() ?? 'owner');
    final password = TextEditingController();
    final endpoint = TextEditingController(text: current?['endpoint']?.toString() ?? 'http://127.0.0.1:8790');
    var transport = current?['transport']?.toString() ?? 'auto';
    var locked = current?['locked'] == true;
    final formKey = GlobalKey<FormState>();
    final saved = await showDialog<bool>(
      context: context,
      builder: (context) => StatefulBuilder(
        builder: (context, setDialogState) => AlertDialog(
          title: Text(current == null ? 'Add Friend Connection' : 'Edit Friend Connection'),
          content: SizedBox(
            width: 520,
            child: Form(
              key: formKey,
              child: SingleChildScrollView(
                child: Column(mainAxisSize: MainAxisSize.min, children: [
                  TextFormField(controller: name, decoration: const InputDecoration(labelText: 'Name'), validator: (v) => v == null || v.trim().isEmpty ? 'Required' : null),
                  TextFormField(controller: username, decoration: const InputDecoration(labelText: 'Username'), validator: (v) => v == null || v.trim().isEmpty ? 'Required' : null),
                  TextFormField(controller: password, obscureText: true, decoration: const InputDecoration(labelText: 'Password', helperText: 'Stored in OS secure storage; never returned by the API.')),
                  DropdownButtonFormField<String>(
                    initialValue: transport,
                    decoration: const InputDecoration(labelText: 'Transport'),
                    items: const [
                      DropdownMenuItem(value: 'auto', child: Text('AUTO — Direct → HTTP')),
                      DropdownMenuItem(value: 'direct', child: Text('DIRECT — FriendRuntime')),
                      DropdownMenuItem(value: 'http', child: Text('HTTP — 8790')),
                    ],
                    onChanged: (value) => setDialogState(() => transport = value ?? 'auto'),
                  ),
                  TextFormField(controller: endpoint, decoration: const InputDecoration(labelText: 'HTTP endpoint')),
                  SwitchListTile(
                    value: locked,
                    onChanged: (value) => setDialogState(() => locked = value),
                    title: const Text('Lock transport'),
                    subtitle: const Text('Prevents AUTO failover.'),
                  ),
                ]),
              ),
            ),
          ),
          actions: [
            TextButton(onPressed: () => Navigator.pop(context, false), child: const Text('Cancel')),
            FilledButton(
              onPressed: () async {
                if (!formKey.currentState!.validate()) return;
                try {
                  await _saveConnection(
                    id: current?['id']?.toString(),
                    name: name.text.trim(),
                    username: username.text.trim(),
                    password: password.text,
                    transport: transport,
                    endpoint: endpoint.text.trim(),
                    locked: locked,
                  );
                  if (context.mounted) Navigator.pop(context, true);
                } catch (error) {
                  if (context.mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('$error')));
                }
              },
              child: const Text('Save'),
            ),
          ],
        ),
      ),
    );
    name.dispose();
    username.dispose();
    password.dispose();
    endpoint.dispose();
    if (saved == true && mounted) setState(() {});
  }

  @override
  Widget build(BuildContext context) {
    return FriendModuleShell(
      title: 'Friend Connections',
      child: ListView(
        children: [
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                Text('Owner Connection Control', style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w700)),
                const SizedBox(height: 6),
                const Text('Owner-only. Profiles are transport settings; passwords stay in OS secure storage. Render is not part of this connection plane.'),
                const SizedBox(height: 14),
                Row(children: [
                  Expanded(child: TextField(controller: _apiUrl, decoration: const InputDecoration(labelText: 'Research OS API URL'))),
                  const SizedBox(width: 10),
                  FilledButton(onPressed: _saveApiUrl, child: const Text('Save API')),
                ]),
              ]),
            ),
          ),
          const SizedBox(height: 12),
          Row(children: [
            Expanded(child: Text('Connections', style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w700))),
            FilledButton.icon(onPressed: _busy ? null : () => _showEditor(), icon: const Icon(Icons.add), label: const Text('Add')),
            const SizedBox(width: 8),
            IconButton(onPressed: _busy ? null : _load, icon: const Icon(Icons.refresh)),
          ]),
          const SizedBox(height: 8),
          ..._connections.map((connection) {
            final id = connection['id']?.toString() ?? '';
            final selected = id == _selected;
            final transport = connection['transport']?.toString() ?? 'auto';
            return Card(
              child: ListTile(
                selected: selected,
                leading: Icon(selected ? Icons.radio_button_checked : Icons.radio_button_unchecked),
                title: Text(connection['name']?.toString() ?? id),
                subtitle: Text('${connection['username'] ?? '-'} • ${transport.toUpperCase()} • ${connection['endpoint'] ?? '-'}'),
                trailing: Wrap(children: [
                  IconButton(tooltip: 'Test', onPressed: _busy ? null : () => _test(id), icon: const Icon(Icons.health_and_safety_outlined)),
                  IconButton(tooltip: 'Edit', onPressed: _busy ? null : () => _showEditor(connection), icon: const Icon(Icons.edit_outlined)),
                  IconButton(tooltip: 'Use', onPressed: () async {
                    final password = await _password(id);
                    widget.api.setFriendConnection(id, password: password);
                    if (mounted) setState(() {
                      _selected = id;
                      _message = 'Selected $id • ${transport.toUpperCase()}';
                    });
                  }, icon: const Icon(Icons.check_circle_outline)),
                ]),
                onTap: () async {
                  final password = await _password(id);
                  widget.api.setFriendConnection(id, password: password);
                  if (mounted) setState(() {
                    _selected = id;
                    _message = 'Selected $id • ${transport.toUpperCase()}';
                  });
                },
              ),
            );
          }),
          if (_connections.isEmpty && !_busy)
            const Card(child: ListTile(leading: Icon(Icons.link_off), title: Text('No connection profiles'), subtitle: Text('Add your first Owner connection.'))),
          if (_busy) const Padding(padding: EdgeInsets.all(20), child: Center(child: CircularProgressIndicator())),
          if (_message.isNotEmpty) Card(child: ListTile(leading: const Icon(Icons.info_outline), title: Text(_message))),
        ],
      ),
    );
  }
}
