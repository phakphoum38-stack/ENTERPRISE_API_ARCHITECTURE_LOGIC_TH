import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_markdown/flutter_markdown.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../../api/research_os_api_client.dart';
import '../../ui/enterprise_components.dart';

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
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('ยกเลิก'),
          ),
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
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('ยกเลิก'),
          ),
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
      await widget.apiClient.syncCloudConversation(
        _syncKey!,
        session.toCloudJson(),
      );
    } on Object catch (error) {
      if (!silent && mounted) {
        setState(() => _error = 'Cloud Sync ไม่สำเร็จ: $error');
      }
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
              .map(
                (item) => _ChatSession.fromJson(
                  Map<String, dynamic>.from(item),
                ),
              )
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
            height: MediaQuery.sizeOf(context).height * 0.72,
            child: Column(
              children: <Widget>[
                Padding(
                  padding: const EdgeInsets.fromLTRB(20, 4, 12, 12),
                  child: Row(
                    children: <Widget>[
                      const Icon(Icons.history),
                      const SizedBox(width: 10),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: <Widget>[
                            Text(
                              'Conversation History',
                              style: Theme.of(context).textTheme.titleLarge,
                            ),
                            Text(
                              _cloudEnabled
                                  ? 'Local history + Cloud Sync'
                                  : 'Local history on this device',
                            ),
                          ],
                        ),
                      ),
                      if (_cloudEnabled)
                        IconButton(
                          tooltip: 'Sync ตอนนี้',
                          onPressed: _syncing
                              ? null
                              : () async {
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
                        ),
                    ],
                  ),
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
                              PopupMenuItem(
                                value: 'rename',
                                child: Text('เปลี่ยนชื่อ'),
                              ),
                              PopupMenuItem(
                                value: 'delete',
                                child: Text('ลบ'),
                              ),
                            ],
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
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.fromLTRB(20, 20, 20, 12),
          child: Column(
            children: <Widget>[
              EnterprisePageHeader(
                title: 'AI Workspace',
                subtitle:
                    'สนทนากับ AI โดยใช้ Session History, Local Memory และ Cloud Sync ตามที่เลือก',
                icon: Icons.auto_awesome_outlined,
                actions: <Widget>[
                  OutlinedButton.icon(
                    onPressed: _loadingSessions ? null : _showHistory,
                    icon: const Icon(Icons.history),
                    label: const Text('History'),
                  ),
                  FilledButton.icon(
                    onPressed: _sending || _loadingSessions
                        ? null
                        : _newConversation,
                    icon: const Icon(Icons.add_comment_outlined),
                    label: const Text('New chat'),
                  ),
                ],
              ),
              const SizedBox(height: 16),
              _ChatWorkspaceToolbar(
                session: _activeSession,
                useMemory: _useMemory,
                cloudEnabled: _cloudEnabled,
                syncing: _syncing,
                sending: _sending,
                onMemoryChanged: (value) => setState(() => _useMemory = value),
                onCloudPressed: _loadingSessions ? null : _configureCloudSync,
                onSyncPressed:
                    !_cloudEnabled || _syncing ? null : _syncNow,
              ),
              const SizedBox(height: 12),
              if (_error != null) ...<Widget>[
                _ErrorPanel(
                  message: _error!,
                  onDismiss: () => setState(() => _error = null),
                ),
                const SizedBox(height: 12),
              ],
              Expanded(
                child: Container(
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
                              padding: const EdgeInsets.fromLTRB(20, 24, 20, 12),
                              itemCount: _messages.length,
                              itemBuilder: (context, index) => _MessageBubble(
                                message: _messages[index],
                              ),
                            ),
                ),
              ),
              const SizedBox(height: 12),
              _Composer(
                controller: _controller,
                sending: _sending,
                loading: _loadingSessions,
                useMemory: _useMemory,
                onSend: _send,
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _ChatWorkspaceToolbar extends StatelessWidget {
  const _ChatWorkspaceToolbar({
    required this.session,
    required this.useMemory,
    required this.cloudEnabled,
    required this.syncing,
    required this.sending,
    required this.onMemoryChanged,
    required this.onCloudPressed,
    required this.onSyncPressed,
  });

  final _ChatSession session;
  final bool useMemory;
  final bool cloudEnabled;
  final bool syncing;
  final bool sending;
  final ValueChanged<bool> onMemoryChanged;
  final VoidCallback? onCloudPressed;
  final VoidCallback? onSyncPressed;

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: EdgeInsets.zero,
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
        child: Wrap(
          spacing: 10,
          runSpacing: 10,
          crossAxisAlignment: WrapCrossAlignment.center,
          children: <Widget>[
            Chip(
              avatar: const Icon(Icons.forum_outlined, size: 18),
              label: Text(session.title),
            ),
            FilterChip(
              selected: useMemory,
              avatar: const Icon(Icons.memory_outlined, size: 18),
              label: const Text('Memory'),
              onSelected: sending ? null : onMemoryChanged,
            ),
            ActionChip(
              avatar: Icon(
                cloudEnabled
                    ? Icons.cloud_done_outlined
                    : Icons.cloud_outlined,
                size: 18,
              ),
              label: Text(cloudEnabled ? 'Cloud connected' : 'Cloud off'),
              onPressed: onCloudPressed,
            ),
            if (cloudEnabled)
              ActionChip(
                avatar: syncing
                    ? const SizedBox(
                        width: 16,
                        height: 16,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      )
                    : const Icon(Icons.sync, size: 18),
                label: Text(syncing ? 'Syncing…' : 'Sync now'),
                onPressed: onSyncPressed,
              ),
          ],
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
    required this.useMemory,
    required this.onSend,
  });

  final TextEditingController controller;
  final bool sending;
  final bool loading;
  final bool useMemory;
  final VoidCallback onSend;

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: EdgeInsets.zero,
      child: Padding(
        padding: const EdgeInsets.all(10),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.end,
          children: <Widget>[
            Expanded(
              child: TextField(
                controller: controller,
                minLines: 1,
                maxLines: 6,
                textInputAction: TextInputAction.newline,
                decoration: InputDecoration(
                  hintText: useMemory
                      ? 'ถาม AI โดยใช้ Memory และบริบทการสนทนา…'
                      : 'ถาม AI โดยใช้บริบทการสนทนา…',
                  border: InputBorder.none,
                  filled: false,
                ),
              ),
            ),
            const SizedBox(width: 8),
            IconButton.filled(
              tooltip: 'ส่ง',
              onPressed: sending || loading ? null : onSend,
              icon: sending
                  ? const SizedBox(
                      width: 20,
                      height: 20,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    )
                  : const Icon(Icons.arrow_upward),
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
        title: const Text('AI Workspace status'),
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
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: <Widget>[
            Container(
              width: 72,
              height: 72,
              alignment: Alignment.center,
              decoration: BoxDecoration(
                color: Theme.of(context).colorScheme.primaryContainer,
                borderRadius: BorderRadius.circular(22),
              ),
              child: Icon(
                Icons.auto_awesome_outlined,
                size: 38,
                color: Theme.of(context).colorScheme.onPrimaryContainer,
              ),
            ),
            const SizedBox(height: 18),
            Text(
              'เริ่ม AI Workspace',
              style: Theme.of(context).textTheme.headlineSmall,
            ),
            const SizedBox(height: 8),
            const ConstrainedBox(
              constraints: BoxConstraints(maxWidth: 620),
              child: Text(
                'บทสนทนาบันทึกบนอุปกรณ์นี้อัตโนมัติ เปิด Memory เมื่อต้องการใช้ Knowledge ของ Research OS และเปิด Cloud Sync เมื่อต้องการคุยต่อข้ามอุปกรณ์',
                textAlign: TextAlign.center,
              ),
            ),
            const SizedBox(height: 20),
            const Wrap(
              alignment: WrapAlignment.center,
              spacing: 8,
              runSpacing: 8,
              children: <Widget>[
                Chip(
                  avatar: Icon(Icons.save_outlined, size: 18),
                  label: Text('Local history'),
                ),
                Chip(
                  avatar: Icon(Icons.memory_outlined, size: 18),
                  label: Text('Memory optional'),
                ),
                Chip(
                  avatar: Icon(Icons.cloud_outlined, size: 18),
                  label: Text('Cloud optional'),
                ),
              ],
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
            color: isUser ? scheme.primary.withValues(alpha: 0.18) : scheme.outlineVariant,
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
            if (message.memoryCount != null) ...<Widget>[
              const SizedBox(height: 10),
              Chip(
                visualDensity: VisualDensity.compact,
                avatar: const Icon(Icons.memory_outlined, size: 16),
                label: Text('Memory ${message.memoryCount} รายการ'),
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
  const _ChatMessage({
    required this.role,
    required this.text,
    this.memoryCount,
  });

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
