import 'package:flutter/material.dart';

import '../../api/provider_selection_store.dart';
import '../../api/research_os_api_client.dart';

class ProviderManagerSection extends StatefulWidget {
  const ProviderManagerSection({required this.apiClient, super.key});

  final ResearchOSApiClient apiClient;

  @override
  State<ProviderManagerSection> createState() => _ProviderManagerSectionState();
}

class _ProviderManagerSectionState extends State<ProviderManagerSection> {
  bool _loading = true;
  bool _saving = false;
  String? _error;
  String _backendDefault = 'unknown';
  List<String> _providers = const <String>[];

  @override
  void initState() {
    super.initState();
    selectedProviderState.addListener(_selectionChanged);
    _load();
  }

  @override
  void dispose() {
    selectedProviderState.removeListener(_selectionChanged);
    super.dispose();
  }

  void _selectionChanged() {
    if (mounted) setState(() {});
  }

  Future<void> _load() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      await ProviderSelectionStore.loadIntoState();
      final payload = await widget.apiClient.getProviders();
      if (!mounted) return;
      final raw = payload['providers'];
      final providers = raw is List
          ? raw.map((item) => item.toString()).toSet().toList()
          : <String>[];
      final selected = selectedProviderState.value;
      if (selected.isNotEmpty && !providers.contains(selected)) {
        providers.insert(0, selected);
      }
      setState(() {
        _backendDefault = payload['active']?.toString() ?? 'unknown';
        _providers = providers;
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

  Future<void> _select(String provider) async {
    if (_saving || provider == selectedProviderState.value) return;
    setState(() {
      _saving = true;
      _error = null;
    });
    try {
      await ProviderSelectionStore.save(provider);
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('เปลี่ยน AI Provider เป็น $provider แล้ว'),
        ),
      );
    } on Object catch (error) {
      if (!mounted) return;
      setState(() => _error = error.toString());
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final selected = selectedProviderState.value;
    final scheme = Theme.of(context).colorScheme;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: <Widget>[
        Card(
          child: ListTile(
            leading: const Icon(Icons.smart_toy_outlined),
            title: const Text('Selected Provider'),
            subtitle: Text(
              'Chat requests จะใช้ Provider นี้ทันที • Backend default: $_backendDefault',
            ),
            trailing: Chip(
              avatar: const Icon(Icons.check_circle_outline, size: 17),
              label: Text(selected),
            ),
          ),
        ),
        const SizedBox(height: 10),
        if (_loading) const LinearProgressIndicator(),
        if (!_loading)
          Card(
            child: Column(
              children: _providers.map((provider) {
                final active = provider == selected;
                return RadioListTile<String>(
                  key: Key('provider-option-$provider'),
                  value: provider,
                  groupValue: selected,
                  onChanged: _saving
                      ? null
                      : (value) {
                          if (value != null) _select(value);
                        },
                  secondary: Icon(
                    active ? Icons.bolt : Icons.smart_toy_outlined,
                    color: active ? scheme.primary : null,
                  ),
                  title: Text(
                    provider,
                    style: TextStyle(
                      fontWeight: active ? FontWeight.w700 : FontWeight.w500,
                    ),
                  ),
                  subtitle: Text(
                    provider == _backendDefault
                        ? 'พร้อมใช้งาน • Backend default'
                        : 'พร้อมใช้งานผ่าน Research OS provider routing',
                  ),
                );
              }).toList(),
            ),
          ),
        if (_error != null) ...<Widget>[
          const SizedBox(height: 10),
          Card(
            child: ListTile(
              leading: Icon(Icons.error_outline, color: scheme.error),
              title: const Text('Provider Manager'),
              subtitle: Text(_error!),
              trailing: IconButton(
                tooltip: 'ลองใหม่',
                onPressed: _loading ? null : _load,
                icon: const Icon(Icons.refresh),
              ),
            ),
          ),
        ],
        const SizedBox(height: 10),
        const Text(
          'API keys และ provider secrets ยังคงอยู่ฝั่ง Backend; แอปบันทึกเฉพาะชื่อ Provider ที่เลือกเท่านั้น.',
        ),
      ],
    );
  }
}
