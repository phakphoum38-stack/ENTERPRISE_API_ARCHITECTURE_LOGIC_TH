import 'dart:async';

import 'package:flutter/material.dart';

import 'friend_module_shell.dart';
import 'owner_api.dart';

class LaunchDeskPage extends StatefulWidget {
  const LaunchDeskPage({required this.api, super.key});
  final OwnerFriendApi api;

  @override
  State<LaunchDeskPage> createState() => _LaunchDeskPageState();
}

class _LaunchDeskPageState extends State<LaunchDeskPage> {
  final _controller = TextEditingController();
  StreamSubscription<Map<String, dynamic>>? _subscription;
  bool _busy = false;
  String _modelText = '';
  String _error = '';
  Map<String, dynamic>? _plan;
  final List<String> _activity = <String>[];

  @override
  void dispose() {
    _subscription?.cancel();
    _controller.dispose();
    super.dispose();
  }

  Future<void> _planLaunch() async {
    final text = _controller.text.trim();
    if (text.isEmpty || _busy) return;
    final api = widget.api;
    if (api is! HttpOwnerFriendApi) {
      setState(() => _error = 'Launch Desk streaming requires the HTTP Owner Friend API.');
      return;
    }
    await _subscription?.cancel();
    setState(() {
      _busy = true;
      _error = '';
      _modelText = '';
      _plan = null;
      _activity.clear();
    });
    try {
      _subscription = api.launchDesk(text).listen((event) {
        if (!mounted) return;
        final type = event['type']?.toString() ?? '';
        if (type == 'tool_event') {
          final phase = event['phase']?.toString() ?? '';
          final tool = event['tool']?.toString() ?? 'tool';
          setState(() => _activity.add('$phase • $tool'));
        } else if (type == 'plan_ready' || type == 'final') {
          final plan = event['plan'];
          if (plan is Map) setState(() => _plan = Map<String, dynamic>.from(plan));
          if (type == 'final') setState(() => _modelText = event['model_text']?.toString() ?? '');
        } else if (type == 'started') {
          setState(() => _activity.add('Launch Desk started'));
        } else if (type == 'model_text_delta') {
          setState(() => _modelText += event['delta']?.toString() ?? '');
        }
      }, onError: (Object error) {
        if (mounted) setState(() => _error = 'Launch Desk error: $error');
      }, onDone: () {
        if (mounted) setState(() => _busy = false);
      });
    } catch (error) {
      if (mounted) setState(() { _error = 'Launch Desk error: $error'; _busy = false; });
    }
  }

  @override
  Widget build(BuildContext context) {
    final plan = _plan;
    final readiness = (plan?['readiness'] as List? ?? const <Object>[]).cast<Object>();
    final risks = (plan?['risks'] as List? ?? const <Object>[]).map((item) => item.toString()).toList();
    final checklist = (plan?['owner_checklist'] as List? ?? const <Object>[]).map((item) => item.toString()).toList();
    final questions = (plan?['follow_up_questions'] as List? ?? const <Object>[]).map((item) => item.toString()).toList();
    return FriendModuleShell(
      title: 'Launch Desk',
      child: ListView(children: [
        Text('Plan a launch with evidence-first readiness gates.', style: Theme.of(context).textTheme.titleMedium),
        const SizedBox(height: 12),
        TextField(key: const Key('launch-desk-input'), controller: _controller, minLines: 4, maxLines: 8, decoration: const InputDecoration(labelText: 'Launch context', hintText: 'Product, QA, infrastructure, risks, rollout notes…')),
        const SizedBox(height: 12),
        FilledButton.icon(key: const Key('launch-desk-plan'), onPressed: _busy ? null : _planLaunch, icon: _busy ? const SizedBox.square(dimension: 18, child: CircularProgressIndicator(strokeWidth: 2)) : const Icon(Icons.rocket_launch_outlined), label: Text(_busy ? 'Planning…' : 'Plan Launch')),
        if (_activity.isNotEmpty) ...[
          const SizedBox(height: 16),
          Text('Activity', style: Theme.of(context).textTheme.titleSmall),
          ..._activity.takeLast(12).map((item) => ListTile(dense: true, leading: const Icon(Icons.bolt_outlined, size: 18), title: Text(item))),
        ],
        if (_error.isNotEmpty) Padding(padding: const EdgeInsets.only(top: 12), child: Text(_error, key: const Key('launch-desk-error'))),
        if (plan != null) ...[
          const SizedBox(height: 18),
          Card(child: ListTile(title: const Text('Readiness score'), trailing: Text('${plan['readiness_score'] ?? '-'} / 100', style: const TextStyle(fontSize: 20, fontWeight: FontWeight.w800)))),
          const SizedBox(height: 12),
          Text('Readiness gates', style: Theme.of(context).textTheme.titleSmall),
          ...readiness.map((raw) {
            final item = Map<String, dynamic>.from(raw as Map);
            return ListTile(dense: true, title: Text(item['area']?.toString() ?? ''), subtitle: Text(item['next_action']?.toString() ?? ''), trailing: Text('${item['score'] ?? '-'}'));
          }),
          _section('Top risks', risks),
          _section('Owner checklist', checklist),
          if (_modelText.isNotEmpty) ...[const SizedBox(height: 12), Text('Agent plan', style: Theme.of(context).textTheme.titleSmall), const SizedBox(height: 6), SelectableText(_modelText, key: const Key('launch-desk-model'))],
          if (questions.isNotEmpty) _section('Follow-up questions', questions),
          if (plan['launch_copy'] != null) ...[const SizedBox(height: 12), Text('Launch copy', style: Theme.of(context).textTheme.titleSmall), const SizedBox(height: 6), SelectableText(plan['launch_copy'].toString(), key: const Key('launch-desk-copy'))],
        ],
      ]),
    );
  }

  Widget _section(String title, List<String> items) => Padding(
        padding: const EdgeInsets.only(top: 14),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Text(title, style: Theme.of(context).textTheme.titleSmall),
          ...items.map((item) => ListTile(dense: true, leading: const Icon(Icons.check_circle_outline, size: 18), title: Text(item))),
        ]),
      );
}

extension on List<String> {
  Iterable<String> takeLast(int count) => skip(length > count ? length - count : 0);
}
