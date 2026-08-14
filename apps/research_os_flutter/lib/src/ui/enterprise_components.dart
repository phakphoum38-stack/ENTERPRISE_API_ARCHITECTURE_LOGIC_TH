import 'package:flutter/material.dart';

class EnterprisePageHeader extends StatelessWidget {
  const EnterprisePageHeader({
    required this.title,
    required this.subtitle,
    this.icon,
    this.actions = const <Widget>[],
    super.key,
  });

  final String title;
  final String subtitle;
  final IconData? icon;
  final List<Widget> actions;

  Widget _titleBlock(BuildContext context) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: <Widget>[
        if (icon != null) ...<Widget>[
          Container(
            width: 44,
            height: 44,
            alignment: Alignment.center,
            decoration: BoxDecoration(
              color: Theme.of(context).colorScheme.primaryContainer,
              borderRadius: BorderRadius.circular(14),
            ),
            child: Icon(
              icon,
              color: Theme.of(context).colorScheme.onPrimaryContainer,
            ),
          ),
          const SizedBox(width: 14),
        ],
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: <Widget>[
              Text(
                title,
                style: Theme.of(context)
                    .textTheme
                    .headlineSmall
                    ?.copyWith(fontWeight: FontWeight.w700),
              ),
              const SizedBox(height: 4),
              Text(subtitle, style: Theme.of(context).textTheme.bodyMedium),
            ],
          ),
        ),
      ],
    );
  }

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, constraints) {
        final compact = constraints.maxWidth < 680;
        // Read the platform view directly. A Scaffold may derive a MediaQuery
        // for its body with consumed viewInsets, which can hide the software
        // keyboard from descendants even though the FlutterView still reports it.
        final keyboardOpen = View.of(context).viewInsets.bottom > 0;

        // On phones the software keyboard already consumes a large part of the
        // viewport. Collapse the page-level header while typing so the active
        // content and composer keep useful vertical space. The app-shell title
        // remains visible, and this header returns automatically when the
        // keyboard closes.
        if (compact && keyboardOpen) {
          return const SizedBox.shrink();
        }

        if (compact) {
          return Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: <Widget>[
              _titleBlock(context),
              if (actions.isNotEmpty) ...<Widget>[
                const SizedBox(height: 14),
                Align(
                  alignment: Alignment.centerLeft,
                  child: Wrap(
                    spacing: 8,
                    runSpacing: 8,
                    children: actions,
                  ),
                ),
              ],
            ],
          );
        }

        return Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: <Widget>[
            Expanded(child: _titleBlock(context)),
            if (actions.isNotEmpty) ...<Widget>[
              const SizedBox(width: 12),
              Flexible(
                child: Align(
                  alignment: Alignment.topRight,
                  child: Wrap(
                    alignment: WrapAlignment.end,
                    spacing: 8,
                    runSpacing: 8,
                    children: actions,
                  ),
                ),
              ),
            ],
          ],
        );
      },
    );
  }
}

class EnterpriseSection extends StatelessWidget {
  const EnterpriseSection({
    required this.title,
    required this.child,
    this.subtitle,
    this.trailing,
    super.key,
  });

  final String title;
  final String? subtitle;
  final Widget child;
  final Widget? trailing;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: <Widget>[
        Row(
          crossAxisAlignment: CrossAxisAlignment.end,
          children: <Widget>[
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: <Widget>[
                  Text(
                    title,
                    style: Theme.of(context)
                        .textTheme
                        .titleLarge
                        ?.copyWith(fontWeight: FontWeight.w700),
                  ),
                  if (subtitle != null) ...<Widget>[
                    const SizedBox(height: 3),
                    Text(subtitle!, style: Theme.of(context).textTheme.bodySmall),
                  ],
                ],
              ),
            ),
            if (trailing != null) trailing!,
          ],
        ),
        const SizedBox(height: 12),
        child,
      ],
    );
  }
}

class EnterpriseStatusTile extends StatelessWidget {
  const EnterpriseStatusTile({
    required this.icon,
    required this.title,
    required this.value,
    this.caption,
    super.key,
  });

  final IconData icon;
  final String title;
  final String value;
  final String? caption;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Row(
          children: <Widget>[
            Icon(icon, size: 26),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: <Widget>[
                  Text(title, style: Theme.of(context).textTheme.labelLarge),
                  const SizedBox(height: 2),
                  Text(
                    value,
                    style: Theme.of(context)
                        .textTheme
                        .titleMedium
                        ?.copyWith(fontWeight: FontWeight.w700),
                  ),
                  if (caption != null) ...<Widget>[
                    const SizedBox(height: 2),
                    Text(caption!, style: Theme.of(context).textTheme.bodySmall),
                  ],
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}
