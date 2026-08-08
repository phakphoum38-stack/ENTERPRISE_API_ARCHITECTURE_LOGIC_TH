import 'package:flutter/material.dart';

class ChatTypingIndicator extends StatefulWidget {
  const ChatTypingIndicator({
    this.label = 'Research OS กำลังคิด…',
    super.key,
  });

  final String label;

  @override
  State<ChatTypingIndicator> createState() => _ChatTypingIndicatorState();
}

class _ChatTypingIndicatorState extends State<ChatTypingIndicator>
    with SingleTickerProviderStateMixin {
  late final AnimationController _controller;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 900),
    )..repeat();
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Align(
      alignment: Alignment.centerLeft,
      child: Container(
        key: const Key('chat-typing-indicator'),
        margin: const EdgeInsets.only(bottom: 14),
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
        decoration: BoxDecoration(
          color: scheme.surfaceContainer,
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: scheme.outlineVariant),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: <Widget>[
            const Icon(Icons.auto_awesome_outlined, size: 16),
            const SizedBox(width: 8),
            Text(widget.label),
            const SizedBox(width: 10),
            AnimatedBuilder(
              animation: _controller,
              builder: (context, _) {
                final phase = (_controller.value * 3).floor() % 3;
                return Row(
                  children: List<Widget>.generate(3, (index) {
                    return Padding(
                      padding: const EdgeInsets.symmetric(horizontal: 2),
                      child: Opacity(
                        opacity: index == phase ? 1 : .28,
                        child: const Icon(Icons.circle, size: 6),
                      ),
                    );
                  }),
                );
              },
            ),
          ],
        ),
      ),
    );
  }
}
