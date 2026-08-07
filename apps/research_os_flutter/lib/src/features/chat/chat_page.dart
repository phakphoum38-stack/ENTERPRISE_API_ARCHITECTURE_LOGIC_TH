import 'dart:convert';

import 'package:flutter/material.dart';
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

  bool _useMemory = true;
  bool _sending = false;
  bool _loadingSessions = true;
  bool _syncing = false;
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
              decoded
                  .whereType<Map>()
                  .map((item) => _ChatSession.fromJson(Map<String, dynamic>.from(item))),
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

  Future<void> _persistSessions({bool cloud = true}) async {
    await _persistLocal();
    if (cloud && _cloudEnabled) {
      await _pushSession(_activeSession, silent: true);
    }
  }

  String _conversationPrompt(String latestPrompt) {
    final history = _messages
        .where((message) => message.text.trim().isNotEmpty)
        .takeLast(10)
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

  Future<void> _newConversation() async {
    if (_sending) return;
    final session = _ChatSession.empty();
    setState(() {
      _activeSession = session;
      _sessions.insert(0, session);
      _error = null;
      _controller.clear();
    });
    await _persistSessions();
  }

  Future<void> _deleteSession(_ChatSession session) async {
    if (_sending) return;
    final deletedId = session.id;
    setState(() {
      _sessions.removeWhere((item) => item.id == deletedId);
      if (_sessions.isEmpty) _sessions.add(_ChatSession.empty());
      if (_activeSession.id == deletedId) _activeSession = _sessions.first;
    });
    await _persistLocal();
    if (_cloudEnabled) {
      try {
        await widget.apiClient.deleteCloudConversation(_syncKey!, deletedId);
      } on Object catch (error) {
        if (mounted) setState(() => _error = 'ลบจาก Cloud ไม่สำเร็จ: $error');
      }
    }
  }

  Future<void> _renameSession(_ChatSession session) async {
    final controller = TextEditingController(text: session.title);
    final value = await showDialog<String>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('เปลี่ยนชื่อบทสนทนา'),
        content: TextField(
          controller: controller,
          autofocus: true,
          decoration: const InputDecoration(labelText: 'ชื่อบทสนทนา'),
        ),
        actions: <Widget>[
          TextButton(onPressed: () => Navigator.pop(context), child: const Text('ยกเลิก')),
          FilledButton(
            onPressed: () => Navigator.pop(context, controller.text.trim()),
            child: const Text('บันทึก'),
          ),
        ],
      ),
    );
    controller.dispose();
    if (value == null || value.isEmpty) return;
    setState(() {
      session.title = value;
      _activeSession = session;
    });
    await _persistSessions();
  }

  Future<void> _configureCloudSync() async {
    final controller = TextEditingController(text: _syncKey ?? '');
    final value = await showDialog<String>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Cloud Conversation Sync'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: <Widget>[
            const Text(
              'ใส่ Sync Key เดียวกันบน iPhone และ Windows เพื่อใช้ประวัติชุดเดียวกัน คีย์จะเก็บเฉพาะบนอุปกรณ์นี้และไม่บันทึกเข้า Knowledge.',
            ),
            const SizedBox(height: 16),
            TextField(
              controller: controller,
              obscureText: true,
              autocorrect: false,
              enableSuggestions: false,
              decoration: const InputDecoration(
                labelText: 'Research OS Sync Key',
                border: OutlineInputBorder(),
              ),
            ),
          ],
        ),
        actions: <Widget>[
          if (_cloudEnabled)
            TextButton(
              onPressed: () => Navigator.pop(context, ''),
              child: const Text('ปิด Cloud Sync'),
            ),
          TextButton(onPressed: () => Navigator.pop(context), child: const Text('ยกเลิก')),
          FilledButton(
            onPressed: () => Navigator.pop(context, controller.text.trim()),
            child: const Text('เชื่อมต่อ'),
          ),
        ],
      ),
    );
    controller.dispose();
    if (value == null) return;

    final prefs = await SharedPreferences.getInstance();
    if (value.isEmpty) {
      await prefs.remove(_syncKeyStorage);
      if (mounted) setState(() => _syncKey = null);
      return;
    }

    await prefs.setString(_syncKeyStorage, value);
    if (mounted) setState(() => _syncKey = value);
    await _syncNow();
  }

  Future<void> _pushSession(_ChatSession session, {bool silent = false}) async {
    if (!_cloudEnabled) return;
    try {
      await widget.apiClient.syncCloudConversation(_syncKey!, session.toCloudJson());
    } on Object catch (error) {
      if (!silent && mounted) setState(() => _error = 'Cloud Sync ไม่สำเร็จ: $error');
    }
  }

  Future<void> _syncNow() async {
    if (!_cloudEnabled || _syncing) return;
    setState(() {
      _syncing = true;
      _error = null;
    });
    try {
      final response = await widget.apiClient.getCloudConversations(_syncKey!);
      final rawSessions = response['sessions'];
      final cloudSessions = rawSessions is List
          ? rawSessions
              .whereType<Map>()
              .map((item) => _ChatSession.fromJson(Map<String, dynamic>.from(item)))
              .toList()
          : <_ChatSession>[];

      final merged = <String, _ChatSession>{
        for (final session in _sessions) session.id: session,
      };
      for (final remote in cloudSessions) {
        final local = merged[remote.id];
        if (local == null || remote.updatedAt.isAfter(local.updatedAt)) {
          merged[remote.id] = remote;
        }
      }
      _sessions
        ..clear()
        ..addAll(merged.values)
        ..sort((a, b) => b.updatedAt.compareTo(a.updatedAt));
      if (_sessions.isEmpty) _sessions.add(_ChatSession.empty());
      _activeSession = _sessions.firstWhere(
        (item) => item.id == _activeSession.id,
        orElse: () => _sessions.first,
      );
      await _persistLocal();

      for (final session in _sessions) {
        await _pushSession(session, silent: true);
      }
    } on Object catch (error) {
      if (mounted) setState(() => _error = 'Cloud Sync ไม่สำเร็จ: $error');
    } finally {
      if (mounted) setState(() => _syncing = false);
    }
  }

  Future<void> _showHistory() async {
    await showModalBottomSheet<void>(
      context: context,
      showDragHandle: true,
      isScrollControlled: true,
      builder: (context) => StatefulBuilder(
        builder: (context, sheetSetState) => SafeArea(
          child: SizedBox(
            height: MediaQuery.sizeOf(context).height * 0.7,
            child: Column(
              children: <Widget>[
                ListTile(
                  leading: Icon(_cloudEnabled ? Icons.cloud_done_outlined : Icons.history),
                  title: const Text('ประวัติการสนทนา'),
                  subtitle: Text(
                    _cloudEnabled
                        ? 'บันทึกบนอุปกรณ์นี้ + Cloud Sync'
                        : 'บันทึกบนอุปกรณ์นี้โดยอัตโนมัติ',
                  ),
                  trailing: _cloudEnabled
                      ? IconButton(
                          tooltip: 'Sync ตอนนี้',
                          onPressed: _syncing ? null : () async {
                            await _syncNow();
                            sheetSetState(() {});
                          },
                          icon: _syncing
                              ? const SizedBox(
                                  width: 20,
                                  height: 20,
                                  child: CircularProgressIndicator(strokeWidth: 2),
                                )
                              : const Icon(Icons.sync),
                        )
                      : null,
                ),
                const Divider(height: 1),
                Expanded(
                  child: ListView.builder(
                    itemCount: _sessions.length,
                    itemBuilder: (context, index) {
                      final session = _sessions[index];
                      return ListTile(
                        selected: session.id == _activeSession.id,
                        leading: const Icon(Icons.forum_outlined),
                        title: Text(session.title),
                        subtitle: Text('${session.messages.length} ข้อความ • ${session.id}'),
                        onTap: () {
                          setState(() => _activeSession = session);
                          Navigator.pop(context);
                          _scrollToBottom();
                        },
                        trailing: PopupMenuButton<String>(
                          onSelected: (value) async {
                            if (value == 'rename') {
                              Navigator.pop(context);
                              await _renameSession(session);
                            } else if (value == 'delete') {
                              await _deleteSession(session);
                              sheetSetState(() {});
                            }
                          },
                          itemBuilder: (context) => const <PopupMenuEntry<String>>[
                            PopupMenuItem(value: 'rename', child: Text('เปลี่ยนชื่อ')),
                            PopupMenuItem(value: 'delete', child: Text('ลบ')),
                          ],
                        ),
                      );
                    },
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
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
        _activeSession.title = prompt.length > 36 ? '${prompt.substring(0, 36)}…' : prompt;
      }
      _controller.clear();
      _sending = true;
      _error = null;
    });
    await _persistSessions();
    await _scrollToBottom();

    try {
      final response = _useMemory
          ? await widget.apiClient.answerWithMemory(contextualPrompt)
          : await widget.apiClient.generateText(contextualPrompt);
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
      appBar: AppBar(
        title: const Text('AI Chat'),
        actions: <Widget>[
          IconButton(
            tooltip: _cloudEnabled ? 'Cloud Sync เชื่อมต่อแล้ว' : 'ตั้งค่า Cloud Sync',
            onPressed: _loadingSessions ? null : _configureCloudSync,
            icon: Icon(_cloudEnabled ? Icons.cloud_done_outlined : Icons.cloud_outlined),
          ),
          IconButton(
            tooltip: 'ประวัติการสนทนา',
            onPressed: _loadingSessions ? null : _showHistory,
            icon: const Icon(Icons.history),
          ),
          IconButton(
            tooltip: 'เริ่มบทสนทนาใหม่',
            onPressed: _sending || _loadingSessions ? null : _newConversation,
            icon: const Icon(Icons.add_comment_outlined),
          ),
          Row(
            mainAxisSize: MainAxisSize.min,
            children: <Widget>[
              const Text('ใช้ Memory'),
              Switch(
                value: _useMemory,
                onChanged: _sending ? null : (value) => setState(() => _useMemory = value),
              ),
              const SizedBox(width: 8),
            ],
          ),
        ],
      ),
      body: Column(
        children: <Widget>[
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 8, 16, 0),
            child: Align(
              alignment: Alignment.centerLeft,
              child: Wrap(
                spacing: 8,
                runSpacing: 8,
                children: <Widget>[
                  Chip(
                    avatar: const Icon(Icons.forum_outlined, size: 18),
                    label: Text('${_activeSession.title} • ${_activeSession.id}'),
                  ),
                  if (_cloudEnabled)
                    Chip(
                      avatar: const Icon(Icons.cloud_done_outlined, size: 18),
                      label: Text(_syncing ? 'Cloud syncing…' : 'Cloud synced'),
                    ),
                ],
              ),
            ),
          ),
          Expanded(
            child: _loadingSessions
                ? const Center(child: CircularProgressIndicator())
                : _messages.isEmpty
                    ? const _EmptyChat()
                    : ListView.builder(
                        controller: _scrollController,
                        padding: const EdgeInsets.all(16),
                        itemCount: _messages.length,
                        itemBuilder: (context, index) => _MessageBubble(message: _messages[index]),
                      ),
          ),
          if (_error != null)
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16),
              child: MaterialBanner(
                content: Text(_error!),
                actions: <Widget>[
                  TextButton(onPressed: () => setState(() => _error = null), child: const Text('ปิด')),
                ],
              ),
            ),
          SafeArea(
            top: false,
            child: Padding(
              padding: const EdgeInsets.all(12),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.end,
                children: <Widget>[
                  Expanded(
                    child: TextField(
                      controller: _controller,
                      minLines: 1,
                      maxLines: 5,
                      textInputAction: TextInputAction.newline,
                      decoration: InputDecoration(
                        hintText: _useMemory
                            ? 'ถาม Gemini โดยใช้ความรู้และบริบทการสนทนา'
                            : 'ถาม Gemini โดยใช้บริบทการสนทนา',
                        border: const OutlineInputBorder(),
                      ),
                    ),
                  ),
                  const SizedBox(width: 8),
                  IconButton.filled(
                    tooltip: 'ส่ง',
                    onPressed: _sending || _loadingSessions ? null : _send,
                    icon: _sending
                        ? const SizedBox(
                            width: 20,
                            height: 20,
                            child: CircularProgressIndicator(strokeWidth: 2),
                          )
                        : const Icon(Icons.send),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _EmptyChat extends StatelessWidget {
  const _EmptyChat();

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: <Widget>[
            Icon(Icons.auto_awesome_outlined, size: 56, color: Theme.of(context).colorScheme.primary),
            const SizedBox(height: 16),
            Text('คุยกับ Gemini', style: Theme.of(context).textTheme.headlineSmall),
            const SizedBox(height: 8),
            const Text(
              'บทสนทนาบันทึกบนอุปกรณ์นี้อัตโนมัติ และสามารถเปิด Cloud Sync เพื่อคุยต่อข้ามอุปกรณ์ได้ โดยไม่บันทึกแชตเข้า Knowledge อัตโนมัติ',
              textAlign: TextAlign.center,
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

  @override
  Widget build(BuildContext context) {
    final isUser = message.role == 'user';
    final scheme = Theme.of(context).colorScheme;
    return Align(
      alignment: isUser ? Alignment.centerRight : Alignment.centerLeft,
      child: Container(
        constraints: const BoxConstraints(maxWidth: 720),
        margin: const EdgeInsets.only(bottom: 12),
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: isUser ? scheme.primaryContainer : scheme.surfaceContainerHighest,
          borderRadius: BorderRadius.circular(16),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: <Widget>[
            Text(message.text),
            if (message.memoryCount != null) ...<Widget>[
              const SizedBox(height: 8),
              Text('อ้างอิง Memory ${message.memoryCount} รายการ', style: Theme.of(context).textTheme.labelSmall),
            ],
          ],
        ),
      ),
    );
  }
}

class _ChatSession {
  _ChatSession({required this.id, required this.title, required this.messages, required this.updatedAt});

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
    DateTime updatedAt;
    if (rawUpdatedAt is int) {
      updatedAt = DateTime.fromMillisecondsSinceEpoch(rawUpdatedAt);
    } else {
      updatedAt = DateTime.tryParse((rawUpdatedAt ?? '').toString()) ?? DateTime.now();
    }
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

  Map<String, Object?> toJson() => <String, Object?>{
        'id': id,
        'title': title,
        'updated_at': updatedAt.toIso8601String(),
        'messages': messages.map((message) => message.toJson()).toList(),
      };

  Map<String, Object?> toCloudJson() => <String, Object?>{
        'id': id,
        'title': title,
        'updated_at': updatedAt.millisecondsSinceEpoch,
        'messages': messages.map((message) => message.toJson()).toList(),
      };
}

class _ChatMessage {
  const _ChatMessage({required this.role, required this.text, this.memoryCount});

  factory _ChatMessage.fromJson(Map<String, dynamic> json) => _ChatMessage(
        role: (json['role'] ?? '').toString(),
        text: (json['text'] ?? '').toString(),
        memoryCount: json['memory_count'] is int ? json['memory_count'] as int : null,
      );

  final String role;
  final String text;
  final int? memoryCount;

  Map<String, Object?> toJson() => <String, Object?>{
        'role': role,
        'text': text,
        if (memoryCount != null) 'memory_count': memoryCount,
      };
}

extension<T> on Iterable<T> {
  Iterable<T> takeLast(int count) {
    final values = toList(growable: false);
    if (values.length <= count) return values;
    return values.sublist(values.length - count);
  }
}
