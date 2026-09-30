import 'dart:async';

import 'package:flutter/material.dart';
import 'package:qr_flutter/qr_flutter.dart';

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
  bool _loading = true;
  bool _error = false;
  String? _message;
  String? _pairingId;
  String? _pairingSecret;
  String? _qrPayload;
  Timer? _pollTimer;
  bool _refreshing = false;
  String _selectedPort = ApiEndpointStore.port1Label;

  @override
  void initState() {
    super.initState();
    final currentProfile = ApiEndpointStore.profileForUrl(widget.apiClient.baseUrl);
    _selectedPort = currentProfile == ApiEndpointStore.connectionOwnerSpecial
        ? ApiEndpointStore.port2Label
        : ApiEndpointStore.port1Label;
    _startPairing();
  }

  @override
  void dispose() {
    _pollTimer?.cancel();
    super.dispose();
  }

  Future<void> _selectPort(String label) async {
    final profile = ApiEndpointStore.profileForPortLabel(label);
    final currentProfile = ApiEndpointStore.profileForUrl(widget.apiClient.baseUrl);
    if (profile == currentProfile) {
      if (mounted) setState(() => _selectedPort = label);
      return;
    }
    setState(() => _refreshing = true);
    try {
      await widget.onConnectionChanged(ApiEndpointStore.profileUrl(profile));
      if (!mounted) return;
      setState(() => _selectedPort = label);
      await _startPairing();
    } finally {
      if (mounted) setState(() => _refreshing = false);
    }
  }

  Future<void> _startPairing() async {
    _pollTimer?.cancel();
    if (mounted) {
      setState(() {
        _loading = true;
        _refreshing = true;
        _error = false;
        _message = null;
        _pairingId = null;
        _pairingSecret = null;
        _qrPayload = null;
      });
    }
    try {
      final result = await widget.apiClient.startPairing();
      final id = result['pairing_id']?.toString().trim() ?? '';
      final secret = result['pairing_secret']?.toString().trim() ?? '';
      final payload = result['qr_payload']?.toString().trim() ?? '';
      if (id.isEmpty || secret.isEmpty || payload.isEmpty) {
        throw const ResearchOSApiException('Research OS did not return a valid QR pairing payload.');
      }
      if (!mounted) return;
      setState(() {
        _loading = false;
        _refreshing = false;
        _pairingId = id;
        _pairingSecret = secret;
        _qrPayload = payload;
        _message = 'Scan this QR code with a trusted device.';
      });
      unawaited(_pollPairing());
    } on Object catch (error) {
      if (!mounted) return;
      setState(() {
        _loading = false;
        _refreshing = false;
        _error = true;
        _message = error.toString();
      });
    }
  }

  Future<void> _pollPairing() async {
    final pairingId = _pairingId;
    final secret = _pairingSecret;
    if (pairingId == null || secret == null) return;

    for (var attempt = 0; attempt < 180; attempt++) {
      if (!mounted) return;
      try {
        final status = await widget.apiClient.getPairingStatus(pairingId, secret);
        if (status['connected'] == true && status['handoff_ready'] == true) {
          final result = await widget.apiClient.exchangeProviderHandoff(secret);
          final session = result['session']?.toString().trim() ?? '';
          if (result['connected'] == true && session.isNotEmpty) {
            widget.apiClient.setSession(session);
            if (!mounted) return;
            setState(() {
              _error = false;
              _message = 'Connected';
            });
            widget.onAuthenticated();
            return;
          }
          throw const ResearchOSApiException('Research OS did not return a valid session handoff.');
        }
        final statusName = status['status']?.toString() ?? 'PENDING';
        if (statusName == 'EXPIRED' || statusName == 'CANCELLED') {
          if (!mounted) return;
          setState(() {
            _error = true;
            _message = 'QR pairing $statusName. Refresh the QR code and try again.';
          });
          return;
        }
      } on ResearchOSApiException {
        // The pairing remains pending or a one-time handoff race is still settling.
      } on Object catch (error) {
        if (!mounted) return;
        setState(() {
          _error = true;
          _message = error.toString();
        });
        return;
      }
      await Future<void>.delayed(const Duration(seconds: 1));
    }

    if (mounted) {
      setState(() {
        _error = true;
        _message = 'QR pairing expired. Refresh the QR code and try again.';
      });
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
                      crossAxisAlignment: CrossAxisAlignment.stretch,
                      children: <Widget>[
                        Icon(Icons.qr_code_2, size: 64, color: scheme.primary),
                        const SizedBox(height: 18),
                        Text(
                          'Research OS',
                          textAlign: TextAlign.center,
                          style: Theme.of(context).textTheme.headlineMedium?.copyWith(fontWeight: FontWeight.w800),
                        ),
                        const SizedBox(height: 8),
                        Text(
                          'Scan to Connect',
                          textAlign: TextAlign.center,
                          style: Theme.of(context).textTheme.titleMedium,
                        ),
                        const SizedBox(height: 24),
                        const Text('PORT', style: TextStyle(fontWeight: FontWeight.w700)),
                        const SizedBox(height: 8),
                        DropdownButtonFormField<String>(
                          key: const ValueKey('login-port-dropdown'),
                          initialValue: _selectedPort,
                          decoration: const InputDecoration(border: OutlineInputBorder()),
                          items: const <DropdownMenuItem<String>>[
                            DropdownMenuItem<String>(value: ApiEndpointStore.port1Label, child: Text(ApiEndpointStore.port1Label)),
                            DropdownMenuItem<String>(value: ApiEndpointStore.port2Label, child: Text(ApiEndpointStore.port2Label)),
                          ],
                          onChanged: _refreshing ? null : (value) {
                            if (value != null) _selectPort(value);
                          },
                        ),
                        const SizedBox(height: 24),
                        if (_qrPayload != null)
                          Center(
                            child: Semantics(
                              label: 'Research OS QR pairing code',
                              child: Container(
                                padding: const EdgeInsets.all(12),
                                decoration: BoxDecoration(
                                  color: Colors.white,
                                  borderRadius: BorderRadius.circular(16),
                                ),
                                child: QrImageView(
                                  data: _qrPayload!,
                                  version: QrVersions.auto,
                                  size: 260,
                                  gapless: false,
                                  backgroundColor: Colors.white,
                                ),
                              ),
                            ),
                          )
                        else
                          const Center(child: SizedBox(width: 48, height: 48, child: CircularProgressIndicator())),
                        const SizedBox(height: 20),
                        Text(
                          _loading ? 'Creating a secure pairing code…' : 'Scan this code with your trusted device.',
                          textAlign: TextAlign.center,
                        ),
                        if (_message != null) ...<Widget>[
                          const SizedBox(height: 12),
                          Text(
                            _message!,
                            textAlign: TextAlign.center,
                            style: TextStyle(color: _error ? scheme.error : scheme.primary),
                          ),
                        ],
                        const SizedBox(height: 22),
                        OutlinedButton.icon(
                          key: const ValueKey('refresh-qr-button'),
                          onPressed: _refreshing ? null : _startPairing,
                          icon: const Icon(Icons.refresh),
                          label: const Text('Refresh QR'),
                        ),
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
