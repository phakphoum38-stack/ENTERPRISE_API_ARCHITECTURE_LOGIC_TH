import 'package:flutter/material.dart';

import '../../api/research_os_api_client.dart';

class SettingsPage extends StatefulWidget {
  const SettingsPage({
    required this.apiClient,
    required this.themeMode,
    required this.onThemeModeChanged,
    super.key,
  });

  final ResearchOSApiClient apiClient;
  final ThemeMode themeMode;
  final ValueChanged<ThemeMode> onThemeModeChanged;

  @override
  State<SettingsPage> createState() => _SettingsPageState();
}

class _SettingsPageState extends State<SettingsPage> {
  bool _loading = true;
  String? _error;
  String _activeProvider = 'unknown';
  List<String> _providers = const <String>[];

  @override
  void initState() {
    super.initState();
    _loadProviders();
  }

  Future<void> _loadProviders() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final payload = await widget.apiClient.getProviders();
      if (!mounted) return;
      final rawProviders = payload['providers'];
      setState(() {
        _activeProvider = payload['active']?.toString() ?? 'unknown';
        _providers = rawProviders is List
            ? rawProviders.map((item) => item.toString()).toList()
            : const <String>[];
        _loading = false;
      });
    } on Object catch (error) {
      if (!mounted) return;
      setState(() {
        _error = error.toString();
        _loading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('การตั้งค่า'),
        actions: <Widget>[
          IconButton(
            tooltip: 'รีเฟรช Provider',
            onPressed: _loading ? null : _loadProviders,
            icon: const Icon(Icons.refresh),
          ),
        ],
      ),
      body: ListView(
        padding: const EdgeInsets.all(20),
        children: <Widget>[
          Text(
            'Settings & Provider Manager',
            style: Theme.of(context).textTheme.headlineMedium,
          ),
          const SizedBox(height: 8),
          Text(
            'จัดการหน้าตาแอปและตรวจสถานะการเชื่อมต่อ โดยไม่แสดง API key',
            style: Theme.of(context).textTheme.bodyLarge,
          ),
          const SizedBox(height: 24),
          Text('Appearance', style: Theme.of(context).textTheme.titleLarge),
          const SizedBox(height: 8),
          SegmentedButton<ThemeMode>(
            segments: const <ButtonSegment<ThemeMode>>[
              ButtonSegment<ThemeMode>(
                value: ThemeMode.system,
                icon: Icon(Icons.brightness_auto),
                label: Text('System'),
              ),
              ButtonSegment<ThemeMode>(
                value: ThemeMode.light,
                icon: Icon(Icons.light_mode_outlined),
                label: Text('Light'),
              ),
              ButtonSegment<ThemeMode>(
                value: ThemeMode.dark,
                icon: Icon(Icons.dark_mode_outlined),
                label: Text('Dark'),
              ),
            ],
            selected: <ThemeMode>{widget.themeMode},
            onSelectionChanged: (selection) {
              if (selection.isNotEmpty) {
                widget.onThemeModeChanged(selection.first);
              }
            },
          ),
          const SizedBox(height: 24),
          Text('Research OS API', style: Theme.of(context).textTheme.titleLarge),
          const SizedBox(height: 8),
          Card(
            child: ListTile(
              leading: const Icon(Icons.dns_outlined),
              title: const Text('API Base URL'),
              subtitle: SelectableText(widget.apiClient.baseUrl),
            ),
          ),
          const SizedBox(height: 16),
          Text('Provider Manager', style: Theme.of(context).textTheme.titleLarge),
          const SizedBox(height: 8),
          if (_loading) const LinearProgressIndicator(),
          if (_error != null)
            Card(
              child: ListTile(
                leading: const Icon(Icons.error_outline),
                title: const Text('โหลด Provider ไม่สำเร็จ'),
                subtitle: Text(_error!),
                trailing: IconButton(
                  tooltip: 'ลองใหม่',
                  onPressed: _loadProviders,
                  icon: const Icon(Icons.refresh),
                ),
              ),
            ),
          if (!_loading && _error == null) ...<Widget>[
            Card(
              child: ListTile(
                leading: const Icon(Icons.smart_toy_outlined),
                title: const Text('Active Provider'),
                subtitle: Text(_activeProvider),
                trailing: const Chip(label: Text('Backend managed')),
              ),
            ),
            const SizedBox(height: 8),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: _providers
                  .map(
                    (provider) => Chip(
                      avatar: Icon(
                        provider == _activeProvider
                            ? Icons.check_circle
                            : Icons.circle_outlined,
                        size: 18,
                      ),
                      label: Text(provider),
                    ),
                  )
                  .toList(),
            ),
          ],
          const SizedBox(height: 24),
          const Card(
            child: ListTile(
              leading: Icon(Icons.security_outlined),
              title: Text('Secrets stay on the backend'),
              subtitle: Text(
                'Flutter จะไม่จัดเก็บหรือแสดง Gemini API key และ GitHub token',
              ),
            ),
          ),
        ],
      ),
    );
  }
}
