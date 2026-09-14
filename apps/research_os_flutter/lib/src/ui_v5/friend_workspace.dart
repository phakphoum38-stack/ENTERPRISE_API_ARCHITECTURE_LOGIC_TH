import 'package:flutter/material.dart';

import '../api/research_os_api_client.dart';
import '../features/chat/voice_conversation_controller.dart';
import 'conversation_core.dart';

class FriendWorkspace extends StatefulWidget {
  const FriendWorkspace({
    required this.apiClient,
    this.conversation,
    super.key,
  });

  final ResearchOSApiClient apiClient;
  final ResearchOSConversationController? conversation;

  @override
  State<FriendWorkspace> createState() => _FriendWorkspaceState();
}

class _FriendWorkspaceState extends State<FriendWorkspace> {
  late final ResearchOSConversationController _conversation =
      widget.conversation ??
          ResearchOSConversationController.fromApiClient(
            apiClient: widget.apiClient,
          );
  late final bool _ownsConversation = widget.conversation == null;
  late final VoiceConversationController _voice = VoiceConversationController();
  final TextEditingController _composer = TextEditingController();

  bool _voiceReady = false;
  bool _voiceInitializing = false;
  bool _voiceListening = false;

  @override
  void initState() {
    super.initState();
    _conversation.addListener(_onConversationChanged);
  }

  @override
  void dispose() {
    _conversation.removeListener(_onConversationChanged);
    if (_ownsConversation) _conversation.dispose();
    _voice.dispose();
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
    final friendTurn = await _conversation.sendText(text);
    if (friendTurn != null && _voiceListening) {
      await _voice.speak(friendTurn.text);
    }
  }

  Future<void> _toggleVoice() async {
    if (_voiceInitializing) return;

    if (_voiceListening) {
      await _voice.stopListening();
      if (mounted) setState(() => _voiceListening = false);
      return;
    }

    if (!_voiceReady) {
      _voiceInitializing = true;
      if (mounted) setState(() {});
      final ready = await _voice.initialize(
        onResult: (text, isFinal) {
          if (!mounted) return;
          setState(() {
            _composer.text = text;
            _composer.selection = TextSelection.collapsed(offset: text.length);
          });
          _conversation.setState(
            isFinal
                ? ResearchOSConversationState.understanding
                : ResearchOSConversationState.listening,
          );
          if (isFinal) {
            _voiceListening = false;
            _send();
          }
        },
        onError: (message) {
          if (!mounted) return;
          setState(() => _voiceListening = false);
          _conversation.setState(ResearchOSConversationState.failed);
        },
        onStatus: (status) {
          if (!mounted) return;
          if (status == 'done' || status == 'notListening') {
            setState(() => _voiceListening = false);
          }
        },
      );
      _voiceInitializing = false;
      _voiceReady = ready;
      if (!ready) {
        if (mounted) setState(() {});
        return;
      }
    }

    final started = await _voice.startListening();
    if (mounted) {
      setState(() => _voiceListening = started);
      if (started) {
        _conversation.setState(ResearchOSConversationState.listening);
      }
    }
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
              onVoice: _toggleVoice,
              voiceListening: _voiceListening,
              voiceInitializing: _voiceInitializing,
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
    required this.onVoice,
    required this.voiceListening,
    required this.voiceInitializing,
  });

  final ResearchOSConversationController controller;
  final TextEditingController composer;
  final VoidCallback onSend;
  final Future<void> Function() onVoice;
  final bool voiceListening;
  final bool voiceInitializing;

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
                                    if (turn.memoryHits > 0) Chip(label: Text('Memory ${turn.memoryHits}')),
                                    if (turn.evidenceIds.isNotEmpty) Chip(label: Text('Evidence ${turn.evidenceIds.length}')),
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
                controller.state == ResearchOSConversationState.failed ||
                controller.state == ResearchOSConversationState.listening ||
                controller.state == ResearchOSConversationState.understanding,
            onSend: onSend,
            onVoice: onVoice,
            voiceListening: voiceListening,
            voiceInitializing: voiceInitializing,
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
  const _Composer({
    required this.controller,
    required this.enabled,
    required this.onSend,
    required this.onVoice,
    required this.voiceListening,
    required this.voiceInitializing,
  });

  final TextEditingController controller;
  final bool enabled;
  final VoidCallback onSend;
  final Future<void> Function() onVoice;
  final bool voiceListening;
  final bool voiceInitializing;

  @override
  Widget build(BuildContext context) => TextField(
        controller: controller,
        enabled: enabled,
        minLines: 1,
        maxLines: 5,
        textInputAction: TextInputAction.newline,
        onSubmitted: (_) => onSend(),
        decoration: InputDecoration(
          hintText: voiceListening ? 'กำลังฟังคุณอยู่…' : 'บอก Friend ว่าต้องการทำอะไร…',
          prefixIcon: IconButton(
            tooltip: voiceListening ? 'หยุดฟัง' : 'คุยด้วยเสียง',
            onPressed: enabled ? onVoice : null,
            icon: Icon(voiceListening ? Icons.stop_circle_outlined : Icons.mic_none_rounded),
          ),
          suffixIcon: voiceInitializing
              ? const Padding(
                  padding: EdgeInsets.all(12),
                  child: SizedBox(
                    width: 20,
                    height: 20,
                    child: CircularProgressIndicator(strokeWidth: 2),
                  ),
                )
              : IconButton(
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
