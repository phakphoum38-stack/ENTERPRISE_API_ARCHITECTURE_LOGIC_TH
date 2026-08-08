import 'package:flutter/material.dart';

import '../../api/api_auto_discovery.dart';
import '../../api/api_connection_preferences.dart';
import '../../api/api_connection_state.dart';
import '../../api/api_endpoint_store.dart';
import '../../api/research_os_api_client.dart';
import '../../ui/enterprise_components.dart';
import 'identity_settings_section.dart';

class SettingsPage extends StatefulWidget {
  const SettingsPage({
    required this.apiClient,
    required this.themeMode,
    required this.onThemeModeChanged,
    this.onApiBaseUrlChanged,
    super.key,
  });

  final ResearchOSApiClient apiClient;
  final ThemeMode themeMode;
  final ValueChanged<ThemeMode> onThemeModeChanged;
  final Future<void> Function(String value)? onApiBaseUrlChanged;

  @override
  State<SettingsPage> createState() => _SettingsPageState();
}

class _SettingsPageState extends State<SettingsPage> {
  bool _loading = true;
  bool _savingEndpoint = false;
  bool _testingConnection = false;
  String? _error;
  String _activeProvider = 'unknown';
  List<String> _providers = const <String>[];
  ApiConnectionPreferences _connectionPreferences =
      ApiConnectionPreferences.defaults;
  late final TextEditingController _apiController;

  @override
  void initState() {
    super.initState();
    _apiController = TextEditingController(text: widget.apiClient.baseUrl);
    _loadPreferences();
    _loadProviders();
  }

  @override
  void dispose() {
    _apiController.dispose();
    super.dispose();
  }

  Future<void> _loadPreferences() async {
    final preferences = await ApiConnectionPreferences.load();
    if (!mounted) return;
    setState(() => _connectionPreferences = preferences);
  }

  Future<void> _savePreferences(ApiConnectionPreferences value) async {
    setState(() => _connectionPreferences = value);
    await value.save();
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

  Future<void> _saveEndpoint([String? preset]) async {
    final callback = widget.onApiBaseUrlChanged;
    if (callback == null || _savingEndpoint) return;
    final value = preset ?? _apiController.text;
    setState(() {
      _savingEndpoint = true;
      _error = null;
    });
    try {
      final normalized = ApiEndpointStore.normalize(value);
      _apiController.text = normalized;
      await callback(normalized);
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('บันทึก API Base URL แล้ว')),
      );
    } on Object catch (error) {
      if (!mounted) return;
      setState(() => _error = error.toString());
    } finally {
      if (mounted) setState(() => _savingEndpoint = false);
    }
  }

  Future<void> _testConnection() async {
    if (_testingConnection) return;
    setState(() {
      _testingConnection = true;
      _error = null;
    });
    try {
      final normalized = ApiEndpointStore.normalize(_apiController.text);
      final result = await ApiAutoDiscovery.probe(
        normalized,
        source: 'settings-test',
      );
      if (!mounted) return;
      if (result == null) {
        setState(() => _error = 'ไม่พบ Research OS API ที่ $normalized');
        return;
      }
      apiConnectionState.value = ApiConnectionSnapshot(
        phase: ApiConnectionPhase.connected,
        baseUrl: result.baseUrl,
        latency: result.latency,
        source: result.source,
      );
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(
            'เชื่อมต่อสำเร็จ • ${result.latency.inMilliseconds} ms',
          ),
        ),
      );
    } on Object catch (error) {
      if (!mounted) return;
      setState(() => _error = error.toString());
    } finally {
      if (mounted) setState(() => _testingConnection = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return ListView(
      padding: const EdgeInsets.fromLTRB(24, 22, 24, 32),
      children: <Widget>[
        EnterprisePageHeader(
          icon: Icons.settings_outlined,
          title: 'Settings',
          subtitle:
              'จัดการ Owner Profile, Appearance, API endpoint และ AI Provider โดยคง Secret ไว้ฝั่ง Backend',
          actions: <Widget>[
            IconButton(
              tooltip: 'รีเฟรช Provider',
              onPressed: _loading ? null : _loadProviders,
              icon: const Icon(Icons.refresh),
            ),
          ],
        ),
        const SizedBox(height: 28),
        EnterpriseSection(
          title: 'Appearance',
          subtitle: 'ธีมของ Research OS',
          child: Card(
            child: Padding(
              padding: const EdgeInsets.all(18),
              child: SegmentedButton<ThemeMode>(
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
            ),
          ),
        ),
        const SizedBox(height: 28),
        const EnterpriseSection(
          title: 'Identity & private profile',
          subtitle:
              'จำอีเมลของเจ้าของบนอุปกรณ์นี้ โดยไม่เปลี่ยนผู้ใช้ทั่วไปให้เป็นโปรไฟล์ส่วนตัว',
          child: IdentitySettingsSection(),
        ),
        const SizedBox(height: 28),
        EnterpriseSection(
          title: 'API Manager',
          subtitle:
              'ค้นหา เชื่อมต่อ ทดสอบ และติดตาม Research OS API โดยอัตโนมัติ',
          child: Column(
            children: <Widget>[
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(18),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: <Widget>[
                      TextField(
                        key: const Key('api-base-url-field'),
                        controller: _apiController,
                        autocorrect: false,
                        enableSuggestions: false,
                        keyboardType: TextInputType.url,
                        decoration: const InputDecoration(
                          labelText: 'Preferred API Base URL',
                          hintText: 'http://192.168.x.x:8787',
                          helperText:
                              'Auto Discovery จะลอง URL นี้ก่อน แล้วค่อยค้นหา endpoint อื่นเมื่อจำเป็น',
                        ),
                      ),
                      const SizedBox(height: 14),
                      Wrap(
                        spacing: 8,
                        runSpacing: 8,
                        children: <Widget>[
                          FilledButton.icon(
                            onPressed:
                                _savingEndpoint ? null : () => _saveEndpoint(),
                            icon: _savingEndpoint
                                ? const SizedBox(
                                    width: 16,
                                    height: 16,
                                    child: CircularProgressIndicator(
                                      strokeWidth: 2,
                                    ),
                                  )
                                : const Icon(Icons.save_outlined),
                            label: const Text('บันทึก'),
                          ),
                          OutlinedButton.icon(
                            onPressed:
                                _testingConnection ? null : _testConnection,
                            icon: _testingConnection
                                ? const SizedBox(
                                    width: 16,
                                    height: 16,
                                    child: CircularProgressIndicator(
                                      strokeWidth: 2,
                                    ),
                                  )
                                : const Icon(Icons.network_ping_outlined),
                            label: const Text('Test Connection'),
                          ),
                          OutlinedButton.icon(
                            onPressed: _savingEndpoint
                                ? null
                                : () => _saveEndpoint(
                                      ApiEndpointStore.localDefault,
                                    ),
                            icon: const Icon(Icons.computer_outlined),
                            label: const Text('Local'),
                          ),
                          OutlinedButton.icon(
                            onPressed: _savingEndpoint
                                ? null
                                : () => _saveEndpoint(
                                      ApiEndpointStore.renderDefault,
                                    ),
                            icon: const Icon(Icons.cloud_outlined),
                            label: const Text('Cloud'),
                          ),
                        ],
                      ),
                      const SizedBox(height: 14),
                      const Divider(height: 1),
                      const SizedBox(height: 12),
                      SelectableText('กำลังใช้: ${widget.apiClient.baseUrl}'),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 10),
              Card(
                child: Column(
                  children: <Widget>[
                    SwitchListTile(
                      title: const Text('Auto Discovery'),
                      subtitle: const Text(
                        'ค้นหา endpoint ที่พร้อมใช้งานและ reconnect อัตโนมัติ',
                      ),
                      value: _connectionPreferences.autoDiscovery,
                      onChanged: (value) => _savePreferences(
                        _connectionPreferences.copyWith(autoDiscovery: value),
                      ),
                    ),
                    const Divider(height: 1),
                    SwitchListTile(
                      title: const Text('Private LAN Scan'),
                      subtitle: const Text(
                        'ค้นหา Research OS API ในเครือข่ายส่วนตัวของอุปกรณ์',
                      ),
                      value: _connectionPreferences.scanLan,
                      onChanged: _connectionPreferences.autoDiscovery
                          ? (value) => _savePreferences(
                                _connectionPreferences.copyWith(scanLan: value),
                              )
                          : null,
                    ),
                    const Divider(height: 1),
                    ListTile(
                      title: const Text('Heartbeat interval'),
                      subtitle: Text(
                        '${_connectionPreferences.heartbeatSeconds} วินาที',
                      ),
                      trailing: DropdownButton<int>(
                        value: _connectionPreferences.heartbeatSeconds,
                        items: const <int>[10, 20, 30, 60]
                            .map(
                              (seconds) => DropdownMenuItem<int>(
                                value: seconds,
                                child: Text('$seconds s'),
                              ),
                            )
                            .toList(),
                        onChanged: (value) {
                          if (value == null) return;
                          _savePreferences(
                            _connectionPreferences.copyWith(
                              heartbeatSeconds: value,
                            ),
                          );
                        },
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 10),
              ValueListenableBuilder<ApiConnectionSnapshot>(
                valueListenable: apiConnectionState,
                builder: (context, connection, _) {
                  return Card(
                    child: ListTile(
                      leading: Icon(
                        connection.phase == ApiConnectionPhase.connected
                            ? Icons.cloud_done_outlined
                            : connection.phase == ApiConnectionPhase.reconnecting
                                ? Icons.sync_outlined
                                : connection.phase == ApiConnectionPhase.searching
                                    ? Icons.search_outlined
                                    : Icons.cloud_off_outlined,
                      ),
                      title: Text(connection.label),
                      subtitle: Text(
                        connection.baseUrl ?? 'ยังไม่มี endpoint',
                      ),
                      trailing: connection.latency == null
                          ? Chip(label: Text(connection.source ?? 'unknown'))
                          : Chip(
                              label: Text(
                                '${connection.latency!.inMilliseconds} ms',
                              ),
                            ),
                    ),
                  );
                },
              ),
            ],
          ),
        ),
        if (_error != null) ...<Widget>[
          const SizedBox(height: 12),
          Card(
            child: ListTile(
              leading: const Icon(Icons.error_outline),
              title: const Text('API Manager'),
              subtitle: Text(_error!),
              trailing: IconButton(
                onPressed: () => setState(() => _error = null),
                icon: const Icon(Icons.close),
              ),
            ),
          ),
        ],
        const SizedBox(height: 28),
        EnterpriseSection(
          title: 'Provider Manager',
          subtitle:
              'Provider ถูกจัดการจาก Backend; Flutter แสดงเฉพาะสถานะและตัวเลือกที่พร้อมใช้',
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: <Widget>[
              if (_loading) const LinearProgressIndicator(),
              if (!_loading && _providers.isNotEmpty) ...<Widget>[
                EnterpriseStatusTile(
                  icon: Icons.smart_toy_outlined,
                  title: 'Active Provider',
                  value: _activeProvider,
                  caption: 'Backend managed',
                ),
                const SizedBox(height: 10),
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
            ],
          ),
        ),
        const SizedBox(height: 28),
        const EnterpriseSection(
          title: 'Security & storage',
          subtitle: 'ค่าใช้งานของแอปแยกจาก Secret และข้อมูล Backend',
          child: Column(
            children: <Widget>[
              Card(
                child: ListTile(
                  leading: Icon(Icons.storage_outlined),
                  title: Text('Local-first storage ready'),
                  subtitle: Text(
                    'ข้อมูล runtime และ configuration ถูกออกแบบให้แยกจาก Secret',
                  ),
                ),
              ),
              SizedBox(height: 8),
              Card(
                child: ListTile(
                  leading: Icon(Icons.security_outlined),
                  title: Text('Secrets stay on the backend'),
                  subtitle: Text(
                    'Flutter จะไม่จัดเก็บ API key หรือ token ของ Provider',
                  ),
                  trailing: Chip(label: Text('Protected')),
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }
}
