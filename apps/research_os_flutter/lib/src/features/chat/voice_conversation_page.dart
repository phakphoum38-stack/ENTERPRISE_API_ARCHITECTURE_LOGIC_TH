import 'package:flutter/material.dart';

import '../../api/research_os_api_client.dart';
import 'voice_conversation_controller.dart';

class VoiceConversationPage extends StatefulWidget {
  const VoiceConversationPage({required this.apiClient, super.key});

  final ResearchOSApiClient apiClient;

  @override
  State<VoiceConversationPage> createState() => _VoiceConversationPageState();
}

enum _VoiceState { idle, listening, thinking, speaking, error }

class _VoiceConversationPageState extends State<VoiceConversationPage> {
  final VoiceConversationController _voice = VoiceConversationController();
  final TextEditingController _textController = TextEditingController();
  final List<_VoiceTurn> _turns = <_VoiceTurn>[];

  _VoiceState _state = _VoiceState.idle;
  bool _useMemory = true;
  bool _starting = false;
  String _transcript = '';
  String? _error;

  @override
  void dispose() {
    _voice.dispose();
    _textController.dispose();
    super.dispose();
  }

  Future<Map<String, dynamic>> _answer(String prompt) {
    return _useMemory
        ? widget.apiClient.answerWithMemory(prompt)
        : widget.apiClient.generateText(prompt);
  }

  Future<void> _sendText() async {
    if (_state == _VoiceState.thinking || _state == _VoiceState.speaking) {
      return;
    }
    final prompt = _textController.text.trim();
    if (prompt.isEmpty) return;

    _textController.clear();
    await _submitPrompt(prompt, speakAnswer: false);
  }

  Future<void> _submitPrompt(
    String prompt, {
    required bool speakAnswer,
  }) async {
    setState(() {
      _turns.add(_VoiceTurn(role: 'user', text: prompt));
      _transcript = '';
      _state = _VoiceState.thinking;
      _error = null;
    });

    try {
      final response = await _answer(prompt);
      final answer =
          (response['text'] ?? response['answer'] ?? '').toString().trim();
      final spoken =
          answer.isEmpty ? 'ขอโทษครับ ผมไม่ได้รับคำตอบจากระบบ' : answer;
      final memoryHits = response['memory_hits'];
      if (!mounted) return;
      setState(() {
        _turns.add(
          _VoiceTurn(
            role: 'assistant',
            text: spoken,
            memoryCount: memoryHits is List ? memoryHits.length : null,
          ),
        );
        _state = speakAnswer ? _VoiceState.speaking : _VoiceState.idle;
      });

      if (speakAnswer) {
        await _voice.speak(spoken);
        if (mounted && !_voice.isSpeaking) {
          setState(() => _state = _VoiceState.idle);
        }
      }
    } on Object catch (error) {
      if (!mounted) return;
      setState(() {
        _state = _VoiceState.error;
        _error = error.toString();
      });
    }
  }

  Future<bool> _ensureVoiceReady() async {
    if (_starting) return false;
    _starting = true;
    try {
      return await _voice.initialize(
        onResult: (text, isFinal) {
          if (!mounted) return;
          setState(() => _transcript = text);
          if (isFinal && text.trim().isNotEmpty) {
            _finishVoiceTurn(text);
          }
        },
        onStatus: (status) {
          if (!mounted ||
              _state == _VoiceState.thinking ||
              _state == _VoiceState.speaking) {
            return;
          }
          if (status == 'listening') {
            setState(() => _state = _VoiceState.listening);
          } else if (status == 'notListening' &&
              _state == _VoiceState.listening) {
            setState(() => _state = _VoiceState.idle);
          }
        },
        onError: (message) {
          if (!mounted) return;
          setState(() {
            _state = _VoiceState.error;
            _error = message;
          });
        },
      );
    } finally {
      _starting = false;
    }
  }

  Future<void> _toggleListening() async {
    if (_state == _VoiceState.speaking) {
      await _voice.stopSpeaking();
      if (mounted) setState(() => _state = _VoiceState.idle);
      return;
    }
    if (_state == _VoiceState.listening) {
      await _voice.stopListening();
      if (mounted) setState(() => _state = _VoiceState.idle);
      return;
    }
    if (_state == _VoiceState.thinking || _starting) return;

    setState(() {
      _error = null;
      _transcript = '';
      _state = _VoiceState.listening;
    });

    try {
      final ready = await _ensureVoiceReady();
      if (!ready) {
        if (mounted) {
          setState(() {
            _state = _VoiceState.error;
            _error =
                'อุปกรณ์นี้ไม่พร้อมสำหรับการรู้จำเสียง หรือยังไม่ได้อนุญาตไมโครโฟน';
          });
        }
        return;
      }
      final started = await _voice.startListening();
      if (!started && mounted) {
        setState(() {
          _state = _VoiceState.error;
          _error =
              'เริ่มฟังเสียงไม่ได้ กรุณาตรวจสอบสิทธิ์ไมโครโฟนและ speech recognition';
        });
      }
    } on Object catch (error) {
      if (!mounted) return;
      setState(() {
        _state = _VoiceState.error;
        _error = error.toString();
      });
    }
  }

  Future<void> _finishVoiceTurn(String text) async {
    if (_state != _VoiceState.listening && _state != _VoiceState.idle) {
      return;
    }
    await _voice.stopListening();
    final prompt = text.trim();
    if (prompt.isEmpty) return;
    await _submitPrompt(prompt, speakAnswer: true);
  }

  String get _stateLabel => switch (_state) {
        _VoiceState.idle => 'พร้อมสนทนา',
        _VoiceState.listening => 'กำลังฟังคุณ…',
        _VoiceState.thinking => 'กำลังคิด…',
        _VoiceState.speaking => 'กำลังพูดตอบ…',
        _VoiceState.error => 'Voice status มีปัญหา',
      };

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final active =
        _state == _VoiceState.listening || _state == _VoiceState.speaking;

    return Scaffold(
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.fromLTRB(20, 20, 20, 16),
          child: Column(
            children: <Widget>[
              Row(
                children: <Widget>[
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: <Widget>[
                        Text('สนทนา AI',
                            style: Theme.of(context).textTheme.headlineSmall),
                        const SizedBox(height: 4),
                        const Text('Friend AI • Text + Voice • Local-first'),
                      ],
                    ),
                  ),
                  FilterChip(
                    selected: _useMemory,
                    avatar: const Icon(Icons.memory_outlined, size: 18),
                    label: const Text('Memory'),
                    onSelected: _state == _VoiceState.thinking
                        ? null
                        : (value) => setState(() => _useMemory = value),
                  ),
                ],
              ),
              const SizedBox(height: 16),
              Expanded(
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: <Widget>[
                    Expanded(
                      flex: 3,
                      child: Card(
                        child: Padding(
                          padding: const EdgeInsets.all(24),
                          child: Column(
                            children: <Widget>[
                              Expanded(
                                child: _turns.isEmpty
                                    ? Center(
                                        child: ConstrainedBox(
                                          constraints: const BoxConstraints(
                                              maxWidth: 560),
                                          child: Column(
                                            mainAxisSize: MainAxisSize.min,
                                            children: <Widget>[
                                              Icon(Icons.auto_awesome,
                                                  size: 72,
                                                  color: scheme.primary),
                                              const SizedBox(height: 20),
                                              Text(
                                                key: Key(
                                                    'voice-conversation-empty-state-title'),
                                                'คุยกับ Research OS Friend ได้เลย',
                                                textAlign: TextAlign.center,
                                                style: Theme.of(context)
                                                    .textTheme
                                                    .headlineMedium,
                                              ),
                                              const SizedBox(height: 10),
                                              const Text(
                                                key: Key(
                                                    'voice-conversation-empty-state-description'),
                                                'พิมพ์ข้อความหรือกดไมโครโฟนเพื่อคุยด้วยเสียง ระบบจะส่งให้ Friend AI และแสดงคำตอบในห้องสนทนา',
                                                textAlign: TextAlign.center,
                                              ),
                                            ],
                                          ),
                                        ),
                                      )
                                    : ListView.builder(
                                        padding:
                                            const EdgeInsets.only(bottom: 20),
                                        itemCount: _turns.length,
                                        itemBuilder: (context, index) {
                                          final turn = _turns[index];
                                          final isUser = turn.role == 'user';
                                          return Align(
                                            alignment: isUser
                                                ? Alignment.centerRight
                                                : Alignment.centerLeft,
                                            child: Container(
                                              constraints: const BoxConstraints(
                                                  maxWidth: 720),
                                              margin: const EdgeInsets.only(
                                                  bottom: 12),
                                              padding: const EdgeInsets.all(16),
                                              decoration: BoxDecoration(
                                                color: isUser
                                                    ? scheme.primaryContainer
                                                    : scheme.surfaceContainer,
                                                borderRadius:
                                                    BorderRadius.circular(18),
                                              ),
                                              child: Column(
                                                crossAxisAlignment:
                                                    CrossAxisAlignment.start,
                                                children: <Widget>[
                                                  Text(
                                                    isUser
                                                        ? 'คุณ'
                                                        : 'Friend AI',
                                                    style: Theme.of(context)
                                                        .textTheme
                                                        .labelLarge,
                                                  ),
                                                  const SizedBox(height: 6),
                                                  Text(turn.text),
                                                  if (turn.memoryCount !=
                                                      null) ...<Widget>[
                                                    const SizedBox(height: 8),
                                                    Text(
                                                      'Memory ${turn.memoryCount} รายการ',
                                                      style: Theme.of(context)
                                                          .textTheme
                                                          .labelSmall,
                                                    ),
                                                  ],
                                                ],
                                              ),
                                            ),
                                          );
                                        },
                                      ),
                              ),
                              if (_transcript.isNotEmpty) ...<Widget>[
                                const SizedBox(height: 10),
                                Container(
                                  width: double.infinity,
                                  padding: const EdgeInsets.all(14),
                                  decoration: BoxDecoration(
                                    borderRadius: BorderRadius.circular(14),
                                    border: Border.all(
                                      color:
                                          scheme.primary.withValues(alpha: .28),
                                    ),
                                  ),
                                  child: Row(
                                    children: <Widget>[
                                      Icon(Icons.hearing,
                                          color: scheme.primary),
                                      const SizedBox(width: 10),
                                      Expanded(child: Text(_transcript)),
                                    ],
                                  ),
                                ),
                              ],
                              const SizedBox(height: 12),
                              _TextComposer(
                                controller: _textController,
                                enabled: _state != _VoiceState.thinking &&
                                    _state != _VoiceState.speaking,
                                onSend: _sendText,
                              ),
                            ],
                          ),
                        ),
                      ),
                    ),
                    const SizedBox(width: 14),
                    SizedBox(
                      width: 300,
                      child: Card(
                        child: Padding(
                          padding: const EdgeInsets.all(22),
                          child: Column(
                            mainAxisAlignment: MainAxisAlignment.center,
                            children: <Widget>[
                              _VoiceOrb(active: active, state: _state),
                              const SizedBox(height: 22),
                              Text(_stateLabel,
                                  style: Theme.of(context).textTheme.titleLarge,
                                  textAlign: TextAlign.center),
                              const SizedBox(height: 8),
                              Text(
                                _state == _VoiceState.error
                                    ? 'ตรวจสอบสิทธิ์ไมโครโฟนและ speech service'
                                    : 'พิมพ์ได้ทันที หรือพูดสั้น ๆ แล้วหยุดเพื่อให้ระบบตอบกลับด้วยเสียง',
                                textAlign: TextAlign.center,
                                style: Theme.of(context).textTheme.bodySmall,
                              ),
                              const SizedBox(height: 24),
                              IconButton.filled(
                                key: const Key('voice-conversation-mic-button'),
                                iconSize: 32,
                                padding: const EdgeInsets.all(18),
                                tooltip: _state == _VoiceState.listening
                                    ? 'หยุดฟัง'
                                    : _state == _VoiceState.speaking
                                        ? 'หยุดพูด'
                                        : 'เริ่มสนทนาด้วยเสียง',
                                onPressed: _toggleListening,
                                icon: Icon(
                                  _state == _VoiceState.listening
                                      ? Icons.stop
                                      : _state == _VoiceState.speaking
                                          ? Icons.stop_circle_outlined
                                          : Icons.mic,
                                ),
                              ),
                              if (_error != null) ...<Widget>[
                                const SizedBox(height: 18),
                                Text(_error!,
                                    textAlign: TextAlign.center,
                                    style: TextStyle(color: scheme.error)),
                                TextButton(
                                  onPressed: () => setState(() {
                                    _error = null;
                                    _state = _VoiceState.idle;
                                  }),
                                  child: const Text('ลองใหม่'),
                                ),
                              ],
                            ],
                          ),
                        ),
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

class _TextComposer extends StatelessWidget {
  const _TextComposer({
    required this.controller,
    required this.enabled,
    required this.onSend,
  });

  final TextEditingController controller;
  final bool enabled;
  final VoidCallback onSend;

  @override
  Widget build(BuildContext context) {
    return TextField(
      key: const Key('research-os-text-composer'),
      controller: controller,
      enabled: enabled,
      minLines: 1,
      maxLines: 5,
      textInputAction: TextInputAction.newline,
      onSubmitted: (_) => onSend(),
      decoration: InputDecoration(
        hintText: 'พิมพ์ข้อความถึง Friend AI…',
        prefixIcon: const Icon(Icons.chat_bubble_outline),
        suffixIcon: IconButton(
          key: const Key('research-os-text-send'),
          tooltip: 'ส่งข้อความ',
          onPressed: enabled ? onSend : null,
          icon: const Icon(Icons.send_rounded),
        ),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(18),
        ),
      ),
    );
  }
}

class _VoiceOrb extends StatelessWidget {
  const _VoiceOrb({required this.active, required this.state});

  final bool active;
  final _VoiceState state;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final icon = switch (state) {
      _VoiceState.idle => Icons.mic_none,
      _VoiceState.listening => Icons.graphic_eq,
      _VoiceState.thinking => Icons.psychology_outlined,
      _VoiceState.speaking => Icons.volume_up_outlined,
      _VoiceState.error => Icons.error_outline,
    };
    return AnimatedContainer(
      duration: const Duration(milliseconds: 260),
      width: active ? 148 : 128,
      height: active ? 148 : 128,
      decoration: BoxDecoration(
        shape: BoxShape.circle,
        color: scheme.primaryContainer,
        border: Border.all(
          color: scheme.primary.withValues(alpha: active ? .72 : .28),
          width: active ? 3 : 1,
        ),
        boxShadow: active
            ? <BoxShadow>[
                BoxShadow(
                  color: scheme.primary.withValues(alpha: .18),
                  blurRadius: 28,
                  spreadRadius: 6,
                ),
              ]
            : const <BoxShadow>[],
      ),
      child: Icon(icon, size: 58, color: scheme.onPrimaryContainer),
    );
  }
}

class _VoiceTurn {
  const _VoiceTurn({required this.role, required this.text, this.memoryCount});

  final String role;
  final String text;
  final int? memoryCount;
}
