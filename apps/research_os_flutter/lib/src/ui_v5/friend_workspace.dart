import 'package:flutter/material.dart';

import '../api/research_os_api_client.dart';
import 'conversation_core.dart';

class FriendWorkspace extends StatefulWidget {
  const FriendWorkspace({required this.apiClient, super.key});

  final ResearchOSApiClient apiClient;

  @override
  State<FriendWorkspace> createState() => _FriendWorkspaceState();
}

class _FriendWorkspaceState extends State<FriendWorkspace> {
  late final ResearchOSConversationController _conversation =
      ResearchOSConversationController(apiClient: widget.apiClient)
        ..addListener(_onConversationChanged);
  final TextEditingController _composer = TextEditingController();

  @override
  void dispose() {
    _conversation
      ..removeListener(_onConversationChanged)
      ..dispose();
    _composer.dispose();
    super.dispose();
  }

  void _onConversationChanged() {
    if (mounted) setState(() {});
  }

  Future<void> _send() async {
    final text = _composer.text.trim();
    if (text.isEmpty) return;
    _composer.clear();
    await _conversation.sendText(text);
  }

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Scaffold(
      backgroundColor: scheme.surface,
      body: SafeArea(
        child: LayoutBuilder(
          builder: (context, constraints) {
            final compact = constraints.maxWidth < 980;
            final conversation = _ConversationPanel(
              controller: _conversation,
              composer: _composer,
              onSend: _send,
            );
            if (compact) {
              return Column(
                children: <Widget>[
                  const _FriendHeader(),
                  Expanded(child: conversation),
                ],
              );
            }
            return Row(
              children: <Widget>[
                Expanded(child: conversation),
                const SizedBox(width: 12),
                const SizedBox(width: 280, child: _ContextPanel()),
              ],
            );
          },
        ),
      ),
    );
  }
}

class _FriendHeader extends StatelessWidget {
  const _FriendHeader();

  @override
  Widget build(BuildContext context) {
    return const Padding(
      padding: EdgeInsets.fromLTRB(20, 18, 20, 10),
      child: Row(
        children: <Widget>[
          _FriendAvatar(size: 42),
          SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: <Widget>[
                Text('Friend', style: TextStyle(fontSize: 20, fontWeight: FontWeight.w800)),
                Text('พร้อมคุย พร้อมทำงาน พร้อมพาไปยัง workspace ที่เหมาะสม'),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _ConversationPanel extends StatelessWidget {
  const _ConversationPanel({
    required this.controller,
    required this.composer,
    required this.onSend,
  });

  final ResearchOSConversationController controller;
  final TextEditingController composer;
  final VoidCallback onSend;

  String _stateLabel(ResearchOSConversationState state) => switch (state) {
        ResearchOSConversationState.idle => 'พร้อมสนทนา',
        ResearchOSConversationState.listening => 'กำลังฟัง',
        ResearchOSConversationState.understanding => 'กำลังทำความเข้าใจ',
        ResearchOSConversationState.thinking => 'กำลังคิด',
        ResearchOSConversationState.working => 'กำลังทำงาน',
        ResearchOSConversationState.speaking => 'กำลังพูด',
        ResearchOSConversationState.needsApproval => 'รอการอนุมัติ',
        ResearchOSConversationState.failed => 'ต้องตรวจสอบ',
      };

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Padding(
      padding: const EdgeInsets.fromLTRB(20, 18, 20, 18),
      child: Column(
        children: <Widget>[
          if (MediaQuery.sizeOf(context).width >= 980) const _FriendHeader(),
          const SizedBox(height: 8),
          Row(
            children: <Widget>[
              const _FriendAvatar(size: 34),
              const SizedBox(width: 10),
              Text(_stateLabel(controller.state), style: Theme.of(context).textTheme.labelLarge),
              const Spacer(),
              FilterChip(
                selected: controller.useMemory,
                avatar: const Icon(Icons.memory_outlined, size: 17),
                label: const Text('Memory'),
                onSelected: (value) => controller.useMemory = value,
              ),
            ],
          ),
          const SizedBox(height: 12),
          Expanded(
            child: controller.turns.isEmpty
                ? const _WelcomeState()
                : ListView.builder(
                    reverse: false,
                    padding: const EdgeInsets.symmetric(vertical: 12),
                    itemCount: controller.turns.length,
                    itemBuilder: (context, index) {
                      final turn = controller.turns[index];
                      final user = turn.role == ResearchOSConversationRole.user;
                      return Align(
                        alignment: user ? Alignment.centerRight : Alignment.centerLeft,
                        child: Container(
                          constraints: const BoxConstraints(maxWidth: 760),
                          margin: const EdgeInsets.only(bottom: 12),
                          padding: const EdgeInsets.all(16),
                          decoration: BoxDecoration(
                            color: user ? scheme.primaryContainer : scheme.surfaceContainerHigh,
                            borderRadius: BorderRadius.circular(20),
                          ),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: <Widget>[
                              Text(user ? 'คุณ' : 'Friend', style: Theme.of(context).textTheme.labelLarge),
                              const SizedBox(height: 6),
                              Text(turn.text),
                              if (turn.memoryHits > 0 || turn.evidenceIds.isNotEmpty) ...<Widget>[
                                const SizedBox(height: 10),
                                Wrap(
                                  spacing: 6,
                                  children: <Widget>[
                                    if (turn.memoryHits > 0)
                                      Chip(label: Text('Memory ${turn.memoryHits}')),
                                    if (turn.evidenceIds.isNotEmpty)
                                      Chip(label: Text('Evidence ${turn.evidenceIds.length}')),
                                  ],
                                ),
                              ],
                            ],
                          ),
                        ),
                      );
                    },
                  ),
          ),
          if (controller.error != null)
            Padding(
              padding: const EdgeInsets.only(bottom: 10),
              child: MaterialBanner(
                content: Text(controller.error!),
                actions: <Widget>[
                  TextButton(onPressed: controller.clearError, child: const Text('ปิด')),
                ],
              ),
            ),
          _Composer(
            controller: composer,
            enabled: controller.state == ResearchOSConversationState.idle ||
                controller.state == ResearchOSConversationState.failed,
            onSend: onSend,
          ),
        ],
      ),
    );
  }
}

class _WelcomeState extends StatelessWidget {
  const _WelcomeState();

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Center(
      child: SingleChildScrollView(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 720),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: <Widget>[
              const _FriendAvatar(size: 92),
              const SizedBox(height: 22),
              Text('คุยกับ Friend ได้เลย', style: Theme.of(context).textTheme.headlineMedium),
              const SizedBox(height: 10),
              Text(
                'ไม่ต้องเลือกว่าจะไปหน้าไหนก่อน บอกสิ่งที่ต้องการ แล้ว Friend จะพาไปยัง workspace ที่เหมาะสม',
                textAlign: TextAlign.center,
                style: Theme.of(context).textTheme.bodyLarge,
              ),
              const SizedBox(height: 22),
              Wrap(
                spacing: 8,
                runSpacing: 8,
                alignment: WrapAlignment.center,
                children: <Widget>[
                  _PromptChip(label: 'ช่วยค้นคว้าเรื่องนี้ให้หน่อย', color: scheme.primaryContainer),
                  _PromptChip(label: 'ดูโค้ดใน repository ให้หน่อย', color: scheme.secondaryContainer),
                  _PromptChip(label: 'วิเคราะห์หลักฐานล่าสุด', color: scheme.tertiaryContainer),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _PromptChip extends StatelessWidget {
  const _PromptChip({required this.label, required this.color});

  final String label;
  final Color color;

  @override
  Widget build(BuildContext context) => Chip(
        backgroundColor: color,
        label: Text(label),
      );
}

class _Composer extends StatelessWidget {
  const _Composer({required this.controller, required this.enabled, required this.onSend});

  final TextEditingController controller;
  final bool enabled;
  final VoidCallback onSend;

  @override
  Widget build(BuildContext context) => TextField(
        controller: controller,
        enabled: enabled,
        minLines: 1,
        maxLines: 5,
        textInputAction: TextInputAction.newline,
        onSubmitted: (_) => onSend(),
        decoration: InputDecoration(
          hintText: 'บอก Friend ว่าต้องการทำอะไร…',
          prefixIcon: const Icon(Icons.chat_bubble_outline),
          suffixIcon: IconButton(
            tooltip: 'ส่ง',
            onPressed: enabled ? onSend : null,
            icon: const Icon(Icons.arrow_upward_rounded),
          ),
          border: OutlineInputBorder(borderRadius: BorderRadius.circular(20)),
        ),
      );
}

class _ContextPanel extends StatelessWidget {
  const _ContextPanel();

  @override
  Widget build(BuildContext context) => Card(
        margin: const EdgeInsets.only(top: 18, right: 18, bottom: 18),
        child: Padding(
          padding: const EdgeInsets.all(18),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: <Widget>[
              Text('Friend Context', style: Theme.of(context).textTheme.titleMedium),
              const SizedBox(height: 14),
              const _ContextRow(icon: Icons.memory_outlined, label: 'Memory', value: 'Ready'),
              const _ContextRow(icon: Icons.fact_check_outlined, label: 'Evidence', value: 'On demand'),
              const _ContextRow(icon: Icons.auto_awesome_outlined, label: 'Copilot', value: 'Available by level'),
              const _ContextRow(icon: Icons.account_tree_outlined, label: 'Workspace', value: 'Adaptive'),
              const Spacer(),
              Text('V5 principle', style: Theme.of(context).textTheme.labelLarge),
              const SizedBox(height: 6),
              const Text('Conversation stays alive while the active workspace changes.'),
            ],
          ),
        ),
      );
}

class _ContextRow extends StatelessWidget {
  const _ContextRow({required this.icon, required this.label, required this.value});

  final IconData icon;
  final String label;
  final String value;

  @override
  Widget build(BuildContext context) => Padding(
        padding: const EdgeInsets.only(bottom: 14),
        child: Row(
          children: <Widget>[
            Icon(icon, size: 19),
            const SizedBox(width: 10),
            Expanded(child: Text(label)),
            Text(value, style: Theme.of(context).textTheme.labelSmall),
          ],
        ),
      );
}

class _FriendAvatar extends StatelessWidget {
  const _FriendAvatar({required this.size});

  final double size;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Container(
      width: size,
      height: size,
      alignment: Alignment.center,
      decoration: BoxDecoration(
        shape: BoxShape.circle,
        color: scheme.primaryContainer,
        border: Border.all(color: scheme.primary.withValues(alpha: .25)),
      ),
      child: Icon(Icons.auto_awesome, size: size * .42, color: scheme.onPrimaryContainer),
    );
  }
}
