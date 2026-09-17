import 'dart:convert';
import 'dart:io';

import 'package:flutter/material.dart';

void main() => runApp(const OwnerExperimentalWorkbenchApp());

class OwnerExperimentalWorkbenchApp extends StatelessWidget {
  const OwnerExperimentalWorkbenchApp({super.key});

  @override
  Widget build(BuildContext context) {
    final scheme = ColorScheme.fromSeed(seedColor: const Color(0xFF6D5DFB));
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      title: 'Research OS — Owner Experimental Workbench',
      theme: ThemeData(useMaterial3: true, colorScheme: scheme, scaffoldBackgroundColor: scheme.surface),
      home: const WorkbenchPage(),
    );
  }
}

enum WorkbenchView { chat, missions, workspace, github, execution, evidence, resources, audit, assurance }
enum CommandMode { chat, work }

typedef Json = Map<String, dynamic>;

class WorkbenchPage extends StatefulWidget {
  const WorkbenchPage({super.key});

  @override
  State<WorkbenchPage> createState() => _WorkbenchPageState();
}

class _WorkbenchPageState extends State<WorkbenchPage> {
  final _prompt = TextEditingController();
  final _endpoint = TextEditingController(text: 'http://127.0.0.1:8787');
  final _scroll = ScrollController();
  final _sessionId = 'owner-experimental-chat';
  final List<_Message> _messages = [];
  final List<_Event> _events = [];

  WorkbenchView _view = WorkbenchView.chat;
  CommandMode _mode = CommandMode.chat;
  bool _busy = false;
  bool _ownerGuard = true;
  bool _approvalRequired = true;
  bool _memory = true;
  bool _evidenceRequired = true;
  String _status = 'Ready';
  String _mission = 'No mission selected';
  String _execution = 'Idle';
  String _provider = 'Existing Research OS provider';
  int _complexity = 3;
  int _risk = 1;
  int _parallelism = 2;

  @override
  void dispose() {
    _prompt.dispose();
    _endpoint.dispose();
    _scroll.dispose();
    super.dispose();
  }

  void _event(String kind, String detail) {
    setState(() => _events.insert(0, _Event(DateTime.now(), kind, detail)));
  }

  Future<void> _send() async {
    final text = _prompt.text.trim();
    if (text.isEmpty || _busy) return;
    final base = _endpoint.text.trim().replaceFirst(RegExp(r'/$'), '');
    if (_ownerGuard == false) {
      _show('Owner guard is disabled. Experimental execution is blocked.');
      return;
    }

    setState(() {
      _messages.add(_Message.user(text));
      _prompt.clear();
      _busy = true;
      _status = 'Sending to API Platform…';
      _execution = 'Running';
    });
    _event('COMMAND', text);
    _scrollBottom();

    try {
      final client = HttpClient();
      try {
        final request = await client.postUrl(Uri.parse('$base/v1/ai/generate'));
        request.headers.contentType = ContentType.json;
        request.headers.set('X-Research-OS-Owner', 'owner');
        request.headers.set('X-Research-OS-Profile', 'default');
        request.headers.set('X-Research-OS-Session', _sessionId);
        request.write(jsonEncode({
          'prompt': text,
          'complexity': _complexity,
          'risk': _risk,
          'parallelism': _parallelism,
          'helper_budget': 0,
          'requested_skills': <String>[],
          'requested_tools': <String>[],
          'session_id': _sessionId,
          'command_mode': _mode.name,
          'mission_id': _mission == 'No mission selected' ? null : _mission,
        }));
        final response = await request.close();
        final body = await utf8.decoder.bind(response).join();
        dynamic decoded;
        try {
          decoded = jsonDecode(body);
        } catch (_) {
          decoded = {'text': body};
        }
        if (response.statusCode < 200 || response.statusCode >= 300) {
          throw HttpException('HTTP ${response.statusCode}: ${_display(decoded)}');
        }
        setState(() {
          _messages.add(_Message.assistant(_display(decoded), decoded));
          _status = 'Connected • API Platform :8787 → Friend :8790';
          _execution = 'Complete';
        });
        _event('RESULT', 'Research OS response received');
        _event('EVIDENCE', _evidenceRequired ? 'Evidence view available; verifier is not bypassed.' : 'Evidence display optional.');
      } finally {
        client.close(force: true);
      }
    } catch (error) {
      setState(() {
        _messages.add(_Message.assistant('Request failed: $error'));
        _status = 'Connection error';
        _execution = 'Failed';
      });
      _event('FAILURE', error.toString());
    } finally {
      setState(() => _busy = false);
      _scrollBottom();
    }
  }

  String _display(dynamic value) {
    if (value is Map<String, dynamic>) {
      final text = value['text'] ?? value['answer'] ?? value['response'];
      if (text != null) return text.toString();
      return const JsonEncoder.withIndent('  ').convert(value);
    }
    return value.toString();
  }

  void _scrollBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scroll.hasClients) {
        _scroll.animateTo(_scroll.position.maxScrollExtent, duration: const Duration(milliseconds: 180), curve: Curves.easeOut);
      }
    });
  }

  void _show(String text) => ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(text)));

  @override
  Widget build(BuildContext context) {
    final wide = MediaQuery.sizeOf(context).width >= 1050;
    return Scaffold(
      body: SafeArea(
        child: Row(
          children: [
            _Navigation(selected: _view, onSelect: (v) => setState(() => _view = v), wide: wide),
            Expanded(child: Column(children: [
              _TopBar(view: _view, status: _status, ownerGuard: _ownerGuard),
              Expanded(child: _buildView()),
            ])),
          ],
        ),
      ),
    );
  }

  Widget _buildView() {
    switch (_view) {
      case WorkbenchView.chat:
        return _chatView();
      case WorkbenchView.missions:
        return _missionsView();
      case WorkbenchView.workspace:
        return _workspaceView();
      case WorkbenchView.github:
        return _githubView();
      case WorkbenchView.execution:
        return _executionView();
      case WorkbenchView.evidence:
        return _evidenceView();
      case WorkbenchView.resources:
        return _resourcesView();
      case WorkbenchView.audit:
        return _auditView();
      case WorkbenchView.assurance:
        return _assuranceView();
    }
  }

  Widget _chatView() => Column(children: [
    _ControlStrip(
      children: [
        SegmentedButton<CommandMode>(segments: const [ButtonSegment(value: CommandMode.chat, label: Text('Chat')), ButtonSegment(value: CommandMode.work, label: Text('Work'))], selected: {_mode}, onSelectionChanged: (s) => setState(() => _mode = s.first)),
        _Toggle(label: 'Memory', value: _memory, onChanged: (v) => setState(() => _memory = v)),
        _Toggle(label: 'Evidence required', value: _evidenceRequired, onChanged: (v) => setState(() => _evidenceRequired = v)),
        const _Badge(icon: Icons.all_inclusive, label: 'No artificial chat quota'),
      ],
    ),
    Expanded(child: Row(children: [
      Expanded(child: _messages.isEmpty ? const _Welcome() : ListView.builder(controller: _scroll, padding: const EdgeInsets.all(22), itemCount: _messages.length, itemBuilder: (_, i) => _MessageBubble(message: _messages[i]))),
      if (MediaQuery.sizeOf(context).width >= 1250) SizedBox(width: 290, child: _InspectorPanel(mission: _mission, execution: _execution, provider: _provider, complexity: _complexity, risk: _risk, parallelism: _parallelism)),
    ])),
    _Composer(controller: _prompt, busy: _busy, onSend: _send, endpoint: _endpoint),
  ]);

  Widget _missionsView() => _Page(title: 'Mission Control', subtitle: 'Intent → plan → execution → evidence → recovery', children: [
    _ActionCard(icon: Icons.add_task, title: 'Create mission', body: 'Define intent, scope, constraints, verification and stop conditions.', action: () { setState(() { _mission = 'mission-${DateTime.now().millisecondsSinceEpoch}'; }); _event('MISSION', 'Created $_mission'); }),
    _ActionCard(icon: Icons.account_tree, title: 'Task dependency graph', body: 'Plan dependencies and checkpoints without claiming execution.', action: () => _show('Planner surface ready; execution remains governed by the existing core.')),
    _ActionCard(icon: Icons.pause_circle_outline, title: 'Recovery / resume', body: 'Pause, resume, retry and checkpoint long-running work.', action: () { setState(() => _execution = 'Recovery pending'); _event('RECOVERY', 'Recovery action requested'); }),
    _InfoGrid(items: {'Mission': _mission, 'Mode': _mode.name, 'Approval': _approvalRequired ? 'Required' : 'Not required', 'Stop conditions': 'Configured', 'Completion rule': _evidenceRequired ? 'Evidence required' : 'Result only', 'Chat quota': 'None in Research OS'}),
  ]);

  Widget _workspaceView() => _Page(title: 'Workspace', subtitle: 'VS Code / local environment control surface', children: [
    _InfoGrid(items: {'Workspace': 'Owner Experimental', 'Repository': 'ENTERPRISE_API_ARCHITECTURE_LOGIC_TH', 'Branch': 'experiment/owner-chat-api-platform', 'Target': 'main seam only', 'API Platform': _endpoint.text, 'Friend': '127.0.0.1:8790'}),
    _ActionCard(icon: Icons.health_and_safety, title: 'Environment Doctor', body: 'Service discovery, port diagnostics, runtime snapshot, dependency and tool availability.', action: () => _event('ENVIRONMENT', 'Doctor check requested')),
    _ActionCard(icon: Icons.lock_outline, title: 'Workspace safety', body: 'Dirty-workspace guard, workspace lock and scope-aware change preview.', action: () => _event('WORKSPACE', 'Safety check requested')),
    _ActionCard(icon: Icons.terminal, title: 'Command palette', body: 'Open repo, search code, inspect status, run governed commands and attach evidence.', action: () => _show('Command palette is a UI surface; no command is executed from this placeholder.')),
  ]);

  Widget _githubView() => _Page(title: 'GitHub Control Plane', subtitle: 'Repository → branch → commit → PR → CI → evidence', children: [
    _InfoGrid(items: {'Repository': 'phakphoum38-stack/ENTERPRISE_API_ARCHITECTURE_LOGIC_TH', 'Branch': 'experiment/owner-chat-api-platform', 'Base': 'main', 'Operation policy': 'Safe Git operations', 'Evidence': 'Bind to exact SHA', 'CI': 'Read / mission trigger surface'}),
    _ActionCard(icon: Icons.search, title: 'Repository & code search', body: 'Find files, symbols and relevant history before proposing changes.', action: () => _event('GITHUB', 'Code search requested')),
    _ActionCard(icon: Icons.merge_type, title: 'PR builder / review mode', body: 'Preview diff, review intent, approvals, checks and lineage before a Git operation.', action: () => _event('GITHUB', 'PR review surface opened')),
    _ActionCard(icon: Icons.verified_outlined, title: 'CI → Research OS', body: 'Attach workflow state, logs and artifacts to a mission without declaring unknown as pass.', action: () => _event('CI', 'CI evidence binding requested')),
  ]);

  Widget _executionView() => _Page(title: 'Execution Console', subtitle: 'Workers, queue, state machine and recovery', children: [
    _InfoGrid(items: {'State': _execution, 'Workers': '0 active (this UI does not fake workers)', 'Queue': 'Not connected', 'Checkpoint': 'Session-scoped', 'Retry': 'Governed', 'Cancellation': 'Available as control surface'}),
    _ActionCard(icon: Icons.account_tree_outlined, title: 'State machine', body: 'PROPOSED → DESIGNED → IMPLEMENTING → VERIFYING → FORENSIC → REVIEW → AUTHORIZED → RELEASED → OPERATING → REBASELINE.', action: () => _show('Lifecycle displayed; current experimental client is not a release authority.')),
    _ActionCard(icon: Icons.groups_outlined, title: 'Worker registry', body: 'Capability, assignment, isolation, result, failure, recovery and evidence surfaces.', action: () => _event('WORKERS', 'Worker registry inspected')),
    _ActionCard(icon: Icons.stop_circle_outlined, title: 'Emergency stop', body: 'Explicit stop control for governed execution.', action: () { setState(() => _execution = 'Stopped'); _event('STOP', 'Emergency stop requested'); }),
  ]);

  Widget _evidenceView() => _Page(title: 'Evidence & Provenance', subtitle: 'Evidence is inspectable; self-report is not independent verification', children: [
    _InfoGrid(items: {'Evidence requirement': _evidenceRequired ? 'ON' : 'OFF', 'Unknown': '≠ PASS', 'Provenance': 'Declared algorithm + actual derivation', 'Lineage': 'Target SHA bound', 'Verification': 'Independent hook', 'Replay': 'Mission timeline'}),
    _ActionCard(icon: Icons.receipt_long, title: 'Evidence ledger', body: 'Show inputs, outputs, hashes, contracts, source lineage and verification state.', action: () => _event('EVIDENCE', 'Ledger view requested')),
    _ActionCard(icon: Icons.fingerprint, title: 'Provenance validator', body: 'Validate artifact identity, declared algorithm and actual digest derivation.', action: () => _event('PROVENANCE', 'Validation requested')),
    _ActionCard(icon: Icons.replay, title: 'Full mission replay', body: 'Reconstruct owner actions, tool calls, file changes, approvals, CI and evidence.', action: () => _event('REPLAY', 'Replay requested')),
  ]);

  Widget _resourcesView() => _Page(title: 'Resource & Provider Control', subtitle: 'No fake chat quota; real execution resources remain governed', children: [
    _InfoGrid(items: {'Chat messages': 'No artificial Research OS quota', 'Execution': 'Policy / Admission / Resource Control', 'Provider': _provider, 'Concurrency': 'Existing core', 'Budget': 'Execution budget only', 'Long-running work': 'Session + mission + execution'}),
    _ActionCard(icon: Icons.tune, title: 'Provider selector', body: 'Inspect the provider seam and keep provider choice separate from chat quota.', action: () => _providerDialog()),
    _ActionCard(icon: Icons.speed, title: 'Resource dashboard', body: 'Workers, concurrency, queue, execution budget and real runtime usage.', action: () => _event('RESOURCE', 'Resource dashboard requested')),
    _ActionCard(icon: Icons.rule, title: 'Policy / admission', body: 'Policy conflicts, governance conflicts and reservation-before-deny diagnostics.', action: () => _event('POLICY', 'Policy inspection requested')),
  ]);

  Widget _auditView() => _Page(title: 'Audit & Forensics', subtitle: 'Every important owner action can become a traceable event', children: [
    _InfoGrid(items: {'Events': '${_events.length}', 'Session': _sessionId, 'Owner': 'owner', 'Audit': 'Local experimental timeline', 'Sensitive output': 'Redaction guard surface', 'Lineage': 'Mission / execution / SHA'}),
    Expanded(child: Card(child: _events.isEmpty ? const Center(child: Text('No events yet.')) : ListView.builder(itemCount: _events.length, itemBuilder: (_, i) { final e = _events[i]; return ListTile(leading: const Icon(Icons.bolt_outlined), title: Text(e.kind), subtitle: Text(e.detail), trailing: Text(_time(e.time)); }))),
  ]);

  Widget _assuranceView() => _Page(title: 'Assurance Center', subtitle: 'P0–P10 assurance surfaces; no verdict is fabricated by the client', children: [
    _InfoGrid(items: {'P0 Identity': 'Owner guard', 'P1 Functional': 'Chat path', 'P2 Integration': '8787 → 8790', 'P3 CI': 'Evidence surface', 'P4 Forensic': 'Audit / replay', 'P5 Provenance': 'Hash lineage', 'P6 Governance': 'Approval / policy', 'P7 Adversarial': 'Guard surface', 'P8 Lifecycle': 'State machine', 'P9 Distributed': 'Workers / concurrency', 'P10 Continuous': 'Rebaseline surface'}),
    _ActionCard(icon: Icons.fact_check_outlined, title: 'Final assurance summary', body: 'Collect claims, evidence and unresolved unknowns without converting unknown into PASS.', action: () => _event('ASSURANCE', 'Summary requested')),
    _ActionCard(icon: Icons.change_circle_outlined, title: 'Rebaseline / retire experiment', body: 'Record supersession and retire the disposable experiment cleanly.', action: () => _event('LIFECYCLE', 'Rebaseline / retire surface opened')),
    _ActionCard(icon: Icons.help_outline, title: 'Why this action?', body: 'Explain intent, files, commands, evidence requirements and possible failure modes.', action: () => _show('Every action should have an inspectable intent and verification path.')),
  ]);

  Future<void> _providerDialog() async {
    final value = await showDialog<String>(context: context, builder: (_) => SimpleDialog(title: const Text('Provider'), children: ['Existing Research OS provider', 'Mock / test provider', 'Provider-neutral'].map((x) => SimpleDialogOption(onPressed: () => Navigator.pop(context, x), child: Text(x))).toList()));
    if (value != null) setState(() => _provider = value);
  }

  String _time(DateTime t) => '${t.hour.toString().padLeft(2, '0')}:${t.minute.toString().padLeft(2, '0')}:${t.second.toString().padLeft(2, '0')}';
}

class _Navigation extends StatelessWidget {
  const _Navigation({required this.selected, required this.onSelect, required this.wide});
  final WorkbenchView selected;
  final ValueChanged<WorkbenchView> onSelect;
  final bool wide;
  @override
  Widget build(BuildContext context) {
    const items = [(WorkbenchView.chat, Icons.forum_outlined, 'Chat'), (WorkbenchView.missions, Icons.route_outlined, 'Missions'), (WorkbenchView.workspace, Icons.code, 'Workspace'), (WorkbenchView.github, Icons.hub_outlined, 'GitHub'), (WorkbenchView.execution, Icons.play_circle_outline, 'Execution'), (WorkbenchView.evidence, Icons.verified_outlined, 'Evidence'), (WorkbenchView.resources, Icons.speed, 'Resources'), (WorkbenchView.audit, Icons.receipt_long, 'Audit'), (WorkbenchView.assurance, Icons.shield_outlined, 'Assurance')];
    return NavigationRailExtendedLike(wide: wide, child: NavigationRail(selectedIndex: items.indexWhere((x) => x.$1 == selected), onDestinationSelected: (i) => onSelect(items[i].$1), labelType: wide ? NavigationRailLabelType.all : NavigationRailLabelType.none, leading: Padding(padding: const EdgeInsets.all(12), child: Icon(Icons.auto_awesome, color: Theme.of(context).colorScheme.primary)), destinations: [for (final x in items) NavigationRailDestination(icon: Icon(x.$2), selectedIcon: Icon(x.$2), label: Text(x.$3))]));
  }
}

class NavigationRailExtendedLike extends StatelessWidget {
  const NavigationRailExtendedLike({required this.child, required this.wide, super.key});
  final Widget child;
  final bool wide;
  @override
  Widget build(BuildContext context) => Container(width: wide ? 150 : 72, decoration: BoxDecoration(border: Border(right: BorderSide(color: Theme.of(context).dividerColor))), child: child);
}

class _TopBar extends StatelessWidget {
  const _TopBar({required this.view, required this.status, required this.ownerGuard});
  final WorkbenchView view;
  final String status;
  final bool ownerGuard;
  @override
  Widget build(BuildContext context) => Container(height: 64, padding: const EdgeInsets.symmetric(horizontal: 18), decoration: BoxDecoration(border: Border(bottom: BorderSide(color: Theme.of(context).dividerColor))), child: Row(children: [const Icon(Icons.science_outlined), const SizedBox(width: 10), const Expanded(child: Column(mainAxisAlignment: MainAxisAlignment.center, crossAxisAlignment: CrossAxisAlignment.start, children: [Text('Research OS', style: TextStyle(fontWeight: FontWeight.w700)), Text('Owner Experimental Workbench', style: TextStyle(fontSize: 12))])), Chip(avatar: Icon(ownerGuard ? Icons.lock : Icons.lock_open, size: 15), label: Text(ownerGuard ? 'OWNER ONLY' : 'BLOCKED')), const SizedBox(width: 10), Text(status, overflow: TextOverflow.ellipsis)]));
}

class _ControlStrip extends StatelessWidget {
  const _ControlStrip({required this.children});
  final List<Widget> children;
  @override
  Widget build(BuildContext context) => Container(padding: const EdgeInsets.fromLTRB(18, 12, 18, 8), child: Wrap(spacing: 10, runSpacing: 8, children: children));
}

class _Toggle extends StatelessWidget {
  const _Toggle({required this.label, required this.value, required this.onChanged});
  final String label; final bool value; final ValueChanged<bool> onChanged;
  @override
  Widget build(BuildContext context) => FilterChip(label: Text(label), selected: value, onSelected: onChanged);
}

class _Badge extends StatelessWidget {
  const _Badge({required this.icon, required this.label});
  final IconData icon; final String label;
  @override
  Widget build(BuildContext context) => Chip(avatar: Icon(icon, size: 16), label: Text(label));
}

class _Welcome extends StatelessWidget {
  const _Welcome();
  @override
  Widget build(BuildContext context) => Center(child: SingleChildScrollView(child: Padding(padding: const EdgeInsets.all(32), child: ConstrainedBox(constraints: const BoxConstraints(maxWidth: 850), child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [Text('Owner Experimental Workbench', style: Theme.of(context).textTheme.headlineMedium?.copyWith(fontWeight: FontWeight.w800)), const SizedBox(height: 10), const Text('A new experimental UI for commanding the existing Research OS stack. Chat is only one surface: missions, workspace, GitHub, execution, evidence, resources, audit and assurance are first-class.'), const SizedBox(height: 24), _InfoGrid(items: {'Transport': 'Flutter → API Platform :8787 → Friend :8790', 'Identity': 'Owner-only experimental guard', 'Quota': 'No artificial Research OS chat-message quota', 'Execution': 'Existing Policy / Admission / Resource Control', 'Verification': 'Evidence-aware; unknown ≠ PASS', 'Lifecycle': 'Full P0–P10 assurance surface'}), const SizedBox(height: 20), Text('Try a command', style: Theme.of(context).textTheme.titleMedium), const SizedBox(height: 8), const Text('“ตรวจงานค้างชุดถัดไป แล้วสรุป evidence ที่ต้องใช้”'), ]))));
}

class _InspectorPanel extends StatelessWidget {
  const _InspectorPanel({required this.mission, required this.execution, required this.provider, required this.complexity, required this.risk, required this.parallelism});
  final String mission, execution, provider; final int complexity, risk, parallelism;
  @override
  Widget build(BuildContext context) => Container(decoration: BoxDecoration(border: Border(left: BorderSide(color: Theme.of(context).dividerColor))), padding: const EdgeInsets.all(16), child: ListView(children: [_PanelTitle(title: 'Live Inspector'), _KV('Mission', mission), _KV('Execution', execution), _KV('Provider', provider), _KV('Complexity', '$complexity'), _KV('Risk', '$risk'), _KV('Parallelism', '$parallelism'), const Divider(height: 28), const _PanelTitle(title: 'Contract'), _KV('API', ':8787 /v1/ai/generate'), _KV('Friend', ':8790 /owner/chat'), _KV('Session', 'owner-experimental-chat'), const Divider(height: 28), const _PanelTitle(title: 'Safety'), _KV('Chat quota', 'None'), _KV('Evidence', 'Inspectable'), _KV('Unknown', 'Not PASS')]),);
}

class _PanelTitle extends StatelessWidget { const _PanelTitle({required this.title}); final String title; @override Widget build(BuildContext context) => Padding(padding: const EdgeInsets.only(bottom: 12), child: Text(title, style: Theme.of(context).textTheme.titleSmall?.copyWith(fontWeight: FontWeight.w800))); }
class _KV extends StatelessWidget { const _KV(this.k, this.v); final String k, v; @override Widget build(BuildContext context) => Padding(padding: const EdgeInsets.symmetric(vertical: 5), child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [Expanded(child: Text(k, style: const TextStyle(fontSize: 12))), Expanded(flex: 2, child: Text(v, style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 12)))])); }

class _Composer extends StatelessWidget {
  const _Composer({required this.controller, required this.busy, required this.onSend, required this.endpoint});
  final TextEditingController controller, endpoint; final bool busy; final VoidCallback onSend;
  @override
  Widget build(BuildContext context) => Material(color: Theme.of(context).colorScheme.surfaceContainer, child: Padding(padding: const EdgeInsets.fromLTRB(16, 10, 16, 14), child: Column(children: [Row(children: [const Icon(Icons.route_outlined, size: 17), const SizedBox(width: 7), Expanded(child: TextField(controller: endpoint, decoration: const InputDecoration(labelText: 'API Platform endpoint', isDense: true, border: OutlineInputBorder()))), const SizedBox(width: 10), const Text('POST /v1/ai/generate')]), const SizedBox(height: 10), Row(crossAxisAlignment: CrossAxisAlignment.end, children: [Expanded(child: TextField(controller: controller, minLines: 1, maxLines: 6, enabled: !busy, onSubmitted: (_) => onSend(), decoration: const InputDecoration(hintText: 'สั่งงาน Research OS…', border: OutlineInputBorder()))), const SizedBox(width: 10), IconButton.filled(onPressed: busy ? null : onSend, icon: busy ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2)) : const Icon(Icons.arrow_upward), tooltip: 'Send')])])));
}

class _MessageBubble extends StatelessWidget {
  const _MessageBubble({required this.message}); final _Message message;
  @override
  Widget build(BuildContext context) { final user = message.role == 'user'; return Align(alignment: user ? Alignment.centerRight : Alignment.centerLeft, child: Container(constraints: const BoxConstraints(maxWidth: 900), margin: const EdgeInsets.only(bottom: 14), padding: const EdgeInsets.all(15), decoration: BoxDecoration(color: user ? Theme.of(context).colorScheme.primaryContainer : Theme.of(context).colorScheme.surfaceContainerHighest, borderRadius: BorderRadius.circular(18)), child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [Text(user ? 'OWNER' : 'FRIEND / RESEARCH OS', style: Theme.of(context).textTheme.labelSmall?.copyWith(fontWeight: FontWeight.w800)), const SizedBox(height: 6), SelectableText(message.text), if (message.raw != null) Align(alignment: Alignment.centerRight, child: TextButton.icon(onPressed: () => showDialog(context: context, builder: (_) => AlertDialog(title: const Text('Raw API response'), content: SingleChildScrollView(child: SelectableText(const JsonEncoder.withIndent('  ').convert(message.raw))), actions: [TextButton(onPressed: () => Navigator.pop(context), child: const Text('Close'))])), icon: const Icon(Icons.data_object, size: 16), label: const Text('Raw API'))]))); }
}

class _Message { const _Message(this.role, this.text, [this.raw]); factory _Message.user(String text) => _Message('user', text); factory _Message.assistant(String text, [dynamic raw]) => _Message('assistant', text, raw); final String role, text; final dynamic raw; }
class _Event { const _Event(this.time, this.kind, this.detail); final DateTime time; final String kind, detail; }

class _Page extends StatelessWidget {
  const _Page({required this.title, required this.subtitle, required this.children});
  final String title, subtitle; final List<Widget> children;
  @override
  Widget build(BuildContext context) => SingleChildScrollView(padding: const EdgeInsets.all(22), child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [Text(title, style: Theme.of(context).textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.w800)), const SizedBox(height: 4), Text(subtitle, style: Theme.of(context).textTheme.bodyMedium), const SizedBox(height: 20), ...children.map((x) => Padding(padding: const EdgeInsets.only(bottom: 14), child: x))]));
}

class _InfoGrid extends StatelessWidget {
  const _InfoGrid({required this.items}); final Map<String, String> items;
  @override
  Widget build(BuildContext context) => LayoutBuilder(builder: (_, c) { final cols = c.maxWidth > 900 ? 3 : c.maxWidth > 560 ? 2 : 1; return GridView.count(crossAxisCount: cols, shrinkWrap: true, physics: const NeverScrollableScrollPhysics(), mainAxisSpacing: 10, crossAxisSpacing: 10, childAspectRatio: 3.4, children: items.entries.map((e) => Card(child: Padding(padding: const EdgeInsets.all(12), child: Column(crossAxisAlignment: CrossAxisAlignment.start, mainAxisAlignment: MainAxisAlignment.center, children: [Text(e.key, style: Theme.of(context).textTheme.labelSmall), const SizedBox(height: 3), Text(e.value, maxLines: 2, overflow: TextOverflow.ellipsis, style: const TextStyle(fontWeight: FontWeight.w700))])))).toList()); });
}

class _ActionCard extends StatelessWidget {
  const _ActionCard({required this.icon, required this.title, required this.body, required this.action});
  final IconData icon; final String title, body; final VoidCallback action;
  @override
  Widget build(BuildContext context) => Card(child: Padding(padding: const EdgeInsets.all(16), child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [Icon(icon, size: 28), const SizedBox(width: 14), Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [Text(title, style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w800)), const SizedBox(height: 4), Text(body)])), const SizedBox(width: 12), OutlinedButton(onPressed: action, child: const Text('Open'))])));
}
