import 'package:flutter/material.dart';

import 'api/v3_api.dart';

class ResearchOSV3App extends StatelessWidget {
  const ResearchOSV3App({super.key, required this.api});

  final V3Api api;

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Research OS V3 Full System',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: const Color(0xFF3157D5)),
        useMaterial3: true,
      ),
      home: V3AppShell(api: api),
    );
  }
}

class V3AppShell extends StatefulWidget {
  const V3AppShell({super.key, required this.api});

  final V3Api api;

  @override
  State<V3AppShell> createState() => _V3AppShellState();
}

class _V3AppShellState extends State<V3AppShell> {
  int _selectedIndex = 0;
  late Future<_V3Snapshot> _snapshot;

  static const _destinations = <NavigationRailDestination>[
    NavigationRailDestination(
      icon: Icon(Icons.home_outlined),
      selectedIcon: Icon(Icons.home),
      label: Text('Home'),
    ),
    NavigationRailDestination(
      icon: Icon(Icons.chat_bubble_outline),
      selectedIcon: Icon(Icons.chat_bubble),
      label: Text('Chat'),
    ),
    NavigationRailDestination(
      icon: Icon(Icons.smart_toy_outlined),
      selectedIcon: Icon(Icons.smart_toy),
      label: Text('Agents'),
    ),
    NavigationRailDestination(
      icon: Icon(Icons.memory_outlined),
      selectedIcon: Icon(Icons.memory),
      label: Text('Memory'),
    ),
    NavigationRailDestination(
      icon: Icon(Icons.extension_outlined),
      selectedIcon: Icon(Icons.extension),
      label: Text('Skills'),
    ),
    NavigationRailDestination(
      icon: Icon(Icons.build_outlined),
      selectedIcon: Icon(Icons.build),
      label: Text('Tools'),
    ),
    NavigationRailDestination(
      icon: Icon(Icons.account_tree_outlined),
      selectedIcon: Icon(Icons.account_tree),
      label: Text('Factory'),
    ),
    NavigationRailDestination(
      icon: Icon(Icons.hub_outlined),
      selectedIcon: Icon(Icons.hub),
      label: Text('Providers'),
    ),
  ];

  @override
  void initState() {
    super.initState();
    _snapshot = _loadSnapshot();
  }

  Future<_V3Snapshot> _loadSnapshot() async {
    final results = await Future.wait([
      widget.api.health(),
      widget.api.master(tasks: 30),
      widget.api.providers(),
      widget.api.skills(),
      widget.api.tools(),
      widget.api.agents(),
    ]);
    return _V3Snapshot(
      health: results[0],
      master: results[1],
      providers: results[2],
      skills: results[3],
      tools: results[4],
      agents: results[5],
    );
  }

  void _refresh() => setState(() => _snapshot = _loadSnapshot());

  @override
  Widget build(BuildContext context) {
    final width = MediaQuery.sizeOf(context).width;
    final extended = width >= 1250;
    return Scaffold(
      body: SafeArea(
        child: Row(
          children: [
            NavigationRail(
              extended: extended,
              selectedIndex: _selectedIndex,
              destinations: _destinations,
              onDestinationSelected: (index) {
                setState(() => _selectedIndex = index);
              },
              leading: Padding(
                padding: const EdgeInsets.symmetric(vertical: 16),
                child: extended
                    ? const Text(
                        'Research OS V3',
                        style: TextStyle(fontWeight: FontWeight.w800),
                      )
                    : const Icon(Icons.auto_awesome),
              ),
            ),
            const VerticalDivider(width: 1),
            Expanded(
              child: IndexedStack(
                index: _selectedIndex,
                children: [
                  _HomePage(snapshot: _snapshot, onRefresh: _refresh),
                  _ChatPage(api: widget.api),
                  _AgentsPage(api: widget.api, snapshot: _snapshot),
                  _MemoryPage(api: widget.api),
                  _SkillsPage(snapshot: _snapshot),
                  _ToolsPage(api: widget.api, snapshot: _snapshot),
                  _FactoryPage(api: widget.api),
                  _ProvidersPage(snapshot: _snapshot, onRefresh: _refresh),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _HomePage extends StatelessWidget {
  const _HomePage({required this.snapshot, required this.onRefresh});

  final Future<_V3Snapshot> snapshot;
  final VoidCallback onRefresh;

  @override
  Widget build(BuildContext context) {
    return _PageFrame(
      title: 'Full System Control Center',
      action: IconButton(
        tooltip: 'Refresh',
        onPressed: onRefresh,
        icon: const Icon(Icons.refresh),
      ),
      child: FutureBuilder<_V3Snapshot>(
        future: snapshot,
        builder: (context, value) {
          if (value.connectionState != ConnectionState.done) {
            return const Center(child: CircularProgressIndicator());
          }
          if (value.hasError) return _ConnectionError(error: value.error);
          final data = value.data!;
          return ListView(
            padding: const EdgeInsets.all(24),
            children: [
              Wrap(
                spacing: 16,
                runSpacing: 16,
                children: [
                  _MetricCard(
                    label: 'Local service',
                    value: data.health['status']?.toString() ?? 'unknown',
                    icon: Icons.dns_outlined,
                  ),
                  _MetricCard(
                    label: 'Active scale',
                    value: data.master['scale']?.toString() ?? '-',
                    icon: Icons.memory,
                  ),
                  _MetricCard(
                    label: 'Maximum scale',
                    value: data.health['maximum_scale']?.toString() ?? '-',
                    icon: Icons.all_inclusive,
                  ),
                  _MetricCard(
                    label: '10^10 capacity',
                    value: _formatInteger(data.health['maximum_logical_capacity']),
                    icon: Icons.schema_outlined,
                  ),
                  _MetricCard(
                    label: 'Skills',
                    value: '${data.skillList.length}',
                    icon: Icons.extension_outlined,
                  ),
                  _MetricCard(
                    label: 'Tools',
                    value: '${data.toolList.length}',
                    icon: Icons.build_outlined,
                  ),
                  _MetricCard(
                    label: 'Agents',
                    value: '${data.agentList.length}',
                    icon: Icons.smart_toy_outlined,
                  ),
                  _MetricCard(
                    label: 'Providers',
                    value: '${data.providerList.length}',
                    icon: Icons.hub_outlined,
                  ),
                ],
              ),
              const SizedBox(height: 24),
              const Text(
                'Unified execution path',
                style: TextStyle(fontSize: 20, fontWeight: FontWeight.w700),
              ),
              const SizedBox(height: 12),
              const Card(
                child: Padding(
                  padding: EdgeInsets.all(20),
                  child: Text(
                    'Request → Unified Master → Brain → Skills / Tools / Agents → Provider → Evidence\n\n'
                    'Software Factory: Master → Factory → Team → Tests → Release\n'
                    'Adaptive profiles scale from 3¹ through 6⁶ up to 10¹⁰. '
                    '10¹⁰ is logical capacity only; real execution remains bounded and lazy.',
                  ),
                ),
              ),
            ],
          );
        },
      ),
    );
  }
}

class _ChatPage extends StatefulWidget {
  const _ChatPage({required this.api});
  final V3Api api;

  @override
  State<_ChatPage> createState() => _ChatPageState();
}

class _ChatPageState extends State<_ChatPage> {
  final _controller = TextEditingController();
  final _scrollController = ScrollController();
  final List<_UiMessage> _messages = [];
  bool _sending = false;
  String? _agent;
  List<Map<String, dynamic>> _agents = const [];

  @override
  void initState() {
    super.initState();
    _loadAgents();
  }

  Future<void> _loadAgents() async {
    try {
      final data = await widget.api.agents();
      if (!mounted) return;
      setState(() => _agents = _maps(data['agents']));
    } catch (_) {}
  }

  @override
  void dispose() {
    _controller.dispose();
    _scrollController.dispose();
    super.dispose();
  }

  Future<void> _send() async {
    final prompt = _controller.text.trim();
    if (prompt.isEmpty || _sending) return;
    setState(() {
      _messages.add(_UiMessage(role: 'user', text: prompt));
      _controller.clear();
      _sending = true;
    });
    try {
      final response = await widget.api.chat(prompt, agent: _agent);
      if (!mounted) return;
      setState(() {
        _messages.add(
          _UiMessage(
            role: 'assistant',
            text: response['text']?.toString() ?? 'No response',
            meta: '${response['provider'] ?? '-'} · ${response['model'] ?? '-'} · memory ${_maps(response['memory_hits']).length}',
          ),
        );
      });
      await Future<void>.delayed(const Duration(milliseconds: 30));
      if (_scrollController.hasClients) {
        await _scrollController.animateTo(
          _scrollController.position.maxScrollExtent,
          duration: const Duration(milliseconds: 180),
          curve: Curves.easeOut,
        );
      }
    } catch (error) {
      if (mounted) {
        setState(() => _messages.add(_UiMessage(role: 'error', text: '$error')));
      }
    } finally {
      if (mounted) setState(() => _sending = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return _PageFrame(
      title: 'AI Chat',
      action: DropdownButtonHideUnderline(
        child: DropdownButton<String?>(
          value: _agent,
          hint: const Text('Auto'),
          items: [
            const DropdownMenuItem<String?>(value: null, child: Text('Auto')),
            ..._agents.map(
              (agent) => DropdownMenuItem<String?>(
                value: agent['name']?.toString(),
                child: Text(agent['name']?.toString() ?? 'agent'),
              ),
            ),
          ],
          onChanged: (value) => setState(() => _agent = value),
        ),
      ),
      child: Column(
        children: [
          Expanded(
            child: _messages.isEmpty
                ? const Center(
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Icon(Icons.auto_awesome, size: 42),
                        SizedBox(height: 12),
                        Text('ถาม Research OS V3 ได้เลย'),
                        SizedBox(height: 6),
                        Text('Chat ใช้ Provider + local Memory + optional Agent จริง'),
                      ],
                    ),
                  )
                : ListView.builder(
                    controller: _scrollController,
                    padding: const EdgeInsets.all(24),
                    itemCount: _messages.length,
                    itemBuilder: (context, index) {
                      final message = _messages[index];
                      final isUser = message.role == 'user';
                      return Align(
                        alignment: isUser ? Alignment.centerRight : Alignment.centerLeft,
                        child: Container(
                          constraints: const BoxConstraints(maxWidth: 820),
                          margin: const EdgeInsets.only(bottom: 14),
                          padding: const EdgeInsets.all(16),
                          decoration: BoxDecoration(
                            color: message.role == 'error'
                                ? Theme.of(context).colorScheme.errorContainer
                                : isUser
                                    ? Theme.of(context).colorScheme.primaryContainer
                                    : Theme.of(context).colorScheme.surfaceContainer,
                            borderRadius: BorderRadius.circular(18),
                          ),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                isUser ? 'You' : message.role == 'error' ? 'Error' : 'Research OS AI',
                                style: const TextStyle(fontWeight: FontWeight.w700),
                              ),
                              const SizedBox(height: 8),
                              SelectableText(message.text),
                              if (message.meta != null) ...[
                                const SizedBox(height: 8),
                                Text(message.meta!, style: Theme.of(context).textTheme.labelSmall),
                              ],
                            ],
                          ),
                        ),
                      );
                    },
                  ),
          ),
          Padding(
            padding: const EdgeInsets.all(16),
            child: TextField(
              controller: _controller,
              minLines: 1,
              maxLines: 6,
              onSubmitted: (_) => _send(),
              decoration: InputDecoration(
                hintText: 'Message Research OS V3',
                border: const OutlineInputBorder(),
                suffixIcon: IconButton(
                  tooltip: 'Send',
                  onPressed: _sending ? null : _send,
                  icon: _sending
                      ? const SizedBox(
                          width: 20,
                          height: 20,
                          child: CircularProgressIndicator(strokeWidth: 2),
                        )
                      : const Icon(Icons.arrow_upward),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _AgentsPage extends StatelessWidget {
  const _AgentsPage({required this.api, required this.snapshot});
  final V3Api api;
  final Future<_V3Snapshot> snapshot;

  Future<void> _run(BuildContext context, String name) async {
    final controller = TextEditingController();
    final prompt = await showDialog<String>(
      context: context,
      builder: (context) => AlertDialog(
        title: Text('Run $name'),
        content: TextField(
          controller: controller,
          autofocus: true,
          minLines: 3,
          maxLines: 8,
          decoration: const InputDecoration(hintText: 'Task for this agent'),
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context), child: const Text('Cancel')),
          FilledButton(onPressed: () => Navigator.pop(context, controller.text), child: const Text('Run')),
        ],
      ),
    );
    controller.dispose();
    if (prompt == null || prompt.trim().isEmpty || !context.mounted) return;
    try {
      final result = await api.runAgent(name, prompt.trim());
      if (!context.mounted) return;
      await showDialog<void>(
        context: context,
        builder: (context) => AlertDialog(
          title: Text('$name result'),
          content: SizedBox(width: 620, child: SelectableText(result['text']?.toString() ?? '-')),
          actions: [TextButton(onPressed: () => Navigator.pop(context), child: const Text('Close'))],
        ),
      );
    } catch (error) {
      if (context.mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('$error')));
    }
  }

  @override
  Widget build(BuildContext context) {
    return _PageFrame(
      title: 'Agent Center',
      child: FutureBuilder<_V3Snapshot>(
        future: snapshot,
        builder: (context, value) {
          if (!value.hasData) return const Center(child: CircularProgressIndicator());
          return ListView(
            padding: const EdgeInsets.all(24),
            children: [
              for (final agent in value.data!.agentList)
                Card(
                  child: ListTile(
                    leading: const CircleAvatar(child: Icon(Icons.smart_toy_outlined)),
                    title: Text(agent['name']?.toString() ?? 'agent'),
                    subtitle: Text(
                      '${agent['role'] ?? ''}\n${agent['description'] ?? ''}\nSkills: ${(agent['skills'] as List?)?.join(', ') ?? '-'}',
                    ),
                    isThreeLine: true,
                    trailing: FilledButton(
                      onPressed: () => _run(context, agent['name']?.toString() ?? ''),
                      child: const Text('Run'),
                    ),
                  ),
                ),
            ],
          );
        },
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
  final _controller = TextEditingController();
  final _searchController = TextEditingController();
  late Future<Map<String, dynamic>> _memory;
  bool _saving = false;

  @override
  void initState() {
    super.initState();
    _memory = widget.api.memory();
  }

  @override
  void dispose() {
    _controller.dispose();
    _searchController.dispose();
    super.dispose();
  }

  void _reload() {
    setState(() => _memory = widget.api.memory(query: _searchController.text.trim()));
  }

  Future<void> _save() async {
    final text = _controller.text.trim();
    if (text.isEmpty || _saving) return;
    setState(() => _saving = true);
    try {
      await widget.api.addMemory(text);
      _controller.clear();
      _reload();
    } catch (error) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('$error')));
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return _PageFrame(
      title: 'Durable Memory',
      action: IconButton(onPressed: _reload, icon: const Icon(Icons.refresh)),
      child: Column(
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(24, 20, 24, 8),
            child: Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _searchController,
                    decoration: const InputDecoration(
                      prefixIcon: Icon(Icons.search),
                      labelText: 'Search memory',
                      border: OutlineInputBorder(),
                    ),
                    onSubmitted: (_) => _reload(),
                  ),
                ),
                const SizedBox(width: 12),
                FilledButton(onPressed: _reload, child: const Text('Search')),
              ],
            ),
          ),
          Expanded(
            child: FutureBuilder<Map<String, dynamic>>(
              future: _memory,
              builder: (context, value) {
                if (!value.hasData) return const Center(child: CircularProgressIndicator());
                final records = _maps(value.data!['memory']);
                if (records.isEmpty) return const Center(child: Text('No memory yet'));
                return ListView.builder(
                  padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 8),
                  itemCount: records.length,
                  itemBuilder: (context, index) {
                    final item = records[index];
                    return Card(
                      child: ListTile(
                        leading: const Icon(Icons.memory),
                        title: Text(item['text']?.toString() ?? ''),
                        subtitle: Text(item['created_at']?.toString() ?? ''),
                      ),
                    );
                  },
                );
              },
            ),
          ),
          Padding(
            padding: const EdgeInsets.all(16),
            child: TextField(
              controller: _controller,
              minLines: 1,
              maxLines: 4,
              decoration: InputDecoration(
                labelText: 'Add explicit memory',
                border: const OutlineInputBorder(),
                suffixIcon: IconButton(
                  onPressed: _saving ? null : _save,
                  icon: const Icon(Icons.save_outlined),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _SkillsPage extends StatelessWidget {
  const _SkillsPage({required this.snapshot});
  final Future<_V3Snapshot> snapshot;

  @override
  Widget build(BuildContext context) {
    return _PageFrame(
      title: 'Unified Skills',
      child: FutureBuilder<_V3Snapshot>(
        future: snapshot,
        builder: (context, value) {
          if (!value.hasData) return const Center(child: CircularProgressIndicator());
          return ListView(
            padding: const EdgeInsets.all(24),
            children: [
              for (final skill in value.data!.skillList)
                Card(
                  child: ListTile(
                    leading: const Icon(Icons.extension_outlined),
                    title: Text(skill['name']?.toString() ?? 'skill'),
                    subtitle: Text('${skill['capability'] ?? ''} · origin=${skill['origin'] ?? ''}\n${skill['description'] ?? ''}'),
                    isThreeLine: true,
                  ),
                ),
            ],
          );
        },
      ),
    );
  }
}

class _ToolsPage extends StatelessWidget {
  const _ToolsPage({required this.api, required this.snapshot});
  final V3Api api;
  final Future<_V3Snapshot> snapshot;

  Future<void> _testTool(BuildContext context, Map<String, dynamic> tool) async {
    final name = tool['name']?.toString() ?? '';
    try {
      Map<String, dynamic> result;
      if (name == 'artifact-note') {
        final approved = await showDialog<bool>(
              context: context,
              builder: (context) => AlertDialog(
                title: const Text('Approval required'),
                content: const Text('This tool writes an artifact note inside your isolated Research OS profile.'),
                actions: [
                  TextButton(onPressed: () => Navigator.pop(context, false), child: const Text('Cancel')),
                  FilledButton(onPressed: () => Navigator.pop(context, true), child: const Text('Approve once')),
                ],
              ),
            ) ??
            false;
        if (!approved) return;
        result = await api.executeTool(
          name,
          <String, dynamic>{'title': 'gui-note', 'text': 'Created from Research OS V3 Tools workspace.'},
          approved: true,
        );
      } else {
        result = await api.executeTool(name, <String, dynamic>{'text': 'Research OS tool check'});
      }
      if (!context.mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('${result['result']}')));
    } catch (error) {
      if (context.mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('$error')));
    }
  }

  @override
  Widget build(BuildContext context) {
    return _PageFrame(
      title: 'Governed Tools',
      child: FutureBuilder<_V3Snapshot>(
        future: snapshot,
        builder: (context, value) {
          if (!value.hasData) return const Center(child: CircularProgressIndicator());
          return ListView(
            padding: const EdgeInsets.all(24),
            children: [
              const Card(
                child: ListTile(
                  leading: Icon(Icons.policy_outlined),
                  title: Text('Tool policy'),
                  subtitle: Text('Read-only tools run directly. Write tools require an explicit one-time approval header.'),
                ),
              ),
              const SizedBox(height: 8),
              for (final tool in value.data!.toolList)
                Card(
                  child: ListTile(
                    leading: Icon(tool['approval_required'] == true ? Icons.lock_outline : Icons.build_outlined),
                    title: Text(tool['name']?.toString() ?? 'tool'),
                    subtitle: Text('${tool['risk'] ?? ''} · ${tool['capability'] ?? ''}\n${tool['description'] ?? ''}'),
                    isThreeLine: true,
                    trailing: OutlinedButton(
                      onPressed: () => _testTool(context, tool),
                      child: Text(tool['approval_required'] == true ? 'Approve & run' : 'Test'),
                    ),
                  ),
                ),
            ],
          );
        },
      ),
    );
  }
}

class _FactoryPage extends StatefulWidget {
  const _FactoryPage({required this.api});
  final V3Api api;

  @override
  State<_FactoryPage> createState() => _FactoryPageState();
}

class _FactoryPageState extends State<_FactoryPage> {
  final _tasks = TextEditingController(text: '30');
  late Future<Map<String, dynamic>> _plan;

  @override
  void initState() {
    super.initState();
    _plan = widget.api.factoryPlan(tasks: 30);
  }

  @override
  void dispose() {
    _tasks.dispose();
    super.dispose();
  }

  void _replan() {
    final tasks = int.tryParse(_tasks.text.trim()) ?? 1;
    setState(() => _plan = widget.api.factoryPlan(tasks: tasks));
  }

  @override
  Widget build(BuildContext context) {
    return _PageFrame(
      title: 'Adaptive Software Factory',
      child: ListView(
        padding: const EdgeInsets.all(24),
        children: [
          Row(
            children: [
              SizedBox(
                width: 220,
                child: TextField(
                  controller: _tasks,
                  keyboardType: TextInputType.number,
                  decoration: const InputDecoration(labelText: 'Estimated leaf tasks', border: OutlineInputBorder()),
                ),
              ),
              const SizedBox(width: 12),
              FilledButton.icon(onPressed: _replan, icon: const Icon(Icons.calculate_outlined), label: const Text('Plan')),
            ],
          ),
          const SizedBox(height: 18),
          FutureBuilder<Map<String, dynamic>>(
            future: _plan,
            builder: (context, value) {
              if (!value.hasData) return const Center(child: CircularProgressIndicator());
              final data = value.data!;
              final decision = data['decision'] is Map
                  ? Map<String, dynamic>.from(data['decision'] as Map)
                  : <String, dynamic>{};
              final stages = data['stage_order'] is List
                  ? List<String>.from((data['stage_order'] as List).map((e) => e.toString()))
                  : const <String>[];
              return Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Wrap(
                    spacing: 12,
                    runSpacing: 12,
                    children: [
                      _MetricCard(label: 'Selected scale', value: data['scale']?.toString() ?? '-', icon: Icons.memory),
                      _MetricCard(label: 'Plan capacity', value: _formatInteger(data['maximum_leaf_capacity']), icon: Icons.schema_outlined),
                      _MetricCard(label: 'System max', value: decision['system_maximum_scale']?.toString() ?? '10^10', icon: Icons.all_inclusive),
                    ],
                  ),
                  const SizedBox(height: 20),
                  for (var i = 0; i < stages.length; i++) ...[
                    Card(
                      child: ListTile(
                        leading: CircleAvatar(child: Text('${i + 1}')),
                        title: Text(stages[i]),
                        subtitle: Text(i == 0 ? 'Unified Master chooses the smallest safe profile.' : 'Governed stage receives bounded work and emits evidence.'),
                      ),
                    ),
                    if (i != stages.length - 1) const Center(child: Icon(Icons.arrow_downward)),
                  ],
                ],
              );
            },
          ),
        ],
      ),
    );
  }
}

class _ProvidersPage extends StatelessWidget {
  const _ProvidersPage({required this.snapshot, required this.onRefresh});
  final Future<_V3Snapshot> snapshot;
  final VoidCallback onRefresh;

  @override
  Widget build(BuildContext context) {
    return _PageFrame(
      title: 'Providers',
      action: IconButton(tooltip: 'Refresh', onPressed: onRefresh, icon: const Icon(Icons.refresh)),
      child: FutureBuilder<_V3Snapshot>(
        future: snapshot,
        builder: (context, value) {
          if (value.connectionState != ConnectionState.done) return const Center(child: CircularProgressIndicator());
          if (value.hasError) return _ConnectionError(error: value.error);
          return ListView(
            padding: const EdgeInsets.all(24),
            children: [
              const Card(
                child: ListTile(
                  leading: Icon(Icons.key_off_outlined),
                  title: Text('Secrets stay outside the desktop app'),
                  subtitle: Text('Credentials are resolved by the V3 service. This screen renders safe status only.'),
                ),
              ),
              const SizedBox(height: 12),
              for (final provider in value.data!.providerList)
                Card(
                  child: ListTile(
                    leading: Icon(provider['ready'] == true ? Icons.check_circle_outline : Icons.pause_circle_outline),
                    title: Text(provider['name']?.toString() ?? 'provider'),
                    subtitle: Text('ready=${provider['ready']} · connected=${provider['connected']} · secret_exposed=${provider['secret_exposed']}'),
                  ),
                ),
            ],
          );
        },
      ),
    );
  }
}

class _PageFrame extends StatelessWidget {
  const _PageFrame({required this.title, required this.child, this.action});
  final String title;
  final Widget child;
  final Widget? action;

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Material(
          color: Theme.of(context).colorScheme.surface,
          child: SizedBox(
            height: 64,
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 24),
              child: Row(
                children: [
                  Expanded(child: Text(title, style: Theme.of(context).textTheme.titleLarge)),
                  if (action != null) action!,
                ],
              ),
            ),
          ),
        ),
        const Divider(height: 1),
        Expanded(child: child),
      ],
    );
  }
}

class _MetricCard extends StatelessWidget {
  const _MetricCard({required this.label, required this.value, required this.icon});
  final String label;
  final String value;
  final IconData icon;

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: 220,
      child: Card(
        child: Padding(
          padding: const EdgeInsets.all(20),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Icon(icon),
              const SizedBox(height: 18),
              Text(label, style: Theme.of(context).textTheme.labelLarge),
              const SizedBox(height: 6),
              Text(value, style: Theme.of(context).textTheme.headlineSmall),
            ],
          ),
        ),
      ),
    );
  }
}

class _ConnectionError extends StatelessWidget {
  const _ConnectionError({required this.error});
  final Object? error;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Text('V3 local service is not ready.\n$error', textAlign: TextAlign.center),
      ),
    );
  }
}

class _UiMessage {
  const _UiMessage({required this.role, required this.text, this.meta});
  final String role;
  final String text;
  final String? meta;
}

class _V3Snapshot {
  const _V3Snapshot({
    required this.health,
    required this.master,
    required this.providers,
    required this.skills,
    required this.tools,
    required this.agents,
  });

  final Map<String, dynamic> health;
  final Map<String, dynamic> master;
  final Map<String, dynamic> providers;
  final Map<String, dynamic> skills;
  final Map<String, dynamic> tools;
  final Map<String, dynamic> agents;

  List<Map<String, dynamic>> get providerList => _maps(providers['providers']);
  List<Map<String, dynamic>> get skillList => _maps(skills['skills']);
  List<Map<String, dynamic>> get toolList => _maps(tools['tools']);
  List<Map<String, dynamic>> get agentList => _maps(agents['agents']);
}

List<Map<String, dynamic>> _maps(Object? value) {
  if (value is! List) return const [];
  return value.whereType<Map>().map((item) => Map<String, dynamic>.from(item)).toList(growable: false);
}

String _formatInteger(Object? value) {
  final number = switch (value) {
    int value => value,
    num value => value.toInt(),
    _ => int.tryParse(value?.toString() ?? ''),
  };
  if (number == null) return '-';
  final raw = number.toString();
  final buffer = StringBuffer();
  for (var index = 0; index < raw.length; index++) {
    if (index > 0 && (raw.length - index) % 3 == 0) buffer.write(',');
    buffer.write(raw[index]);
  }
  return buffer.toString();
}
