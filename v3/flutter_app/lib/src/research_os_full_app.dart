import 'dart:convert';

import 'package:flutter/material.dart';

import 'api/v3_api.dart';
import 'full_control_operational.dart';

class ResearchOSFullApp extends StatelessWidget {
  const ResearchOSFullApp({super.key, required this.api});

  final V3Api api;

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      title: 'Research OS · Full Control Center',
      themeMode: ThemeMode.dark,
      darkTheme: ThemeData(
        brightness: Brightness.dark,
        useMaterial3: true,
        scaffoldBackgroundColor: const Color(0xFF07111E),
        colorScheme: ColorScheme.fromSeed(seedColor: const Color(0xFF5A43E8), brightness: Brightness.dark),
        cardTheme: const CardThemeData(elevation: 0, margin: EdgeInsets.zero),
        inputDecorationTheme: InputDecorationTheme(
          filled: true,
          fillColor: const Color(0xFF0B1725),
          border: OutlineInputBorder(borderRadius: BorderRadius.circular(10), borderSide: const BorderSide(color: Color(0xFF203044))),
          enabledBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(10), borderSide: const BorderSide(color: Color(0xFF203044))),
        ),
      ),
      home: _FullShell(api: api),
    );
  }
}

class _Nav {
  const _Nav(this.label, this.icon, this.group);
  final String label;
  final IconData icon;
  final String group;
}

const _nav = <_Nav>[
  _Nav('Home', Icons.home_outlined, 'MAIN'),
  _Nav('Chat AI', Icons.chat_bubble_outline, 'MAIN'),
  _Nav('Agents', Icons.smart_toy_outlined, 'MAIN'),
  _Nav('Memory', Icons.memory_outlined, 'MAIN'),
  _Nav('Skills', Icons.extension_outlined, 'MAIN'),
  _Nav('Tools', Icons.build_outlined, 'MAIN'),
  _Nav('Factory', Icons.account_tree_outlined, 'MAIN'),
  _Nav('Providers', Icons.hub_outlined, 'MAIN'),
  _Nav('Files', Icons.folder_outlined, 'WORKSPACE'),
  _Nav('Repositories', Icons.inventory_2_outlined, 'WORKSPACE'),
  _Nav('GitHub', Icons.code, 'WORKSPACE'),
  _Nav('Drive', Icons.cloud_outlined, 'WORKSPACE'),
  _Nav('Runtime', Icons.dns_outlined, 'SYSTEM'),
  _Nav('Installer', Icons.inventory_outlined, 'SYSTEM'),
  _Nav('Backup', Icons.backup_outlined, 'SYSTEM'),
  _Nav('Restore', Icons.restore_outlined, 'SYSTEM'),
  _Nav('Shell', Icons.terminal_outlined, 'SYSTEM'),
];

class _Snapshot {
  const _Snapshot({required this.health, required this.master, required this.skills, required this.tools, required this.agents, required this.providers});
  final Map<String, dynamic> health;
  final Map<String, dynamic> master;
  final Map<String, dynamic> skills;
  final Map<String, dynamic> tools;
  final Map<String, dynamic> agents;
  final Map<String, dynamic> providers;

  List<Map<String, dynamic>> list(Map<String, dynamic> source, String key) {
    final value = source[key];
    if (value is! List) return const [];
    return value.whereType<Map>().map((item) => Map<String, dynamic>.from(item)).toList();
  }

  List<Map<String, dynamic>> get skillList => list(skills, 'skills');
  List<Map<String, dynamic>> get toolList => list(tools, 'tools');
  List<Map<String, dynamic>> get agentList => list(agents, 'agents');
  List<Map<String, dynamic>> get providerList => list(providers, 'providers');
}

class _FullShell extends StatefulWidget {
  const _FullShell({required this.api});
  final V3Api api;

  @override
  State<_FullShell> createState() => _FullShellState();
}

class _FullShellState extends State<_FullShell> {
  int _selected = 1;
  late Future<_Snapshot> _future;

  @override
  void initState() {
    super.initState();
    _future = _load();
  }

  Future<_Snapshot> _load() async {
    final values = await Future.wait<Map<String, dynamic>>([
      widget.api.health(),
      widget.api.master(tasks: 30, risk: 2, parallelism: 4),
      widget.api.skills(),
      widget.api.tools(),
      widget.api.agents(),
      widget.api.providers(),
    ]);
    return _Snapshot(health: values[0], master: values[1], skills: values[2], tools: values[3], agents: values[4], providers: values[5]);
  }

  void _refresh() => setState(() => _future = _load());

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Column(
          children: [
            _TopBar(snapshot: _future, onRefresh: _refresh),
            const Divider(height: 1),
            Expanded(
              child: Row(
                children: [
                  SizedBox(width: 205, child: _Sidebar(selected: _selected, onSelected: (value) => setState(() => _selected = value))),
                  const VerticalDivider(width: 1),
                  Expanded(child: _content()),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _content() {
    switch (_selected) {
      case 0:
        return _HomePage(snapshot: _future, onRefresh: _refresh);
      case 1:
        return _ChatPage(api: widget.api, snapshot: _future);
      case 2:
        return _AgentsPage(api: widget.api, snapshot: _future);
      case 3:
        return _MemoryPage(api: widget.api);
      case 4:
        return _CatalogPage(title: 'Skills', snapshot: _future, kind: 'skills');
      case 5:
        return _ToolsPage(api: widget.api, snapshot: _future);
      case 6:
        return _FactoryPage(api: widget.api);
      case 7:
        return _CatalogPage(title: 'Providers', snapshot: _future, kind: 'providers');
      case 8:
        return FullFilesPage(api: widget.api);
      case 9:
        return FullRepositoriesPage(api: widget.api);
      case 10:
        return FullStatusToolPage(api: widget.api, title: 'GitHub', subtitle: 'Local repository mirror + governed integration status', tool: 'github-status', icon: Icons.code);
      case 11:
        return FullStatusToolPage(api: widget.api, title: 'Drive', subtitle: 'DRIVE_VIRTUAL_CLOUD persistent storage and tool source', tool: 'drive-status', icon: Icons.cloud_outlined);
      case 12:
        return FullStatusToolPage(api: widget.api, title: 'Runtime', subtitle: 'V3 service runtime and bundled Python status', tool: 'runtime-status', icon: Icons.dns_outlined);
      case 13:
        return FullStatusToolPage(api: widget.api, title: 'Installer', subtitle: 'Installed runtime, build SHA and upgrade policy', tool: 'installer-status', icon: Icons.inventory_outlined);
      case 14:
        return FullBackupPage(api: widget.api);
      case 15:
        return FullRestorePage(api: widget.api);
      case 16:
        return FullShellPage(api: widget.api);
      default:
        return const SizedBox.shrink();
    }
  }
}

class _TopBar extends StatelessWidget {
  const _TopBar({required this.snapshot, required this.onRefresh});
  final Future<_Snapshot> snapshot;
  final VoidCallback onRefresh;

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      height: 68,
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 15),
        child: Row(
          children: [
            Container(width: 38, height: 38, decoration: BoxDecoration(color: const Color(0xFF3157D5), borderRadius: BorderRadius.circular(10)), child: const Icon(Icons.auto_awesome)),
            const SizedBox(width: 10),
            const Column(mainAxisAlignment: MainAxisAlignment.center, crossAxisAlignment: CrossAxisAlignment.start, children: [
              Text('Research OS', style: TextStyle(fontSize: 19, fontWeight: FontWeight.w800)),
              Text('Full Control Center', style: TextStyle(color: Colors.white54, fontSize: 11)),
            ]),
            const SizedBox(width: 22),
            Expanded(
              child: FutureBuilder<_Snapshot>(
                future: snapshot,
                builder: (context, value) {
                  if (!value.hasData) return const LinearProgressIndicator(minHeight: 2);
                  final data = value.data!;
                  return Wrap(spacing: 16, runSpacing: 4, crossAxisAlignment: WrapCrossAlignment.center, children: [
                    _TopChip(Icons.circle, 'Local Service', data.health['status']?.toString() ?? '-'),
                    _TopChip(Icons.link, '127.0.0.1', '8788'),
                    _TopChip(Icons.info_outline, 'Version', data.health['version']?.toString() ?? '-'),
                    _TopChip(Icons.account_tree_outlined, 'Scale', '${data.master['scale'] ?? '-'} → ${data.health['maximum_scale'] ?? '-'}'),
                    _TopChip(Icons.extension_outlined, 'Skills', '${data.skillList.length}'),
                    _TopChip(Icons.smart_toy_outlined, 'Agents', '${data.agentList.length}'),
                  ]);
                },
              ),
            ),
            SizedBox(width: 190, child: TextField(decoration: const InputDecoration(isDense: true, hintText: 'Search (Ctrl+K)', prefixIcon: Icon(Icons.search)))),
            const SizedBox(width: 8),
            IconButton(onPressed: onRefresh, icon: const Icon(Icons.refresh)),
            const CircleAvatar(radius: 16, child: Icon(Icons.person_outline, size: 18)),
            const SizedBox(width: 7),
            const Column(mainAxisAlignment: MainAxisAlignment.center, crossAxisAlignment: CrossAxisAlignment.start, children: [Text('Researcher', style: TextStyle(fontSize: 11)), Text('Full Access', style: TextStyle(fontSize: 10, color: Color(0xFF49E38B)))]),
          ],
        ),
      ),
    );
  }
}

class _TopChip extends StatelessWidget {
  const _TopChip(this.icon, this.label, this.value);
  final IconData icon;
  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return Row(mainAxisSize: MainAxisSize.min, children: [Icon(icon, size: 12, color: const Color(0xFF49E38B)), const SizedBox(width: 4), Text('$label ', style: const TextStyle(color: Colors.white54, fontSize: 10)), Text(value, style: const TextStyle(fontSize: 10, fontWeight: FontWeight.w700))]);
  }
}

class _Sidebar extends StatelessWidget {
  const _Sidebar({required this.selected, required this.onSelected});
  final int selected;
  final ValueChanged<int> onSelected;

  @override
  Widget build(BuildContext context) {
    return ListView(
      padding: const EdgeInsets.fromLTRB(8, 9, 8, 9),
      children: [
        for (var index = 0; index < _nav.length; index++) ...[
          if (index == 0 || _nav[index - 1].group != _nav[index].group)
            Padding(padding: const EdgeInsets.fromLTRB(9, 12, 8, 5), child: Text(_nav[index].group, style: const TextStyle(color: Colors.white38, fontSize: 10, fontWeight: FontWeight.w700))),
          Material(
            color: selected == index ? const Color(0xFF302271) : Colors.transparent,
            borderRadius: BorderRadius.circular(9),
            child: ListTile(dense: true, visualDensity: const VisualDensity(vertical: -2.5), leading: Icon(_nav[index].icon, size: 19), title: Text(_nav[index].label, style: const TextStyle(fontSize: 12.5)), onTap: () => onSelected(index)),
          ),
        ],
        const SizedBox(height: 14),
        const Card(child: Padding(padding: EdgeInsets.all(12), child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [Text('Researcher', style: TextStyle(fontWeight: FontWeight.w700, fontSize: 12)), SizedBox(height: 3), Text('Full Access', style: TextStyle(color: Color(0xFF49E38B), fontSize: 11))]))),
      ],
    );
  }
}

class _HomePage extends StatelessWidget {
  const _HomePage({required this.snapshot, required this.onRefresh});
  final Future<_Snapshot> snapshot;
  final VoidCallback onRefresh;

  @override
  Widget build(BuildContext context) {
    return _Frame(
      title: 'Full Control Center',
      subtitle: 'One Research OS app · V3 single backend authority',
      action: FilledButton.tonalIcon(onPressed: onRefresh, icon: const Icon(Icons.refresh), label: const Text('Refresh')),
      child: FutureBuilder<_Snapshot>(
        future: snapshot,
        builder: (context, value) {
          if (!value.hasData) return const Center(child: CircularProgressIndicator());
          final data = value.data!;
          return ListView(padding: const EdgeInsets.all(18), children: [
            Wrap(spacing: 10, runSpacing: 10, children: [
              _Metric('System', data.health['status']?.toString() ?? '-', Icons.monitor_heart_outlined),
              _Metric('Unified Master', data.master['scale']?.toString() ?? '-', Icons.account_tree_outlined),
              _Metric('Skills', '${data.skillList.length}', Icons.extension_outlined),
              _Metric('Tools', '${data.toolList.length}', Icons.build_outlined),
              _Metric('Agents', '${data.agentList.length}', Icons.smart_toy_outlined),
              _Metric('Providers', '${data.providerList.length}', Icons.hub_outlined),
            ]),
            const SizedBox(height: 16),
            _Card(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: const [
              Text('Unified execution path', style: TextStyle(fontWeight: FontWeight.w800, fontSize: 17)),
              SizedBox(height: 8),
              Text('Request → Unified Master → Brain → Skills / Tools / Agents → Provider → Evidence'),
              SizedBox(height: 5),
              Text('Software Factory: Master → Factory → Team → Tests → Release', style: TextStyle(color: Colors.white60)),
              SizedBox(height: 5),
              Text('Adaptive logical capacity 3¹ → 10¹⁰; execution remains lazy and bounded.', style: TextStyle(color: Color(0xFF49E38B))),
            ])),
          ]);
        },
      ),
    );
  }
}

class _Conversation {
  _Conversation(this.title);
  String title;
  final List<_Message> messages = [];
}

class _Message {
  const _Message(this.user, this.text, {this.meta});
  final bool user;
  final String text;
  final String? meta;
}

class _ChatPage extends StatefulWidget {
  const _ChatPage({required this.api, required this.snapshot});
  final V3Api api;
  final Future<_Snapshot> snapshot;

  @override
  State<_ChatPage> createState() => _ChatPageState();
}

class _ChatPageState extends State<_ChatPage> {
  final _composer = TextEditingController();
  final _search = TextEditingController();
  final List<_Conversation> _conversations = [_Conversation('สร้างแผนพัฒนา Research OS V3.1')];
  int _selected = 0;
  bool _sending = false;
  String? _provider;

  @override
  void dispose() {
    _composer.dispose();
    _search.dispose();
    super.dispose();
  }

  void _newChat() => setState(() { _conversations.insert(0, _Conversation('New Chat')); _selected = 0; });

  Future<void> _send() async {
    final text = _composer.text.trim();
    if (text.isEmpty || _sending) return;
    final conversation = _conversations[_selected];
    setState(() {
      conversation.messages.add(_Message(true, text));
      if (conversation.title == 'New Chat') conversation.title = text.length > 42 ? '${text.substring(0, 42)}…' : text;
      _composer.clear();
      _sending = true;
    });
    try {
      final response = await widget.api.chat(text, preferredProvider: _provider);
      if (!mounted) return;
      setState(() => conversation.messages.add(_Message(false, response['text']?.toString() ?? 'No response', meta: '${response['provider'] ?? '-'} · ${response['model'] ?? '-'}')));
    } catch (error) {
      if (mounted) setState(() => conversation.messages.add(_Message(false, 'Error: $error')));
    } finally {
      if (mounted) setState(() => _sending = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final current = _conversations[_selected];
    return LayoutBuilder(builder: (context, constraints) {
      final showRight = constraints.maxWidth >= 1120;
      return Column(children: [
        Expanded(child: Row(children: [
          SizedBox(width: 270, child: _ConversationPane(conversations: _conversations, selected: _selected, onSelected: (value) => setState(() => _selected = value), onNew: _newChat, search: _search)),
          const VerticalDivider(width: 1),
          Expanded(child: _ChatCenter(api: widget.api, snapshot: widget.snapshot, conversation: current, composer: _composer, provider: _provider, sending: _sending, onProvider: (value) => setState(() => _provider = value), onSend: _send)),
          if (showRight) ...[const VerticalDivider(width: 1), SizedBox(width: 290, child: _SystemPanel(snapshot: widget.snapshot))],
        ])),
        const _ToolDiscoveryStrip(),
      ]);
    });
  }
}

class _ConversationPane extends StatelessWidget {
  const _ConversationPane({required this.conversations, required this.selected, required this.onSelected, required this.onNew, required this.search});
  final List<_Conversation> conversations;
  final int selected;
  final ValueChanged<int> onSelected;
  final VoidCallback onNew;
  final TextEditingController search;

  @override
  Widget build(BuildContext context) {
    return Padding(padding: const EdgeInsets.all(12), child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      Row(children: [const Expanded(child: Text('Conversations', style: TextStyle(fontWeight: FontWeight.w800))), FilledButton.icon(onPressed: onNew, icon: const Icon(Icons.add, size: 16), label: const Text('New Chat'))]),
      const SizedBox(height: 9),
      TextField(controller: search, decoration: const InputDecoration(isDense: true, hintText: 'Search conversations...', prefixIcon: Icon(Icons.search))),
      const SizedBox(height: 9),
      const Wrap(spacing: 6, children: [Chip(label: Text('All')), Chip(label: Text('Pinned')), Chip(label: Text('Today'))]),
      const SizedBox(height: 6),
      Expanded(child: ListView.builder(itemCount: conversations.length, itemBuilder: (context, index) => Card(color: selected == index ? const Color(0xFF302271) : null, child: ListTile(dense: true, title: Text(conversations[index].title, maxLines: 2, overflow: TextOverflow.ellipsis), subtitle: Text('${conversations[index].messages.length} messages'), onTap: () => onSelected(index))))),
    ]));
  }
}

class _ChatCenter extends StatelessWidget {
  const _ChatCenter({required this.api, required this.snapshot, required this.conversation, required this.composer, required this.provider, required this.sending, required this.onProvider, required this.onSend});
  final V3Api api;
  final Future<_Snapshot> snapshot;
  final _Conversation conversation;
  final TextEditingController composer;
  final String? provider;
  final bool sending;
  final ValueChanged<String?> onProvider;
  final VoidCallback onSend;

  @override
  Widget build(BuildContext context) {
    return Column(children: [
      Padding(padding: const EdgeInsets.fromLTRB(16, 13, 16, 10), child: Row(children: [Expanded(child: Text(conversation.title, style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 17))), const Icon(Icons.star_border), const SizedBox(width: 10), const Icon(Icons.share_outlined)])),
      const Divider(height: 1),
      Expanded(child: conversation.messages.isEmpty ? const Center(child: Column(mainAxisSize: MainAxisSize.min, children: [Icon(Icons.auto_awesome, size: 44, color: Color(0xFF8B7BFF)), SizedBox(height: 10), Text('Research OS AI', style: TextStyle(fontWeight: FontWeight.w800, fontSize: 18)), Text('Ask Research OS using V3 Brain, Skills, Tools, Agents and Memory.', style: TextStyle(color: Colors.white54))])) : ListView.builder(padding: const EdgeInsets.all(16), itemCount: conversation.messages.length, itemBuilder: (context, index) => _Bubble(conversation.messages[index]))),
      Padding(padding: const EdgeInsets.all(12), child: FutureBuilder<_Snapshot>(future: snapshot, builder: (context, value) {
        final providers = value.data?.providerList ?? const <Map<String, dynamic>>[];
        return Row(children: [
          Expanded(child: TextField(controller: composer, minLines: 1, maxLines: 5, onSubmitted: (_) => onSend(), decoration: const InputDecoration(hintText: 'Message Research OS AI…', prefixIcon: Icon(Icons.attach_file)))),
          const SizedBox(width: 8),
          SizedBox(width: 160, child: DropdownButtonFormField<String>(initialValue: provider, isExpanded: true, decoration: const InputDecoration(isDense: true), items: [const DropdownMenuItem(value: null, child: Text('Auto Provider')), ...providers.map((item) => DropdownMenuItem(value: item['name']?.toString(), child: Text(item['name']?.toString() ?? '-')))], onChanged: onProvider)),
          const SizedBox(width: 8),
          FilledButton.icon(onPressed: sending ? null : onSend, icon: const Icon(Icons.send), label: const Text('Send')),
        ]);
      })),
    ]);
  }
}

class _Bubble extends StatelessWidget {
  const _Bubble(this.message);
  final _Message message;

  @override
  Widget build(BuildContext context) {
    return Align(alignment: message.user ? Alignment.centerRight : Alignment.centerLeft, child: Container(constraints: const BoxConstraints(maxWidth: 760), margin: const EdgeInsets.only(bottom: 10), padding: const EdgeInsets.all(13), decoration: BoxDecoration(color: message.user ? const Color(0xFF2B2363) : const Color(0xFF0B1725), border: Border.all(color: const Color(0xFF203044)), borderRadius: BorderRadius.circular(12)), child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [Text(message.text), if (message.meta != null) ...[const SizedBox(height: 6), Text(message.meta!, style: const TextStyle(color: Colors.white38, fontSize: 10))]])));
  }
}

class _SystemPanel extends StatelessWidget {
  const _SystemPanel({required this.snapshot});
  final Future<_Snapshot> snapshot;

  @override
  Widget build(BuildContext context) {
    return FutureBuilder<_Snapshot>(future: snapshot, builder: (context, value) {
      if (!value.hasData) return const Center(child: CircularProgressIndicator());
      final data = value.data!;
      return ListView(padding: const EdgeInsets.all(11), children: [
        _SideCard('System Status', '${data.health['status'] ?? '-'}', Icons.monitor_heart_outlined),
        const SizedBox(height: 9),
        _SideCard('Unified Master', '${data.master['scale'] ?? '-'} → ${data.health['maximum_scale'] ?? '-'}', Icons.account_tree_outlined),
        const SizedBox(height: 9),
        _SideCard('Skills & Tools', '${data.skillList.length} / ${data.toolList.length}', Icons.extension_outlined),
        const SizedBox(height: 9),
        _SideCard('Active Agents', '${data.agentList.length}', Icons.smart_toy_outlined),
        const SizedBox(height: 9),
        _SideCard('Providers', '${data.providerList.length}', Icons.hub_outlined),
      ]);
    });
  }
}

class _SideCard extends StatelessWidget {
  const _SideCard(this.title, this.value, this.icon);
  final String title;
  final String value;
  final IconData icon;

  @override
  Widget build(BuildContext context) => Card(child: Padding(padding: const EdgeInsets.all(13), child: Row(children: [Icon(icon, color: const Color(0xFF8B7BFF)), const SizedBox(width: 10), Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [Text(title, style: const TextStyle(color: Colors.white54, fontSize: 11)), Text(value, style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 16, color: Color(0xFF49E38B)))]) )])));
}

class _ToolDiscoveryStrip extends StatelessWidget {
  const _ToolDiscoveryStrip();

  @override
  Widget build(BuildContext context) {
    const steps = [
      ('1. Intent Analysis', Icons.manage_search),
      ('2. Tool Search', Icons.search),
      ('3. Evaluation', Icons.verified_user_outlined),
      ('4. Permission', Icons.security_outlined),
      ('5. Planning', Icons.route_outlined),
      ('6. Execution', Icons.play_circle_outline),
      ('7. Result & Learn', Icons.school_outlined),
    ];
    return Container(height: 98, decoration: const BoxDecoration(border: Border(top: BorderSide(color: Color(0xFF203044)))), child: Padding(padding: const EdgeInsets.all(8), child: Row(children: [
      for (var index = 0; index < steps.length; index++) ...[
        Expanded(child: Card(child: Padding(padding: const EdgeInsets.all(8), child: Row(children: [Icon(steps[index].$2, size: 18, color: const Color(0xFF8B7BFF)), const SizedBox(width: 6), Expanded(child: Text(steps[index].$1, style: const TextStyle(fontSize: 10.5, fontWeight: FontWeight.w700)))]))),
        if (index < steps.length - 1) const Icon(Icons.arrow_forward, size: 14, color: Colors.white38),
      ],
    ])));
  }
}

class _AgentsPage extends StatelessWidget {
  const _AgentsPage({required this.api, required this.snapshot});
  final V3Api api;
  final Future<_Snapshot> snapshot;

  Future<void> _run(BuildContext context, Map<String, dynamic> agent) async {
    final controller = TextEditingController();
    final prompt = await showDialog<String>(context: context, builder: (dialogContext) => AlertDialog(title: Text('Run ${agent['name']}'), content: TextField(controller: controller, minLines: 3, maxLines: 6, decoration: const InputDecoration(labelText: 'Task')), actions: [TextButton(onPressed: () => Navigator.pop(dialogContext), child: const Text('Cancel')), FilledButton(onPressed: () => Navigator.pop(dialogContext, controller.text.trim()), child: const Text('Run'))]));
    controller.dispose();
    if (prompt == null || prompt.isEmpty || !context.mounted) return;
    try { final result = await api.runAgent(agent['name']?.toString() ?? '', prompt); if (context.mounted) _showJson(context, 'Agent Result', result); } catch (error) { if (context.mounted) _snack(context, 'Agent failed: $error'); }
  }

  @override
  Widget build(BuildContext context) => _Frame(title: 'Agent Center', subtitle: 'Role-based V3 agents', child: FutureBuilder<_Snapshot>(future: snapshot, builder: (context, value) {
    if (!value.hasData) return const Center(child: CircularProgressIndicator());
    return ListView(padding: const EdgeInsets.all(16), children: [for (final item in value.data!.agentList) Card(child: ListTile(leading: const CircleAvatar(child: Icon(Icons.smart_toy_outlined)), title: Text(item['name']?.toString() ?? '-'), subtitle: Text('${item['role'] ?? ''}\n${item['description'] ?? ''}'), isThreeLine: true, trailing: FilledButton.tonal(onPressed: () => _run(context, item), child: const Text('Run'))))]);
  }));
}

class _MemoryPage extends StatefulWidget {
  const _MemoryPage({required this.api});
  final V3Api api;
  @override State<_MemoryPage> createState() => _MemoryPageState();
}

class _MemoryPageState extends State<_MemoryPage> {
  final _query = TextEditingController();
  final _newMemory = TextEditingController();
  late Future<Map<String, dynamic>> _future;
  @override void initState() { super.initState(); _future = widget.api.memory(); }
  @override void dispose() { _query.dispose(); _newMemory.dispose(); super.dispose(); }
  void _search() => setState(() => _future = widget.api.memory(query: _query.text.trim()));
  Future<void> _add() async { final text = _newMemory.text.trim(); if (text.isEmpty) return; await widget.api.addMemory(text, tags: const ['full-control-center']); _newMemory.clear(); _search(); }
  @override Widget build(BuildContext context) => _Frame(title: 'Memory', subtitle: 'User/profile-isolated durable memory', child: Column(children: [
    Row(children: [Expanded(child: TextField(controller: _query, onSubmitted: (_) => _search(), decoration: const InputDecoration(labelText: 'Search Memory', prefixIcon: Icon(Icons.search)))), const SizedBox(width: 8), FilledButton(onPressed: _search, child: const Text('Search'))]),
    const SizedBox(height: 8),
    Row(children: [Expanded(child: TextField(controller: _newMemory, decoration: const InputDecoration(labelText: 'Add durable memory'))), const SizedBox(width: 8), FilledButton.tonal(onPressed: _add, child: const Text('Add'))]),
    const SizedBox(height: 10),
    Expanded(child: FutureBuilder<Map<String, dynamic>>(future: _future, builder: (context, value) { if (!value.hasData) return const Center(child: CircularProgressIndicator()); final items = _maps(value.data!['memory']); return ListView(children: [for (final item in items) Card(child: ListTile(leading: const Icon(Icons.memory), title: Text(item['text']?.toString() ?? '-'), subtitle: Text((item['tags'] as List?)?.join(', ') ?? '')))]); })),
  ]));
}

class _CatalogPage extends StatelessWidget {
  const _CatalogPage({required this.title, required this.snapshot, required this.kind});
  final String title;
  final Future<_Snapshot> snapshot;
  final String kind;
  @override Widget build(BuildContext context) => _Frame(title: title, subtitle: 'Live V3 registry', child: FutureBuilder<_Snapshot>(future: snapshot, builder: (context, value) {
    if (!value.hasData) return const Center(child: CircularProgressIndicator());
    final items = kind == 'skills' ? value.data!.skillList : value.data!.providerList;
    return ListView(padding: const EdgeInsets.all(16), children: [for (final item in items) Card(child: ListTile(leading: Icon(kind == 'skills' ? Icons.extension_outlined : Icons.hub_outlined), title: Text(item['name']?.toString() ?? '-'), subtitle: Text(item['description']?.toString() ?? item['model']?.toString() ?? item['capability']?.toString() ?? '-')))]);
  }));
}

class _ToolsPage extends StatelessWidget {
  const _ToolsPage({required this.api, required this.snapshot});
  final V3Api api;
  final Future<_Snapshot> snapshot;

  Future<void> _run(BuildContext context, Map<String, dynamic> tool) async {
    final args = TextEditingController(text: '{}');
    var approved = false;
    final payload = await showDialog<(String, bool)?>(context: context, builder: (dialogContext) => StatefulBuilder(builder: (context, setState) => AlertDialog(title: Text('Run ${tool['name']}'), content: Column(mainAxisSize: MainAxisSize.min, children: [TextField(controller: args, minLines: 4, maxLines: 8, decoration: const InputDecoration(labelText: 'JSON arguments')), CheckboxListTile(value: approved, onChanged: (value) => setState(() => approved = value ?? false), title: const Text('Owner approval'))]), actions: [TextButton(onPressed: () => Navigator.pop(dialogContext), child: const Text('Cancel')), FilledButton(onPressed: () => Navigator.pop(dialogContext, (args.text, approved)), child: const Text('Run'))])));
    args.dispose();
    if (payload == null || !context.mounted) return;
    try { final decoded = jsonDecode(payload.$1); if (decoded is! Map) throw const FormatException('Arguments must be JSON object'); final result = await api.executeTool(tool['name']?.toString() ?? '', Map<String, dynamic>.from(decoded), approved: payload.$2); if (context.mounted) _showJson(context, 'Tool Result', result); } catch (error) { if (context.mounted) _snack(context, 'Tool failed: $error'); }
  }

  @override Widget build(BuildContext context) => _Frame(title: 'Tools', subtitle: 'Governed V3 Tool Registry', child: FutureBuilder<_Snapshot>(future: snapshot, builder: (context, value) {
    if (!value.hasData) return const Center(child: CircularProgressIndicator());
    return ListView(padding: const EdgeInsets.all(16), children: [for (final item in value.data!.toolList) Card(child: ListTile(leading: const Icon(Icons.build_outlined), title: Text(item['name']?.toString() ?? '-'), subtitle: Text('${item['description'] ?? ''}\nRisk: ${item['risk'] ?? '-'} · approval: ${item['approval_required'] ?? false}'), isThreeLine: true, trailing: FilledButton.tonal(onPressed: () => _run(context, item), child: const Text('Run'))))]);
  }));
}

class _FactoryPage extends StatefulWidget {
  const _FactoryPage({required this.api}); final V3Api api; @override State<_FactoryPage> createState() => _FactoryPageState();
}
class _FactoryPageState extends State<_FactoryPage> {
  final _tasks = TextEditingController(text: '30'); final _risk = TextEditingController(text: '2'); final _parallelism = TextEditingController(text: '4'); Map<String, dynamic>? _plan;
  @override void dispose() { _tasks.dispose(); _risk.dispose(); _parallelism.dispose(); super.dispose(); }
  Future<void> _run() async { final result = await widget.api.factoryPlan(tasks: int.tryParse(_tasks.text) ?? 30, risk: int.tryParse(_risk.text) ?? 2, parallelism: int.tryParse(_parallelism.text) ?? 4); if (mounted) setState(() => _plan = result); }
  @override Widget build(BuildContext context) => _Frame(title: 'Software Factory', subtitle: 'Master → Factory → Team → Tests → Release', child: ListView(padding: const EdgeInsets.all(16), children: [Row(children: [Expanded(child: TextField(controller: _tasks, decoration: const InputDecoration(labelText: 'Tasks'))), const SizedBox(width: 8), Expanded(child: TextField(controller: _risk, decoration: const InputDecoration(labelText: 'Risk'))), const SizedBox(width: 8), Expanded(child: TextField(controller: _parallelism, decoration: const InputDecoration(labelText: 'Parallelism'))), const SizedBox(width: 8), FilledButton.icon(onPressed: _run, icon: const Icon(Icons.account_tree_outlined), label: const Text('Plan'))]), const SizedBox(height: 12), if (_plan != null) _Card(child: SelectableText(const JsonEncoder.withIndent('  ').convert(_plan), style: const TextStyle(fontFamily: 'Consolas')))]));
}

class _Frame extends StatelessWidget {
  const _Frame({required this.title, required this.subtitle, required this.child, this.action});
  final String title; final String subtitle; final Widget child; final Widget? action;
  @override Widget build(BuildContext context) => Column(children: [Padding(padding: const EdgeInsets.fromLTRB(18, 14, 18, 10), child: Row(children: [Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [Text(title, style: const TextStyle(fontSize: 20, fontWeight: FontWeight.w800)), Text(subtitle, style: const TextStyle(color: Colors.white54, fontSize: 11))])), if (action != null) action!])), const Divider(height: 1), Expanded(child: child)]);
}

class _Metric extends StatelessWidget {
  const _Metric(this.label, this.value, this.icon); final String label; final String value; final IconData icon;
  @override Widget build(BuildContext context) => SizedBox(width: 180, height: 100, child: Card(child: Padding(padding: const EdgeInsets.all(13), child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [Icon(icon, color: const Color(0xFF8B7BFF), size: 20), const Spacer(), Text(label, style: const TextStyle(color: Colors.white54, fontSize: 11)), Text(value, maxLines: 1, overflow: TextOverflow.ellipsis, style: const TextStyle(fontSize: 17, fontWeight: FontWeight.w800, color: Color(0xFF49E38B)))]))));
}

class _Card extends StatelessWidget {
  const _Card({required this.child}); final Widget child; @override Widget build(BuildContext context) => Card(child: Padding(padding: const EdgeInsets.all(14), child: child));
}

List<Map<String, dynamic>> _maps(dynamic value) { if (value is! List) return const []; return value.whereType<Map>().map((item) => Map<String, dynamic>.from(item)).toList(); }
void _snack(BuildContext context, String text) => ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(text)));
Future<void> _showJson(BuildContext context, String title, Map<String, dynamic> value) => showDialog<void>(context: context, builder: (dialogContext) => AlertDialog(title: Text(title), content: SizedBox(width: 760, child: SingleChildScrollView(child: SelectableText(const JsonEncoder.withIndent('  ').convert(value), style: const TextStyle(fontFamily: 'Consolas')))), actions: [TextButton(onPressed: () => Navigator.pop(dialogContext), child: const Text('Close'))]));
