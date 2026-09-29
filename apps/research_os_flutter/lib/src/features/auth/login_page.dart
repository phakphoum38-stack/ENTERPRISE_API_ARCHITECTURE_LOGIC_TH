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

    final currentProfile =
        ApiEndpointStore.profileForUrl(widget.apiClient.baseUrl);
    _selectedPort = currentProfile == ApiEndpointStore.connectionOwnerSpecial
        ? ApiEndpointStore.port2Label
        : ApiEndpointStore.port1Label;

    _loadProviders();
  }

  Future<void> _loadProviders() async {
    try {
      final response = await widget.apiClient.getIdentityProviders();
      final raw = response['providers'];
      final providers = raw is List
          ? raw
              .whereType<Map>()
              .map((item) {
                return Map<String, dynamic>.from(
                  item.map((key, value) => MapEntry(key.toString(), value)),
                );
              })
              .where((item) => item['available'] == true)
              .toList(growable: false)
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

  String _selectedLoginMethod = '';
  String _selectedUserLevel = '';
  String _selectedPort = ApiEndpointStore.port1Label;

  Future<void> _selectPort(String label) async {
    final profile = ApiEndpointStore.profileForPortLabel(label);
    final currentProfile =
        ApiEndpointStore.profileForUrl(widget.apiClient.baseUrl);

    if (profile == currentProfile) {
      if (mounted) {
        setState(() => _selectedPort = label);
      }
      return;
    }

    await widget.onConnectionChanged(
      ApiEndpointStore.profileUrl(profile),
    );

    if (mounted) {
      setState(() => _selectedPort = label);
    }
  }

  String _providerIdForLoginMethod(String method) {
    switch (method) {
      case ApiEndpointStore.loginWindows:
        return 'microsoft';
      case ApiEndpointStore.loginGitHub:
        return 'github';
      case ApiEndpointStore.loginGoogle:
        return 'google';
      default:
        return '';
    }
  }

  Map<String, dynamic>? _providerForLoginMethod(String method) {
    final providerId = _providerIdForLoginMethod(method);
    if (providerId.isEmpty) return null;

    for (final provider in _providers) {
      if (provider['id']?.toString().toLowerCase() == providerId) {
        return provider;
      }
    }
    return null;
  }

  Future<void> _continueLogin() async {
    final method = _selectedLoginMethod;

    if (method.isEmpty) {
      setState(() {
        _error = true;
        _message = 'Please select a login method.';
      });
      return;
    }

    if (method == ApiEndpointStore.loginNone) {
      setState(() {
        _error = false;
        _message = 'No login selected.';
      });
      return;
    }

    if (method == ApiEndpointStore.loginCustom) {
      setState(() {
        _error = false;
        _message = 'Custom login is available through the configured API.';
      });
      return;
    }

    final provider = _providerForLoginMethod(method);
    if (provider == null) {
      setState(() {
        _error = true;
        _message = 'The selected login provider is not available.';
      });
      return;
    }

    await _login(provider);
  }

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;

    const loginMethods = <String, String>{
      ApiEndpointStore.loginWindows: 'Windows',
      ApiEndpointStore.loginGitHub: 'GitHub',
      ApiEndpointStore.loginGoogle: 'Google',
      ApiEndpointStore.loginNone: 'None',
      ApiEndpointStore.loginCustom: 'Custom',
    };

    const userLevels = <String, String>{
      ApiEndpointStore.userLevelOwner: 'Owner',
      ApiEndpointStore.userLevelDeveloper: 'Developer',
      ApiEndpointStore.userLevelGeneral: 'General',
    };

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
                      crossAxisAlignment: CrossAxisAlignment.stretch,
                      children: <Widget>[
                        Icon(
                          Icons.hub_outlined,
                          size: 64,
                          color: scheme.primary,
                        ),
                        const SizedBox(height: 18),
                        Text(
                          'Research OS',
                          textAlign: TextAlign.center,
                          style: Theme.of(context)
                              .textTheme
                              .headlineMedium
                              ?.copyWith(fontWeight: FontWeight.w800),
                        ),
                        const SizedBox(height: 8),
                        Text(
                          'Sign in to continue',
                          textAlign: TextAlign.center,
                          style: Theme.of(context).textTheme.bodyLarge,
                        ),
                        const SizedBox(height: 28),

                        // --------------------------------------------------
                        // PORT
                        // --------------------------------------------------
                        const Text(
                          'PORT',
                          style: TextStyle(fontWeight: FontWeight.w700),
                        ),
                        const SizedBox(height: 8),
                        DropdownButtonFormField<String>(
                          key: const ValueKey('login-port-dropdown'),
                          initialValue: _selectedPort,
                          decoration: const InputDecoration(
                            border: OutlineInputBorder(),
                          ),
                          items: const <DropdownMenuItem<String>>[
                            DropdownMenuItem<String>(
                              value: ApiEndpointStore.port1Label,
                              child: Text(ApiEndpointStore.port1Label),
                            ),
                            DropdownMenuItem<String>(
                              value: ApiEndpointStore.port2Label,
                              child: Text(ApiEndpointStore.port2Label),
                            ),
                          ],
                          onChanged: (value) {
                            if (value != null) {
                              _selectPort(value);
                            }
                          },
                        ),

                        const SizedBox(height: 20),

                        // --------------------------------------------------
                        // LOGIN
                        // --------------------------------------------------
                        const Text(
                          'LOGIN',
                          style: TextStyle(fontWeight: FontWeight.w700),
                        ),
                        const SizedBox(height: 8),
                        DropdownButtonFormField<String>(
                          key: const ValueKey('login-method-dropdown'),
                          initialValue: _selectedLoginMethod.isEmpty
                              ? null
                              : _selectedLoginMethod,
                          decoration: const InputDecoration(
                            hintText: 'Select Login Method',
                            border: OutlineInputBorder(),
                          ),
                          items: loginMethods.entries
                              .map(
                                (entry) => DropdownMenuItem<String>(
                                  value: entry.key,
                                  child: Text(entry.value),
                                ),
                              )
                              .toList(growable: false),
                          onChanged: (value) {
                            if (value == null) return;
                            setState(() {
                              _selectedLoginMethod = value;
                              _message = null;
                              _error = false;
                            });
                          },
                        ),

                        const SizedBox(height: 20),

                        // --------------------------------------------------
                        // USER LEVEL
                        // --------------------------------------------------
                        const Text(
                          'USER LEVEL',
                          style: TextStyle(fontWeight: FontWeight.w700),
                        ),
                        const SizedBox(height: 8),
                        DropdownButtonFormField<String>(
                          key: const ValueKey('login-user-level-dropdown'),
                          initialValue: _selectedUserLevel.isEmpty
                              ? null
                              : _selectedUserLevel,
                          decoration: const InputDecoration(
                            hintText: 'Select User Level',
                            border: OutlineInputBorder(),
                          ),
                          items: userLevels.entries
                              .map(
                                (entry) => DropdownMenuItem<String>(
                                  value: entry.key,
                                  child: Text(entry.value),
                                ),
                              )
                              .toList(growable: false),
                          onChanged: (value) {
                            if (value == null) return;
                            setState(() {
                              _selectedUserLevel = value;
                              _message = null;
                              _error = false;
                            });
                          },
                        ),

                        const SizedBox(height: 24),

                        // The selected user level is UI context only.
                        // Authorization remains server-derived.
                        FilledButton.icon(
                          onPressed:
                              _busyProvider == null ? _continueLogin : null,
                          icon: _busyProvider != null
                              ? const SizedBox(
                                  width: 18,
                                  height: 18,
                                  child: CircularProgressIndicator(
                                    strokeWidth: 2,
                                  ),
                                )
                              : const Icon(Icons.login),
                          label: Text(
                            _busyProvider == null
                                ? 'Continue'
                                : 'Signing in...',
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

                        // Keep provider availability out of the primary
                        // surface. The dropdown remains the single LOGIN
                        // entry point; provider details stay folded.
                        if (_loading) ...<Widget>[
                          const SizedBox(height: 16),
                          const Center(
                            child: SizedBox(
                              width: 20,
                              height: 20,
                              child: CircularProgressIndicator(
                                strokeWidth: 2,
                              ),
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
      ),
    );
  }
}
