import 'dart:io';

import 'package:flutter/material.dart';

import 'owner_api.dart';

class OwnerFriendAppV4 extends StatefulWidget {
  const OwnerFriendAppV4({
    required this.api,
    this.startup,
    this.startupError,
    super.key,
  });

  final OwnerFriendApi api;
  final Map<String, dynamic>? startup;
  final String? startupError;

  @override
  State<OwnerFriendAppV4> createState() => _OwnerFriendAppV4State();
}

class _OwnerFriendAppV4State extends State<OwnerFriendAppV4> {
  int _section = 0;
  bool _railExpanded = true;

  @override
  Widget build(BuildContext context) {
    const titles = <String>['Chat', 'Capabilities', 'Memory', 'Provider'];
    final connected = widget.startupError == null;

    return MaterialApp(
      debugShowCheckedModeBanner: false,
      title: 'Research OS Owner Special',
      theme: ThemeData(
        useMaterial3: true,
        colorSchemeSeed: const Color(0xFF6558D9),
        scaffoldBackgroundColor: const Color(0xFFF7F7FA),
      ),
      home: Scaffold(
        body: SafeArea(
          child: Row(
            children: <Widget>[
              AnimatedContainer(
                duration: const Duration(milliseconds: 180),
                width: _railExpanded ? 220 : 76,
                child: NavigationRail(
                  extended: _railExpanded,
                  selectedIndex: _section,
                  onDestinationSelected: (value) => setState(() => _section = value),
                  leading: IconButton(
                    tooltip: _railExpanded ? 'ย่อเมนู' : 'ขยายเมนู',
                    onPressed: () => setState(() => _railExpanded = !_railExpanded),
                    icon: const Icon(Icons.menu),
                  ),
                  destinations: const <NavigationRailDestination>[
                    NavigationRailDestination(icon: Icon(Icons.chat_bubble_outline), selectedIcon: Icon(Icons.chat_bubble), label: Text('Friend Chat')),
                    NavigationRailDestination(icon: Icon(Icons.auto_awesome_outlined), selectedIcon: Icon(Icons.auto_awesome), label: Text('Capabilities')),
                    NavigationRailDestination(icon: Icon(Icons.memory_outlined), selectedIcon: Icon(Icons.memory), label: Text('Memory')),
                    NavigationRailDestination(icon: Icon(Icons.tune_outlined), selectedIcon: Icon(Icons.tune), label: Text('Provider')),
                  ],
                  trailing: Padding(
                    padding: const EdgeInsets.all(12),
                    child: Row(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: <Widget>[
                        Icon(connected ? Icons.check_circle : Icons.error_outline, size: 18),
                        if (_railExpanded) ...<Widget>[
                          const SizedBox(width: 8),
                          Flexible(child: Text(connected ? 'Service online' : 'Service offline')),
                        ],
                      ],
                    ),
                  ),
                ),
              ),
              const VerticalDivider(width: 1),
              Expanded(
                child: Column(
                  children: <Widget>[
                    SizedBox(
                      height: 64,
                      child: Padding(
                        padding: const EdgeInsets.symmetric(horizontal: 22),
                        child: Row(
                          children: <Widget>[
                            Text(titles[_section], style: Theme.of(context).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w700)),
                            const Spacer(),
                            Chip(avatar: Icon(connected ? Icons.link : Icons.link_off, size: 16), label: Text(connected ? 'Friend connected' : 'Friend offline')),
                            const SizedBox(width: 8),
                            const Chip(label: Text('UI V4')),
                          ],
                        ),
                      ),
                    ),
                    const Divider(height: 1),
                    Expanded(
                      child: IndexedStack(
                        index: _section,
                        children: <Widget>[
                          _FriendChatV4(api: widget.api),
                          _CapabilitiesV4(api: widget.api, startup: widget.startup),
                          _MemoryV4(api: widget.api),
                          _ProviderV4(api: widget.api),
                        ],
                      ),
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

class _Tool {
  const _Tool(this.name, this.label, this.state, this.icon);
  final String name;
  final String label;
  final String state;
  final IconData icon;
}

const _tools = <_Tool>[
  _Tool('echo', 'Echo', 'ready', Icons.reply_outlined),
  _Tool('summarize', 'Summarize', 'ready', Icons.summarize_outlined),
  _Tool('schedule.generate', 'Schedule', 'ready', Icons.calendar_month_outlined),
  _Tool('web', 'Web', 'implemented', Icons.language),
  _Tool('github', 'GitHub', 'implemented', Icons.code),
  _Tool('file', 'File', 'implemented', Icons.description_outlined),
  _Tool('python', 'Python', 'implemented', Icons.data_object),
  _Tool('shell', 'Shell', 'implemented', Icons.terminal),
  _Tool('github-actions', 'GitHub Actions', 'external', Icons.play_circle_outline),
  _Tool('github-repository', 'GitHub Repository', 'external', Icons.folder_shared_outlined),
  _Tool('yaml-validator', 'YAML Validator', 'ready', Icons.fact_check_outlined),
  _Tool('python-validator', 'Python Validator', 'ready', Icons.rule_folder_outlined),
  _Tool('git-branch', 'Git Branch', 'ready', Icons.account_tree_outlined),
  _Tool('pr-gate', 'PR Gate', 'ready', Icons.verified_outlined),
  _Tool('google-oauth', 'Google OAuth', 'needs_connection', Icons.key_outlined),
];

class _FriendChatV4 extends StatefulWidget {
  const _FriendChatV4({required this.api});
  final OwnerFriendApi api;

  @override
  State<_FriendChatV4> createState() => _FriendChatV4State();
}

class _FriendChatV4State extends State<_FriendChatV4> {
  final _controller = TextEditingController();
  final _scrollController = ScrollController();
  final _turns = <Map<String, String>>[];
  final _selectedTools = <String>{'echo', 'summarize'};

  bool _busy = false;
  bool _turbo = true;
  bool _toolsOpen = false;
  String _mode = 'Normal';
  String _runtime = '-';
  String _provider = '-';
  String _toolStatus = '';

  @override
  void dispose() {
    _controller.dispose();
    _scrollController.dispose();
    super.dispose();
  }

  List<String> _skillsForMode() {
    switch (_mode) {
      case 'Deep Research':
        return const ['research', 'analysis', 'planning', 'memory', 'quality'];
      case 'Files':
        return const ['documents', 'analysis', 'memory', 'quality'];
      case 'Web':
        return const ['research', 'analysis', 'quality'];
      case 'Schedule':
        return const ['automation', 'planning', 'memory', 'quality'];
      default:
        return const ['analysis', 'planning', 'memory', 'quality'];
    }
  }

  Future<void> _send() async {
    final text = _controller.text.trim();
    if (text.isEmpty || _busy) return;

    setState(() => _busy = true);
    try {
      final response = await widget.api.chat(
        text,
        complexity: _mode == 'Deep Research' ? 9 : 6,
        risk: 3,
        parallelism: _mode == 'Deep Research' ? 16 : 8,
        helperBudget: _turbo ? 1000000 : 0,
        requestedSkills: _skillsForMode(),
        requestedTools: _selectedTools.toList()..sort(),
      );

      final decision = response['decision'];
      final tools = decision is Map ? (decision['tools']?.toString() ?? '') : '';
      final answer = response['text']?.toString() ?? '';
      final provider = response['provider']?.toString() ?? '-';

      if (!mounted) return;
      setState(() {
        _turns.add({'user': text, 'answer': answer});
        _runtime = decision is Map ? (decision['scale']?.toString() ?? '-') : '-';
        _provider = provider;
        _toolStatus = tools.isEmpty ? 'Tools: none selected by runtime' : 'Runtime tools: $tools';
        _controller.clear();
      });
      _scrollToBottom();
    } catch (error) {
      if (!mounted) return;
      setState(() => _turns.add({'user': text, 'answer': 'Friend Service error: $error'}));
      _scrollToBottom();
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(_scrollController.position.maxScrollExtent, duration: const Duration(milliseconds: 220), curve: Curves.easeOut);
      }
    });
  }

  void _showTools() {
    setState(() => _toolsOpen = !_toolsOpen);
  }

  void _selectMode(String mode) {
    setState(() {
      _mode = mode;
      if (mode == 'Web') _selectedTools.add('web');
      if (mode == 'Deep Research') {
        _selectedTools.addAll(['web', 'file', 'python']);
      }
      if (mode == 'Schedule') _selectedTools.add('schedule.generate');
    });
  }

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, constraints) {
        final width = (constraints.maxWidth - 40).clamp(0.0, 1100.0);
        return Center(
          child: SizedBox(
            width: width,
            child: Padding(
              padding: const EdgeInsets.fromLTRB(8, 16, 8, 16),
              child: Column(
                children: <Widget>[
                  _RuntimeBar(runtime: _runtime, provider: _provider, turbo: _turbo, onTurbo: (value) => setState(() => _turbo = value)),
                  const SizedBox(height: 10),
                  if (_toolStatus.isNotEmpty)
                    Align(alignment: Alignment.centerLeft, child: Text(_toolStatus, style: Theme.of(context).textTheme.bodySmall)),
                  if (_toolStatus.isNotEmpty) const SizedBox(height: 6),
                  Expanded(
                    child: _turns.isEmpty
                        ? _EmptyState(mode: _mode)
                        : ListView.builder(
                            controller: _scrollController,
                            padding: const EdgeInsets.symmetric(vertical: 12),
                            itemCount: _turns.length,
                            itemBuilder: (context, index) {
                              final turn = _turns[index];
                              return Padding(
                                padding: const EdgeInsets.only(bottom: 16),
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.stretch,
                                  children: <Widget>[
                                    Align(alignment: Alignment.centerRight, child: _Bubble(text: turn['user'] ?? '', user: true)),
                                    const SizedBox(height: 8),
                                    _Bubble(text: turn['answer'] ?? '', user: false),
                                  ],
                                ),
                              );
                            },
                          ),
                  ),
                  _Composer(
                    controller: _controller,
                    busy: _busy,
                    mode: _mode,
                    toolsOpen: _toolsOpen,
                    selectedTools: _selectedTools,
                    onTools: _showTools,
                    onSend: _send,
                    onMode: _selectMode,
                    onToggleTool: (name) => setState(() => _selectedTools.contains(name) ? _selectedTools.remove(name) : _selectedTools.add(name)),
                  ),
                ],
              ),
            ),
          ),
        );
      },
    );
  }
}

class _RuntimeBar extends StatelessWidget {
  const _RuntimeBar({required this.runtime, required this.provider, required this.turbo, required this.onTurbo});
  final String runtime;
  final String provider;
  final bool turbo;
  final ValueChanged<bool> onTurbo;

  @override
  Widget build(BuildContext context) => Card(
        margin: EdgeInsets.zero,
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
          child: Row(
            children: <Widget>[
              const Icon(Icons.bolt_outlined, size: 20),
              const SizedBox(width: 8),
              Text('Brain: $runtime'),
              const SizedBox(width: 16),
              Text('Provider: $provider'),
              const Spacer(),
              const Text('Turbo 1M'),
              Switch(value: turbo, onChanged: onTurbo),
            ],
          ),
        ),
      );
}

class _EmptyState extends StatelessWidget {
  const _EmptyState({required this.mode});
  final String mode;

  @override
  Widget build(BuildContext context) => Center(
        child: SingleChildScrollView(
          child: Padding(
            padding: const EdgeInsets.all(24),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: <Widget>[
                const CircleAvatar(radius: 34, child: Icon(Icons.auto_awesome, size: 30)),
                const SizedBox(height: 18),
                Text('วันนี้ให้ Research OS Friend ช่วยอะไร?', textAlign: TextAlign.center, style: Theme.of(context).textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.w700)),
                const SizedBox(height: 8),
                Text('โหมด $mode • พิมพ์คำสั่งด้านล่างได้เลย', textAlign: TextAlign.center),
                const SizedBox(height: 18),
                const Wrap(spacing: 8, runSpacing: 8, alignment: WrapAlignment.center, children: <Widget>[
                  Chip(avatar: Icon(Icons.analytics_outlined, size: 16), label: Text('Analysis')),
                  Chip(avatar: Icon(Icons.memory_outlined, size: 16), label: Text('Memory')),
                  Chip(avatar: Icon(Icons.verified_outlined, size: 16), label: Text('Quality')),
                ]),
              ],
            ),
          ),
        ),
      );
}

class _Bubble extends StatelessWidget {
  const _Bubble({required this.text, required this.user});
  final String text;
  final bool user;

  @override
  Widget build(BuildContext context) => Align(
        alignment: user ? Alignment.centerRight : Alignment.centerLeft,
        child: Container(
          constraints: const BoxConstraints(maxWidth: 820),
          padding: const EdgeInsets.all(14),
          decoration: BoxDecoration(
            color: user ? Theme.of(context).colorScheme.primaryContainer : Theme.of(context).colorScheme.surface,
            borderRadius: BorderRadius.circular(16),
            border: Border.all(color: Theme.of(context).dividerColor),
          ),
          child: SelectableText(text),
        ),
      );
}

class _Composer extends StatelessWidget {
  const _Composer({required this.controller, required this.busy, required this.mode, required this.toolsOpen, required this.selectedTools, required this.onTools, required this.onSend, required this.onMode, required this.onToggleTool});
  final TextEditingController controller;
  final bool busy;
  final String mode;
  final bool toolsOpen;
  final Set<String> selectedTools;
  final VoidCallback onTools;
  final VoidCallback onSend;
  final ValueChanged<String> onMode;
  final ValueChanged<String> onToggleTool;

  @override
  Widget build(BuildContext context) {
    final selected = _tools.where((tool) => selectedTools.contains(tool.name)).toList();
    return Card(
      margin: EdgeInsets.zero,
      child: Padding(
        padding: const EdgeInsets.fromLTRB(10, 8, 10, 10),
        child: Column(
          children: <Widget>[
            if (toolsOpen)
              Container(
                constraints: const BoxConstraints(maxHeight: 250),
                padding: const EdgeInsets.only(bottom: 8),
                child: SingleChildScrollView(
                  child: Wrap(
                    spacing: 6,
                    runSpacing: 6,
                    children: _tools.map((tool) {
                      final active = selectedTools.contains(tool.name);
                      return FilterChip(
                        selected: active,
                        avatar: Icon(tool.icon, size: 17),
                        label: Text('${tool.label} · ${tool.state}'),
                        onSelected: (_) => onToggleTool(tool.name),
                      );
                    }).toList(),
                  ),
                ),
              ),
            if (selected.isNotEmpty)
              Align(
                alignment: Alignment.centerLeft,
                child: Wrap(spacing: 5, runSpacing: 4, children: selected.map((tool) => Chip(label: Text(tool.label), onDeleted: () => onToggleTool(tool.name))).toList()),
              ),
            Row(
              crossAxisAlignment: CrossAxisAlignment.end,
              children: <Widget>[
                IconButton(key: const Key('friend-v4-tools-menu'), tooltip: 'เครื่องมือ', onPressed: onTools, icon: Icon(toolsOpen ? Icons.close : Icons.add_circle_outline)),
                PopupMenuButton<String>(
                  tooltip: 'โหมดการทำงาน',
                  onSelected: onMode,
                  itemBuilder: (context) => const <PopupMenuEntry<String>>[
                    PopupMenuItem(value: 'Normal', child: Text('Normal')),
                    PopupMenuItem(value: 'Files', child: Text('Files')),
                    PopupMenuItem(value: 'Web', child: Text('Web')),
                    PopupMenuItem(value: 'Deep Research', child: Text('Deep Research')),
                    PopupMenuItem(value: 'Schedule', child: Text('Schedule')),
                  ],
                  child: Chip(avatar: const Icon(Icons.tune, size: 16), label: Text(mode)),
                ),
                const SizedBox(width: 6),
                Expanded(
                  child: TextField(
                    key: const Key('friend-v4-input'),
                    controller: controller,
                    minLines: 1,
                    maxLines: 6,
                    textInputAction: TextInputAction.newline,
                    onSubmitted: (_) => onSend(),
                    decoration: const InputDecoration(
                      hintText: 'พิมพ์ข้อความถึง Research OS Friend…',
                      border: OutlineInputBorder(borderRadius: BorderRadius.all(Radius.circular(16))),
                      contentPadding: EdgeInsets.symmetric(horizontal: 14, vertical: 12),
                    ),
                  ),
                ),
                const SizedBox(width: 6),
                IconButton.filled(
                  key: const Key('friend-v4-send'),
                  tooltip: busy ? 'กำลังส่ง…' : 'ส่ง',
                  onPressed: busy ? null : onSend,
                  icon: busy ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2)) : const Icon(Icons.arrow_upward),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

class _CapabilitiesV4 extends StatelessWidget {
  const _CapabilitiesV4({required this.api, required this.startup});
  final OwnerFriendApi api;
  final Map<String, dynamic>? startup;

  @override
  Widget build(BuildContext context) => FutureBuilder<Map<String, dynamic>>(
        future: api.status(),
        builder: (context, snapshot) {
          final data = snapshot.data ?? startup ?? const <String, dynamic>{};
          return ListView(
            padding: const EdgeInsets.all(24),
            children: <Widget>[
              Text('Capabilities & Unified Tools', style: Theme.of(context).textTheme.headlineSmall),
              const SizedBox(height: 12),
              ..._tools.map((tool) => ListTile(leading: Icon(tool.icon), title: Text(tool.label), subtitle: Text('${tool.name} • ${tool.state}'), trailing: const Icon(Icons.chevron_right))),
              const Divider(),
              Text('Runtime: ${data['capabilities'] ?? '-'}'),
            ],
          );
        },
      );
}

class _MemoryV4 extends StatelessWidget {
  const _MemoryV4({required this.api});
  final OwnerFriendApi api;

  @override
  Widget build(BuildContext context) => FutureBuilder<Map<String, dynamic>>(
        future: api.memory(),
        builder: (context, snapshot) {
          final data = snapshot.data ?? const <String, dynamic>{};
          final items = data['items'];
          return ListView(
            padding: const EdgeInsets.all(24),
            children: <Widget>[
              Text('Memory', style: Theme.of(context).textTheme.headlineSmall),
              Text('Items: ${data['count'] ?? 0}'),
              const SizedBox(height: 12),
              if (items is List) ...items.map((item) => Card(child: Padding(padding: const EdgeInsets.all(12), child: SelectableText(item.toString())))),
            ],
          );
        },
      );
}

class _ProviderV4 extends StatefulWidget {
  const _ProviderV4({required this.api});
  final OwnerFriendApi api;

  @override
  State<_ProviderV4> createState() => _ProviderV4State();
}

class _ProviderV4State extends State<_ProviderV4> {
  final _baseUrl = TextEditingController();
  final _model = TextEditingController();
  final _key = TextEditingController();
  String _status = '';

  @override
  void dispose() {
    _baseUrl.dispose();
    _model.dispose();
    _key.dispose();
    super.dispose();
  }

  Future<void> _configure() async {
    try {
      final result = await widget.api.configureProvider(baseUrl: _baseUrl.text.trim(), model: _model.text.trim(), apiKey: _key.text.trim());
      if (mounted) setState(() => _status = result.toString());
    } catch (error) {
      if (mounted) setState(() => _status = error.toString());
    }
  }

  @override
  Widget build(BuildContext context) => ListView(
        padding: const EdgeInsets.all(24),
        children: <Widget>[
          Text('Provider', style: Theme.of(context).textTheme.headlineSmall),
          const SizedBox(height: 12),
          TextField(controller: _baseUrl, decoration: const InputDecoration(labelText: 'Base URL', border: OutlineInputBorder())),
          const SizedBox(height: 10),
          TextField(controller: _model, decoration: const InputDecoration(labelText: 'Model', border: OutlineInputBorder())),
          const SizedBox(height: 10),
          TextField(controller: _key, obscureText: true, decoration: const InputDecoration(labelText: 'API key (optional)', border: OutlineInputBorder())),
          const SizedBox(height: 12),
          Row(children: <Widget>[FilledButton.icon(onPressed: _configure, icon: const Icon(Icons.save), label: const Text('Save Provider')), const SizedBox(width: 8), OutlinedButton.icon(onPressed: () async { final result = await widget.api.testProvider(); if (mounted) setState(() => _status = result.toString()); }, icon: const Icon(Icons.bolt), label: const Text('Test'))]),
          if (_status.isNotEmpty) Padding(padding: const EdgeInsets.only(top: 12), child: SelectableText(_status)),
        ],
      );
}
