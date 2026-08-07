import 'package:flutter/material.dart';

import '../../api/research_os_api_client.dart';

class ChatPage extends StatefulWidget {
  const ChatPage({
    required this.apiClient,
    super.key,
  });

  final ResearchOSApiClient apiClient;

  @override
  State<ChatPage> createState() => _ChatPageState();
}

class _ChatPageState extends State<ChatPage> {
  final TextEditingController _controller = TextEditingController();
  final ScrollController _scrollController = ScrollController();
  final List<_ChatMessage> _messages = <_ChatMessage>[];
  bool _useMemory = true;
  bool _sending = false;
  String? _error;
  late String _sessionId = _newSessionId();

  static String _newSessionId() {
    final value = DateTime.now().microsecondsSinceEpoch.toRadixString(36);
    return 'chat-$value';
  }

  @override
  void dispose() {
    _controller.dispose();
    _scrollController.dispose();
    super.dispose();
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

  void _newConversation() {
    if (_sending) return;
    setState(() {
      _messages.clear();
      _error = null;
      _controller.clear();
      _sessionId = _newSessionId();
    });
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
      _controller.clear();
      _sending = true;
      _error = null;
    });
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
            tooltip: 'เริ่มบทสนทนาใหม่',
            onPressed: _sending ? null : _newConversation,
            icon: const Icon(Icons.add_comment_outlined),
          ),
          Row(
            mainAxisSize: MainAxisSize.min,
            children: <Widget>[
              const Text('ใช้ Memory'),
              Switch(
                value: _useMemory,
                onChanged: _sending
                    ? null
                    : (value) => setState(() => _useMemory = value),
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
              child: Chip(
                avatar: const Icon(Icons.forum_outlined, size: 18),
                label: Text('Session $_sessionId'),
              ),
            ),
          ),
          Expanded(
            child: _messages.isEmpty
                ? const _EmptyChat()
                : ListView.builder(
                    controller: _scrollController,
                    padding: const EdgeInsets.all(16),
                    itemCount: _messages.length,
                    itemBuilder: (context, index) {
                      return _MessageBubble(message: _messages[index]);
                    },
                  ),
          ),
          if (_error != null)
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16),
              child: MaterialBanner(
                content: Text(_error!),
                actions: <Widget>[
                  TextButton(
                    onPressed: () => setState(() => _error = null),
                    child: const Text('ปิด'),
                  ),
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
                    onPressed: _sending ? null : _send,
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
            Icon(
              Icons.auto_awesome_outlined,
              size: 56,
              color: Theme.of(context).colorScheme.primary,
            ),
            const SizedBox(height: 16),
            Text(
              'คุยกับ Gemini',
              style: Theme.of(context).textTheme.headlineSmall,
            ),
            const SizedBox(height: 8),
            const Text(
              'บทสนทนาใน Session เดียวกันจะต่อเนื่องกัน และสามารถเปิด Memory เพื่ออ้างอิงความรู้จากห้องสมุดของเรา',
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
              Text(
                'อ้างอิง Memory ${message.memoryCount} รายการ',
                style: Theme.of(context).textTheme.labelSmall,
              ),
            ],
          ],
        ),
      ),
    );
  }
}

class _ChatMessage {
  const _ChatMessage({
    required this.role,
    required this.text,
    this.memoryCount,
  });

  final String role;
  final String text;
  final int? memoryCount;
}

extension<T> on Iterable<T> {
  Iterable<T> takeLast(int count) {
    final values = toList(growable: false);
    if (values.length <= count) return values;
    return values.sublist(values.length - count);
  }
}
