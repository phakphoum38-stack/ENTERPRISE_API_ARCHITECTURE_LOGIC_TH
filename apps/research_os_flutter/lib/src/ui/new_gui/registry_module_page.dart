import 'package:flutter/material.dart';

import '../../api/research_os_api_client.dart';
import 'module_adapter_pages.dart';

enum ResearchRegistryKind { skills, tools }

class ResearchRegistryModulePage extends StatefulWidget {
  const ResearchRegistryModulePage({
    required this.apiClient,
    required this.kind,
    super.key,
  });

  final ResearchOSApiClient apiClient;
  final ResearchRegistryKind kind;

  @override
  State<ResearchRegistryModulePage> createState() =>
      _ResearchRegistryModulePageState();
}

class _ResearchRegistryModulePageState
    extends State<ResearchRegistryModulePage> {
  late Future<Map<String, dynamic>> _future;

  String get _key => widget.kind == ResearchRegistryKind.skills ? 'skills' : 'tools';
  String get _title => widget.kind == ResearchRegistryKind.skills ? 'Skills' : 'Tools';

  @override
  void initState() {
    super.initState();
    _reload();
  }

  void _reload() {
    _future = widget.kind == ResearchRegistryKind.skills
        ? widget.apiClient.getSkills()
        : widget.apiClient.getTools();
  }

  void _retry() {
    setState(_reload);
  }

  @override
  Widget build(BuildContext context) {
    return ResearchModuleSurface(
      title: _title,
      subtitle:
          'Read-only live registry from the existing Owner/Friend runtime. No duplicate registry is created in Flutter.',
      child: FutureBuilder<Map<String, dynamic>>(
        future: _future,
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.waiting) {
            return const Center(child: CircularProgressIndicator());
          }
          if (snapshot.hasError) {
            return _RegistryError(
              message: snapshot.error.toString(),
              onRetry: _retry,
            );
          }

          final payload = snapshot.data ?? const <String, dynamic>{};
          final raw = payload[_key];
          final items = raw is List
              ? raw.map((item) => item.toString()).toList(growable: false)
              : const <String>[];
          final source = (payload['source'] ?? 'unknown').toString();

          return Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: <Widget>[
              Wrap(
                spacing: 10,
                runSpacing: 10,
                children: <Widget>[
                  _RegistryMetric(
                    label: 'Registered',
                    value: '${items.length}',
                    icon: widget.kind == ResearchRegistryKind.skills
                        ? Icons.psychology_alt_outlined
                        : Icons.build_circle_outlined,
                  ),
                  _RegistryMetric(
                    label: 'Source',
                    value: source,
                    icon: Icons.link_outlined,
                  ),
                  const _RegistryMetric(
                    label: 'Access',
                    value: 'Read only',
                    icon: Icons.visibility_outlined,
                  ),
                ],
              ),
              const SizedBox(height: 18),
              if (items.isEmpty)
                const Text('Registry is connected but contains no published entries.')
              else
                Wrap(
                  spacing: 10,
                  runSpacing: 10,
                  children: <Widget>[
                    for (final item in items)
                      Chip(
                        key: Key('new-gui-registry-$_key-$item'),
                        avatar: Icon(
                          widget.kind == ResearchRegistryKind.skills
                              ? Icons.auto_awesome_outlined
                              : Icons.extension_outlined,
                          size: 16,
                        ),
                        label: Text(item),
                      ),
                  ],
                ),
            ],
          );
        },
      ),
    );
  }
}

class _RegistryMetric extends StatelessWidget {
  const _RegistryMetric({
    required this.label,
    required this.value,
    required this.icon,
  });

  final String label;
  final String value;
  final IconData icon;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: 190,
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: const Color(0xFF11192B),
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: const Color(0xFF26344F)),
      ),
      child: Row(
        children: <Widget>[
          Icon(icon, color: const Color(0xFF7EA2FF)),
          const SizedBox(width: 10),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: <Widget>[
                Text(
                  label,
                  style: const TextStyle(
                    color: Color(0xFF8EA4C5),
                    fontSize: 10,
                  ),
                ),
                const SizedBox(height: 3),
                Text(
                  value,
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                  style: const TextStyle(fontWeight: FontWeight.w700),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _RegistryError extends StatelessWidget {
  const _RegistryError({required this.message, required this.onRetry});

  final String message;
  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: const Color(0xFF11192B),
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: const Color(0xFFFF6B7A)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          const Text(
            'Owner/Friend registry is unavailable',
            style: TextStyle(fontWeight: FontWeight.w700),
          ),
          const SizedBox(height: 8),
          Text(message),
          const SizedBox(height: 12),
          OutlinedButton.icon(
            onPressed: onRetry,
            icon: const Icon(Icons.refresh_rounded),
            label: const Text('Retry'),
          ),
        ],
      ),
    );
  }
}
