import 'dart:async';
import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../../api/provider_selection_store.dart';
import '../../api/research_os_api_client.dart';
import '../../api/research_os_stream_client.dart';
import '../../ui/enterprise_components.dart';
import 'chat_message_card.dart';
import 'chat_typing_indicator.dart';

class ChatPageV2 extends StatefulWidget {
  const ChatPageV2({required this.apiClient, super.key});

  final ResearchOSApiClient apiClient;

  @override
  State<ChatPageV2> createState() => _ChatPageV2State();
}

class _ChatPageV2State extends State<ChatPageV2> {
  static const _storageKey = 'research_os_chat_sessions_v2';

  final TextEditingController _controller = TextEditingController();
  final ScrollController _scrollController = ScrollController();
  final List<_ChatSessionV2> _sessions = <_ChatSessionV2>[];

  late final ResearchOSStreamClient _streamClient;
  ResearchOSStreamHandle? _streamHandle;
  StreamSubscription<ResearchOSStreamEvent>? _streamSubscription;

  late _ChatSessionV2 _activeSession = _ChatSessionV2.empty();
  bool _loading = true;
  bool _sending = false;
  bool _useMemory = true;
  String? _error;

  List<_ChatMessageV2> get _messages => _activeSession.messages;

  @override
  void initState() {
    super.initState();
    _streamClient = ResearchOSStreamClient(baseUrl: widget.apiClient.baseUrl);
    unawaited(_restore());
  }

  @override
  void dispose() {
    unawaited(_streamSubscription?.cancel());
    unawaited(_streamHandle?.cancel());
    _streamClient.close();
    _controller.dispose();
    _scrollController.dispose();
    super.dispose();
  }

  Future<void> _restore() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final raw = prefs.getString(_storageKey);
      if (raw != null && raw.isNotEmpty) {
        final decoded = jsonDecode(raw);
        if (decoded is List) {
          _sessions.addAll(
            decoded.whereType<Map>().map(
                  (item) => _ChatSessionV2.fromJson(
                    Map<String, dynamic>.from(item),
                  ),
                ),
          );
        }
      }
      _sessions.sort((a, b) => b.updatedAt.compareTo(a.updatedAt));
      if (_sessions.isEmpty) _sessions.add(_ChatSessionV2.empty());
      _activeSession = _sessions.first;
    } on Object catch (error) {
      _error = 'โหลดประวัติ Chat 2.0 ไม่สำเร็จ: $error';
      _sessions
        ..clear()
        ..add(_ChatSessionV2.empty());
      _activeSession = _sessions.first;
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _persist() async {
    _activeSession.updatedAt = DateTime.now();
    _sessions.sort((a, b) => b.updatedAt.compareTo(a.updatedAt));
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(
      _storageKey,
      jsonEncode(_sessions.map((session) => session.toJson()).toList()),
    );
  }

  String _conversationPrompt(String latestPrompt) {
    final history = _messages
        .where((message) => message.text.trim().isNotEmpty)
        .toList(growable: false);
    final start = history.length > 10 ? history.length - 10 : 0;
    final context = history.skip(start).map((message) {
      final role = message.role == 'user' ? 'User' : 'Assistant';
      return '$role: ${message.text}';
    }).join('\n');
    if (context.isEmpty) return latestPrompt;
    return '''Continue this Research OS conversation consistently.
Use prior turns as conversation context. Do not treat assistant statements as verified facts unless supported by memory.

Conversation so far:
$context

User: $latestPrompt''';
  }

  Future<void> _newChat() async {
    if (_sending) return;
    final session = _ChatSessionV2.empty();
    setState(() {
      _sessions.insert(0, session);
      _activeSession = session;
      _controller.clear();
      _error = null;
    });
    await _persist();
  }

  Future<void> _showHistory() async {
    await showModalBottomSheet<void>(
      context: context,
      showDragHandle: true,
      isScrollControlled: true,
      builder: (sheetContext) => SafeArea(
        child: SizedBox(
          height: MediaQuery.sizeOf(sheetContext).height * .7,
          child: Column(
            children: <Widget>[
              const ListTile(
                leading: Icon(Icons.history),
                title: Text('Conversation History'),
                subtitle: Text('Chat 2.0 local-first history'),
              ),
              const Divider(height: 1),
              Expanded(
                child: ListView.builder(
                  padding: const EdgeInsets.all(12),
                  itemCount: _sessions.length,
                  itemBuilder: (context, index) {
                    final session = _sessions[index];
                    return Card(
                      child: ListTile(
                        selected: session.id == _activeSession.id,
                        leading: const Icon(Icons.forum_outlined),
                        title: Text(session.title),
                        subtitle: Text('${session.messages.length} ข้อความ'),
                        onTap: () {
                          setState(() => _activeSession = session);
                          Navigator.pop(sheetContext);
                          unawaited(_scrollToBottom());
                        },
                        trailing: IconButton(
                          tooltip: 'ลบ',
                          onPressed: _sending
                              ? null
                              : () async {
                                  setState(() {
                                    _sessions.removeWhere(
                                      (item) => item.id == session.id,
                                    );
                                    if (_sessions.isEmpty) {
                                      _sessions.add(_ChatSessionV2.empty());
                                    }
                                    if (_activeSession.id == session.id) {
                                      _activeSession = _sessions.first;
                                    }
                                  });
                                  await _persist();
                                  if (sheetContext.mounted) {
                                    Navigator.pop(sheetContext);
                                  }
                                },
                          icon: const Icon(Icons.delete_outline),
                        ),
                      ),
                    );
                  },
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Future<void> _send({String? overridePrompt}) async {
    final prompt = (overridePrompt ?? _controller.text).trim();
    if (prompt.isEmpty || _sending) return;

    final provider = selectedProviderState.value;
    final contextualPrompt = _conversationPrompt(prompt);
    final userMessage = _ChatMessageV2(
      role: 'user',
      text: prompt,
      createdAt: DateTime.now(),
      provider: provider,
    );
    final assistantMessage = _ChatMessageV2(
      role: 'assistant',
      text: '',
      createdAt: DateTime.now(),
      provider: provider,
      streaming: true,
    );

    setState(() {
      _messages.add(userMessage);
      _messages.add(assistantMessage);
      if (_activeSession.title == 'บทสนทนาใหม่') {
        _activeSession.title = prompt.length > 42
            ? '${prompt.substring(0, 42)}…'
            : prompt;
      }
      _controller.clear();
      _sending = true;
      _error = null;
    });
    await _persist();
    await _scrollToBottom();

    try {
      final handle = await _streamClient.start(
        prompt: contextualPrompt,
        useMemory: _useMemory,
        provider: provider,
        sessionId: _activeSession.id,
      );
      _streamHandle = handle;
      final completer = Completer<void>();
      _streamSubscription = handle.events.listen(
        (event) {
          if (!mounted) return;
          if (event.isDelta) {
            setState(() {
              assistantMessage.text += event.text;
              assistantMessage.provider = event.provider ?? assistantMessage.provider;
            });
            unawaited(_scrollToBottom());
          } else if (event.type == 'meta' && event.memoryCount != null) {
            setState(() => assistantMessage.memoryCount = event.memoryCount);
          } else if (event.isDone) {
            setState(() {
              assistantMessage.streaming = false;
              assistantMessage.provider = event.provider ?? assistantMessage.provider;
              assistantMessage.memoryCount =
                  event.memoryCount ?? assistantMessage.memoryCount;
            });
          } else if (event.isError) {
            setState(() {
              assistantMessage.streaming = false;
              _error = event.detail ?? 'Streaming error';
            });
          }
        },
        onError: (Object error) {
          if (mounted) setState(() => _error = error.toString());
          if (!completer.isCompleted) completer.complete();
        },
        onDone: () {
          if (!completer.isCompleted) completer.complete();
        },
        cancelOnError: false,
      );
      await completer.future;
    } on Object catch (streamError) {
      // Compatibility fallback for an older Local API or a proxy that does not
      // support NDJSON streaming yet.
      try {
        final response = _useMemory
            ? await widget.apiClient.answerWithMemory(
                contextualPrompt,
                provider: provider,
              )
            : await widget.apiClient.generateText(
                contextualPrompt,
                provider: provider,
              );
        final text = (response['text'] ?? response['answer'] ?? '').toString();
        final memoryHits = response['memory_hits'];
        if (mounted) {
          setState(() {
            assistantMessage.text = text.isEmpty ? 'ไม่ได้รับข้อความตอบกลับ' : text;
            assistantMessage.streaming = false;
            assistantMessage.provider =
                response['provider']?.toString() ?? assistantMessage.provider;
            assistantMessage.memoryCount =
                memoryHits is List ? memoryHits.length : null;
          });
        }
      } on Object catch (fallbackError) {
        if (mounted) {
          setState(() {
            assistantMessage.streaming = false;
            assistantMessage.text = assistantMessage.text.isEmpty
                ? 'การตอบกลับถูกขัดจังหวะ'
                : assistantMessage.text;
            _error = 'Streaming: $streamError\nFallback: $fallbackError';
          });
        }
      }
    } finally {
      _streamHandle = null;
      _streamSubscription = null;
      if (mounted) setState(() => _sending = false);
      await _persist();
      await _scrollToBottom();
    }
  }

  Future<void> _stopGeneration() async {
    final handle = _streamHandle;
    if (handle != null) {
      // Cancelling the underlying response closes the stream controller, which
      // lets the active listener receive onDone and release the send completer.
      await handle.cancel();
    } else {
      await _streamSubscription?.cancel();
    }
    if (!mounted) return;
    setState(() {
      _sending = false;
      if (_messages.isNotEmpty && _messages.last.role == 'assistant') {
        _messages.last.streaming = false;
        if (_messages.last.text.isEmpty) {
          _messages.last.text = 'หยุดการตอบแล้ว';
        }
      }
    });
    await _persist();
  }

  Future<void> _retry(int assistantIndex) async {
    if (_sending || assistantIndex <= 0) return;
    var userIndex = assistantIndex - 1;
    while (userIndex >= 0 && _messages[userIndex].role != 'user') {
      userIndex -= 1;
    }
    if (userIndex < 0) return;
    final prompt = _messages[userIndex].text;
    setState(() => _messages.removeRange(userIndex + 1, _messages.length));
    await _persist();
    await _send(overridePrompt: prompt);
  }

  Future<void> _editPrompt(int userIndex) async {
    if (_sending || userIndex < 0 || userIndex >= _messages.length) return;
    final message = _messages[userIndex];
    if (message.role != 'user') return;
    final editor = TextEditingController(text: message.text);
    final edited = await showDialog<String>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('แก้ไข Prompt'),
        content: TextField(
          key: const Key('chat-edit-dialog-field'),
          controller: editor,
          autofocus: true,
          minLines: 2,
          maxLines: 8,
        ),
        actions: <Widget>[
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('ยกเลิก'),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(context, editor.text.trim()),
            child: const Text('ส่งใหม่'),
          ),
        ],
      ),
    );
    editor.dispose();
    if (edited == null || edited.isEmpty) return;
    setState(() => _messages.removeRange(userIndex, _messages.length));
    await _persist();
    await _send(overridePrompt: edited);
  }

  Future<void> _scrollToBottom() async {
    await Future<void>.delayed(const Duration(milliseconds: 35));
    if (!mounted || !_scrollController.hasClients) return;
    await _scrollController.animateTo(
      _scrollController.position.maxScrollExtent,
      duration: const Duration(milliseconds: 180),
      curve: Curves.easeOut,
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.fromLTRB(20, 20, 20, 12),
          child: Column(
            children: <Widget>[
              EnterprisePageHeader(
                title: 'AI Workspace',
                subtitle:
                    'Chat 2.0 • Streaming • Provider-aware • Local-first history',
                icon: Icons.auto_awesome_outlined,
                actions: <Widget>[
                  OutlinedButton.icon(
                    onPressed: _loading ? null : _showHistory,
                    icon: const Icon(Icons.history),
                    label: const Text('History'),
                  ),
                  FilledButton.icon(
                    onPressed: _sending || _loading ? null : _newChat,
                    icon: const Icon(Icons.add_comment_outlined),
                    label: const Text('New chat'),
                  ),
                ],
              ),
              const SizedBox(height: 14),
              Card(
                child: Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                  child: Row(
                    children: <Widget>[
                      ValueListenableBuilder<String>(
                        valueListenable: selectedProviderState,
                        builder: (context, provider, _) => Chip(
                          avatar: const Icon(Icons.smart_toy_outlined, size: 17),
                          label: Text(provider),
                        ),
                      ),
                      const SizedBox(width: 8),
                      FilterChip(
                        selected: _useMemory,
                        avatar: const Icon(Icons.memory_outlined, size: 17),
                        label: const Text('Memory'),
                        onSelected: _sending
                            ? null
                            : (value) => setState(() => _useMemory = value),
                      ),
                      const Spacer(),
                      if (_sending)
                        OutlinedButton.icon(
                          key: const Key('chat-stop-generation'),
                          onPressed: _stopGeneration,
                          icon: const Icon(Icons.stop_circle_outlined),
                          label: const Text('Stop'),
                        ),
                    ],
                  ),
                ),
              ),
              if (_error != null) ...<Widget>[
                const SizedBox(height: 10),
                Card(
                  child: ListTile(
                    leading: const Icon(Icons.error_outline),
                    title: const Text('Chat status'),
                    subtitle: Text(_error!),
                    trailing: IconButton(
                      onPressed: () => setState(() => _error = null),
                      icon: const Icon(Icons.close),
                    ),
                  ),
                ),
              ],
              const SizedBox(height: 10),
              Expanded(
                child: Container(
                  width: double.infinity,
                  decoration: BoxDecoration(
                    color: Theme.of(context).colorScheme.surface,
                    borderRadius: BorderRadius.circular(18),
                    border: Border.all(color: Theme.of(context).dividerColor),
                  ),
                  child: _loading
                      ? const Center(child: CircularProgressIndicator())
                      : _messages.isEmpty
                          ? const _EmptyChatV2()
                          : ListView.builder(
                              controller: _scrollController,
                              padding: const EdgeInsets.fromLTRB(20, 24, 20, 12),
                              itemCount: _messages.length,
                              itemBuilder: (context, index) {
                                final message = _messages[index];
                                if (message.role == 'assistant' &&
                                    message.streaming &&
                                    message.text.isEmpty) {
                                  return ChatTypingIndicator(
                                    provider: message.provider,
                                  );
                                }
                                return ChatMessageCard(
                                  role: message.role,
                                  text: message.text,
                                  createdAt: message.createdAt,
                                  provider: message.provider,
                                  memoryCount: message.memoryCount,
                                  onEdit: message.role == 'user'
                                      ? () => _editPrompt(index)
                                      : null,
                                  onRetry: message.role == 'assistant' && !_sending
                                      ? () => _retry(index)
                                      : null,
                                );
                              },
                            ),
                ),
              ),
              const SizedBox(height: 12),
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(10),
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.end,
                    children: <Widget>[
                      Expanded(
                        child: TextField(
                          key: const Key('chat-v2-composer'),
                          controller: _controller,
                          minLines: 1,
                          maxLines: 7,
                          decoration: const InputDecoration(
                            hintText: 'ถาม Research OS…',
                            border: InputBorder.none,
                            filled: false,
                          ),
                        ),
                      ),
                      const SizedBox(width: 8),
                      IconButton.filled(
                        tooltip: 'ส่ง',
                        onPressed: _sending || _loading ? null : _send,
                        icon: _sending
                            ? const SizedBox(
                                width: 19,
                                height: 19,
                                child: CircularProgressIndicator(strokeWidth: 2),
                              )
                            : const Icon(Icons.arrow_upward),
                      ),
                    ],
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _EmptyChatV2 extends StatelessWidget {
  const _EmptyChatV2();

  @override
  Widget build(BuildContext context) {
    return Center(
      child: SingleChildScrollView(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: <Widget>[
            Icon(
              Icons.auto_awesome_outlined,
              size: 58,
              color: Theme.of(context).colorScheme.primary,
            ),
            const SizedBox(height: 16),
            Text(
              'Research OS Chat 2.0',
              style: Theme.of(context)
                  .textTheme
                  .headlineSmall
                  ?.copyWith(fontWeight: FontWeight.w800),
            ),
            const SizedBox(height: 8),
            const Text(
              'คุยต่อเนื่อง บันทึกอัตโนมัติ เลือก Provider ได้ และรองรับ Streaming',
              textAlign: TextAlign.center,
            ),
          ],
        ),
      ),
    );
  }
}

class _ChatSessionV2 {
  _ChatSessionV2({
    required this.id,
    required this.title,
    required this.messages,
    required this.updatedAt,
  });

  factory _ChatSessionV2.empty() {
    final now = DateTime.now();
    return _ChatSessionV2(
      id: 'chat2-${now.microsecondsSinceEpoch.toRadixString(36)}',
      title: 'บทสนทนาใหม่',
      messages: <_ChatMessageV2>[],
      updatedAt: now,
    );
  }

  factory _ChatSessionV2.fromJson(Map<String, dynamic> json) {
    final rawMessages = json['messages'];
    return _ChatSessionV2(
      id: (json['id'] ?? '').toString(),
      title: (json['title'] ?? 'บทสนทนา').toString(),
      messages: rawMessages is List
          ? rawMessages
              .whereType<Map>()
              .map(
                (item) => _ChatMessageV2.fromJson(
                  Map<String, dynamic>.from(item),
                ),
              )
              .toList()
          : <_ChatMessageV2>[],
      updatedAt: DateTime.tryParse((json['updated_at'] ?? '').toString()) ??
          DateTime.now(),
    );
  }

  final String id;
  String title;
  final List<_ChatMessageV2> messages;
  DateTime updatedAt;

  Map<String, Object?> toJson() => <String, Object?>{
        'id': id,
        'title': title,
        'updated_at': updatedAt.toIso8601String(),
        'messages': messages.map((message) => message.toJson()).toList(),
      };
}

class _ChatMessageV2 {
  _ChatMessageV2({
    required this.role,
    required this.text,
    required this.createdAt,
    this.provider,
    this.memoryCount,
    this.streaming = false,
  });

  factory _ChatMessageV2.fromJson(Map<String, dynamic> json) {
    final memory = json['memory_count'];
    return _ChatMessageV2(
      role: (json['role'] ?? '').toString(),
      text: (json['text'] ?? '').toString(),
      createdAt: DateTime.tryParse((json['created_at'] ?? '').toString()) ??
          DateTime.now(),
      provider: json['provider']?.toString(),
      memoryCount: memory is num ? memory.toInt() : null,
    );
  }

  final String role;
  String text;
  final DateTime createdAt;
  String? provider;
  int? memoryCount;
  bool streaming;

  Map<String, Object?> toJson() => <String, Object?>{
        'role': role,
        'text': text,
        'created_at': createdAt.toIso8601String(),
        if (provider != null) 'provider': provider,
        if (memoryCount != null) 'memory_count': memoryCount,
      };
}
