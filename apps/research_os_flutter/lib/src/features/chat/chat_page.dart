import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_markdown/flutter_markdown.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../../api/research_os_api_client.dart';

class ChatPage extends StatefulWidget {
  const ChatPage({required this.apiClient, super.key});

  final ResearchOSApiClient apiClient;

  @override
  State<ChatPage> createState() => _ChatPageState();
}

class _ChatPageState extends State<ChatPage> {
  static const _storageKey = 'research_os_chat_sessions_v1';
  static const _syncKeyStorage = 'research_os_cloud_sync_key_v1';

  final TextEditingController _controller = TextEditingController();
  final ScrollController _scrollController = ScrollController();
  final List<_ChatSession> _sessions = <_ChatSession>[];

  bool _sending = false;
  bool _loadingSessions = true;
  String? _syncKey;
  String? _error;
  late _ChatSession _activeSession = _ChatSession.empty();

  List<_ChatMessage> get _messages => _activeSession.messages;
  bool get _cloudEnabled => _syncKey != null && _syncKey!.isNotEmpty;

  @override
  void initState() {
    super.initState();
    _restoreSessions();
  }

  @override
  void dispose() {
    _controller.dispose();
    _scrollController.dispose();
    super.dispose();
  }

  Future<void> _restoreSessions() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      _syncKey = prefs.getString(_syncKeyStorage)?.trim();
      final raw = prefs.getString(_storageKey);
      if (raw != null && raw.isNotEmpty) {
        final decoded = jsonDecode(raw);
        if (decoded is List) {
          _sessions
            ..clear()
            ..addAll(
              decoded.whereType<Map>().map(
                    (item) => _ChatSession.fromJson(
                      Map<String, dynamic>.from(item),
                    ),
                  ),
            );
        }
      }
      _sessions.sort((a, b) => b.updatedAt.compareTo(a.updatedAt));
      if (_sessions.isNotEmpty) {
        _activeSession = _sessions.first;
      } else {
        _activeSession = _ChatSession.empty();
        _sessions.add(_activeSession);
      }
    } on Object catch (error) {
      _error = 'โหลดประวัติการสนทนาไม่สำเร็จ: $error';
      _activeSession = _ChatSession.empty();
      _sessions
        ..clear()
        ..add(_activeSession);
    } finally {
      if (mounted) setState(() => _loadingSessions = false);
    }
  }

  Future<void> _persistLocal() async {
    _activeSession.updatedAt = DateTime.now();
    _sessions.sort((a, b) => b.updatedAt.compareTo(a.updatedAt));
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(
      _storageKey,
      jsonEncode(_sessions.map((session) => session.toJson()).toList()),
    );
  }

  Future<void> _persistSessions() async {
    await _persistLocal();
    if (_cloudEnabled) await _pushSession(_activeSession);
  }

  Future<void> _pushSession(_ChatSession session) async {
    if (!_cloudEnabled) return;
    try {
      await widget.apiClient.syncCloudConversation(
        _syncKey!,
        session.toCloudJson(),
      );
    } on Object {
      // Cloud sync is optional; local conversation remains authoritative.
    }
  }

  String _conversationPrompt(String latestPrompt) {
    final recent = _messages
        .where((message) => message.text.trim().isNotEmpty)
        .toList(growable: false);
    final history = recent
        .skip(recent.length > 10 ? recent.length - 10 : 0)
        .map((message) {
          final role = message.role == 'user' ? 'User' : 'Assistant';
          return '$role: ${message.text}';
        })
        .join('\n');
    if (history.isEmpty) return latestPrompt;
    return '''Continue this Research OS conversation consistently.
Use prior turns only as conversation context; do not treat assistant statements as verified facts unless supported by memory.

Conversation so far:
$history

User: $latestPrompt''';
  }

  Future<void> _scrollToBottom() async {
    await Future<void>.delayed(const Duration(milliseconds: 50));
    if (!mounted || !_scrollController.hasClients) return;
    await _scrollController.animateTo(
      _scrollController.position.maxScrollExtent,
      duration: const Duration(milliseconds: 220),
      curve: Curves.easeOut,
    );
  }

  Future<void> _send() async {
    final prompt = _controller.text.trim();
    if (prompt.isEmpty || _sending) return;

    final contextualPrompt = _conversationPrompt(prompt);
    setState(() {
      _messages.add(_ChatMessage(role: 'user', text: prompt));
      if (_messages.length == 1 && _activeSession.title == 'บทสนทนาใหม่') {
        _activeSession.title = prompt.length > 36
            ? '${prompt.substring(0, 36)}…'
            : prompt;
      }
      _controller.clear();
      _sending = true;
      _error = null;
    });
    await _persistSessions();
    await _scrollToBottom();

    try {
      final response = await widget.apiClient.answerWithMemory(contextualPrompt);
      final answer = (response['text'] ?? response['answer'] ?? '').toString();
      final memoryHits = response['memory_hits'];
      if (!mounted) return;
      setState(() {
        _messages.add(
          _ChatMessage(
            role: 'assistant',
            text: answer.isEmpty ? 'ไม่ได้รับข้อความตอบกลับ' : answer,
            memoryCount: memoryHits is List ? memoryHits.length : null,
          ),
        );
      });
      await _persistSessions();
      await _scrollToBottom();
    } on Object catch (error) {
      if (!mounted) return;
      setState(() => _error = error.toString());
    } finally {
      if (mounted) setState(() => _sending = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Padding(
          key: const Key('minimal-chat-page'),
          padding: const EdgeInsets.fromLTRB(12, 12, 12, 10),
          child: Column(
            children: <Widget>[
              if (_error != null) ...<Widget>[
                _ErrorPanel(
                  message: _error!,
                  onDismiss: () => setState(() => _error = null),
                ),
                const SizedBox(height: 10),
              ],
              Expanded(
                child: Container(
                  key: const Key('minimal-chat-surface'),
                  width: double.infinity,
                  decoration: BoxDecoration(
                    color: Theme.of(context).colorScheme.surface,
                    borderRadius: BorderRadius.circular(18),
                    border: Border.all(color: Theme.of(context).dividerColor),
                  ),
                  child: _loadingSessions
                      ? const Center(child: CircularProgressIndicator())
                      : _messages.isEmpty
                          ? const _EmptyChat()
                          : ListView.builder(
                              controller: _scrollController,
                              padding: const EdgeInsets.fromLTRB(16, 18, 16, 10),
                              itemCount: _messages.length,
                              itemBuilder: (context, index) => _MessageBubble(
                                message: _messages[index],
                              ),
                            ),
                ),
              ),
              const SizedBox(height: 10),
              _Composer(
                controller: _controller,
                sending: _sending,
                loading: _loadingSessions,
                onSend: _send,
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _Composer extends StatelessWidget {
  const _Composer({
    required this.controller,
    required this.sending,
    required this.loading,
    required this.onSend,
  });

  final TextEditingController controller;
  final bool sending;
  final bool loading;
  final VoidCallback onSend;

  @override
  Widget build(BuildContext context) {
    return Card(
      key: const Key('minimal-chat-composer'),
      margin: EdgeInsets.zero,
      child: Padding(
        padding: const EdgeInsets.all(10),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: <Widget>[
            TextField(
              controller: controller,
              minLines: 2,
              maxLines: 6,
              textInputAction: TextInputAction.newline,
              decoration: const InputDecoration(
                hintText: 'เขียนข้อความที่ต้องการ...',
                border: InputBorder.none,
                filled: false,
              ),
            ),
            const SizedBox(height: 6),
            Align(
              alignment: Alignment.centerRight,
              child: FilledButton.icon(
                key: const Key('ai-conversation-button'),
                onPressed: sending || loading ? null : onSend,
                icon: sending
                    ? const SizedBox(
                        width: 18,
                        height: 18,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      )
                    : const Icon(Icons.auto_awesome),
                label: Text(sending ? 'กำลังสนทนา...' : 'สนทนา AI'),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _ErrorPanel extends StatelessWidget {
  const _ErrorPanel({required this.message, required this.onDismiss});

  final String message;
  final VoidCallback onDismiss;

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: EdgeInsets.zero,
      child: ListTile(
        leading: const Icon(Icons.error_outline),
        title: const Text('AI Chat'),
        subtitle: Text(message),
        trailing: IconButton(
          tooltip: 'ปิด',
          onPressed: onDismiss,
          icon: const Icon(Icons.close),
        ),
      ),
    );
  }
}

class _EmptyChat extends StatelessWidget {
  const _EmptyChat();

  @override
  Widget build(BuildContext context) {
    return Center(
      child: SingleChildScrollView(
        padding: const EdgeInsets.all(28),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: <Widget>[
            Container(
              width: 58,
              height: 58,
              alignment: Alignment.center,
              decoration: BoxDecoration(
                color: Theme.of(context).colorScheme.primaryContainer,
                borderRadius: BorderRadius.circular(18),
              ),
              child: Icon(
                Icons.auto_awesome_outlined,
                size: 30,
                color: Theme.of(context).colorScheme.onPrimaryContainer,
              ),
            ),
            const SizedBox(height: 16),
            Text(
              'มีอะไรให้ช่วย?',
              key: const Key('minimal-chat-empty-title'),
              style: Theme.of(context).textTheme.headlineSmall,
            ),
            const SizedBox(height: 6),
            Text(
              'เขียนข้อความ แล้วกด สนทนา AI เพื่อเริ่มคุย',
              textAlign: TextAlign.center,
              style: TextStyle(
                color: Theme.of(context).colorScheme.onSurfaceVariant,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _MessageBubble extends StatelessWidget {
  const _MessageBubble({required this.message});

  final _ChatMessage message;

  bool _looksLikeMarkdown(String value) {
    if (value.contains('```') || value.contains('**') || value.contains('`')) {
      return true;
    }
    return RegExp(r'(^|\n)(#{1,6}\s|[-*]\s|\d+\.\s|>\s)').hasMatch(value);
  }

  Future<void> _copy(BuildContext context) async {
    await Clipboard.setData(ClipboardData(text: message.text));
    if (!context.mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Text('คัดลอกคำตอบแล้ว'),
        duration: Duration(seconds: 1),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final isUser = message.role == 'user';
    final scheme = Theme.of(context).colorScheme;
    final renderMarkdown = !isUser && _looksLikeMarkdown(message.text);

    return Align(
      alignment: isUser ? Alignment.centerRight : Alignment.centerLeft,
      child: Container(
        constraints: const BoxConstraints(maxWidth: 780),
        margin: const EdgeInsets.only(bottom: 14),
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: isUser ? scheme.primaryContainer : scheme.surfaceContainer,
          borderRadius: BorderRadius.circular(18),
          border: Border.all(
            color: isUser
                ? scheme.primary.withValues(alpha: 0.18)
                : scheme.outlineVariant,
          ),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: <Widget>[
            Row(
              mainAxisSize: MainAxisSize.min,
              children: <Widget>[
                CircleAvatar(
                  radius: 13,
                  child: Icon(
                    isUser ? Icons.person_outline : Icons.auto_awesome_outlined,
                    size: 15,
                  ),
                ),
                const SizedBox(width: 8),
                Text(
                  isUser ? 'คุณ' : 'Research OS AI',
                  style: Theme.of(context).textTheme.labelLarge,
                ),
                if (!isUser) ...<Widget>[
                  const SizedBox(width: 6),
                  IconButton(
                    tooltip: 'คัดลอกคำตอบ',
                    visualDensity: VisualDensity.compact,
                    constraints: const BoxConstraints(),
                    padding: const EdgeInsets.all(6),
                    onPressed: () => _copy(context),
                    icon: const Icon(Icons.copy_outlined, size: 16),
                  ),
                ],
              ],
            ),
            const SizedBox(height: 10),
            if (renderMarkdown)
              MarkdownBody(
                data: message.text,
                styleSheet: MarkdownStyleSheet.fromTheme(Theme.of(context)),
              )
            else
              Text(message.text),
            if (message.memoryCount != null && message.memoryCount! > 0) ...<Widget>[
              const SizedBox(height: 10),
              Text(
                'ใช้ Memory ${message.memoryCount} รายการ',
                style: Theme.of(context).textTheme.labelSmall,
              ),
            ],
          ],
        ),
      ),
    );
  }
}

class _ChatSession {
  _ChatSession({
    required this.id,
    required this.title,
    required this.messages,
    required this.updatedAt,
  });

  factory _ChatSession.empty() {
    final now = DateTime.now();
    return _ChatSession(
      id: 'chat-${now.microsecondsSinceEpoch.toRadixString(36)}',
      title: 'บทสนทนาใหม่',
      messages: <_ChatMessage>[],
      updatedAt: now,
    );
  }

  factory _ChatSession.fromJson(Map<String, dynamic> json) {
    final rawMessages = json['messages'];
    final rawUpdatedAt = json['updated_at'];
    final updatedAt = rawUpdatedAt is int
        ? DateTime.fromMillisecondsSinceEpoch(rawUpdatedAt)
        : DateTime.tryParse((rawUpdatedAt ?? '').toString()) ?? DateTime.now();
    return _ChatSession(
      id: (json['id'] ?? '').toString(),
      title: (json['title'] ?? 'บทสนทนา').toString(),
      messages: rawMessages is List
          ? rawMessages
              .whereType<Map>()
              .map((item) => _ChatMessage.fromJson(Map<String, dynamic>.from(item)))
              .toList()
          : <_ChatMessage>[],
      updatedAt: updatedAt,
    );
  }

  final String id;
  String title;
  final List<_ChatMessage> messages;
  DateTime updatedAt;

  Map<String, dynamic> toJson() => <String, dynamic>{
        'id': id,
        'title': title,
        'updated_at': updatedAt.toIso8601String(),
        'messages': messages.map((message) => message.toJson()).toList(),
      };

  Map<String, Object?> toCloudJson() => <String, Object?>{
        'id': id,
        'title': title,
        'updated_at': updatedAt.toIso8601String(),
        'messages': messages.map((message) => message.toJson()).toList(),
      };
}

class _ChatMessage {
  _ChatMessage({
    required this.role,
    required this.text,
    this.memoryCount,
  });

  factory _ChatMessage.fromJson(Map<String, dynamic> json) => _ChatMessage(
        role: (json['role'] ?? 'user').toString(),
        text: (json['text'] ?? '').toString(),
        memoryCount: json['memory_count'] is int ? json['memory_count'] as int : null,
      );

  final String role;
  final String text;
  final int? memoryCount;

  Map<String, dynamic> toJson() => <String, dynamic>{
        'role': role,
        'text': text,
        if (memoryCount != null) 'memory_count': memoryCount,
      };
}
