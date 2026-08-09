import 'package:flutter/material.dart';

import '../../api/api_endpoint_store.dart';
import '../../api/research_os_api_client.dart';
import '../../ui/enterprise_components.dart';

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
  String? _error;
  String _activeProvider = 'unknown';
  String _activeSource = 'unknown';
  String _activeReason = '';
  List<Map<String, dynamic>> _providerStatuses = const <Map<String, dynamic>>[];
  Map<String, List<String>> _capabilities = const <String, List<String>>{};
  late final TextEditingController _apiController;

  @override
  void initState() {
    super.initState();
    _apiController = TextEditingController(text: widget.apiClient.baseUrl);
    _loadProviders();
  }

  @override
  void dispose() {
    _apiController.dispose();
    super.dispose();
  }

  Future<void> _loadProviders() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final payload = await widget.apiClient.getProviderGateway();
      if (!mounted) return;
      final gateway = payload['gateway'];
      if (gateway is! Map) {
        throw const ResearchOSApiException('Research OS AI Gateway response is missing.');
      }
      final selected = gateway['selected'];
      final rawProviders = gateway['providers'];
      final rawRegistry = gateway['registry'];
      final capabilityMap = <String, List<String>>{};
      if (rawRegistry is List) {
        for (final item in rawRegistry) {
          if (item is! Map) continue;
          final name = item['name']?.toString();
          if (name == null || name.isEmpty) continue;
          final rawCapabilities = item['capabilities'];
          capabilityMap[name] = rawCapabilities is List
              ? rawCapabilities.map((value) => value.toString()).toList()
              : const <String>[];
        }
      }
      setState(() {
        _activeProvider = selected is Map ? selected['provider']?.toString() ?? 'unknown' : 'unknown';
        _activeSource = selected is Map ? selected['source']?.toString() ?? 'unknown' : 'unknown';
        _activeReason = selected is Map ? selected['reason']?.toString() ?? '' : '';
        _providerStatuses = rawProviders is List
            ? rawProviders
                .whereType<Map>()
                .map((item) => Map<String, dynamic>.from(item))
                .toList()
            : const <Map<String, dynamic>>[];
        _capabilities = capabilityMap;
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
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('บันทึก API Base URL แล้ว')));
    } on Object catch (error) {
      if (!mounted) return;
      setState(() => _error = error.toString());
    } finally {
      if (mounted) setState(() => _savingEndpoint = false);
    }
  }

  IconData _providerIcon(String state) {
    switch (state) {
      case 'available':
        return Icons.check_circle_outline;
      case 'needs_setup':
        return Icons.key_outlined;
      case 'offline':
        return Icons.cloud_off_outlined;
      default:
        return Icons.info_outline;
    }
  }

  String _providerStateLabel(String state) {
    switch (state) {
      case 'available':
        return 'Available';
      case 'needs_setup':
        return 'Needs setup';
      case 'offline':
        return 'Offline';
      default:
        return state;
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
          subtitle: 'จัดการ Appearance, API endpoint และ AI Provider โดยคง Secret ไว้ฝั่ง Backend',
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
          subtitle: 'ธีมของ Research OS Desktop',
          child: Card(
            child: Padding(
              padding: const EdgeInsets.all(18),
              child: SegmentedButton<ThemeMode>(
                segments: const <ButtonSegment<ThemeMode>>[
                  ButtonSegment<ThemeMode>(value: ThemeMode.system, icon: Icon(Icons.brightness_auto), label: Text('System')),
                  ButtonSegment<ThemeMode>(value: ThemeMode.light, icon: Icon(Icons.light_mode_outlined), label: Text('Light')),
                  ButtonSegment<ThemeMode>(value: ThemeMode.dark, icon: Icon(Icons.dark_mode_outlined), label: Text('Dark')),
                ],
                selected: <ThemeMode>{widget.themeMode},
                onSelectionChanged: (selection) {
                  if (selection.isNotEmpty) widget.onThemeModeChanged(selection.first);
                },
              ),
            ),
          ),
        ),
        const SizedBox(height: 28),
        EnterpriseSection(
          title: 'Research OS API',
          subtitle: 'สลับ Local API หรือ Cloud API ได้โดยไม่ต้อง Build แอปใหม่',
          child: Card(
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
                      labelText: 'API Base URL',
                      hintText: 'http://192.168.x.x:8787',
                      helperText: 'ใส่ URL ของ API บนเครื่อง Windows ได้ภายหลัง โดยไม่ต้อง Build แอปใหม่',
                    ),
                  ),
                  const SizedBox(height: 14),
                  Wrap(
                    spacing: 8,
                    runSpacing: 8,
                    children: <Widget>[
                      FilledButton.icon(
                        onPressed: _savingEndpoint ? null : () => _saveEndpoint(),
                        icon: _savingEndpoint
                            ? const SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2))
                            : const Icon(Icons.save_outlined),
                        label: const Text('บันทึก'),
                      ),
                      OutlinedButton.icon(
                        onPressed: _savingEndpoint ? null : () => _saveEndpoint(ApiEndpointStore.localDefault),
                        icon: const Icon(Icons.computer_outlined),
                        label: const Text('Local 127.0.0.1'),
                      ),
                      OutlinedButton.icon(
                        onPressed: _savingEndpoint ? null : () => _saveEndpoint(ApiEndpointStore.renderDefault),
                        icon: const Icon(Icons.cloud_outlined),
                        label: const Text('Render'),
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
        ),
        const SizedBox(height: 28),
        EnterpriseSection(
          title: 'Provider Manager',
          subtitle: 'AI Gateway ตรวจหาและเลือก Provider; Flutter แสดงสถานะโดยไม่รับหรือเปิดเผย Secret',
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: <Widget>[
              if (_loading) const LinearProgressIndicator(),
              if (_error != null)
                Card(
                  child: ListTile(
                    leading: const Icon(Icons.error_outline),
                    title: const Text('โหลด Provider ไม่สำเร็จ'),
                    subtitle: Text(_error!),
                    trailing: IconButton(onPressed: _loadProviders, icon: const Icon(Icons.refresh)),
                  ),
                ),
              if (!_loading && _error == null) ...<Widget>[
                EnterpriseStatusTile(
                  icon: Icons.smart_toy_outlined,
                  title: 'Selected Provider',
                  value: _activeProvider,
                  caption: 'Source: $_activeSource${_activeReason.isEmpty ? '' : ' • $_activeReason'}',
                ),
                const SizedBox(height: 12),
                ..._providerStatuses.map((provider) {
                  final name = provider['provider']?.toString() ?? 'unknown';
                  final state = provider['state']?.toString() ?? 'unknown';
                  final source = provider['source']?.toString() ?? 'unknown';
                  final ready = provider['ready'] == true;
                  final credentialPresent = provider['credential_present'] == true;
                  final capabilities = _capabilities[name] ?? const <String>[];
                  final endpoint = provider['endpoint']?.toString();
                  return Padding(
                    padding: const EdgeInsets.only(bottom: 8),
                    child: Card(
                      key: Key('provider-status-$name'),
                      child: ListTile(
                        leading: Icon(_providerIcon(state)),
                        title: Row(
                          children: <Widget>[
                            Expanded(child: Text(name)),
                            if (name == _activeProvider) const Chip(label: Text('Selected')),
                          ],
                        ),
                        subtitle: Text(
                          '${_providerStateLabel(state)} • source: $source'
                          '${credentialPresent ? ' • credential detected' : ''}'
                          '${capabilities.isEmpty ? '' : ' • ${capabilities.join(', ')}'}'
                          '${endpoint == null || endpoint.isEmpty ? '' : '\n$endpoint'}',
                        ),
                        trailing: Icon(ready ? Icons.check_circle : Icons.remove_circle_outline),
                      ),
                    ),
                  );
                }),
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
              Card(child: ListTile(leading: Icon(Icons.storage_outlined), title: Text('Local-first storage ready'), subtitle: Text('เมื่อรัน API บน Windows ให้ RESEARCH_OS_DATA_DIR ชี้ไปยังพื้นที่ข้อมูลบนเครื่อง'))),
              SizedBox(height: 8),
              Card(child: ListTile(leading: Icon(Icons.security_outlined), title: Text('Secrets stay on the backend'), subtitle: Text('Flutter ไม่จัดเก็บหรือแสดง Gemini API key, OpenAI key, GitHub token หรือ Google refresh token'), trailing: Chip(label: Text('Protected')))),
            ],
          ),
        ),
      ],
    );
  }
}
