import 'dart:convert';
import 'dart:io';

import 'package:flutter/material.dart';

void main() {
  runApp(const OwnerExperimentalChatApp());
}

class OwnerExperimentalChatApp extends StatelessWidget {
  const OwnerExperimentalChatApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      title: 'Research OS — Owner Experimental Chat',
      theme: ThemeData(
        useMaterial3: true,
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.indigo),
      ),
      home: const ChatPage(),
    );
  }
}

class ChatPage extends StatefulWidget {
  const ChatPage({super.key});

  @override
  State<ChatPage> createState() => _ChatPageState();
}

class _ChatPageState extends State<ChatPage> {
  final _promptController = TextEditingController();
  final _endpointController = TextEditingController(
    text: 'http://127.0.0.1:8787',
  );
  final _scrollController = ScrollController();
  final List<_Message> _messages = [];
  bool _busy = false;
  String _status = 'Ready';

  @override
  void dispose() {
    _promptController.dispose();
    _endpointController.dispose();
    _scrollController.dispose();
    super.dispose();
  }

  Future<void> _send() async {
    final prompt = _promptController.text.trim();
    final baseUrl = _endpointController.text.trim().replaceFirst(RegExp(r'/$'), '');
    if (prompt.isEmpty || _busy) return;

    setState(() {
      _messages.add(_Message.user(prompt));
      _promptController.clear();
      _busy = true;
      _status = 'Sending to API Platform…';
    });
    _scrollToBottom();

    try {
      final client = HttpClient();
      try {
        final request = await client.postUrl(
          Uri.parse('$baseUrl/v1/ai/generate'),
        );
        request.headers.contentType = ContentType.json;
        request.headers.set('X-Research-OS-Owner', 'owner');
        request.headers.set('X-Research-OS-Profile', 'default');
        request.headers.set('X-Research-OS-Session', 'owner-experimental-chat');
        request.write(jsonEncode({
          'prompt': prompt,
          'complexity': 3,
          'risk': 1,
          'parallelism': 2,
          'helper_budget': 0,
          'requested_skills': <String>[],
          'requested_tools': <String>[],
          'session_id': 'owner-experimental-chat',
        }));

        final response = await request.close();
        final body = await utf8.decoder.bind(response).join();
        dynamic decoded;
        try {
          decoded = jsonDecode(body);
        } catch (_) {
          decoded = {'text': body};
        }

        if (response.statusCode < 200 || response.statusCode >= 300) {
          throw Exception('HTTP ${response.statusCode}: ${_display(decoded)}');
        }

        setState(() {
          _messages.add(_Message.assistant(_display(decoded), decoded));
          _status = 'Connected • API Platform → Friend';
        });
      } finally {
        client.close(force: true);
      }
    } catch (error) {
      setState(() {
        _messages.add(_Message.assistant('Request failed: $error'));
        _status = 'Connection error';
      });
    } finally {
      setState(() => _busy = false);
      _scrollToBottom();
    }
  }

  String _display(dynamic value) {
    if (value is Map<String, dynamic>) {
      final text = value['text'] ?? value['answer'] ?? value['response'];
      if (text != null) return text.toString();
      return const JsonEncoder.withIndent('  ').convert(value);
    }
    return value.toString();
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
    return Scaffold(
      appBar: AppBar(
        title: const Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Owner Experimental Chat'),
            Text(
              'Flutter → API Platform → Friend',
              style: TextStyle(fontSize: 12, fontWeight: FontWeight.normal),
            ),
          ],
        ),
      ),
      body: Column(
        children: [
          _ConnectionBar(
            endpointController: _endpointController,
            status: _status,
          ),
          Expanded(
            child: _messages.isEmpty
                ? const _EmptyState()
                : ListView.builder(
                    controller: _scrollController,
                    padding: const EdgeInsets.fromLTRB(20, 12, 20, 20),
                    itemCount: _messages.length,
                    itemBuilder: (_, index) => _Bubble(message: _messages[index]),
                  ),
          ),
          _Composer(
            controller: _promptController,
            busy: _busy,
            onSend: _send,
          ),
        ],
      ),
    );
  }
}

class _ConnectionBar extends StatelessWidget {
  const _ConnectionBar({required this.endpointController, required this.status});

  final TextEditingController endpointController;
  final String status;

  @override
  Widget build(BuildContext context) {
    return Material(
      elevation: 1,
      child: Padding(
        padding: const EdgeInsets.fromLTRB(16, 10, 16, 10),
        child: Row(
          children: [
            const Icon(Icons.route_outlined, size: 18),
            const SizedBox(width: 8),
            Expanded(
              child: TextField(
                controller: endpointController,
                decoration: const InputDecoration(
                  labelText: 'API Platform',
                  hintText: 'http://127.0.0.1:8787',
                  isDense: true,
                  border: OutlineInputBorder(),
                ),
              ),
            ),
            const SizedBox(width: 12),
            Flexible(child: Text(status, overflow: TextOverflow.ellipsis)),
          ],
        ),
      ),
    );
  }
}

class _Composer extends StatelessWidget {
  const _Composer({required this.controller, required this.busy, required this.onSend});

  final TextEditingController controller;
  final bool busy;
  final VoidCallback onSend;

  @override
  Widget build(BuildContext context) {
    return SafeArea(
      top: false,
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.end,
          children: [
            Expanded(
              child: TextField(
                controller: controller,
                minLines: 1,
                maxLines: 5,
                enabled: !busy,
                onSubmitted: (_) => onSend(),
                decoration: const InputDecoration(
                  hintText: 'สั่งงาน Research OS เช่น “เขียนงานถัดไปให้ผม”',
                  border: OutlineInputBorder(),
                ),
              ),
            ),
            const SizedBox(width: 10),
            IconButton.filled(
              onPressed: busy ? null : onSend,
              icon: busy
                  ? const SizedBox(
                      width: 20,
                      height: 20,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    )
                  : const Icon(Icons.arrow_upward),
              tooltip: 'Send',
            ),
          ],
        ),
      ),
    );
  }
}

class _Bubble extends StatelessWidget {
  const _Bubble({required this.message});

  final _Message message;

  @override
  Widget build(BuildContext context) {
    final isUser = message.role == 'user';
    return Align(
      alignment: isUser ? Alignment.centerRight : Alignment.centerLeft,
      child: Container(
        constraints: const BoxConstraints(maxWidth: 820),
        margin: const EdgeInsets.only(bottom: 12),
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: isUser
              ? Theme.of(context).colorScheme.primaryContainer
              : Theme.of(context).colorScheme.surfaceContainerHighest,
          borderRadius: BorderRadius.circular(16),
        ),
        child: SelectableText(message.text),
      ),
    );
  }
}

class _EmptyState extends StatelessWidget {
  const _EmptyState();

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(Icons.forum_outlined, size: 56, color: Theme.of(context).colorScheme.primary),
          const SizedBox(height: 14),
          const Text('Owner-only experimental workbench', style: TextStyle(fontSize: 20, fontWeight: FontWeight.w600)),
          const SizedBox(height: 8),
          const Text('This client sends commands to the existing Research OS API path.'),
        ],
      ),
    );
  }
}

class _Message {
  const _Message(this.role, this.text, [this.raw]);

  factory _Message.user(String text) => _Message('user', text);
  factory _Message.assistant(String text, [dynamic raw]) => _Message('assistant', text, raw);

  final String role;
  final String text;
  final dynamic raw;
}
