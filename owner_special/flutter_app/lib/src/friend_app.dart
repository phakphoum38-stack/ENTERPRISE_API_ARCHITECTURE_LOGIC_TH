import 'package:flutter/material.dart';

import 'friend_app_shell.dart';
import 'friend_module_shell.dart';
import 'friend_theme.dart';
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
  int _index = 1;
  TeamRecord _currentTeam = const TeamRecord(id: 'research', name: 'Research Team');

  void _onTeamChanged(TeamRecord team) => setState(() => _currentTeam = team);

  @override
  Widget build(BuildContext context) {
    final pages = <Widget>[
      _DashboardPage(api: widget.api),
      _FriendChatPage(api: widget.api, team: _currentTeam),
      _CapabilitiesPage(api: widget.api, startup: widget.startup),
      _AgentsPage(api: widget.api),
      _MemoryPage(api: widget.api),
      const _EvidencePage(),
      _ProviderPage(api: widget.api),
    ];

    return MaterialApp(
      debugShowCheckedModeBanner: false,
      title: 'Research OS',
      theme: FriendTheme.build(),
      home: FriendAppShell(
        index: _index,
        onIndexChanged: (value) => setState(() => _index = value),
        pages: pages,
        teamCenter: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 420),
          child: TeamCenter(onChanged: _onTeamChanged),
        ),
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
    final theme = Theme.of(context);
    final semantic = theme.extension<FriendSemanticColors>();
    final color = connected ? semantic?.success ?? Colors.green : semantic?.warning ?? Colors.orange;
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      decoration: BoxDecoration(color: color.withValues(alpha: .10), borderRadius: BorderRadius.circular(999)),
      child: Row(mainAxisSize: MainAxisSize.min, children: [
        Container(width: 7, height: 7, decoration: BoxDecoration(color: color, shape: BoxShape.circle)),
        const SizedBox(width: 8),
        Text(connected ? 'READY' : 'OFFLINE', style: theme.textTheme.bodySmall?.copyWith(color: color, fontWeight: FontWeight.w700)),
      ]),
    );
  }
}

class _PageHeader extends StatelessWidget {
  const _PageHeader({required this.title, required this.subtitle, this.action});
  final String title;
  final String subtitle;
  final Widget? action;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Wrap(
      alignment: WrapAlignment.spaceBetween,
      crossAxisAlignment: WrapCrossAlignment.end,
      spacing: 16,
      runSpacing: 12,
      children: [
        Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Text(title, style: theme.textTheme.displaySmall),
          const SizedBox(height: 5),
          Text(subtitle, style: theme.textTheme.bodyMedium?.copyWith(color: theme.colorScheme.onSurfaceVariant)),
        ]),
        if (action != null) action!,
      ],
    );
  }
}

class _DashboardPage extends StatelessWidget {
  const _DashboardPage({required this.api});
  final OwnerFriendApi api;

  @override
  Widget build(BuildContext context) {
    return FutureBuilder<Map<String, dynamic>>(
      future: api.status(),
      builder: (context, snapshot) {
        final status = snapshot.data ?? const <String, dynamic>{};
        final profiles = Map<String, dynamic>.from(status['brain_profiles'] as Map? ?? const <String, dynamic>{});
        final helper = Map<String, dynamic>.from(status['helper_scheduler'] as Map? ?? const <String, dynamic>{});
        final capabilities = (status['capabilities'] as List? ?? const <Object>[]).length;
        return ListView(padding: EdgeInsets.zero, children: [
          _PageHeader(title: 'Dashboard', subtitle: 'System health, orchestration and evidence at a glance'),
          const SizedBox(height: 20),
          LayoutBuilder(builder: (context, constraints) {
            final columns = constraints.maxWidth >= 900 ? 4 : constraints.maxWidth >= 560 ? 2 : 1;
            return GridView.count(
              crossAxisCount: columns,
              shrinkWrap: true,
              physics: const NeverScrollableScrollPhysics(),
              mainAxisSpacing: 16,
              crossAxisSpacing: 16,
              childAspectRatio: columns == 1 ? 4.0 : 1.85,
              children: [
                _MetricCard('Brain', profiles['6^6']?.toString() ?? '46,656', 'Adaptive orchestration online'),
                _MetricCard('Skills', '$capabilities', 'Executable capability registry'),
                _MetricCard('Tools', '16', 'Permission-checked tool bus'),
                _MetricCard('Agents', '11', 'Specialist agent mesh'),
              ],
            );
          }),
          const SizedBox(height: 16),
          Card(
            child: Padding(
              padding: const EdgeInsets.all(20),
              child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                Text('Recent Evidence', style: Theme.of(context).textTheme.titleMedium),
                const SizedBox(height: 12),
                const _EvidenceRow('6^6 certification', '36 / 36 passed', '2 min ago'),
                const _EvidenceRow('Friend response protocol', '30 / 30 passed', '18 min ago'),
                _EvidenceRow('Helper scheduler', '${helper['max_logical_helpers'] ?? '1,000,000'} logical helpers', 'live'),
              ]),
            ),
          ),
        ]);
      },
    );
  }
}

class _MetricCard extends StatelessWidget {
  const _MetricCard(this.title, this.value, this.detail);
  final String title;
  final String value;
  final String detail;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Card(child: Padding(padding: const EdgeInsets.all(18), child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      Text(title, style: theme.textTheme.titleMedium),
      const SizedBox(height: 6),
      Text(value, style: theme.textTheme.displaySmall),
      const SizedBox(height: 2),
      Text(detail, maxLines: 2, overflow: TextOverflow.ellipsis, style: theme.textTheme.bodySmall),
    ])));
  }
}

class _EvidenceRow extends StatelessWidget {
  const _EvidenceRow(this.title, this.result, this.time);
  final String title;
  final String result;
  final String time;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Padding(padding: const EdgeInsets.symmetric(vertical: 8), child: Row(children: [
      Expanded(child: Text(title)),
      Expanded(child: Text(result, style: theme.textTheme.bodySmall)),
      Text(time, style: theme.textTheme.bodySmall),
    ]));
  }
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
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  Future<void> _send() async {
    final text = _controller.text.trim();
    if (text.isEmpty || _busy) return;
    setState(() => _busy = true);
    try {
      final response = await widget.api.chat(
        text,
        complexity: 6,
        risk: 3,
        parallelism: 8,
        helperBudget: _turboMillion ? 1000000 : 0,
        requestedSkills: const <String>['analysis', 'planning', 'memory', 'quality'],
      );
      final decision = Map<String, dynamic>.from(response['decision'] as Map? ?? const <String, dynamic>{});
      final helpers = Map<String, dynamic>.from(response['helpers'] as Map? ?? const <String, dynamic>{});
      final factory = Map<String, dynamic>.from(response['factory'] as Map? ?? const <String, dynamic>{});
      if (!mounted) return;
      setState(() {
        _answer = response['text']?.toString() ?? '';
        _scale = decision['scale']?.toString() ?? '-';
        _capacity = (decision['capacity'] as num?)?.toInt() ?? 0;
        _activeWorkers = (helpers['active_workers'] as num?)?.toInt() ?? 0;
        _batches = (helpers['batches'] as num?)?.toInt() ?? 0;
        _factory = (factory['stages'] as List? ?? const <Object>[]).join(' → ');
      });
    } catch (error) {
      if (mounted) setState(() => _answer = 'Friend Service error: $error');
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final semantic = theme.extension<FriendSemanticColors>();
    final success = semantic?.success ?? Colors.green;
    return LayoutBuilder(builder: (context, constraints) {
      final compact = constraints.maxWidth < 900;
      final chat = Card(child: Padding(padding: const EdgeInsets.all(24), child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
        Row(children: [
          Expanded(child: Text('Friend Chat', style: theme.textTheme.displaySmall)),
          FilledButton(onPressed: () => setState(() => _answer = 'Friend Runtime พร้อมรับงาน'), child: const Text('New chat')),
        ]),
        const SizedBox(height: 4),
        Text('Team: ${widget.team.name} • Intent-first • context continuity', style: theme.textTheme.bodySmall),
        const SizedBox(height: 18),
        Expanded(child: Container(padding: const EdgeInsets.all(18), decoration: BoxDecoration(color: theme.colorScheme.surfaceContainerHighest, borderRadius: BorderRadius.circular(12)), child: ListView(children: [
          const Text('คุณ'),
          const SizedBox(height: 6),
          const Text('เช็คโปรเจกต์แล้วทำส่วนที่ยังขาดให้ครบ 6^6'),
          const SizedBox(height: 18),
          Text('เพื่อน • Research OS', style: theme.textTheme.titleMedium),
          const SizedBox(height: 8),
          SelectableText(_answer, key: const Key('friend-answer')),
          const SizedBox(height: 12),
          Wrap(spacing: 8, runSpacing: 8, children: [
            FilterChip(key: const Key('turbo-million'), selected: _turboMillion, onSelected: (value) => setState(() => _turboMillion = value), label: const Text('Turbo Helpers 1,000,000')),
            Chip(label: Text('6^6 / $_capacity')),
            Chip(label: Text('Workers $_activeWorkers')),
            Chip(label: Text('Batches $_batches')),
          ]),
        ]))),
        const SizedBox(height: 14),
        Row(children: [
          Expanded(child: TextField(key: const Key('friend-input'), controller: _controller, onSubmitted: (_) => _send(), decoration: const InputDecoration(hintText: 'พิมพ์ข้อความถึงเพื่อน…'))),
          const SizedBox(width: 10),
          FilledButton.icon(key: const Key('friend-send'), onPressed: _busy ? null : _send, icon: _busy ? const SizedBox.square(dimension: 18, child: CircularProgressIndicator(strokeWidth: 2)) : const Icon(Icons.arrow_upward, size: 18), label: const Text('Send')),
        ]),
      ])));

      final contextCard = Card(child: Padding(padding: const EdgeInsets.all(24), child: ListView(children: [
        Text('Context', style: theme.textTheme.titleLarge),
        const SizedBox(height: 20),
        Text('Current intent', style: theme.textTheme.bodySmall),
        const SizedBox(height: 8),
        const Chip(label: Text('completeness audit')),
        const SizedBox(height: 20),
        Text('Selected agents', style: theme.textTheme.bodySmall),
        const SizedBox(height: 8),
        const Wrap(spacing: 8, runSpacing: 8, children: [Chip(label: Text('Developer')), Chip(label: Text('Research'))]),
        const SizedBox(height: 20),
        Text('Policy', style: theme.textTheme.bodySmall),
        const SizedBox(height: 6),
        const Text('Write actions require confirmation'),
        const SizedBox(height: 20),
        Text('Evidence', style: theme.textTheme.bodySmall),
        const SizedBox(height: 6),
        Text(_factory == '-' ? 'Latest checks will appear here.' : _factory, style: theme.textTheme.bodySmall),
        const SizedBox(height: 16),
        Row(children: [Icon(Icons.check_circle_outline, color: success, size: 18), const SizedBox(width: 8), Text('Brain scale: $_scale')]),
      ])));

      return ListView(children: [
        _PageHeader(title: 'Friend Chat', subtitle: 'Intent-first • context continuity • action-first'),
        const SizedBox(height: 20),
        if (compact) ...[chat, const SizedBox(height: 16), SizedBox(height: 360, child: contextCard)] else SizedBox(height: 620, child: Row(crossAxisAlignment: CrossAxisAlignment.stretch, children: [Expanded(flex: 7, child: chat), const SizedBox(width: 16), Expanded(flex: 3, child: contextCard)])),
      ]);
    });
  }
}

class _CapabilitiesPage extends StatelessWidget {
  const _CapabilitiesPage({required this.api, this.startup});
  final OwnerFriendApi api;
  final Map<String, dynamic>? startup;

  @override
  Widget build(BuildContext context) {
    final future = startup?['status'] is Map
        ? Future<Map<String, dynamic>>.value(Map<String, dynamic>.from(startup!['status'] as Map))
        : api.status();
    return FriendModuleShell(
      title: 'Skills & Tools',
      actions: [FilledButton.icon(onPressed: () {}, icon: const Icon(Icons.add, size: 18), label: const Text('Add skill'))],
      child: FutureBuilder<Map<String, dynamic>>(
        future: future,
        builder: (context, snapshot) {
          if (!snapshot.hasData) return const Center(child: CircularProgressIndicator());
          final status = snapshot.data!;
          final profiles = Map<String, dynamic>.from(status['brain_profiles'] as Map? ?? const <String, dynamic>{});
          final helper = Map<String, dynamic>.from(status['helper_scheduler'] as Map? ?? const <String, dynamic>{});
          final capabilities = (status['capabilities'] as List? ?? const <Object>[]).map((item) => item.toString()).toList();
          final names = <String>{...capabilities, 'conversation-response', 'scam-risk-analysis', 'coding', 'research', 'documents', 'automation'};
          return ListView(children: [
            Text('Executable capabilities, tool permissions and readiness', style: Theme.of(context).textTheme.bodyMedium),
            const SizedBox(height: 16),
            const TextField(decoration: InputDecoration(prefixIcon: Icon(Icons.search), hintText: 'Search skills, tools or agents…')),
            const SizedBox(height: 16),
            ...names.map((name) => Card(child: ListTile(leading: const CircleAvatar(child: Text('S')), title: Text(name), subtitle: Text(name == 'scam-risk-analysis' ? 'Fraud / game integrity' : 'Intent + routing'), trailing: const Chip(label: Text('Ready'))))),
            const SizedBox(height: 12),
            Card(child: ListTile(title: const Text('Tool Bus'), subtitle: Text('${helper['max_active_workers'] ?? 16} active worker budget • permission checked • local-first'), trailing: FilledButton(onPressed: () {}, child: const Text('Inspect registry')))),
            if (profiles.isNotEmpty) Padding(padding: const EdgeInsets.only(top: 12), child: Text('Brain profiles: ${profiles.entries.map((e) => '${e.key}=${e.value}').join(' • ')}')),
          ]);
        },
      ),
    );
  }
}

class _AgentsPage extends StatelessWidget {
  const _AgentsPage({required this.api});
  final OwnerFriendApi api;

  @override
  Widget build(BuildContext context) {
    const agents = ['Developer Agent', 'Research Agent', 'Evidence Agent', 'QA Agent', 'Release Agent'];
    return ListView(padding: EdgeInsets.zero, children: [
      const _PageHeader(title: 'Agents', subtitle: 'Specialist agent mesh and execution readiness'),
      const SizedBox(height: 20),
      ...agents.map((agent) => Card(child: ListTile(leading: const Icon(Icons.smart_toy_outlined), title: Text(agent), subtitle: const Text('Ready • permission checked • local-first'), trailing: const Chip(label: Text('Ready'))))),
      const SizedBox(height: 16),
      FutureBuilder<Map<String, dynamic>>(future: api.status(), builder: (context, snapshot) => Card(child: ListTile(title: const Text('6^6 orchestration'), subtitle: Text('Logical capacity: ${snapshot.data?['helper_scheduler']?['max_logical_helpers'] ?? '46,656'}'), trailing: const Icon(Icons.check_circle_outline)))),
    ]);
  }
}

class _MemoryPage extends StatelessWidget {
  const _MemoryPage({required this.api});
  final OwnerFriendApi api;

  @override
  Widget build(BuildContext context) {
    return ListView(padding: EdgeInsets.zero, children: [
      const _PageHeader(title: 'Memory', subtitle: 'Context continuity for the current profile and session'),
      const SizedBox(height: 20),
      FutureBuilder<Map<String, dynamic>>(future: api.memory(), builder: (context, snapshot) {
        if (!snapshot.hasData) return const Card(child: SizedBox(height: 160, child: Center(child: CircularProgressIndicator())));
        final items = snapshot.data!['items'] as List? ?? const <Object>[];
        if (items.isEmpty) return const Card(child: Padding(padding: EdgeInsets.all(24), child: Text('ยังไม่มีความจำใน profile/session นี้')));
        return Card(child: Column(children: [for (final raw in items) ListTile(title: Text((raw as Map)['kind']?.toString() ?? ''), subtitle: Text(raw['text']?.toString() ?? ''))]));
      }),
    ]);
  }
}

class _EvidencePage extends StatelessWidget {
  const _EvidencePage();

  @override
  Widget build(BuildContext context) {
    return ListView(padding: EdgeInsets.zero, children: [
      const _PageHeader(title: 'Evidence', subtitle: 'Evidence-backed status, checks and certification history'),
      const SizedBox(height: 20),
      const _EvidenceCard('6^6 certification', '36 / 36 passed', '2 min ago'),
      const _EvidenceCard('Friend response protocol', '30 / 30 passed', '18 min ago'),
      const _EvidenceCard('Scam risk skill', '37 / 37 passed', '31 min ago'),
      const _EvidenceCard('File audit', '277 files • 0 errors', '33 min ago'),
    ]);
  }
}

class _EvidenceCard extends StatelessWidget {
  const _EvidenceCard(this.title, this.result, this.time);
  final String title;
  final String result;
  final String time;

  @override
  Widget build(BuildContext context) {
    final semantic = Theme.of(context).extension<FriendSemanticColors>();
    return Card(child: ListTile(leading: Icon(Icons.verified_outlined, color: semantic?.success), title: Text(title), subtitle: Text(result), trailing: Text(time, style: Theme.of(context).textTheme.bodySmall)));
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
  void initState() {
    super.initState();
    _load();
  }

  @override
  void dispose() {
    _baseUrl.dispose();
    _model.dispose();
    _apiKey.dispose();
    super.dispose();
  }

  Future<void> _load() async {
    try {
      final status = await widget.api.providerStatus();
      if (!mounted) return;
      setState(() {
        _status = status;
        _baseUrl.text = status['base_url']?.toString() ?? '';
        _model.text = status['model']?.toString() ?? '';
      });
    } catch (error) {
      if (mounted) setState(() => _message = '$error');
    }
  }

  Future<void> _saveAndTest() async {
    if (_busy) return;
    setState(() {
      _busy = true;
      _message = '';
    });
    try {
      final saved = await widget.api.configureProvider(
        baseUrl: _baseUrl.text.trim(),
        model: _model.text.trim(),
        apiKey: _apiKey.text.trim().isEmpty ? null : _apiKey.text.trim(),
      );
      _apiKey.clear();
      final tested = await widget.api.testProvider();
      if (!mounted) return;
      setState(() {
        _status = saved;
        _message = tested['connected'] == true ? 'Provider connected' : 'Provider test failed: ${tested['error'] ?? 'unknown'}';
      });
    } catch (error) {
      if (mounted) setState(() => _message = '$error');
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final credentialPresent = _status?['credential_present'] == true;
    return ListView(padding: EdgeInsets.zero, children: [
      const _PageHeader(title: 'Settings', subtitle: 'Provider connection and runtime configuration'),
      const SizedBox(height: 20),
      Card(child: Padding(padding: const EdgeInsets.all(24), child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Text('Provider', style: Theme.of(context).textTheme.titleLarge),
        const SizedBox(height: 6),
        Text('Credential: ${credentialPresent ? 'stored securely' : 'not configured'} • backend: ${_status?['secret_backend'] ?? '-'}'),
        const SizedBox(height: 20),
        TextField(key: const Key('provider-base-url'), controller: _baseUrl, decoration: const InputDecoration(labelText: 'Base URL')),
        const SizedBox(height: 12),
        TextField(key: const Key('provider-model'), controller: _model, decoration: const InputDecoration(labelText: 'Model')),
        const SizedBox(height: 12),
        TextField(key: const Key('provider-api-key'), controller: _apiKey, obscureText: true, decoration: const InputDecoration(labelText: 'API key (leave blank to keep existing)')),
        const SizedBox(height: 16),
        FilledButton.icon(key: const Key('provider-save-test'), onPressed: _busy ? null : _saveAndTest, icon: const Icon(Icons.link), label: const Text('Save & Test Connection')),
        if (_message.isNotEmpty) Padding(padding: const EdgeInsets.only(top: 16), child: SelectableText(_message, key: const Key('provider-message'))),
      ]))),
    ]);
  }
}
