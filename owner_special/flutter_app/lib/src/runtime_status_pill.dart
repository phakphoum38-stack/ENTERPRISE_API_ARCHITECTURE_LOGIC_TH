import 'dart:async';

import 'package:flutter/material.dart';

import 'owner_api.dart';

class RuntimeStatusPill extends StatefulWidget {
  const RuntimeStatusPill({required this.api, required this.fallback, super.key});

  final OwnerFriendApi api;
  final Widget fallback;

  @override
  State<RuntimeStatusPill> createState() => _RuntimeStatusPillState();
}

class _RuntimeStatusPillState extends State<RuntimeStatusPill> {
  Timer? _timer;
  bool _connected = false;
  bool _loading = true;
  int _skills = 0;
  int _tools = 0;
  int _reusable = 0;

  @override
  void initState() {
    super.initState();
    _refresh();
    _timer = Timer.periodic(const Duration(seconds: 10), (_) => _refresh());
  }

  @override
  void dispose() {
    _timer?.cancel();
    super.dispose();
  }

  Future<void> _refresh() async {
    try {
      final status = await widget.api.status();
      final skills = status['skills'];
      final tools = status['tools'];
      final learning = status['self_learning'];
      final learningMap = learning is Map ? Map<String, dynamic>.from(learning) : const <String, dynamic>{};
      if (!mounted) return;
      setState(() {
        _connected = true;
        _loading = false;
        _skills = skills is List ? skills.length : 0;
        _tools = tools is List ? tools.length : 0;
        _reusable = (learningMap['persistent_reusable'] as num?)?.toInt() ?? 0;
      });
    } catch (_) {
      if (!mounted) return;
      setState(() {
        _connected = false;
        _loading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_loading) return widget.fallback;

    final theme = Theme.of(context);
    final color = _connected ? const Color(0xFF34D399) : const Color(0xFFF59E0B);
    final label = _connected
        ? 'Connected • S$_skills T$_tools L$_reusable'
        : 'Offline';

    return Tooltip(
      message: _connected
          ? 'Friend runtime • $_skills skills • $_tools tools • $_reusable reusable learning records'
          : 'Friend runtime unavailable at the configured loopback service',
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 7),
        decoration: BoxDecoration(
          color: color.withValues(alpha: .10),
          borderRadius: BorderRadius.circular(999),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(
              width: 6,
              height: 6,
              decoration: BoxDecoration(color: color, shape: BoxShape.circle),
            ),
            const SizedBox(width: 7),
            Text(
              label,
              style: theme.textTheme.labelMedium?.copyWith(
                color: color,
                fontWeight: FontWeight.w700,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
