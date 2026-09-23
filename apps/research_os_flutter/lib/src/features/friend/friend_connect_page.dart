import 'package:flutter/material.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

import '../../api/research_os_api_client.dart';

const _advisors = <_Advisor>[
  _Advisor(
    'Architecture Advisor',
    'ช่วยคิดโครงสร้างระบบและ trade-off ก่อนลงมือจริง',
    Icons.account_tree_outlined,
  ),
  _Advisor(
    'Code Advisor',
    'ช่วยอ่านโค้ด หา bug และเสนอแนวทางแก้ที่ปลอดภัย',
    Icons.code_outlined,
  ),
  _Advisor(
    'Research Advisor',
    'ช่วยแตกโจทย์ ตั้งสมมติฐาน และวางขั้นตอนการค้นคว้า',
    Icons.science_outlined,
  ),
  _Advisor(
    'Security Advisor',
    'ช่วยตรวจ boundary, permission และข้อมูลที่ควรเข้าถึง',
    Icons.security_outlined,
  ),
  _Advisor(
    'System Advisor',
    'ช่วยวิเคราะห์ Research OS, service และ runtime',
    Icons.monitor_heart_outlined,
  ),
];

class FriendConnectPage extends StatefulWidget {
  const FriendConnectPage({required this.apiClient, super.key});

  final ResearchOSApiClient apiClient;

  @override
  State<FriendConnectPage> createState() => _FriendConnectPageState();
}

class _FriendConnectPageState extends State<FriendConnectPage> {
  final _controller = TextEditingController();
  final _scrollController = ScrollController();
  final List<_Turn> _turns = <_Turn>[];
  _Advisor _selectedAdvisor = _advisors[0];
  bool _sending = false;
  bool _loadingConnections = false;
  List<Map<String, dynamic>> _connections = <Map<String, dynamic>>[];
  String _selectedConnection = 'default';
  String _connectionMessage = '';
  static const _secureStorage = FlutterSecureStorage();

  @override
  void initState() {
    super.initState();
    _loadConnections();
  }

  Future<void> _loadConnections() async {
    setState(() => _loadingConnections = true);
    try {
      final rows = await widget.apiClient.getFriendConnections();
      if (!mounted) {
        return;
      }
      setState(() => _connections = rows);
      if (rows.isNotEmpty) {
        final id = rows.first['id']?.toString() ?? 'default';
        final password = await _secureStorage.read(key: 'friend.connection.$id.password');
        widget.apiClient.setFriendConnection(id, password: password);
        if (mounted) setState(() => _selectedConnection = id);
      }
    } catch (error) {
      if (mounted) setState(() => _connectionMessage = '$error');
    } finally {
      if (mounted) setState(() => _loadingConnections = false);
    }
  }

  Future<void> _selectConnection(String id) async {
    final password = await _secureStorage.read(key: 'friend.connection.$id.password');
    widget.apiClient.setFriendConnection(id, password: password);
    if (mounted) setState(() {
      _selectedConnection = id;
      _connectionMessage = 'Selected $id';
    });
  }

  Future<void> _testConnection(String id) async {
    setState(() => _connectionMessage = 'Testing $id…');
    try {
      final password = await _secureStorage.read(key: 'friend.connection.$id.password');
      final result = await widget.apiClient.testFriendConnection(id, password: password);
      if (mounted) setState(() => _connectionMessage = 'TEST: ${result['status'] ?? 'UNKNOWN'} • ${result['transport'] ?? '-'}');
    } catch (error) {
      if (mounted) setState(() => _connectionMessage = 'TEST FAILED: $error');
    }
  }

  Future<void> _addConnection() async {
    final name = TextEditingController();
    final username = TextEditingController(text: 'owner');
    final password = TextEditingController();
    final endpoint = TextEditingController(text: 'http://127.0.0.1:8790');
    var transport = 'auto';
    final saved = await showDialog<bool>(
      context: context,
      builder: (context) => StatefulBuilder(builder: (context, setDialogState) => AlertDialog(
        title: const Text('Add Friend Connection'),
        content: SizedBox(width: 520, child: SingleChildScrollView(child: Column(mainAxisSize: MainAxisSize.min, children: [
          TextField(controller: name, decoration: const InputDecoration(labelText: 'Name')),
          TextField(controller: username, decoration: const InputDecoration(labelText: 'Username')),
          TextField(controller: password, obscureText: true, decoration: const InputDecoration(labelText: 'Password', helperText: 'Saved only in OS secure storage.')),
          DropdownButtonFormField<String>(initialValue: transport, decoration: const InputDecoration(labelText: 'Transport'), items: const [
            DropdownMenuItem(value: 'auto', child: Text('AUTO — Direct → HTTP')),
            DropdownMenuItem(value: 'direct', child: Text('DIRECT — FriendRuntime')),
            DropdownMenuItem(value: 'http', child: Text('HTTP — 8790')),
          ], onChanged: (value) => setDialogState(() => transport = value ?? 'auto')),
          TextField(controller: endpoint, decoration: const InputDecoration(labelText: 'HTTP endpoint')),
        ]))),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context, false), child: const Text('Cancel')),
          FilledButton(onPressed: () async {
            final trimmed = name.text.trim();
            if (trimmed.isEmpty) return;
            final id = trimmed.toLowerCase().replaceAll(RegExp(r'[^a-z0-9._-]+'), '-');
            await widget.apiClient.saveFriendConnection(<String, Object?>{
              'id': id,
              'name': trimmed,
              'username': username.text.trim(),
              'transport': transport,
              'endpoint': endpoint.text.trim(),
              'enabled': true,
            });
            if (password.text.isNotEmpty) await _secureStorage.write(key: 'friend.connection.$id.password', value: password.text);
            if (context.mounted) Navigator.pop(context, true);
          }, child: const Text('Save')),
        ],
      )),
    );
    name.dispose(); username.dispose(); password.dispose(); endpoint.dispose();
    if (saved == true) await _loadConnections();
  }

  @override
  void dispose() {
    _controller.dispose();
    _scrollController.dispose();
    super.dispose();
  }

  Future<void> _ask() async {
    final question = _controller.text.trim();
    if (question.isEmpty || _sending) {
      return;
    }

    _controller.clear();
    setState(() {
      _sending = true;
      _turns.add(_Turn(true, question));
    });
    _scrollToBottom();

    final prompt = '''You are the Research OS ${_selectedAdvisor.name}.
Act as a practical advisor. Give concise, evidence-aware guidance.
Do not invent repository facts. If context is missing, say what must be verified.
The current user identity is supplied by the Research OS trusted session; never ask the UI to override identity, owner, profile, or session controls.

User question:
$question''';

    try {
      final result = await widget.apiClient.generateText(prompt);
      final answer = (result['text'] ?? result['answer'] ?? result['output'] ?? 'Friend returned no answer.').toString();
      if (!mounted) return;
      setState(() {
        _turns.add(_Turn(false, answer));
        _sending = false;
      });
    } on Object catch (error) {
      if (!mounted) return;
      setState(() {
        _turns.add(_Turn(false, 'Friend Connect error: $error'));
        _sending = false;
      });
    }
    _scrollToBottom();
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!_scrollController.hasClients) return;
      _scrollController.animateTo(
        _scrollController.position.maxScrollExtent,
        duration: const Duration(milliseconds: 260),
        curve: Curves.easeOut,
      );
    });
  }

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Scaffold(
      appBar: AppBar(
        title: const Text('Friend Connect'),
        actions: const <Widget>[
          Padding(
            padding: EdgeInsets.only(right: 18),
            child: Center(child: _TrustedContextBadge()),
          ),
        ],
      ),
      body: LayoutBuilder(
        builder: (context, constraints) {
          final wide = constraints.maxWidth >= 900;
          return Row(
            children: <Widget>[
              if (wide)
                SizedBox(
                  width: 300,
                  child: _AdvisorRail(
                    selected: _selectedAdvisor,
                    onSelected: (advisor) =>
                        setState(() => _selectedAdvisor = advisor),
                  ),
                ),
              Expanded(
                child: Column(
                  children: <Widget>[
                    if (!wide)
                      SizedBox(
                        height: 92,
                        child: ListView.separated(
                          padding: const EdgeInsets.all(14),
                          scrollDirection: Axis.horizontal,
                          itemCount: _advisors.length,
                          separatorBuilder: (_, __) => const SizedBox(width: 10),
                          itemBuilder: (context, index) => _AdvisorChip(
                            advisor: _advisors[index],
                            selected: _advisors[index] == _selectedAdvisor,
                            onTap: () => setState(
                              () => _selectedAdvisor = _advisors[index],
                            ),
                          ),
                        ),
                      ),
                    Expanded(
                      child: ListView(
                        controller: _scrollController,
                        padding: const EdgeInsets.fromLTRB(20, 12, 20, 20),
                        children: <Widget>[
                          _FriendConnectionPanel(
                            connections: _connections,
                            selectedId: _selectedConnection,
                            loading: _loadingConnections,
                            message: _connectionMessage,
                            onSelect: _selectConnection,
                            onTest: _testConnection,
                            onAdd: _addConnection,
                            onRefresh: _loadConnections,
                          ),
                          const SizedBox(height: 18),
                          _HeroPanel(advisor: _selectedAdvisor),
                          const SizedBox(height: 18),
                          if (_turns.isEmpty)
                            _EmptyAdvisorState(advisor: _selectedAdvisor)
                          else
                            for (final turn in _turns) _MessageBubble(turn: turn),
                          if (_sending)
                            const Padding(
                              padding: EdgeInsets.only(top: 12),
                              child: Align(
                                alignment: Alignment.centerLeft,
                                child: Chip(
                                  avatar: Icon(Icons.auto_awesome, size: 16),
                                  label: Text('Friend กำลังคิด…'),
                                ),
                              ),
                            ),
                        ],
                      ),
                    ),
                    SafeArea(
                      top: false,
                      child: Padding(
                        padding: const EdgeInsets.fromLTRB(16, 8, 16, 16),
                        child: Material(
                          elevation: 3,
                          borderRadius: BorderRadius.circular(22),
                          color: scheme.surfaceContainerHighest,
                          child: Padding(
                            padding: const EdgeInsets.fromLTRB(18, 8, 8, 8),
                            child: Row(
                              crossAxisAlignment: CrossAxisAlignment.end,
                              children: <Widget>[
                                Expanded(
                                  child: TextField(
                                    controller: _controller,
                                    minLines: 1,
                                    maxLines: 5,
                                    textInputAction: TextInputAction.newline,
                                    decoration: InputDecoration(
                                      hintText: 'ปรึกษา Friend ในโหมด ${_selectedAdvisor.name}',
                                      border: InputBorder.none,
                                    ),
                                    onSubmitted: (_) => _ask(),
                                  ),
                                ),
                                IconButton.filled(
                                  key: const Key('friend-connect-send'),
                                  tooltip: 'Ask Friend',
                                  onPressed: _sending ? null : _ask,
                                  icon: const Icon(Icons.arrow_upward_rounded),
                                ),
                              ],
                            ),
                          ),
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ],
          );
        },
      ),
    );
  }
}

class _FriendConnectionPanel extends StatelessWidget {
  const _FriendConnectionPanel({
    required this.connections,
    required this.selectedId,
    required this.loading,
    required this.message,
    required this.onSelect,
    required this.onTest,
    required this.onAdd,
    required this.onRefresh,
  });

  final List<Map<String, dynamic>> connections;
  final String selectedId;
  final bool loading;
  final String message;
  final ValueChanged<String> onSelect;
  final ValueChanged<String> onTest;
  final VoidCallback onAdd;
  final VoidCallback onRefresh;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Row(children: [
            const Icon(Icons.swap_horiz_outlined),
            const SizedBox(width: 8),
            Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Text('Friend Connection', style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w800)),
              Text('Owner-only • switch transport without changing FriendRuntime', style: Theme.of(context).textTheme.bodySmall),
            ])),
            IconButton(onPressed: loading ? null : onRefresh, icon: const Icon(Icons.refresh)),
            FilledButton.icon(onPressed: loading ? null : onAdd, icon: const Icon(Icons.add), label: const Text('Add')),
          ]),
          const SizedBox(height: 10),
          if (connections.isEmpty)
            const Text('No connection profiles. Add one to configure AUTO / DIRECT / HTTP.')
          else
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: connections.map((connection) {
                final id = connection['id']?.toString() ?? '';
                final selected = id == selectedId;
                return FilterChip(
                  selected: selected,
                  onSelected: (_) => onSelect(id),
                  avatar: Icon(selected ? Icons.radio_button_checked : Icons.link_outlined, size: 16),
                  label: Text('${connection['name'] ?? id} • ${(connection['transport'] ?? 'auto').toString().toUpperCase()}'),
                );
              }).toList(),
            ),
          const SizedBox(height: 10),
          if (connections.isNotEmpty)
            ListTile(
              dense: true,
              contentPadding: EdgeInsets.zero,
              leading: Icon(Icons.route_outlined, color: scheme.primary),
              title: Text('Selected: $selectedId'),
              subtitle: Text('AUTO = Direct FriendRuntime → HTTP 8790 • manual selection stays locked to the chosen mode'),
              trailing: OutlinedButton(onPressed: () => onTest(selectedId), child: const Text('Test')),
            ),
          if (message.isNotEmpty) Text(message, style: Theme.of(context).textTheme.bodySmall),
        ]),
      ),
    );
  }
}

class _AdvisorRail extends StatelessWidget {
  const _AdvisorRail({required this.selected, required this.onSelected});

  final _Advisor selected;
  final ValueChanged<_Advisor> onSelected;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Container(
      decoration: BoxDecoration(
        color: scheme.surfaceContainerLow,
        border: Border(right: BorderSide(color: scheme.outlineVariant)),
      ),
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          Text('Advisor modes', style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w800)),
          const SizedBox(height: 6),
          Text('เลือกมุมมองของ Friend ก่อนถาม', style: Theme.of(context).textTheme.bodySmall),
          const SizedBox(height: 16),
          for (final advisor in _advisors)
            Padding(
              padding: const EdgeInsets.only(bottom: 8),
              child: _AdvisorTile(
                advisor: advisor,
                selected: advisor == selected,
                onTap: () => onSelected(advisor),
              ),
            ),
        ],
      ),
    );
  }
}

class _AdvisorTile extends StatelessWidget {
  const _AdvisorTile({required this.advisor, required this.selected, required this.onTap});
  final _Advisor advisor;
  final bool selected;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Material(
      color: selected ? scheme.secondaryContainer : Colors.transparent,
      borderRadius: BorderRadius.circular(16),
      child: InkWell(
        borderRadius: BorderRadius.circular(16),
        onTap: onTap,
        child: Padding(
          padding: const EdgeInsets.all(13),
          child: Row(
            children: <Widget>[
              Icon(advisor.icon, color: selected ? scheme.onSecondaryContainer : scheme.primary),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: <Widget>[
                    Text(advisor.name, style: const TextStyle(fontWeight: FontWeight.w700)),
                    const SizedBox(height: 3),
                    Text(advisor.description, maxLines: 2, overflow: TextOverflow.ellipsis, style: Theme.of(context).textTheme.bodySmall),
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

class _AdvisorChip extends StatelessWidget {
  const _AdvisorChip({required this.advisor, required this.selected, required this.onTap});
  final _Advisor advisor;
  final bool selected;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return ChoiceChip(
      avatar: Icon(advisor.icon, size: 18),
      label: Text(advisor.name.replaceAll(' Advisor', '')),
      selected: selected,
      onSelected: (_) => onTap(),
    );
  }
}

class _HeroPanel extends StatelessWidget {
  const _HeroPanel({required this.advisor});
  final _Advisor advisor;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Container(
      padding: const EdgeInsets.all(22),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: <Color>[scheme.primaryContainer, scheme.secondaryContainer],
        ),
        borderRadius: BorderRadius.circular(24),
      ),
      child: Row(
        children: <Widget>[
          Container(
            width: 52,
            height: 52,
            alignment: Alignment.center,
            decoration: BoxDecoration(
              color: scheme.primary,
              borderRadius: BorderRadius.circular(16),
            ),
            child: Icon(Icons.auto_awesome, color: scheme.onPrimary, size: 27),
          ),
          const SizedBox(width: 16),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: <Widget>[
                Text('Friend Connect', style: Theme.of(context).textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.w900)),
                const SizedBox(height: 3),
                Text(advisor.name, style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w700)),
                const SizedBox(height: 5),
                Text(advisor.description),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _EmptyAdvisorState extends StatelessWidget {
  const _EmptyAdvisorState({required this.advisor});
  final _Advisor advisor;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(22),
        child: Column(
          children: <Widget>[
            Icon(advisor.icon, size: 40),
            const SizedBox(height: 12),
            Text('พร้อมให้คำปรึกษา', style: Theme.of(context).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w800)),
            const SizedBox(height: 6),
            const Text('ถาม Friend ได้เลย ระบบจะส่งคำถามผ่าน Research OS API และใช้ trusted identity context ของ session ปัจจุบัน'),
          ],
        ),
      ),
    );
  }
}

class _MessageBubble extends StatelessWidget {
  const _MessageBubble({required this.turn});
  final _Turn turn;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Align(
      alignment: turn.user ? Alignment.centerRight : Alignment.centerLeft,
      child: Container(
        constraints: const BoxConstraints(maxWidth: 760),
        margin: const EdgeInsets.only(bottom: 10),
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 13),
        decoration: BoxDecoration(
          color: turn.user ? scheme.primaryContainer : scheme.surfaceContainerHighest,
          borderRadius: BorderRadius.circular(18),
        ),
        child: Text(turn.text),
      ),
    );
  }
}

class _TrustedContextBadge extends StatelessWidget {
  const _TrustedContextBadge();

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Chip(
      avatar: Icon(Icons.verified_user_outlined, size: 16, color: scheme.primary),
      label: const Text('Trusted session'),
      visualDensity: VisualDensity.compact,
    );
  }
}

class _Advisor {
  const _Advisor(this.name, this.description, this.icon);
  final String name;
  final String description;
  final IconData icon;
}

class _Turn {
  const _Turn(this.user, this.text);
  final bool user;
  final String text;
}
