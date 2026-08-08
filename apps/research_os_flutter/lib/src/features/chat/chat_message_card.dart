import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_markdown/flutter_markdown.dart';

class ChatMessageCard extends StatelessWidget {
  const ChatMessageCard({
    required this.role,
    required this.text,
    required this.createdAt,
    this.provider,
    this.memoryCount,
    this.onRetry,
    this.onEdit,
    super.key,
  });

  final String role;
  final String text;
  final DateTime createdAt;
  final String? provider;
  final int? memoryCount;
  final VoidCallback? onRetry;
  final VoidCallback? onEdit;

  bool get isUser => role == 'user';

  bool _looksLikeMarkdown(String value) {
    if (value.contains('```') || value.contains('**') || value.contains('`')) {
      return true;
    }
    return RegExp(r'(^|\n)(#{1,6}\s|[-*]\s|\d+\.\s|>\s)').hasMatch(value);
  }

  String _formatTime(DateTime value) {
    final local = value.toLocal();
    final hour = local.hour.toString().padLeft(2, '0');
    final minute = local.minute.toString().padLeft(2, '0');
    return '$hour:$minute';
  }

  Future<void> _copy(BuildContext context) async {
    await Clipboard.setData(ClipboardData(text: text));
    if (!context.mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Text('คัดลอกข้อความแล้ว'),
        duration: Duration(seconds: 1),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final renderMarkdown = !isUser && _looksLikeMarkdown(text);

    return Align(
      alignment: isUser ? Alignment.centerRight : Alignment.centerLeft,
      child: Container(
        key: Key('chat-message-${isUser ? 'user' : 'assistant'}'),
        constraints: const BoxConstraints(maxWidth: 820),
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
                if (!isUser && provider != null && provider!.trim().isNotEmpty) ...<Widget>[
                  const SizedBox(width: 8),
                  Chip(
                    key: const Key('chat-provider-badge'),
                    visualDensity: VisualDensity.compact,
                    avatar: const Icon(Icons.smart_toy_outlined, size: 14),
                    label: Text(provider!),
                  ),
                ],
                const Spacer(),
                Text(
                  _formatTime(createdAt),
                  key: const Key('chat-message-time'),
                  style: Theme.of(context).textTheme.labelSmall?.copyWith(
                        color: scheme.onSurfaceVariant,
                      ),
                ),
              ],
            ),
            const SizedBox(height: 10),
            if (renderMarkdown)
              MarkdownBody(
                data: text,
                selectable: true,
                styleSheet: MarkdownStyleSheet.fromTheme(Theme.of(context)),
              )
            else
              SelectableText(text),
            if (memoryCount != null) ...<Widget>[
              const SizedBox(height: 10),
              Chip(
                key: const Key('chat-memory-badge'),
                visualDensity: VisualDensity.compact,
                avatar: const Icon(Icons.memory_outlined, size: 16),
                label: Text('Memory $memoryCount รายการ'),
              ),
            ],
            const SizedBox(height: 8),
            Wrap(
              spacing: 2,
              children: <Widget>[
                IconButton(
                  key: const Key('chat-copy-message'),
                  tooltip: 'คัดลอก',
                  visualDensity: VisualDensity.compact,
                  onPressed: () => _copy(context),
                  icon: const Icon(Icons.copy_outlined, size: 18),
                ),
                if (isUser && onEdit != null)
                  IconButton(
                    key: const Key('chat-edit-prompt'),
                    tooltip: 'แก้ไข Prompt',
                    visualDensity: VisualDensity.compact,
                    onPressed: onEdit,
                    icon: const Icon(Icons.edit_outlined, size: 18),
                  ),
                if (!isUser && onRetry != null)
                  IconButton(
                    key: const Key('chat-retry-response'),
                    tooltip: 'ลองใหม่',
                    visualDensity: VisualDensity.compact,
                    onPressed: onRetry,
                    icon: const Icon(Icons.refresh_outlined, size: 18),
                  ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}
