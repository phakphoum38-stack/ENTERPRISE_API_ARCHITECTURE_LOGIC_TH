import 'dart:convert';

import 'package:flutter/material.dart';

import '../../api/research_os_api_client.dart';
import '../../features/local_api/local_api_control_page.dart';
import '../../features/monitor/system_monitor_page.dart';
import 'research_os_module_catalog.dart';

class ResearchMemoryModulePage extends StatefulWidget {
  const ResearchMemoryModulePage({required this.apiClient, super.key});

  final ResearchOSApiClient apiClient;

  @override
  State<ResearchMemoryModulePage> createState() =>
      _ResearchMemoryModulePageState();
}

class _ResearchMemoryModulePageState extends State<ResearchMemoryModulePage> {
  final TextEditingController _controller = TextEditingController();
  Map<String, dynamic>? _result;
  String? _error;
  bool _working = false;

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  Future<void> _search() async {
    final query = _controller.text.trim();
    if (query.isEmpty || _working) return;
    setState(() {
      _working = true;
      _error = null;
    });
    try {
      final result = await widget.apiClient.searchMemory(query);
      if (mounted) setState(() => _result = result);
    } on Object catch (error) {
      if (mounted) setState(() => _error = error.toString());
    } finally {
      if (mounted) setState(() => _working = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return ResearchModuleSurface(
      title: 'Memory',
      subtitle: 'Search the existing memory/evidence runtime without replacing it.',
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: <Widget>[
          TextField(
            key: const Key('new-gui-memory-query'),
            controller: _controller,
            decoration: const InputDecoration(labelText: 'Search memory'),
            onSubmitted: (_) => _search(),
          ),
          const SizedBox(height: 10),
          Align(
            alignment: Alignment.centerLeft,
            child: FilledButton.icon(
              key: const Key('new-gui-memory-search'),
              onPressed: _working ? null : _search,
              icon: _working
                  ? const SizedBox(
                      width: 16,
                      height: 16,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    )
                  : const Icon(Icons.search_rounded),
              label: const Text('Search'),
            ),
          ),
          if (_error != null) ...<Widget>[
            const SizedBox(height: 12),
            Text(_error!, style: const TextStyle(color: Color(0xFFFF6B7A))),
          ],
          if (_result != null) ...<Widget>[
            const SizedBox(height: 14),
            SelectableText(
              const JsonEncoder.withIndent('  ').convert(_result),
              style: const TextStyle(fontFamily: 'monospace', fontSize: 12),
            ),
          ],
        ],
      ),
    );
  }
}

class ResearchProvidersModulePage extends StatefulWidget {
  const ResearchProvidersModulePage({required this.apiClient, super.key});

  final ResearchOSApiClient apiClient;

  @override
  State<ResearchProvidersModulePage> createState() =>
      _ResearchProvidersModulePageState();
}

class _ResearchProvidersModulePageState
    extends State<ResearchProvidersModulePage> {
  late Future<Map<String, dynamic>> _future;

  @override
  void initState() {
    super.initState();
    _future = widget.apiClient.getProviders();
  }

  @override
  Widget build(BuildContext context) {
    return ResearchModuleSurface(
      title: 'Providers',
      subtitle: 'Live provider data from /v1/providers.',
      child: FutureBuilder<Map<String, dynamic>>(
        future: _future,
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.waiting) {
            return const Center(child: CircularProgressIndicator());
          }
          if (snapshot.hasError) return Text(snapshot.error.toString());
          return SelectableText(
            const JsonEncoder.withIndent('  ').convert(
              snapshot.data ?? const <String, dynamic>{},
            ),
            style: const TextStyle(fontFamily: 'monospace', fontSize: 12),
          );
        },
      ),
    );
  }
}

class ResearchFactoryModulePage extends StatefulWidget {
  const ResearchFactoryModulePage({required this.apiClient, super.key});

  final ResearchOSApiClient apiClient;

  @override
  State<ResearchFactoryModulePage> createState() =>
      _ResearchFactoryModulePageState();
}

class _ResearchFactoryModulePageState extends State<ResearchFactoryModulePage> {
  late Future<Map<String, dynamic>> _future;

  @override
  void initState() {
    super.initState();
    _future = widget.apiClient.getOrchestrations(limit: 20);
  }

  @override
  Widget build(BuildContext context) {
    return ResearchModuleSurface(
      title: 'Factory',
      subtitle: 'Existing orchestration runtime exposed as a control-center module.',
      child: FutureBuilder<Map<String, dynamic>>(
        future: _future,
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.waiting) {
            return const Center(child: CircularProgressIndicator());
          }
          if (snapshot.hasError) return Text(snapshot.error.toString());
          return SelectableText(
            const JsonEncoder.withIndent('  ').convert(
              snapshot.data ?? const <String, dynamic>{},
            ),
            style: const TextStyle(fontFamily: 'monospace', fontSize: 12),
          );
        },
      ),
    );
  }
}

class ResearchRuntimeHub extends StatelessWidget {
  const ResearchRuntimeHub({required this.apiClient, super.key});

  final ResearchOSApiClient apiClient;

  @override
  Widget build(BuildContext context) {
    return DefaultTabController(
      length: 2,
      child: Column(
        children: <Widget>[
          const Material(
            child: TabBar(
              tabs: <Widget>[
                Tab(text: 'Local API & Service'),
                Tab(text: 'System Monitor'),
              ],
            ),
          ),
          Expanded(
            child: TabBarView(
              children: <Widget>[
                const LocalApiControlPage(),
                SystemMonitorPage(apiClient: apiClient),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class ResearchModuleAdapterPage extends StatelessWidget {
  const ResearchModuleAdapterPage({required this.module, super.key});

  final ResearchOSModuleDefinition module;

  @override
  Widget build(BuildContext context) {
    return ResearchModuleSurface(
      title: module.label,
      subtitle: module.availability == 'planned'
          ? 'Dedicated surface is intentionally not faked. Integration evidence must be established before mutable controls are enabled.'
          : 'The capability exists; this surface will bind to the existing runtime adapter.',
      child: Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: const Color(0xFF11192B),
          borderRadius: BorderRadius.circular(14),
          border: Border.all(color: const Color(0xFF26344F)),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: <Widget>[
            Text(
              'Status: ${module.availability}',
              style: const TextStyle(fontWeight: FontWeight.w700),
            ),
            const SizedBox(height: 8),
            Text('Source: ${module.backendSource ?? 'not established'}'),
          ],
        ),
      ),
    );
  }
}

class ResearchModuleSurface extends StatelessWidget {
  const ResearchModuleSurface({
    required this.title,
    required this.subtitle,
    required this.child,
    super.key,
  });

  final String title;
  final String subtitle;
  final Widget child;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF090E1A),
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.all(20),
          children: <Widget>[
            Text(title, style: Theme.of(context).textTheme.headlineSmall),
            const SizedBox(height: 4),
            Text(
              subtitle,
              style: const TextStyle(color: Color(0xFF8EA4C5)),
            ),
            const SizedBox(height: 18),
            child,
          ],
        ),
      ),
    );
  }
}
