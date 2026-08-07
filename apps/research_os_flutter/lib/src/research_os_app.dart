import 'package:flutter/material.dart';

import 'api/api_endpoint_store.dart';
import 'api/research_os_api_client.dart';
import 'app_shell.dart';

class ResearchOSApp extends StatefulWidget {
  const ResearchOSApp({super.key});

  @override
  State<ResearchOSApp> createState() => _ResearchOSAppState();
}

class _ResearchOSAppState extends State<ResearchOSApp> {
  ThemeMode _themeMode = ThemeMode.system;
  ResearchOSApiClient? _apiClient;
  String? _apiBaseUrl;

  @override
  void initState() {
    super.initState();
    _loadApiEndpoint();
  }

  Future<void> _loadApiEndpoint() async {
    final url = await ApiEndpointStore.load();
    if (!mounted) return;
    setState(() {
      _apiBaseUrl = url;
      _apiClient = ResearchOSApiClient(baseUrl: url);
    });
  }

  Future<void> _changeApiEndpoint(String value) async {
    final normalized = ApiEndpointStore.normalize(value);
    await ApiEndpointStore.save(normalized);
    final previous = _apiClient;
    if (!mounted) return;
    setState(() {
      _apiBaseUrl = normalized;
      _apiClient = ResearchOSApiClient(baseUrl: normalized);
    });
    previous?.close();
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
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.indigo),
        useMaterial3: true,
      ),
      darkTheme: ThemeData(
        colorScheme: ColorScheme.fromSeed(
          seedColor: Colors.indigo,
          brightness: Brightness.dark,
        ),
        useMaterial3: true,
      ),
      themeMode: _themeMode,
      home: apiClient == null || _apiBaseUrl == null
          ? const Scaffold(
              body: Center(child: CircularProgressIndicator()),
            )
          : ResearchOSAppShell(
              key: ValueKey(_apiBaseUrl),
              apiClient: apiClient,
              themeMode: _themeMode,
              onThemeModeChanged: (value) {
                setState(() => _themeMode = value);
              },
              onApiBaseUrlChanged: _changeApiEndpoint,
            ),
    );
  }
}
