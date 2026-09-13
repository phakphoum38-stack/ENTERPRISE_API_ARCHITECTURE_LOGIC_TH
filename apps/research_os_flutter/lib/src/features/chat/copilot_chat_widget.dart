import 'package:flutter/material.dart';

import '../../api/research_os_api_client.dart';

class CopilotChatWidget extends StatefulWidget {
  const CopilotChatWidget({
    required this.apiClient,
    this.contextPaths = const <String>['README.md', 'tools/research_os_api/README.md'],
    super.key,
  });

  final ResearchOSApiClient apiClient;
  final List<String> contextPaths;

  @override
  State<CopilotChatWidget> createState() => _CopilotChatWidgetState();
}

class _CopilotChatWidgetState extends State<CopilotChatWidget> {
  final TextEditingController _controller = TextEditingController();
  final List<_CopilotTurn> _turns = <_CopilotTurn>[];
  bool _sending = false;
  String? _contextSummary;

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  Future<void> _send() async {
    final message = _controller.text.trim();
    if (message.isEmpty || _sending) return;
    _controller.clear();
    setState(() {
      _sending = true;
      _turns.add(_CopilotTurn(role: 'user', text: message));
    });
    try {
      final result = await widget.apiClient.chatWithCopilot(
        message: message,
        paths: widget.contextPaths,
        contextQuery: message,
      );
      final context = (result['context'] as Map?)?.cast<String, dynamic>() ??
          const <String, dynamic>{};
      final files = (context['files'] as List?)?.length ?? 0;
      final memoryCount = (context['memory_count'] as num?)?.toInt() ?? 0;
      final repository = (context['repository'] ?? 'repository').toString();
      final reply = (result['reply'] ?? result['text'] ?? 'Copilot returned no reply.')
          .toString();
      if (!mounted) return;
      setState(() {
        _contextSummary =
            '$repository • $files files • $memoryCount memory hits';
        _turns.add(_CopilotTurn(role: 'assistant', text: reply));
        _sending = false;
      });
    } on Object catch (error) {
      if (!mounted) return;
      setState(() {
        _turns.add(_CopilotTurn(role: 'assistant', text: 'Copilot error: $error'));
        _sending = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: <Widget>[
            Text(
              'Copilot Chat',
              style: Theme.of(
                context,
              ).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w800),
            ),
            const SizedBox(height: 6),
            Text(
              'Enterprise API widget with trusted repository context',
              style: Theme.of(context).textTheme.bodySmall,
            ),
            const SizedBox(height: 12),
            Container(
              key: const Key('copilot-context-summary'),
              width: double.infinity,
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: scheme.surfaceContainerHighest,
                borderRadius: BorderRadius.circular(12),
              ),
              child: Text(
                _contextSummary ??
                    'พร้อมส่งบริบทจาก repository และ trusted user scope',
              ),
            ),
            const SizedBox(height: 12),
            Expanded(
              child: _turns.isEmpty
                  ? const Center(
                      child: Text('ยังไม่มีข้อความ เริ่มถาม Copilot ได้เลย'),
                    )
                  : ListView.builder(
                      itemCount: _turns.length,
                      itemBuilder: (context, index) {
                        final turn = _turns[index];
                        final isUser = turn.role == 'user';
                        return Align(
                          alignment: isUser
                              ? Alignment.centerRight
                              : Alignment.centerLeft,
                          child: Container(
                            margin: const EdgeInsets.only(bottom: 10),
                            padding: const EdgeInsets.all(12),
                            decoration: BoxDecoration(
                              color: isUser
                                  ? scheme.primaryContainer
                                  : scheme.surfaceContainerLow,
                              borderRadius: BorderRadius.circular(12),
                            ),
                            child: Text(turn.text),
                          ),
                        );
                      },
                    ),
            ),
            const SizedBox(height: 12),
            Row(
              children: <Widget>[
                Expanded(
                  child: TextField(
                    key: const Key('copilot-chat-input'),
                    controller: _controller,
                    minLines: 1,
                    maxLines: 4,
                    decoration: const InputDecoration(
                      labelText: 'Ask Copilot',
                      hintText: 'เช่น ช่วยสรุป architecture และความเสี่ยง',
                    ),
                    onSubmitted: (_) => _send(),
                  ),
                ),
                const SizedBox(width: 12),
                FilledButton.icon(
                  key: const Key('copilot-chat-send'),
                  onPressed: _sending ? null : _send,
                  icon: _sending
                      ? const SizedBox(
                          width: 16,
                          height: 16,
                          child: CircularProgressIndicator(strokeWidth: 2),
                        )
                      : const Icon(Icons.send_rounded),
                  label: const Text('Send'),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

class _CopilotTurn {
  const _CopilotTurn({required this.role, required this.text});

  final String role;
  final String text;
}
