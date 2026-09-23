import 'dart:async';

import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';

import '../../api/api_endpoint_store.dart';
import '../../api/research_os_api_client.dart';

class LoginPage extends StatefulWidget {
  const LoginPage({
    required this.apiClient,
    required this.onAuthenticated,
    required this.onConnectionChanged,
    required this.connectionProfile,
    super.key,
  });

  final ResearchOSApiClient apiClient;
  final VoidCallback onAuthenticated;
  final Future<void> Function(String baseUrl) onConnectionChanged;
  final String connectionProfile;

  @override
  State<LoginPage> createState() => _LoginPageState();
}

class _LoginPageState extends State<LoginPage> {
  List<Map<String, dynamic>> _providers = const <Map<String, dynamic>>[];
  bool _loading = true;
  String? _busyProvider;
  String? _message;
  bool _error = false;

  @override
  void initState() {
    super.initState();
    _loadProviders();
  }

  Future<void> _loadProviders() async {
    try {
      final response = await widget.apiClient.getIdentityProviders();
      final raw = response['providers'];
      final providers = raw is List
          ? raw.whereType<Map>().map((item) {
              return Map<String, dynamic>.from(
                item.map((key, value) => MapEntry(key.toString(), value)),
              );
            }).where((item) => item['available'] == true).toList(growable: false)
          : const <Map<String, dynamic>>[];
      if (!mounted) return;
      setState(() {
        _providers = providers;
        _loading = false;
      });
    } on Object catch (error) {
      if (!mounted) return;
      setState(() {
        _loading = false;
        _error = true;
        _message = error.toString();
      });
    }
  }

  Future<void> _login(Map<String, dynamic> provider) async {
    final id = provider['id']?.toString().trim() ?? '';
    final name = provider['name']?.toString().trim() ?? id;
    if (id.isEmpty || _busyProvider != null) return;
    setState(() {
      _busyProvider = id;
      _message = null;
      _error = false;
    });
    try {
      final response = await widget.apiClient.startProviderLogin(id);
      final state = response['state']?.toString().trim() ?? '';
      final rawUrl = response['authorization_url']?.toString().trim() ?? '';
      final uri = Uri.tryParse(rawUrl);
      if (state.isEmpty || uri == null || !uri.hasScheme) {
        throw const ResearchOSApiException(
          'Research OS ไม่ได้รับ OAuth state หรือ authorization URL ที่ถูกต้อง',
        );
      }
      final opened = await launchUrl(uri, mode: LaunchMode.externalApplication);
      if (!opened) {
        throw ResearchOSApiException('เปิด $name Sign-In ไม่สำเร็จ');
      }
      setState(() {
        _message = 'กรุณาเข้าสู่ระบบในเบราว์เซอร์ กำลังรอการยืนยัน…';
      });
      if (await _waitForHandoff(state)) {
        if (mounted) widget.onAuthenticated();
      } else {
        throw const ResearchOSApiException(
          'การเข้าสู่ระบบหมดเวลา กรุณาลองใหม่อีกครั้ง',
        );
      }
    } on Object catch (error) {
      if (!mounted) return;
      setState(() {
        _error = true;
        _message = error.toString();
      });
    } finally {
      if (mounted) setState(() => _busyProvider = null);
    }
  }

  Future<bool> _waitForHandoff(String state) async {
    for (var attempt = 0; attempt < 120; attempt++) {
      await Future<void>.delayed(const Duration(seconds: 1));
      try {
        final result = await widget.apiClient.exchangeProviderHandoff(state);
        final session = result['session']?.toString().trim() ?? '';
        if (result['connected'] == true && session.isNotEmpty) {
          widget.apiClient.setSession(session);
          return true;
        }
      } on ResearchOSApiException {
        // Handoff is unavailable until the provider callback completes.
      }
      if (!mounted) return false;
    }
    return false;
  }

  Future<void> _selectConnection(String profile) async {
    if (profile == ApiEndpointStore.profileForUrl(widget.apiClient.baseUrl)) {
      return;
    }
    await widget.onConnectionChanged(ApiEndpointStore.profileUrl(profile));
  }

  IconData _providerIcon(String id) {
    switch (id) {
      case 'microsoft':
        return Icons.window;
      case 'github':
        return Icons.code;
      default:
        return Icons.account_circle_outlined;
    }
  }

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Scaffold(
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.symmetric(vertical: 24),
          child: Center(
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 560),
              child: Padding(
            padding: const EdgeInsets.all(28),
            child: Card(
              child: Padding(
                padding: const EdgeInsets.all(30),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: <Widget>[
                    Icon(Icons.hub_outlined, size: 64, color: scheme.primary),
                    const SizedBox(height: 18),
                    Text(
                      'Research OS',
                      style: Theme.of(context)
                          .textTheme
                          .headlineMedium
                          ?.copyWith(fontWeight: FontWeight.w800),
                    ),
                    const SizedBox(height: 8),
                    Text(
                      'Sign in to continue',
                      style: Theme.of(context).textTheme.bodyLarge,
                    ),
                    const SizedBox(height: 24),
                    Container(
                      decoration: BoxDecoration(
                        border: Border.all(color: Theme.of(context).dividerColor),
                        borderRadius: BorderRadius.circular(16),
                      ),
                      child: ExpansionTile(
                        initiallyExpanded: false,
                        leading: const Icon(Icons.login_outlined),
                        title: const Text(
                          'Login',
                          style: TextStyle(fontWeight: FontWeight.w700),
                        ),
                        subtitle: Text(
                          _loading
                              ? 'กำลังตรวจสอบตัวเลือกการเข้าสู่ระบบ…'
                              : 'เลือกผู้ให้บริการภายใน',
                        ),
                        childrenPadding:
                            const EdgeInsets.fromLTRB(14, 0, 14, 14),
                        children: <Widget>[
                          if (_loading)
                            const Padding(
                              padding: EdgeInsets.all(18),
                              child: CircularProgressIndicator(),
                            )
                          else if (_providers.isEmpty)
                            const Padding(
                              padding: EdgeInsets.all(18),
                              child: Text(
                                'ยังไม่มีผู้ให้บริการที่พร้อมใช้งาน',
                                textAlign: TextAlign.center,
                              ),
                            )
                          else
                            ..._providers.map(
                              (provider) => Padding(
                                padding: const EdgeInsets.only(top: 8),
                                child: SizedBox(
                                  width: double.infinity,
                                  child: OutlinedButton.icon(
                                    onPressed: _busyProvider == null
                                        ? () => _login(provider)
                                        : null,
                                    icon: _busyProvider ==
                                            provider['id']?.toString()
                                        ? const SizedBox(
                                            width: 18,
                                            height: 18,
                                            child: CircularProgressIndicator(
                                              strokeWidth: 2,
                                            ),
                                          )
                                        : Icon(
                                            _providerIcon(
                                              provider['id']?.toString() ?? '',
                                            ),
                                          ),
                                    label: Text(
                                      _busyProvider ==
                                              provider['id']?.toString()
                                          ? 'กำลังเปิด…'
                                          : 'Continue with ${provider['name']}',
                                    ),
                                  ),
                                ),
                              ),
                            ),
                        ],
                      ),
                    ),
                    const SizedBox(height: 12),
                    Container(
                      decoration: BoxDecoration(
                        border: Border.all(color: Theme.of(context).dividerColor),
                        borderRadius: BorderRadius.circular(16),
                      ),
                      child: ExpansionTile(
                        initiallyExpanded: false,
                        leading: const Icon(Icons.link_outlined),
                        title: const Text(
                          'Connection',
                          style: TextStyle(fontWeight: FontWeight.w700),
                        ),
                        subtitle: Text(
                          ApiEndpointStore.profileLabel(widget.connectionProfile),
                        ),
                        childrenPadding:
                            const EdgeInsets.fromLTRB(14, 0, 14, 14),
                        children: <Widget>[
                          RadioGroup<String>(
                            groupValue: widget.connectionProfile,
                            onChanged: (value) {
                              if (value != null) {
                                _selectConnection(value);
                              }
                            },
                            child: Column(
                              children: <Widget>[
                                RadioListTile<String>(
                                  value: ApiEndpointStore.connectionResearchOs,
                                  title: const Text('Research OS'),
                                ),
                                RadioListTile<String>(
                                  value: ApiEndpointStore.connectionDeveloperRuntime,
                                  title: const Text('Developer Runtime'),
                                ),
                              ],
                            ),
                          ),
                        ],
                      ),
                    ),
                    if (_message != null) ...<Widget>[
                      const SizedBox(height: 18),
                      Text(
                        _message!,
                        textAlign: TextAlign.center,
                        style: TextStyle(
                          color: _error ? scheme.error : scheme.primary,
                        ),
                      ),
                    ],
                  ],
                ),
              ),
            ),
          ),
        ),
      ),
    ),
  );
  ),
  );
  }
}
