import 'package:flutter/material.dart';

import '../api/v3_api.dart';

class V3ChatPage extends StatefulWidget {
  const V3ChatPage({super.key, required this.api});

  final V3Api api;

  @override
  State<V3ChatPage> createState() => _V3ChatPageState();
}

class _V3ChatPageState extends State<V3ChatPage> {
  final TextEditingController _controller = TextEditingController();
  final ScrollController _scrollController = ScrollController();
  final List<_ChatMessage> _messages = <_ChatMessage>[];

  String _provider = 'auto';
  String _sessionId = 'default';
  bool _sending = false;
  String? _error;

  static const List<(String, String)> _providerOptions = <(String, String)>[
    ('auto', 'Auto'),
    ('gemini', 'Gemini'),
    ('openai-compatible', 'OpenAI'),
  ];

  @override
  void dispose() {
    _controller.dispose();
    _scrollController.dispose();
    super.dispose();
  }

  void _newChat() {
    setState(() {
      _messages.clear();
      _error = null;
      _sessionId = 'session-${DateTime.now().millisecondsSinceEpoch}';
    });
    _controller.clear();
  }

  Future<void> _send() async {
    final message = _controller.text.trim();
    if (message.isEmpty || _sending) return;

    _controller.clear();
    setState(() {
      _sending = true;
      _error = null;
      _messages.add(_ChatMessage.user(message));
    });
    _scrollToBottom();

    try {
      final response = await widget.api.chat(
        message,
        sessionId: _sessionId,
        provider: _provider,
      );
      if (!mounted) return;
      final text = (response['text'] ?? response['answer'] ?? '').toString();
      final provider = response['provider']?.toString() ?? 'unknown';
      final model = response['model']?.toString() ?? '';
      final memoryCount = switch (response['memory_count']) {
        int value => value,
        num value => value.toInt(),
        _ => int.tryParse(response['memory_count']?.toString() ?? '') ?? 0,
      };
      setState(() {
        _messages.add(
          _ChatMessage.assistant(
            text.isEmpty ? '(empty response)' : text,
            provider: provider,
            model: model,
            memoryCount: memoryCount,
          ),
        );
      });
    } catch (error) {
      if (mounted) setState(() => _error = error.toString());
    } finally {
      if (mounted) {
        setState(() => _sending = false);
        _scrollToBottom();
      }
    }
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!_scrollController.hasClients) return;
      _scrollController.animateTo(
        _scrollController.position.maxScrollExtent,
        duration: const Duration(milliseconds: 180),
        curve: Curves.easeOut,
      );
    });
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Material(
          color: Theme.of(context).colorScheme.surface,
          child: SizedBox(
            height: 64,
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 24),
              child: Row(
                children: [
                  Expanded(
                    child: Text(
                      'AI Chat',
                      style: Theme.of(context).textTheme.titleLarge,
                    ),
                  ),
                  DropdownButtonHideUnderline(
                    child: DropdownButton<String>(
                      key: const Key('chat-provider-selector'),
                      value: _provider,
                      items: [
                        for (final option in _providerOptions)
                          DropdownMenuItem<String>(
                            value: option.$1,
                            child: Text(option.$2),
                          ),
                      ],
                      onChanged: _sending
                          ? null
                          : (value) {
                              if (value != null) setState(() => _provider = value);
                            },
                    ),
                  ),
                  const SizedBox(width: 12),
                  OutlinedButton.icon(
                    key: const Key('new-chat-button'),
                    onPressed: _sending ? null : _newChat,
                    icon: const Icon(Icons.add),
                    label: const Text('New chat'),
                  ),
                ],
              ),
            ),
          ),
        ),
        const Divider(height: 1),
        Expanded(
          child: _messages.isEmpty
              ? const _EmptyChat()
              : ListView.builder(
                  key: const Key('chat-message-list'),
                  controller: _scrollController,
                  padding: const EdgeInsets.fromLTRB(24, 24, 24, 12),
                  itemCount: _messages.length,
                  itemBuilder: (context, index) =>
                      _MessageBubble(message: _messages[index]),
                ),
        ),
        if (_error != null)
          Material(
            color: Theme.of(context).colorScheme.errorContainer,
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 10),
              child: Row(
                children: [
                  Icon(Icons.error_outline,
                      color: Theme.of(context).colorScheme.onErrorContainer),
                  const SizedBox(width: 10),
                  Expanded(
                    child: Text(
                      _error!,
                      key: const Key('chat-error'),
                      style: TextStyle(
                        color: Theme.of(context).colorScheme.onErrorContainer,
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),
        Padding(
          padding: const EdgeInsets.fromLTRB(16, 12, 16, 16),
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              Expanded(
                child: TextField(
                  key: const Key('chat-input'),
                  controller: _controller,
                  enabled: !_sending,
                  minLines: 1,
                  maxLines: 6,
                  textInputAction: TextInputAction.newline,
                  decoration: const InputDecoration(
                    border: OutlineInputBorder(),
                    hintText: 'Message Research OS V3.2',
                  ),
                  onSubmitted: (_) => _send(),
                ),
              ),
              const SizedBox(width: 10),
              IconButton.filled(
                key: const Key('chat-send-button'),
                tooltip: 'Send',
                onPressed: _sending ? null : _send,
                icon: _sending
                    ? const SizedBox.square(
                        dimension: 18,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      )
                    : const Icon(Icons.arrow_upward),
              ),
            ],
          ),
        ),
      ],
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
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 620),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(Icons.auto_awesome,
                  size: 44, color: Theme.of(context).colorScheme.primary),
              const SizedBox(height: 16),
              Text(
                'Unified Research OS Chat',
                style: Theme.of(context).textTheme.headlineSmall,
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 10),
              const Text(
                'Messages go through the local V3.2 service, Unified Master, '
                'user-scoped memory, and the selected provider. Provider keys '
                'remain outside the Flutter app.',
                textAlign: TextAlign.center,
              ),
            ],
          ),
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
    final isUser = message.role == _ChatRole.user;
    final scheme = Theme.of(context).colorScheme;
    return Align(
      alignment: isUser ? Alignment.centerRight : Alignment.centerLeft,
      child: Container(
        key: ValueKey<String>('chat-${message.role.name}-${message.text}'),
        constraints: const BoxConstraints(maxWidth: 760),
        margin: const EdgeInsets.only(bottom: 12),
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
        decoration: BoxDecoration(
          color: isUser ? scheme.primaryContainer : scheme.surfaceContainerHigh,
          borderRadius: BorderRadius.circular(18),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(message.text),
            if (!isUser && message.provider != null) ...[
              const SizedBox(height: 8),
              Text(
                [
                  message.provider!,
                  if (message.model != null && message.model!.isNotEmpty)
                    message.model!,
                  if (message.memoryCount > 0) 'memory ${message.memoryCount}',
                ].join(' · '),
                key: const Key('chat-response-metadata'),
                style: Theme.of(context).textTheme.labelSmall,
              ),
            ],
          ],
        ),
      ),
    );
  }
}

enum _ChatRole { user, assistant }

class _ChatMessage {
  const _ChatMessage._(
    this.role,
    this.text, {
    this.provider,
    this.model,
    this.memoryCount = 0,
  });

  factory _ChatMessage.user(String text) =>
      _ChatMessage._(_ChatRole.user, text);

  factory _ChatMessage.assistant(
    String text, {
    required String provider,
    required String model,
    required int memoryCount,
  }) =>
      _ChatMessage._(
        _ChatRole.assistant,
        text,
        provider: provider,
        model: model,
        memoryCount: memoryCount,
      );

  final _ChatRole role;
  final String text;
  final String? provider;
  final String? model;
  final int memoryCount;
}
