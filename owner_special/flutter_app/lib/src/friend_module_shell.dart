import 'package:flutter/material.dart';

class FriendModuleShell extends StatelessWidget {
  const FriendModuleShell({required this.title, required this.child, this.actions = const <Widget>[], super.key});
  final String title;
  final Widget child;
  final List<Widget> actions;

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        color: Theme.of(context).colorScheme.surface.withValues(alpha: .72),
        borderRadius: BorderRadius.circular(22),
        border: Border.all(color: Theme.of(context).dividerColor.withValues(alpha: .08)),
      ),
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Row(children: [Expanded(child: Text(title, style: Theme.of(context).textTheme.titleMedium)), ...actions]),
          const SizedBox(height: 16),
          Expanded(child: child),
        ],
      ),
    );
  }
}
