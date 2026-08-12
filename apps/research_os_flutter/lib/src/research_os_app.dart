import 'dart:async';

import 'package:flutter/material.dart';

import 'api/api_endpoint_store.dart';
import 'api/local_companion_probe.dart';
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
    unawaited(probeLocalCompanionService());
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

  ThemeData _buildTheme(Brightness brightness) {
    final dark = brightness == Brightness.dark;
    final scheme = ColorScheme.fromSeed(
      seedColor: const Color(0xFF1976D2),
      brightness: brightness,
      surface: dark ? const Color(0xFF101419) : const Color(0xFFF7F9FC),
    );

    final borderColor = dark
        ? Colors.white.withValues(alpha: .10)
        : Colors.black.withValues(alpha: .08);

    return ThemeData(
      useMaterial3: true,
      brightness: brightness,
      colorScheme: scheme,
      scaffoldBackgroundColor: dark
          ? const Color(0xFF0C1015)
          : const Color(0xFFF3F6FA),
      dividerColor: borderColor,
      appBarTheme: AppBarTheme(
        elevation: 0,
        scrolledUnderElevation: 0,
        centerTitle: false,
        backgroundColor: dark
            ? const Color(0xFF101419)
            : const Color(0xFFFDFEFF),
        surfaceTintColor: Colors.transparent,
        titleTextStyle: TextStyle(
          color: scheme.onSurface,
          fontSize: 18,
          fontWeight: FontWeight.w700,
        ),
      ),
      cardTheme: CardThemeData(
        elevation: 0,
        margin: EdgeInsets.zero,
        color: dark ? const Color(0xFF151A21) : Colors.white,
        surfaceTintColor: Colors.transparent,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(16),
          side: BorderSide(color: borderColor),
        ),
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: dark ? const Color(0xFF151A21) : Colors.white,
        contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 13),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: BorderSide(color: borderColor),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: BorderSide(color: borderColor),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: BorderSide(color: scheme.primary, width: 1.4),
        ),
      ),
      filledButtonTheme: FilledButtonThemeData(
        style: FilledButton.styleFrom(
          padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 13),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
        ),
      ),
      outlinedButtonTheme: OutlinedButtonThemeData(
        style: OutlinedButton.styleFrom(
          padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 13),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
          side: BorderSide(color: borderColor),
        ),
      ),
      chipTheme: ChipThemeData(
        side: BorderSide(color: borderColor),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
      ),
      listTileTheme: ListTileThemeData(
        contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 2),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      ),
    );
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
