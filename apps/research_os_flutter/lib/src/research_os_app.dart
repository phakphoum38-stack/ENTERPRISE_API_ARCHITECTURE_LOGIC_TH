import 'package:flutter/material.dart';

import 'api/api_endpoint_store.dart';
import 'api/research_os_api_client.dart';
import 'app_shell.dart';
import 'features/auth/login_page.dart';
import 'ui/research_os_design_tokens.dart';

class ResearchOSApp extends StatefulWidget {
  const ResearchOSApp({super.key});

  @override
  State<ResearchOSApp> createState() => _ResearchOSAppState();
}

class _ResearchOSAppState extends State<ResearchOSApp> {
  ThemeMode _themeMode = ThemeMode.system;
  ResearchOSApiClient? _apiClient;
  String? _apiBaseUrl;
  bool? _authenticated;

  @override
  void initState() {
    super.initState();
    _loadApiEndpoint();
  }

  Future<void> _loadApiEndpoint() async {
    final url = await ApiEndpointStore.load();
    if (!mounted) return;
    final client = ResearchOSApiClient(baseUrl: url);
    bool authenticated = false;
    try {
      final status = await client.getAuthStatus();
      authenticated = status['connected'] == true;
    } on Object {
      authenticated = false;
    }
    if (!mounted) {
      client.close();
      return;
    }
    setState(() {
      _apiBaseUrl = url;
      _apiClient = client;
      _authenticated = authenticated;
    });
  }

  Future<void> _changeApiEndpoint(String value) async {
    final normalized = ApiEndpointStore.normalize(value);
    await ApiEndpointStore.save(normalized);
    final previous = _apiClient;
    if (!mounted) return;
    final client = ResearchOSApiClient(baseUrl: normalized);
    setState(() {
      _apiBaseUrl = normalized;
      _apiClient = client;
      _authenticated = false;
    });
    previous?.close();
  }

  ThemeData _buildTheme(Brightness brightness) {
    if (brightness == Brightness.dark) {
      return ResearchOSDesignTokens.darkTheme();
    }
    return ResearchOSDesignTokens.lightTheme();
  }

  @override
  void dispose() {
    _apiClient?.close();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final apiClient = _apiClient;

    return MaterialApp(
      debugShowCheckedModeBanner: false,
      title: 'Research OS',
      theme: _buildTheme(Brightness.light),
      darkTheme: _buildTheme(Brightness.dark),
      themeMode: _themeMode,
      home: apiClient == null || _apiBaseUrl == null || _authenticated == null
          ? const Scaffold(
              body: Center(child: CircularProgressIndicator()),
            )
          : _authenticated!
              ? ResearchOSAppShell(
              key: ValueKey(_apiBaseUrl),
              apiClient: apiClient,
              themeMode: _themeMode,
              onThemeModeChanged: (value) {
                setState(() => _themeMode = value);
              },
              onApiBaseUrlChanged: _changeApiEndpoint,
            )
                      : LoginPage(
                  key: ValueKey(_apiBaseUrl),
                  apiClient: apiClient,
                  connectionProfile: ApiEndpointStore.profileForUrl(_apiBaseUrl!),
                  onConnectionChanged: _changeApiEndpoint,
                  onAuthenticated: () {
                    setState(() => _authenticated = true);
                  },
                ),
    );
  }
}
