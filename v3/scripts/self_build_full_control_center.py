from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

REQUIRED_NAV = (
    "Home", "Chat AI", "Agents", "Memory", "Skills", "Tools", "Factory", "Providers",
    "Files", "Repositories", "GitHub", "Drive", "Runtime", "Installer", "Backup", "Restore", "Shell",
)

DART_TEMPLATE = r'''import 'package:flutter/material.dart';

import 'api/v3_api.dart';

class ResearchOSV3App extends StatelessWidget {
  const ResearchOSV3App({super.key, required this.api});

  final V3Api api;

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Research OS Full Control Center',
      debugShowCheckedModeBanner: false,
      themeMode: ThemeMode.dark,
      darkTheme: ThemeData(
        brightness: Brightness.dark,
        colorScheme: ColorScheme.fromSeed(
          seedColor: const Color(0xFF6246EA),
          brightness: Brightness.dark,
        ),
        useMaterial3: true,
        scaffoldBackgroundColor: const Color(0xFF08111E),
        cardTheme: const CardThemeData(
          elevation: 0,
          margin: EdgeInsets.zero,
        ),
      ),
      home: _FullControlShell(api: api),
    );
  }
}

class _NavItem {
  const _NavItem(this.label, this.icon, this.group);
  final String label;
  final IconData icon;
  final String group;
}

const _navItems = <_NavItem>[
  _NavItem('Home', Icons.home_outlined, 'MAIN'),
  _NavItem('Chat AI', Icons.chat_bubble_outline, 'MAIN'),
  _NavItem('Agents', Icons.smart_toy_outlined, 'MAIN'),
  _NavItem('Memory', Icons.memory_outlined, 'MAIN'),
  _NavItem('Skills', Icons.extension_outlined, 'MAIN'),
  _NavItem('Tools', Icons.build_outlined, 'MAIN'),
  _NavItem('Factory', Icons.account_tree_outlined, 'MAIN'),
  _NavItem('Providers', Icons.hub_outlined, 'MAIN'),
  _NavItem('Files', Icons.folder_outlined, 'WORKSPACE'),
  _NavItem('Repositories', Icons.inventory_2_outlined, 'WORKSPACE'),
  _NavItem('GitHub', Icons.code, 'WORKSPACE'),
  _NavItem('Drive', Icons.cloud_outlined, 'WORKSPACE'),
  _NavItem('Runtime', Icons.dns_outlined, 'SYSTEM'),
  _NavItem('Installer', Icons.inventory_outlined, 'SYSTEM'),
  _NavItem('Backup', Icons.backup_outlined, 'SYSTEM'),
  _NavItem('Restore', Icons.restore_outlined, 'SYSTEM'),
  _NavItem('Shell', Icons.terminal_outlined, 'SYSTEM'),
];

class _FullControlShell extends StatefulWidget {
  const _FullControlShell({required this.api});
  final V3Api api;

  @override
  State<_FullControlShell> createState() => _FullControlShellState();
}

class _FullControlShellState extends State<_FullControlShell> {
  int _selected = 0;
  late Future<_SystemSnapshot> _snapshot;

  @override
  void initState() {
    super.initState();
    _snapshot = _load();
  }

  Future<_SystemSnapshot> _load() async {
    final values = await Future.wait<Map<String, dynamic>>([
      widget.api.health(),
      widget.api.master(tasks: 30),
      widget.api.skills(),
      widget.api.tools(),
      widget.api.agents(),
      widget.api.providers(),
    ]);
    return _SystemSnapshot(
      health: values[0],
      master: values[1],
      skills: values[2],
      tools: values[3],
      agents: values[4],
      providers: values[5],
    );
  }

  void _refresh() => setState(() => _snapshot = _load());

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Column(
          children: [
            _TopBar(snapshot: _snapshot, onRefresh: _refresh),
            const Divider(height: 1),
            Expanded(
              child: Row(
                children: [
                  SizedBox(
                    width: 190,
                    child: _SideBar(
                      selected: _selected,
                      onSelected: (value) => setState(() => _selected = value),
                    ),
                  ),
                  const VerticalDivider(width: 1),
                  Expanded(
                    child: _PageRouter(
                      index: _selected,
                      api: widget.api,
                      snapshot: _snapshot,
                      onRefresh: _refresh,
                    ),
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

class _TopBar extends StatelessWidget {
  const _TopBar({required this.snapshot, required this.onRefresh});
  final Future<_SystemSnapshot> snapshot;
  final VoidCallback onRefresh;

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      height: 70,
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 18),
        child: Row(
          children: [
            Container(
              width: 38,
              height: 38,
              decoration: BoxDecoration(
                color: const Color(0xFF3157D5),
                borderRadius: BorderRadius.circular(10),
              ),
              child: const Icon(Icons.auto_awesome, color: Colors.white),
            ),
            const SizedBox(width: 12),
            const Column(
              mainAxisAlignment: MainAxisAlignment.center,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('Research OS', style: TextStyle(fontSize: 20, fontWeight: FontWeight.w800)),
                Text('Full Control Center', style: TextStyle(fontSize: 12, color: Colors.white60)),
              ],
            ),
            const SizedBox(width: 28),
            Expanded(
              child: FutureBuilder<_SystemSnapshot>(
                future: snapshot,
                builder: (context, value) {
                  if (!value.hasData) return const LinearProgressIndicator(minHeight: 2);
                  final data = value.data!;
                  return Wrap(
                    spacing: 18,
                    runSpacing: 6,
                    crossAxisAlignment: WrapCrossAlignment.center,
                    children: [
                      _TopMetric('Service', data.health['status']?.toString() ?? '-'),
                      _TopMetric('Version', data.health['version']?.toString() ?? '-'),
                      _TopMetric('Scale', '${data.master['scale'] ?? '-'} → ${data.health['maximum_scale'] ?? '-'}'),
                      _TopMetric('Skills', '${data.skillList.length}'),
                      _TopMetric('Tools', '${data.toolList.length}'),
                      _TopMetric('Agents', '${data.agentList.length}'),
                    ],
                  );
                },
              ),
            ),
            IconButton(onPressed: onRefresh, tooltip: 'Refresh system status', icon: const Icon(Icons.refresh)),
            const CircleAvatar(radius: 16, child: Icon(Icons.person_outline, size: 18)),
          ],
        ),
      ),
    );
  }
}

class _TopMetric extends StatelessWidget {
  const _TopMetric(this.label, this.value);
  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Text('$label: ', style: const TextStyle(color: Colors.white54, fontSize: 12)),
        Text(value, style: const TextStyle(color: Color(0xFF47E68A), fontWeight: FontWeight.w700, fontSize: 12)),
      ],
    );
  }
}

class _SideBar extends StatelessWidget {
  const _SideBar({required this.selected, required this.onSelected});
  final int selected;
  final ValueChanged<int> onSelected;

  @override
  Widget build(BuildContext context) {
    String? group;
    return ListView.builder(
      padding: const EdgeInsets.fromLTRB(10, 12, 10, 12),
      itemCount: _navItems.length + 1,
      itemBuilder: (context, rawIndex) {
        if (rawIndex == _navItems.length) {
          return const Padding(
            padding: EdgeInsets.only(top: 18),
            child: Card(
              child: Padding(
                padding: EdgeInsets.all(12),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('Researcher', style: TextStyle(fontWeight: FontWeight.w700)),
                    SizedBox(height: 4),
                    Text('Full Access', style: TextStyle(fontSize: 12, color: Color(0xFF47E68A))),
                  ],
                ),
              ),
            ),
          );
        }
        final item = _navItems[rawIndex];
        final changed = item.group != group;
        group = item.group;
        return Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            if (changed)
              Padding(
                padding: const EdgeInsets.fromLTRB(10, 14, 8, 6),
                child: Text(item.group, style: const TextStyle(color: Colors.white38, fontSize: 11, fontWeight: FontWeight.w700)),
              ),
            Material(
              color: selected == rawIndex ? const Color(0xFF302271) : Colors.transparent,
              borderRadius: BorderRadius.circular(9),
              child: ListTile(
                dense: true,
                visualDensity: const VisualDensity(vertical: -2),
                leading: Icon(item.icon, size: 20),
                title: Text(item.label, style: const TextStyle(fontSize: 13)),
                onTap: () => onSelected(rawIndex),
              ),
            ),
          ],
        );
      },
    );
  }
}

class _PageRouter extends StatelessWidget {
  const _PageRouter({required this.index, required this.api, required this.snapshot, required this.onRefresh});
  final int index;
  final V3Api api;
  final Future<_SystemSnapshot> snapshot;
  final VoidCallback onRefresh;

  @override
  Widget build(BuildContext context) {
    switch (index) {
      case 0:
        return _HomePage(snapshot: snapshot, onRefresh: onRefresh);
      case 1:
        return _ChatControlPage(api: api, snapshot: snapshot);
      case 2:
        return _CatalogPage(title: 'Agent Center', future: snapshot, kind: 'agents');
      case 3:
        return _MemoryPage(api: api);
      case 4:
        return _CatalogPage(title: 'Skills', future: snapshot, kind: 'skills');
      case 5:
        return _CatalogPage(title: 'Tools', future: snapshot, kind: 'tools');
      case 6:
        return _FactoryPage(api: api);
      case 7:
        return _CatalogPage(title: 'Providers', future: snapshot, kind: 'providers');
      default:
        return _OperationalPage(item: _navItems[index], api: api, snapshot: snapshot);
    }
  }
}

class _HomePage extends StatelessWidget {
  const _HomePage({required this.snapshot, required this.onRefresh});
  final Future<_SystemSnapshot> snapshot;
  final VoidCallback onRefresh;

  @override
  Widget build(BuildContext context) {
    return _Frame(
      title: 'Full Control Center',
      subtitle: 'Morning GUI · V3.1 single backend authority',
      action: FilledButton.tonalIcon(onPressed: onRefresh, icon: const Icon(Icons.refresh), label: const Text('Refresh')),
      child: FutureBuilder<_SystemSnapshot>(
        future: snapshot,
        builder: (context, value) {
          if (value.connectionState != ConnectionState.done) return const Center(child: CircularProgressIndicator());
          if (value.hasError) return Center(child: Text('Research OS service unavailable: ${value.error}'));
          final data = value.data!;
          return ListView(
            padding: const EdgeInsets.all(20),
            children: [
              Wrap(
                spacing: 12,
                runSpacing: 12,
                children: [
                  _MetricCard('System Status', data.health['status']?.toString() ?? '-', Icons.monitor_heart_outlined),
                  _MetricCard('Unified Master', data.master['scale']?.toString() ?? '-', Icons.account_tree_outlined),
                  _MetricCard('Skills', '${data.skillList.length}', Icons.extension_outlined),
                  _MetricCard('Tools', '${data.toolList.length}', Icons.build_outlined),
                  _MetricCard('Agents', '${data.agentList.length}', Icons.smart_toy_outlined),
                  _MetricCard('Providers', '${data.providerList.length}', Icons.hub_outlined),
                ],
              ),
              const SizedBox(height: 18),
              const Text('AI Core', style: TextStyle(fontWeight: FontWeight.w800, fontSize: 18)),
              const SizedBox(height: 10),
              const _FeatureGrid(items: [
                ('Unified Master', Icons.auto_awesome), ('Skills', Icons.extension), ('Tools', Icons.build),
                ('Agents', Icons.smart_toy), ('Memory', Icons.memory), ('Factory', Icons.account_tree),
              ]),
              const SizedBox(height: 18),
              const Text('Workspace', style: TextStyle(fontWeight: FontWeight.w800, fontSize: 18)),
              const SizedBox(height: 10),
              const _FeatureGrid(items: [
                ('Files', Icons.folder), ('Repositories', Icons.inventory_2), ('GitHub', Icons.code), ('Drive', Icons.cloud),
              ]),
              const SizedBox(height: 18),
              const Text('System', style: TextStyle(fontWeight: FontWeight.w800, fontSize: 18)),
              const SizedBox(height: 10),
              const _FeatureGrid(items: [
                ('Runtime', Icons.dns), ('Installer', Icons.inventory), ('Backup', Icons.backup),
                ('Restore', Icons.restore), ('Shell', Icons.terminal),
              ]),
            ],
          );
        },
      ),
    );
  }
}

class _FeatureGrid extends StatelessWidget {
  const _FeatureGrid({required this.items});
  final List<(String, IconData)> items;

  @override
  Widget build(BuildContext context) {
    return Wrap(
      spacing: 12,
      runSpacing: 12,
      children: [
        for (final item in items)
          SizedBox(
            width: 170,
            height: 86,
            child: Card(
              child: Padding(
                padding: const EdgeInsets.all(14),
                child: Row(children: [Icon(item.$2, color: const Color(0xFF8C7CFF)), const SizedBox(width: 12), Expanded(child: Text(item.$1, style: const TextStyle(fontWeight: FontWeight.w700)))]),
              ),
            ),
          ),
      ],
    );
  }
}

class _ChatControlPage extends StatefulWidget {
  const _ChatControlPage({required this.api, required this.snapshot});
  final V3Api api;
  final Future<_SystemSnapshot> snapshot;

  @override
  State<_ChatControlPage> createState() => _ChatControlPageState();
}

class _ChatControlPageState extends State<_ChatControlPage> {
  final _controller = TextEditingController();
  final _messages = <_Message>[];
  bool _sending = false;
  String? _provider;

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  Future<void> _send() async {
    final text = _controller.text.trim();
    if (text.isEmpty || _sending) return;
    setState(() {
      _messages.add(_Message(true, text));
      _controller.clear();
      _sending = true;
    });
    try {
      final response = await widget.api.chat(text, preferredProvider: _provider);
      if (!mounted) return;
      setState(() => _messages.add(_Message(false, response['text']?.toString() ?? 'No response', meta: '${response['provider'] ?? '-'} · ${response['model'] ?? '-'}')));
    } catch (error) {
      if (mounted) setState(() => _messages.add(_Message(false, 'Error: $error')));
    } finally {
      if (mounted) setState(() => _sending = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return FutureBuilder<_SystemSnapshot>(
      future: widget.snapshot,
      builder: (context, value) {
        final data = value.data;
        final providers = data?.providerList ?? const <Map<String, dynamic>>[];
        return Row(
          children: [
            SizedBox(width: 255, child: _ConversationPanel()),
            const VerticalDivider(width: 1),
            Expanded(
              child: Column(
                children: [
                  Padding(
                    padding: const EdgeInsets.fromLTRB(18, 14, 18, 10),
                    child: Row(
                      children: [
                        const Expanded(child: Text('Chat AI · Research OS', style: TextStyle(fontSize: 18, fontWeight: FontWeight.w800))),
                        SizedBox(
                          width: 190,
                          child: DropdownButtonFormField<String>(
                            value: _provider,
                            isExpanded: true,
                            decoration: const InputDecoration(labelText: 'Provider', isDense: true),
                            items: [
                              const DropdownMenuItem(value: null, child: Text('Auto')),
                              ...providers.map((p) => DropdownMenuItem(value: p['name']?.toString(), child: Text(p['name']?.toString() ?? 'provider'))),
                            ],
                            onChanged: (v) => setState(() => _provider = v),
                          ),
                        ),
                      ],
                    ),
                  ),
                  const Divider(height: 1),
                  Expanded(
                    child: _messages.isEmpty
                        ? const _EmptyChat()
                        : ListView.builder(
                            padding: const EdgeInsets.all(20),
                            itemCount: _messages.length,
                            itemBuilder: (context, index) => _MessageBubble(message: _messages[index]),
                          ),
                  ),
                  Padding(
                    padding: const EdgeInsets.fromLTRB(16, 8, 16, 8),
                    child: Row(
                      children: [
                        Expanded(
                          child: TextField(
                            controller: _controller,
                            minLines: 1,
                            maxLines: 5,
                            onSubmitted: (_) => _send(),
                            decoration: const InputDecoration(
                              hintText: 'Message Research OS AI…',
                              border: OutlineInputBorder(),
                              prefixIcon: Icon(Icons.attach_file),
                            ),
                          ),
                        ),
                        const SizedBox(width: 8),
                        FilledButton.icon(onPressed: _sending ? null : _send, icon: const Icon(Icons.send), label: const Text('Send')),
                      ],
                    ),
                  ),
                  const _ToolDiscoveryStrip(),
                ],
              ),
            ),
            const VerticalDivider(width: 1),
            SizedBox(width: 285, child: _ContextPanel(snapshot: widget.snapshot)),
          ],
        );
      },
    );
  }
}

class _ConversationPanel extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.all(12),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Row(children: [const Expanded(child: Text('Conversations', style: TextStyle(fontWeight: FontWeight.w800))), FilledButton.tonal(onPressed: () {}, child: const Text('+ New'))]),
          const SizedBox(height: 10),
          const TextField(decoration: InputDecoration(hintText: 'Search conversations…', prefixIcon: Icon(Icons.search), isDense: true, border: OutlineInputBorder())),
          const SizedBox(height: 12),
          for (final item in const [
            'สร้างแผนพัฒนา Research OS V3.1', 'วิเคราะห์ Architecture ระบบ', 'สรุปความสามารถของระบบ',
            'Factory Stage 5 → 6', 'ตรวจสอบ Provider Status', 'Backup และ Restore'
          ])
            Card(
              child: ListTile(
                dense: true,
                leading: const Icon(Icons.chat_bubble_outline, size: 18),
                title: Text(item, maxLines: 2, overflow: TextOverflow.ellipsis, style: const TextStyle(fontSize: 12)),
              ),
            ),
        ],
      ),
    );
  }
}

class _EmptyChat extends StatelessWidget {
  const _EmptyChat();
  @override
  Widget build(BuildContext context) {
    return const Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(Icons.auto_awesome, size: 52, color: Color(0xFF8C7CFF)),
          SizedBox(height: 14),
          Text('Research OS AI', style: TextStyle(fontSize: 22, fontWeight: FontWeight.w800)),
          SizedBox(height: 6),
          Text('Provider + local Memory + Agents + Skills + governed Tools'),
        ],
      ),
    );
  }
}

class _Message {
  const _Message(this.user, this.text, {this.meta});
  final bool user;
  final String text;
  final String? meta;
}

class _MessageBubble extends StatelessWidget {
  const _MessageBubble({required this.message});
  final _Message message;
  @override
  Widget build(BuildContext context) {
    return Align(
      alignment: message.user ? Alignment.centerRight : Alignment.centerLeft,
      child: Container(
        constraints: const BoxConstraints(maxWidth: 760),
        margin: const EdgeInsets.only(bottom: 12),
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: message.user ? const Color(0xFF241B59) : const Color(0xFF101C2D),
          borderRadius: BorderRadius.circular(14),
          border: Border.all(color: Colors.white10),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(message.user ? 'You' : 'Research OS AI', style: const TextStyle(fontWeight: FontWeight.w800)),
            const SizedBox(height: 7),
            SelectableText(message.text),
            if (message.meta != null) ...[const SizedBox(height: 7), Text(message.meta!, style: const TextStyle(color: Colors.white54, fontSize: 11))],
          ],
        ),
      ),
    );
  }
}

class _ContextPanel extends StatelessWidget {
  const _ContextPanel({required this.snapshot});
  final Future<_SystemSnapshot> snapshot;

  @override
  Widget build(BuildContext context) {
    return FutureBuilder<_SystemSnapshot>(
      future: snapshot,
      builder: (context, value) {
        if (!value.hasData) return const Center(child: CircularProgressIndicator());
        final data = value.data!;
        return ListView(
          padding: const EdgeInsets.all(12),
          children: [
            const Text('AI Context', style: TextStyle(fontWeight: FontWeight.w800, fontSize: 16)),
            const SizedBox(height: 10),
            _InfoCard('Active Provider', data.providerList.isEmpty ? 'none' : data.providerList.first['name']?.toString() ?? 'provider', Icons.hub_outlined),
            const SizedBox(height: 10),
            _InfoCard('System Status', data.health['status']?.toString() ?? '-', Icons.monitor_heart_outlined),
            const SizedBox(height: 10),
            _InfoCard('Unified Master', '${data.master['scale'] ?? '-'} / max ${data.health['maximum_scale'] ?? '-'}', Icons.account_tree_outlined),
            const SizedBox(height: 10),
            _InfoCard('Skills / Tools', '${data.skillList.length} / ${data.toolList.length}', Icons.extension_outlined),
            const SizedBox(height: 10),
            _InfoCard('Active Agents', '${data.agentList.length}', Icons.smart_toy_outlined),
            const SizedBox(height: 10),
            const Card(
              child: Padding(
                padding: EdgeInsets.all(12),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('Quick Actions', style: TextStyle(fontWeight: FontWeight.w800)),
                    SizedBox(height: 10),
                    Wrap(spacing: 8, runSpacing: 8, children: [
                      Chip(label: Text('New Chat')), Chip(label: Text('Import File')), Chip(label: Text('Run Tool')), Chip(label: Text('View Evidence')),
                    ]),
                  ],
                ),
              ),
            ),
          ],
        );
      },
    );
  }
}

class _ToolDiscoveryStrip extends StatelessWidget {
  const _ToolDiscoveryStrip();
  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.fromLTRB(16, 4, 16, 10),
      padding: const EdgeInsets.all(10),
      decoration: BoxDecoration(color: const Color(0xFF0D1725), borderRadius: BorderRadius.circular(10), border: Border.all(color: Colors.white10)),
      child: const SingleChildScrollView(
        scrollDirection: Axis.horizontal,
        child: Row(
          children: [
            Text('Tool Discovery: ', style: TextStyle(fontWeight: FontWeight.w800)),
            Text('Analysis → Research → Tool Match → Permission → Plan → Execute → Quality/Evidence', style: TextStyle(color: Colors.white70)),
          ],
        ),
      ),
    );
  }
}

class _MemoryPage extends StatefulWidget {
  const _MemoryPage({required this.api});
  final V3Api api;
  @override
  State<_MemoryPage> createState() => _MemoryPageState();
}

class _MemoryPageState extends State<_MemoryPage> {
  late Future<Map<String, dynamic>> _memory;
  @override
  void initState() { super.initState(); _memory = widget.api.memory(); }
  @override
  Widget build(BuildContext context) {
    return _Frame(title: 'Memory', subtitle: 'User/profile-isolated durable context', child: FutureBuilder<Map<String, dynamic>>(
      future: _memory,
      builder: (context, value) {
        if (!value.hasData) return const Center(child: CircularProgressIndicator());
        final items = _maps(value.data!['memory']);
        return ListView(padding: const EdgeInsets.all(20), children: [for (final m in items) Card(child: ListTile(leading: const Icon(Icons.memory), title: Text(m['text']?.toString() ?? '-'), subtitle: Text((m['tags'] as List?)?.join(', ') ?? '')))]);
      },
    ));
  }
}

class _CatalogPage extends StatelessWidget {
  const _CatalogPage({required this.title, required this.future, required this.kind});
  final String title;
  final Future<_SystemSnapshot> future;
  final String kind;

  @override
  Widget build(BuildContext context) {
    return _Frame(title: title, subtitle: 'Live V3 registry data', child: FutureBuilder<_SystemSnapshot>(
      future: future,
      builder: (context, value) {
        if (!value.hasData) return const Center(child: CircularProgressIndicator());
        final data = switch (kind) {
          'agents' => value.data!.agentList,
          'skills' => value.data!.skillList,
          'tools' => value.data!.toolList,
          _ => value.data!.providerList,
        };
        return ListView(padding: const EdgeInsets.all(20), children: [for (final item in data) Card(child: ListTile(leading: const Icon(Icons.circle_outlined), title: Text(item['name']?.toString() ?? item['provider']?.toString() ?? kind), subtitle: Text(_describe(item))))]);
      },
    ));
  }
}

class _FactoryPage extends StatefulWidget {
  const _FactoryPage({required this.api});
  final V3Api api;
  @override
  State<_FactoryPage> createState() => _FactoryPageState();
}

class _FactoryPageState extends State<_FactoryPage> {
  late Future<Map<String, dynamic>> _plan;
  @override
  void initState() { super.initState(); _plan = widget.api.factoryPlan(tasks: 30); }
  @override
  Widget build(BuildContext context) {
    return _Frame(title: 'Software Factory', subtitle: 'Master → Factory → Team → Tests → Release', child: FutureBuilder<Map<String, dynamic>>(
      future: _plan,
      builder: (context, value) {
        if (!value.hasData) return const Center(child: CircularProgressIndicator());
        final plan = value.data!;
        final stages = (plan['stage_order'] as List?)?.map((e) => e.toString()).toList() ?? const <String>[];
        return ListView(padding: const EdgeInsets.all(20), children: [
          _MetricCard('Selected scale', plan['scale']?.toString() ?? '-', Icons.all_inclusive),
          const SizedBox(height: 14),
          for (var i = 0; i < stages.length; i++) Card(child: ListTile(leading: CircleAvatar(child: Text('${i + 1}')), title: Text(stages[i]), trailing: const Icon(Icons.check_circle_outline, color: Color(0xFF47E68A))))
        ]);
      },
    ));
  }
}

class _OperationalPage extends StatelessWidget {
  const _OperationalPage({required this.item, required this.api, required this.snapshot});
  final _NavItem item;
  final V3Api api;
  final Future<_SystemSnapshot> snapshot;

  @override
  Widget build(BuildContext context) {
    final details = switch (item.label) {
      'Files' => 'Local-first workspace files. Write operations must use governed tools and approval.',
      'Repositories' => 'Repository workspace. GitHub integration remains governed by the V3 skill/tool boundary.',
      'GitHub' => 'GitHub integration capability is available through the unified skill registry.',
      'Drive' => 'Google Drive is persistent storage/tool source; executable packages require checksum validation.',
      'Runtime' => 'V3 local service and bounded execution runtime.',
      'Installer' => 'Windows installer staging and validation remain release-gated.',
      'Backup' => 'Backup candidates are evidence-first and never overwrite canonical source silently.',
      'Restore' => 'Restore is a governed write operation and requires explicit approval.',
      'Shell' => 'Shell/command execution is not implicit. Use governed tool execution with risk checks.',
      _ => 'Research OS operational surface.',
    };
    return _Frame(
      title: item.label,
      subtitle: item.group,
      child: ListView(
        padding: const EdgeInsets.all(20),
        children: [
          Card(child: Padding(padding: const EdgeInsets.all(20), child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [Icon(item.icon, size: 34, color: const Color(0xFF8C7CFF)), const SizedBox(height: 12), Text(details), const SizedBox(height: 12), const Text('Status: connected to V3 governance boundary', style: TextStyle(color: Color(0xFF47E68A), fontWeight: FontWeight.w700))]))),
          const SizedBox(height: 14),
          const _ToolDiscoveryCard(),
        ],
      ),
    );
  }
}

class _ToolDiscoveryCard extends StatelessWidget {
  const _ToolDiscoveryCard();
  @override
  Widget build(BuildContext context) {
    const steps = [
      ('1. Analysis', 'Understand intent, scope, risk and required capability.'),
      ('2. Research', 'Search the Skill registry, Tool registry, integrations and approved Drive packages.'),
      ('3. Evaluate', 'Match capability, read/write risk, reliability and evidence requirements.'),
      ('4. Permission', 'Fail closed when a write capability requires owner approval.'),
      ('5. Planning', 'Choose the smallest safe tool chain and bounded execution plan.'),
      ('6. Execution', 'Run only through governed V3 tool/skill/agent paths.'),
      ('7. Quality', 'Validate result, hashes, tests and evidence before accepting it.'),
    ];
    return Card(child: Padding(padding: const EdgeInsets.all(18), child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      const Text('Tool Discovery Skills', style: TextStyle(fontWeight: FontWeight.w800, fontSize: 17)),
      const SizedBox(height: 12),
      for (final step in steps) Padding(padding: const EdgeInsets.only(bottom: 10), child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [const Icon(Icons.check_circle_outline, size: 18, color: Color(0xFF47E68A)), const SizedBox(width: 8), Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [Text(step.$1, style: const TextStyle(fontWeight: FontWeight.w700)), Text(step.$2, style: const TextStyle(color: Colors.white60, fontSize: 12))]))]))
    ])));
  }
}

class _Frame extends StatelessWidget {
  const _Frame({required this.title, required this.child, this.subtitle, this.action});
  final String title;
  final String? subtitle;
  final Widget? action;
  final Widget child;
  @override
  Widget build(BuildContext context) {
    return Column(children: [
      Padding(padding: const EdgeInsets.fromLTRB(20, 16, 20, 12), child: Row(children: [Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [Text(title, style: const TextStyle(fontSize: 21, fontWeight: FontWeight.w800)), if (subtitle != null) Text(subtitle!, style: const TextStyle(color: Colors.white54, fontSize: 12))])), if (action != null) action!])),
      const Divider(height: 1),
      Expanded(child: child),
    ]);
  }
}

class _MetricCard extends StatelessWidget {
  const _MetricCard(this.label, this.value, this.icon);
  final String label;
  final String value;
  final IconData icon;
  @override
  Widget build(BuildContext context) {
    return SizedBox(width: 180, height: 104, child: Card(child: Padding(padding: const EdgeInsets.all(14), child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [Icon(icon, size: 20, color: const Color(0xFF8C7CFF)), const Spacer(), Text(label, style: const TextStyle(color: Colors.white54, fontSize: 12)), Text(value, maxLines: 1, overflow: TextOverflow.ellipsis, style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 18, color: Color(0xFF47E68A)))]))));
  }
}

class _InfoCard extends StatelessWidget {
  const _InfoCard(this.label, this.value, this.icon);
  final String label;
  final String value;
  final IconData icon;
  @override
  Widget build(BuildContext context) {
    return Card(child: Padding(padding: const EdgeInsets.all(12), child: Row(children: [Icon(icon, color: const Color(0xFF8C7CFF)), const SizedBox(width: 10), Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [Text(label, style: const TextStyle(color: Colors.white54, fontSize: 11)), Text(value, style: const TextStyle(fontWeight: FontWeight.w700))]))])));
  }
}

class _SystemSnapshot {
  const _SystemSnapshot({required this.health, required this.master, required this.skills, required this.tools, required this.agents, required this.providers});
  final Map<String, dynamic> health;
  final Map<String, dynamic> master;
  final Map<String, dynamic> skills;
  final Map<String, dynamic> tools;
  final Map<String, dynamic> agents;
  final Map<String, dynamic> providers;
  List<Map<String, dynamic>> get skillList => _maps(skills['skills']);
  List<Map<String, dynamic>> get toolList => _maps(tools['tools']);
  List<Map<String, dynamic>> get agentList => _maps(agents['agents']);
  List<Map<String, dynamic>> get providerList => _maps(providers['providers']);
}

List<Map<String, dynamic>> _maps(dynamic value) {
  if (value is! List) return const [];
  return value.whereType<Map>().map((item) => Map<String, dynamic>.from(item)).toList();
}

String _describe(Map<String, dynamic> item) {
  for (final key in const ['description', 'role', 'capability', 'status', 'model']) {
    final value = item[key];
    if (value != null && value.toString().isNotEmpty) return value.toString();
  }
  return item.entries.where((e) => e.key != 'name').take(3).map((e) => '${e.key}: ${e.value}').join(' · ');
}
''';


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description="Research OS self-build Full Control Center generator")
    parser.add_argument("--workspace", required=True)
    parser.add_argument("--requirement", required=True)
    args = parser.parse_args()

    workspace = Path(args.workspace).resolve()
    requirement_path = Path(args.requirement).resolve()
    requirement = json.loads(requirement_path.read_text(encoding="utf-8"))
    requested_nav = tuple(requirement.get("required_navigation", ()))
    missing = [item for item in REQUIRED_NAV if item not in requested_nav]
    if missing:
        raise SystemExit(f"owner requirement missing navigation entries: {missing}")
    policy = requirement.get("release_policy", {})
    if policy.get("mutate_canonical_source") is not False or policy.get("merge") is not False or policy.get("deploy") is not False:
        raise SystemExit("unsafe self-build release policy")

    target = workspace / "v3" / "flutter_app" / "lib" / "src" / "research_os_v3_app.dart"
    if not target.parent.is_dir():
        raise SystemExit(f"self-built Flutter source missing: {target.parent}")
    target.write_text(DART_TEMPLATE, encoding="utf-8", newline="\n")

    evidence = {
        "schema_version": 1,
        "contract": "research-os-self-build-full-control-center-v1",
        "status": "generated",
        "ui_source_of_truth": requirement["ui_source_of_truth"],
        "backend_source_of_truth": requirement["backend_source_of_truth"],
        "navigation": list(requested_nav),
        "tool_discovery_skill": requirement["tool_discovery_skill"],
        "data_binding": requirement["data_binding"],
        "generated_file": target.relative_to(workspace).as_posix(),
        "generated_sha256": sha256(target),
        "canonical_source_mutated": False,
        "merge": False,
        "deploy": False,
    }
    out = workspace / "SELF_BUILD_FULL_CONTROL_CENTER.json"
    out.write_text(json.dumps(evidence, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(evidence, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
